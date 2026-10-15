import base64
import os
import shutil
import tempfile
from uuid import UUID, uuid4
from typing import Optional
import cv2
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Header, BackgroundTasks, Request
from fastapi.responses import FileResponse
import numpy as np
from pydantic import BaseModel

from corpocmente.infrastructure.ai.adapters import GeminiApiAdapter
from corpocmente.application.use_cases.ingest_knowledge_use_case import IngestKnowledgeUseCase
from corpocmente.application.dtos.knowledge_dtos import IngestionRequest
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.ui.api.auth_routes import require_auth, require_admin
from corpocmente.config import settings
from corpocmente.domain.services.session_manager import (
    SessionStateManager, SessionError, SessionConflictError,
    SessionNotFoundError, SessionExpiredError
)

_yolo_pose_model = None

def get_yolo_pose_model():
    global _yolo_pose_model
    if _yolo_pose_model is None:
        import torch
        from ultralytics import YOLO
        _orig_torch_load = torch.load
        def _safe_torch_load(*args, **kwargs):
            kwargs["weights_only"] = False
            return _orig_torch_load(*args, **kwargs)
        torch.load = _safe_torch_load
        _yolo_pose_model = YOLO("yolo26n-pose.pt")
    return _yolo_pose_model

router = APIRouter(prefix="/api/v1", tags=["Evaluaciones", "Conocimiento"])

class ResultadoWorkerDTO(BaseModel):
    similitud: float
    feedback: str
    estado: str


VIDEOS_DIR = "/tmp/corpocmente_videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)
FRAMES_DIR = "/tmp/corpocmente_frames"
os.makedirs(FRAMES_DIR, exist_ok=True)

def get_db():
    return PostgrestClient()

def require_worker(x_worker_token: Optional[str] = Header(None)) -> None:
    """
    Verifica que el header X-Worker-Token coincida con el token de servicio configurado.
    El Worker de Colab no tiene token de usuario; usa un shared secret.
    """
    if not x_worker_token or x_worker_token != settings.WORKER_SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de Worker inválido o ausente."
        )

def ejecutar_evaluacion_background(
    eval_id: str,
    video_alumno_path: str,
    tecnica_id: UUID,
    tecnica_nombre: str,
    video_referencia_path: Optional[str],
    persona_idx: Optional[int] = None,
    session_id: Optional[str] = None
):
    import logging
    logger = logging.getLogger(__name__)
    try:
        from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
        from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
        from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
        from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
        from corpocmente.domain.services.session_manager import SessionStateManager

        yolo = YOLOPoseAdapter()
        qdrant = QdrantVectorAdapter()
        gemini = GeminiApiAdapter()
        qwen = QwenEmbeddingAdapter()

        facade = IntelligenceAnalysisFacade(
            yolo_adapter=yolo,
            qdrant_adapter=qdrant,
            gemini_adapter=gemini,
            qwen_adapter=qwen
        )

        res = facade.ejecutar_analisis_completo(
            video_path=video_alumno_path,
            tecnica_id=tecnica_id,
            tecnica_nombre=tecnica_nombre,
            video_referencia_path=video_referencia_path,
            evaluacion_id=eval_id,
            persona_idx=persona_idx
        )

        db = get_db()
        db.rpc("worker_update_result", {
            "p_evaluacion_id": str(eval_id),
            "p_similitud": res.similitud,
            "p_feedback_es": res.feedback,
            "p_estado": "completado"
        })
        if session_id:
            SessionStateManager.finalizar_operacion(session_id, exito=True, eliminar_video=False)
        logger.info(f"Evaluación {eval_id} completada en background con similitud {res.similitud}%.")
    except Exception as e:
        logger.error(f"Error procesando evaluación {eval_id} en background: {e}", exc_info=True)
        if session_id:
            try:
                from corpocmente.domain.services.session_manager import SessionStateManager
                SessionStateManager.finalizar_operacion(session_id, exito=False, error=str(e), eliminar_video=False)
            except Exception:
                pass
        try:
            db = get_db()
            db.rpc("worker_update_result", {
                "p_evaluacion_id": str(eval_id),
                "p_similitud": 0.0,
                "p_feedback_es": f"Ocurrió un error al procesar el análisis biomecánico: {str(e)}",
                "p_estado": "error"
            })
        except Exception:
            pass

@router.post("/evaluaciones/analizar", status_code=status.HTTP_200_OK)
async def analizar_video(
    background_tasks: BackgroundTasks,
    tecnica_id: UUID = Form(...),
    tecnica_nombre: str = Form(...),
    profesor_id: Optional[UUID] = Form(None),
    video: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None),
    persona_idx: Optional[int] = Form(None),
    alumno_id: UUID = Form(...),
    authorization: Optional[str] = Header(None)
):
    caller = require_auth(authorization)

    # Autorización: solo el propio alumno o un admin pueden crear evaluaciones
    if caller.get("role") != "admin" and str(caller.get("uid")) != str(alumno_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes crear evaluaciones a nombre de otro usuario."
        )

    db = get_db()

    # 1. Verificar si existe patrón activo en PostgreSQL / Qdrant
    from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
    qdrant = QdrantVectorAdapter()
    patron_id = qdrant._get_patron_activo_db(tecnica_id)
    video_ref_id = None
    video_ref_path = None

    try:
        if profesor_id:
            videos_ref = db.rpc("get_video_referencia_by_tecnica_profesor", {
                "p_tecnica_id": str(tecnica_id),
                "p_profesor_id": str(profesor_id),
            })
        else:
            videos_ref = db.rpc("get_video_referencia_by_tecnica", {
                "p_tecnica_id": str(tecnica_id)
            })
        if videos_ref:
            video_ref_id = videos_ref[0]["id"]
            video_ref_path = videos_ref[0].get("url_video_gcs")
    except Exception:
        videos_ref = []

    if not patron_id and not videos_ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un patrón biomecánico activo registrado para esta técnica."
        )

    # 2. Resolver sesión o video directo
    from corpocmente.domain.services.session_manager import (
        SessionStateManager, SessionState, SessionConflictError, SessionNotFoundError, SessionExpiredError
    )
    target_persona_idx = None
    eval_id = str(uuid4())

    if session_id:
        try:
            sesion = SessionStateManager.obtener_sesion(session_id)
        except SessionNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada.")
        except SessionExpiredError:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Sesión expirada.")

        if sesion.get("estado") != SessionState.PERSONA_SELECTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"La sesión está en estado '{sesion.get('estado')}'. Se requiere confirmación de persona previa."
            )

        target_persona_idx = sesion.get("persona_idx_seleccionada")
        if persona_idx is not None and persona_idx != target_persona_idx:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El persona_idx ({persona_idx}) no coincide con el seleccionado en la sesión ({target_persona_idx})."
            )

        video_path = sesion.get("video_path")
        try:
            SessionStateManager.iniciar_operacion(session_id, tecnica_id=str(tecnica_id))
        except SessionConflictError as e_conf:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e_conf))
    elif video:
        if not video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de archivo no soportado. Debe ser un video (MP4, AVI, MOV, MKV)."
            )
        video_path = os.path.join(VIDEOS_DIR, f"{eval_id}.mp4")
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)

        target_persona_idx = persona_idx if persona_idx is not None else 0
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar session_id o subir un archivo de video."
        )

    # 3. Registrar en base de datos
    try:
        created = db.rpc("create_evaluacion", {
            "p_id": eval_id,
            "p_alumno_id": str(alumno_id),
            "p_tecnica_id": str(tecnica_id),
            "p_video_referencia_id": str(video_ref_id) if video_ref_id else None,
            "p_url_video_alumno": video_path
        })
    except Exception as e:
        if session_id:
            SessionStateManager.finalizar_operacion(session_id, exito=False, error=str(e), eliminar_video=False)
        raise HTTPException(status_code=500, detail=f"Error creando evaluación: {e}")

    # 4. Iniciar análisis en segundo plano
    background_tasks.add_task(
        ejecutar_evaluacion_background,
        eval_id,
        video_path,
        tecnica_id,
        tecnica_nombre,
        video_ref_path,
        target_persona_idx,
        session_id
    )

    return {"evaluacion_id": eval_id, "estado": "procesando"}

# --- Endpoints para el Worker de Colab Web ---

@router.get("/evaluaciones/pendientes")
async def listar_pendientes(x_worker_token: Optional[str] = Header(None)):
    """El Worker de Colab consulta esto para obtener la siguiente tarea."""
    require_worker(x_worker_token)
    db = get_db()
    try:
        pendientes = db.rpc("worker_claim_next_pending", {})
    except Exception:
        pendientes = []

    if not pendientes:
        return None

    eval_data = pendientes[0]
    return {
        "id": eval_data["id"],
        "video_path": eval_data["video_path"],
        "tecnica_id": eval_data["tecnica_id"],
        "tecnica_nombre": eval_data["tecnica_nombre"],
        "estado": eval_data["estado"]
    }

@router.get("/evaluaciones/video/{evaluacion_id}")
async def descargar_video_alumno(evaluacion_id: UUID, x_worker_token: Optional[str] = Header(None)):
    """El Worker descarga el archivo de video del alumno."""
    require_worker(x_worker_token)
    db = get_db()
    try:
        rows = db.rpc("worker_get_video_path", {"p_evaluacion_id": str(evaluacion_id)})
    except Exception:
        rows = []

    if not rows:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    video_path = rows[0]["video_path"]
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video no encontrado localmente")

    return FileResponse(video_path, media_type="video/mp4", filename=f"{evaluacion_id}.mp4")

@router.post("/evaluaciones/resultado/{evaluacion_id}")
async def recibir_resultado(
    evaluacion_id: UUID,
    payload: ResultadoWorkerDTO,
    x_worker_token: Optional[str] = Header(None)
):
    """El Worker POSTea el resultado final."""
    require_worker(x_worker_token)
    db = get_db()
    try:
        updated_ok = db.rpc("worker_update_result", {
            "p_evaluacion_id": str(evaluacion_id),
            "p_similitud": payload.similitud,
            "p_feedback_es": payload.feedback,
            "p_estado": payload.estado
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando resultado: {e}")

    if not updated_ok:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    return {"status": "ok"}

@router.get("/evaluaciones/{evaluacion_id}")
async def consultar_evaluacion(
    evaluacion_id: UUID,
    authorization: Optional[str] = Header(None)
):
    """El frontend consulta el estado de una evaluación (polling)."""
    caller = require_auth(authorization)

    db = get_db()
    try:
        evaluaciones = db.rpc("get_evaluacion_by_id", {
            "p_evaluacion_id": str(evaluacion_id)
        })
    except Exception:
        evaluaciones = []

    if not evaluaciones:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    eval_data = evaluaciones[0]

    # Autorización: solo el dueño de la evaluación o un admin
    if caller.get("role") != "admin" and str(caller.get("uid")) != str(eval_data["alumno_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar esta evaluación."
        )

    # Convertir ruta local del video de referencia a URL pública estática
    raw_video_path = eval_data.get("video_referencia_url") or ""
    video_ref_url = None
    if raw_video_path:
        filename = os.path.basename(raw_video_path)
        video_ref_url = f"/static/videos/{filename}"

    # Fotograma crítico anotado con el error si ya fue procesado
    frame_error_url = None
    frame_candidate = os.path.join(FRAMES_DIR, f"critico_{evaluacion_id}.jpg")
    if os.path.exists(frame_candidate):
        frame_error_url = f"/static/frames/critico_{evaluacion_id}.jpg"

    return {
        "id": eval_data["id"],
        "estado": eval_data["estado"],
        "similitud": eval_data["porcentaje_similitud"],
        "feedback": eval_data["feedback_gemini_es"] or eval_data["feedback_gemini_pt"],
        "tecnica_id": eval_data["tecnica_id"],
        "tecnica_nombre": eval_data["tecnica_nombre"],
        "video_referencia_url": video_ref_url,
        "video_referencia_profesor_nombre": eval_data.get("video_referencia_profesor_nombre"),
        "frame_error_url": frame_error_url,
    }

@router.post("/evaluaciones/validar-spam", status_code=status.HTTP_200_OK)
async def validar_spam(video: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    """
    Endpoint HTTP aislado para validar tempranamente si un video es de Jiu-Jitsu (SPAM filter).
    Requiere cualquier usuario autenticado.
    """
    require_auth(authorization)

    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        shutil.copyfileobj(video.file, temp_video)
        temp_video_path = temp_video.name

    try:
        gemini_adapter = GeminiApiAdapter()
        es_valido = gemini_adapter.validar_es_jiujitsu(temp_video_path)
        if not es_valido:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El video proporcionado no parece estar relacionado con Jiu-Jitsu o Grappling."
            )
        return {"status": "ok", "message": "El video es válido."}
    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)


# --- Endpoints de Ingestión de Conocimiento (RAG) ---

@router.post("/conocimiento/teoria", status_code=status.HTTP_201_CREATED)
async def ingerir_teoria(payload: IngestionRequest, authorization: Optional[str] = Header(None)):
    """
    Endpoint HTTP: Ingestión de teoría del profesor al sistema RAG.
    Persiste tanto en Qdrant (vectores) como en PostgreSQL (metadata).
    """
    caller = require_auth(authorization)
    if caller.get("role") not in ("admin", "profesor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de profesor o administrador."
        )

    use_case = IngestKnowledgeUseCase()
    resultado = use_case.execute(
        tecnica_id=payload.tecnica_id,
        contenido_texto=payload.contenido_texto,
        profesor_id=caller.get("uid"),
        sucursal_id=caller.get("sucursal_id"),
    )
    return {"status": "ok", "chunks_procesados": resultado.chunks_procesados}


from corpocmente.application.use_cases.list_theory_use_case import ListTheoryUseCase
from corpocmente.application.use_cases.delete_theory_use_case import DeleteTheoryUseCase


@router.get("/conocimiento/teoria/{tecnica_id}", status_code=status.HTTP_200_OK)
async def listar_teoria(
    tecnica_id: UUID,
    solo_mios: bool = False,
    authorization: Optional[str] = Header(None)
):
    """
    Endpoint HTTP: Lista los chunks de teoría de una técnica.

    - Cualquier usuario autenticado puede ver el material de una técnica.
    - Con ?solo_mios=true, un profesor ve únicamente sus propios aportes.
    """
    caller = require_auth(authorization)

    profesor_id = caller.get("uid") if solo_mios else None

    use_case = ListTheoryUseCase()
    chunks = use_case.execute(tecnica_id=str(tecnica_id), profesor_id=profesor_id)

    return {
        "tecnica_id": str(tecnica_id),
        "total": len(chunks),
        "chunks": chunks,
    }


@router.delete("/conocimiento/teoria/{tecnica_id}", status_code=status.HTTP_200_OK)
async def eliminar_teoria(
    tecnica_id: UUID,
    authorization: Optional[str] = Header(None)
):
    """
    Endpoint HTTP: Elimina TODA la teoría que el profesor autenticado subió
    para esta técnica (en Postgres y en Qdrant).
    """
    caller = require_auth(authorization)
    if caller.get("role") not in ("admin", "profesor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de profesor o administrador."
        )

    use_case = DeleteTheoryUseCase()
    resultado = use_case.execute(
        tecnica_id=str(tecnica_id),
        profesor_id=caller.get("uid"),
    )
    return {"status": "ok", **resultado}


@router.post("/evaluaciones/primer-frame", status_code=status.HTTP_200_OK)
async def obtener_primer_frame(
    video: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Extrae el primer fotograma con detecciones válidas de personas (buscando en [0, 15, 30, 45, 60]),
    guarda el video en /tmp/corpocmente_videos/{session_id}.mp4 y devuelve bboxes con padding del 15%
    y la imagen en Base64 para el selector interactivo.
    """
    require_auth(authorization)

    if not video.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado. Debe ser un video (MP4, AVI, MOV, MKV)."
        )

    session_id = str(uuid4())
    video_path = os.path.join(VIDEOS_DIR, f"{session_id}.mp4")

    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    yolo = get_yolo_pose_model()
    target_frames = [0, 15, 30, 45, 60]

    cap = cv2.VideoCapture(video_path)
    try:
        frame_idx_encontrado = None
        frame_encontrado = None
        personas_encontradas = []

        for target in target_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, target)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            results = yolo.predict(source=frame, conf=0.15, verbose=False)
            if not results or results[0].keypoints is None or len(results[0].keypoints.data) == 0:
                continue

            raw_personas = results[0].keypoints.data.cpu().numpy()
            valid_personas = []
            for p in raw_personas:
                if p.shape == (17, 3) and np.count_nonzero((p[:, 2] > 0.3) & (p[:, 0] > 0)) >= 4:
                    valid_personas.append(p)

            if valid_personas:
                frame_idx_encontrado = target
                frame_encontrado = frame
                h_img, w_img = frame.shape[:2]

                for idx, p in enumerate(valid_personas):
                    mask = (p[:, 2] > 0.3) & (p[:, 0] > 0)
                    pts = p[mask, :2]
                    min_x, min_y = float(pts[:, 0].min()), float(pts[:, 1].min())
                    max_x, max_y = float(pts[:, 0].max()), float(pts[:, 1].max())

                    pad_x = (max_x - min_x) * 0.15
                    pad_y = (max_y - min_y) * 0.15

                    x1 = max(0.0, min_x - pad_x)
                    y1 = max(0.0, min_y - pad_y)
                    x2 = min(float(w_img), max_x + pad_x)
                    y2 = min(float(h_img), max_y + pad_y)

                    personas_encontradas.append({
                        "idx": idx,
                        "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        "confianza": round(float(p[mask, 2].mean()), 3),
                        "keypoints_validos": int(np.count_nonzero(mask))
                    })
                break

        if frame_encontrado is None or not personas_encontradas:
            if os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except Exception:
                    pass
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se detectaron personas válidas en los primeros fotogramas del video."
            )

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        ret, buffer = cv2.imencode('.jpg', frame_encontrado, encode_param)
        if not ret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error codificando fotograma a JPEG."
            )
        import base64
        frame_b64 = base64.b64encode(buffer).decode('utf-8')

        SessionStateManager.crear_sesion(
            session_id=session_id,
            video_path=video_path,
            personas_detectadas=personas_encontradas,
            frame_idx=frame_idx_encontrado
        )

        return {
            "session_id": session_id,
            "frame_idx_analizado": frame_idx_encontrado,
            "frame_width": w_img,
            "frame_height": h_img,
            "frame_base64": frame_b64,
            "personas": personas_encontradas
        }
    finally:
        cap.release()


@router.post("/evaluaciones/{session_id}/seleccionar-persona", status_code=status.HTTP_200_OK)
async def confirmar_seleccion_persona(
    session_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Registra y confirma explícitamente la identidad de la persona seleccionada para la sesión.
    Transiciona el estado de la sesión a PERSONA_SELECTED.
    """
    require_auth(authorization)
    target_idx = None
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                target_idx = body.get("persona_idx")
        except Exception:
            pass
    elif "form" in content_type:
        try:
            form = await request.form()
            val = form.get("persona_idx")
            if val is not None:
                target_idx = int(val)
        except Exception:
            pass
    else:
        try:
            body = await request.json()
            if isinstance(body, dict):
                target_idx = body.get("persona_idx")
        except Exception:
            try:
                form = await request.form()
                val = form.get("persona_idx")
                if val is not None:
                    target_idx = int(val)
            except Exception:
                pass

    if target_idx is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe especificar persona_idx.")

    try:
        sesion = SessionStateManager.seleccionar_persona(session_id, target_idx)
        return {
            "session_id": session_id,
            "estado": sesion["estado"],
            "persona_idx_seleccionada": sesion["persona_idx_seleccionada"]
        }
    except SessionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SessionError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))



