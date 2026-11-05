import base64
import io
import json
import logging
import os
import re
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import hashlib
import threading
import time
from pathlib import Path
from uuid import UUID, uuid4
from typing import Optional
import cv2
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Header, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
import numpy as np
import requests
from pydantic import BaseModel
from urllib.parse import quote, quote_plus
from corpocmente.application.use_cases.ingest_knowledge_use_case import IngestKnowledgeUseCase
from corpocmente.application.dtos.knowledge_dtos import IngestionRequest
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.ui.api.auth_routes import require_auth, require_admin, require_active_subscription, get_user_idioma
from corpocmente.config import settings
from corpocmente.domain.services.session_manager import (
    SessionStateManager, SessionError, SessionConflictError,
    SessionNotFoundError, SessionExpiredError
)

logger = logging.getLogger(__name__)
MANUALES_DIR = settings.manuales_dir
MANUALES_DIR.mkdir(parents=True, exist_ok=True)
PDF_PAGE_IMAGES_DIR = Path(__file__).resolve().parents[3] / "storage" / "manuales" / "paginas"
MAX_MANUAL_BYTES = 100 * 1024 * 1024
WORKER_HEADERS = {
    "ngrok-skip-browser-warning": "1",
    "User-Agent": "CorpocmenteBackend/1.0",
}
IMAGE_MIME_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".bmp": "image/bmp", ".tif": "image/tiff",
    ".tiff": "image/tiff",
}

# Estado temporal de las ingestas. Los documentos y vectores permanecen en disco/Qdrant;
# este mapa solo permite que la interfaz consulte el progreso durante la sesión del backend.
_knowledge_jobs: dict[str, dict] = {}
_knowledge_job_paths: dict[str, str] = {}
_knowledge_jobs_lock = threading.Lock()


def _set_knowledge_progress(job_id: str, progress: int, stage: str, **extra):
    with _knowledge_jobs_lock:
        if job_id in _knowledge_jobs:
            _knowledge_jobs[job_id].update({"avance": max(0, min(100, int(progress))), "etapa": stage}, **extra)

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
    feedback_summary: Optional[str] = None

def clean_fallback_summary(feedback: Optional[str]) -> str:
    if not feedback:
        return "Technique feedback"
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", feedback.strip())
    summary = sentences[0].strip() if sentences else feedback.strip()
    if "(" in summary and ")" not in summary[summary.rfind("("):]:
        summary = summary[:summary.rfind("(")].rstrip(" ,;:")
    words = summary.split()
    if len(words) > 8:
        summary = " ".join(words[:8]) + "..."
    return summary


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
    session_id: Optional[str] = None,
    idioma: str = "es"
):
    import logging
    logger = logging.getLogger(__name__)
    try:
        from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
        from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
        from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
        from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
        from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
        from corpocmente.domain.services.session_manager import SessionStateManager

        yolo = YOLOPoseAdapter()
        qdrant = QdrantVectorAdapter()
        gemini = LocalVLMAdapter()
        qwen = QwenEmbeddingAdapter()

        facade = IntelligenceAnalysisFacade(
            yolo_adapter=yolo,
            qdrant_adapter=qdrant,
            gemini_adapter=gemini,
            qwen_adapter=qwen
        )

        # Obtener mensaje del profesor para la técnica si está configurado
        mensaje_profesor = ""
        try:
            db_tec = get_db()
            tec_rows = db_tec.get("tecnicas", {"id": f"eq.{tecnica_id}", "select": "mensaje_profesor"})
            if tec_rows and isinstance(tec_rows, list) and len(tec_rows) > 0:
                mensaje_profesor = tec_rows[0].get("mensaje_profesor") or ""
        except Exception as e_msg:
            logger.debug("Fallo consultando mensaje_profesor via PostgREST: %s", e_msg)

        if not mensaje_profesor:
            try:
                import psycopg2
                from corpocmente.config import settings
                db_url = getattr(settings, "DATABASE_URL", "postgres://postgres:postgres@localhost:5432/corpocmente")
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                cur.execute("SELECT mensaje_profesor FROM tecnicas WHERE id = %s", (str(tecnica_id),))
                row = cur.fetchone()
                cur.close()
                conn.close()
                if row and row[0]:
                    mensaje_profesor = str(row[0])
            except Exception as e_sql:
                logger.debug("Fallo consultando mensaje_profesor via SQL fallback: %s", e_sql)

        res = facade.ejecutar_analisis_completo(
            video_path=video_alumno_path,
            tecnica_id=tecnica_id,
            tecnica_nombre=tecnica_nombre,
            video_referencia_path=video_referencia_path,
            evaluacion_id=eval_id,
            persona_idx=persona_idx,
            mensaje_profesor=mensaje_profesor,
            idioma=idioma
        )

        # Calcular timestamp del error en segundos
        timestamp_error_segundos = res.timestamp_error_segundos
        if timestamp_error_segundos is None and os.path.exists(video_alumno_path):
            try:
                import cv2
                cap = cv2.VideoCapture(video_alumno_path)
                fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
                cap.release()
                if fps > 0 and res.frame_alumno_idx is not None:
                    timestamp_error_segundos = round(float(res.frame_alumno_idx) / fps, 2)
            except Exception as e_fps:
                logger.warning("Error calculando FPS para timestamp_error_segundos: %s", e_fps)

        if timestamp_error_segundos is None:
            timestamp_error_segundos = 0.0

        # Guardar metadata de la evaluación para consulta inmediata en GET /evaluaciones/{id}
        meta_data = {
            "evaluacion_id": str(eval_id),
            "timestamp_error_segundos": timestamp_error_segundos,
            "frame_alumno_idx": res.frame_alumno_idx,
            "url_video_alumno": video_alumno_path,
            "articulaciones_criticas": res.articulaciones_criticas or [],
            "nombres_articulaciones_criticas": res.nombres_articulaciones_criticas or [],
        }
        os.makedirs(FRAMES_DIR, exist_ok=True)
        meta_path = os.path.join(FRAMES_DIR, f"meta_{eval_id}.json")
        try:
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump(meta_data, mf)
        except Exception as e_meta:
            logger.warning("No se pudo guardar meta JSON: %s", e_meta)

        # Guardar en base de datos con reintentos y fallback SQL con commit explícito (evita Race Condition)
        db = get_db()
        actualizado = False
        for intento in range(3):
            try:
                rpc_res = db.rpc("worker_update_result", {
                    "p_evaluacion_id": str(eval_id),
                    "p_similitud": res.similitud,
                    "p_feedback_es": res.feedback,
                    "p_estado": "completado",
                    "p_feedback_summary": res.feedback_summary or "Technique feedback",
                })
                if rpc_res is True or (isinstance(rpc_res, list) and len(rpc_res) > 0):
                    actualizado = True
                    break
            except Exception as e_rpc:
                logger.warning("Intento %d de worker_update_result via PostgREST falló: %s", intento + 1, e_rpc)
            time.sleep(0.2)

        if not actualizado:
            try:
                import psycopg2
                from corpocmente.config import settings
                db_url = getattr(settings, "DATABASE_URL", "postgres://postgres:postgres@localhost:5432/corpocmente")
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE evaluaciones_alumnos
                    SET porcentaje_similitud = %s,
                        feedback_gemini_es = %s,
                        estado = %s,
                        feedback_summary = %s
                    WHERE id = %s;
                    """,
                    (res.similitud, res.feedback, "completado", res.feedback_summary or "Technique feedback", str(eval_id))
                )
                conn.commit()
                cur.close()
                conn.close()
                actualizado = True
                logger.info("worker_update_result confirmado vía fallback psycopg2 con commit explícito.")
            except Exception as e_sql:
                logger.error("Fallo definitivo guardando resultado en Postgres: %s", e_sql)

        # Esperar 0.5s para asegurar visibilidad en PostgREST/transacciones antes de que el frontend haga polling
        time.sleep(0.5)

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
    finally:
        import gc, torch
        gc.collect()
        if torch.backends.mps.is_available():
            try:
                torch.mps.empty_cache()
            except Exception:
                pass
        from corpocmente.infrastructure.ai.adapters import log_ram_usage
        log_ram_usage("post_yolo")

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
    idioma: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None)
):
    caller = require_active_subscription(authorization)

    # Autorización: solo el propio alumno o un admin pueden crear evaluaciones
    if caller.get("role") != "admin" and str(caller.get("uid")) != str(alumno_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot create evaluations on behalf of another user."
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
            detail="No active biomechanical pattern registered for this technique."
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        except SessionExpiredError:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session expired.")

        if sesion.get("estado") != SessionState.PERSONA_SELECTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Session is in state '{sesion.get('estado')}'. Person confirmation required first."
            )

        target_persona_idx = sesion.get("persona_idx_seleccionada")
        if persona_idx is not None and persona_idx != target_persona_idx:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The persona_idx ({persona_idx}) does not match session selection ({target_persona_idx})."
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
                detail="Unsupported file format. Must be a video (MP4, AVI, MOV, MKV)."
            )
        video_path = os.path.join(VIDEOS_DIR, f"{eval_id}.mp4")
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)

        target_persona_idx = persona_idx if persona_idx is not None else 0
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide session_id or upload a video file."
        )

    # 3. Registrar en base de datos
    try:
        created = db.rpc("create_evaluacion", {
            "p_id": eval_id,
            "p_alumno_id": str(alumno_id),
            "p_tecnica_id": str(tecnica_id),
            "p_video_referencia_id": str(video_ref_id) if video_ref_id else None,
            "p_url_video_alumno": video_path,
            "p_sucursal_id": caller.get("sucursal_id") or None
        })
    except Exception as e:
        if session_id:
            SessionStateManager.finalizar_operacion(session_id, exito=False, error=str(e), eliminar_video=False)
        raise HTTPException(status_code=500, detail=f"Error creando evaluación: {e}")

    # 4. Iniciar análisis en segundo plano
    from corpocmente.ui.api.auth_routes import get_user_idioma
    idioma_eval = (idioma.strip().lower() if idioma else None) or get_user_idioma(str(alumno_id)) or "es"

    background_tasks.add_task(
        ejecutar_evaluacion_background,
        eval_id,
        video_path,
        tecnica_id,
        tecnica_nombre,
        video_ref_path,
        target_persona_idx,
        session_id,
        idioma_eval
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
            "p_estado": payload.estado,
            "p_feedback_summary": payload.feedback_summary
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

    # Convertir ruta local del video del alumno a URL pública estática y recuperar timestamp del error
    meta_candidate = os.path.join(FRAMES_DIR, f"meta_{evaluacion_id}.json")
    timestamp_error_segundos = eval_data.get("timestamp_error_segundos")
    raw_video_alumno = eval_data.get("url_video_alumno") or ""
    if not raw_video_alumno:
        try:
            row = db.get("evaluaciones_alumnos", {"id": f"eq.{evaluacion_id}", "select": "url_video_alumno"})
            if row and len(row) > 0:
                raw_video_alumno = row[0].get("url_video_alumno") or ""
        except Exception:
            pass
    articulaciones_criticas = eval_data.get("articulaciones_criticas") or []
    nombres_articulaciones_criticas = eval_data.get("nombres_articulaciones_criticas") or []

    if os.path.exists(meta_candidate):
        try:
            with open(meta_candidate, "r", encoding="utf-8") as mf:
                meta_json = json.load(mf)
                if timestamp_error_segundos is None:
                    timestamp_error_segundos = meta_json.get("timestamp_error_segundos", 0.0)
                if not raw_video_alumno:
                    raw_video_alumno = meta_json.get("url_video_alumno") or ""
                if not articulaciones_criticas:
                    articulaciones_criticas = meta_json.get("articulaciones_criticas") or []
                if not nombres_articulaciones_criticas:
                    nombres_articulaciones_criticas = meta_json.get("nombres_articulaciones_criticas") or []
        except Exception:
            pass

    caller_idioma = caller.get("idioma") or get_user_idioma(caller.get("uid")) or "es"
    from corpocmente.infrastructure.ai.adapters import obtener_nombres_articulaciones
    joints_source = nombres_articulaciones_criticas or articulaciones_criticas or []
    nombres_articulaciones_criticas = obtener_nombres_articulaciones(joints_source, idioma=caller_idioma)

    if timestamp_error_segundos is None:
        timestamp_error_segundos = 0.0

    video_alumno_url = None
    if raw_video_alumno:
        filename_alumno = os.path.basename(raw_video_alumno)
        target_video = os.path.join(VIDEOS_DIR, filename_alumno)
        if not os.path.exists(target_video) and os.path.exists(raw_video_alumno) and target_video != raw_video_alumno:
            try:
                shutil.copy2(raw_video_alumno, target_video)
            except Exception:
                pass
        video_alumno_url = f"/static/videos/{filename_alumno}"

    # Convertir ruta local del video de referencia a URL pública estática
    raw_video_path = eval_data.get("video_referencia_url") or ""
    video_ref_url = None
    if raw_video_path:
        filename = os.path.basename(raw_video_path)
        target_ref = os.path.join(VIDEOS_DIR, filename)
        if not os.path.exists(target_ref):
            if os.path.exists(raw_video_path):
                try:
                    shutil.copy2(raw_video_path, target_ref)
                except Exception:
                    pass
            else:
                # Buscar en raíz del repositorio si el nombre o fallback coincide
                repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
                cand_root = os.path.join(repo_root, filename)
                if os.path.exists(cand_root):
                    try:
                        shutil.copy2(cand_root, target_ref)
                    except Exception:
                        pass
                elif "67beb825" in filename:
                    fallback_esc = os.path.join(repo_root, "profesor salida de Guardia Parandose.mp4")
                    if os.path.exists(fallback_esc):
                        try:
                            shutil.copy2(fallback_esc, target_ref)
                        except Exception:
                            pass
        video_ref_url = f"/static/videos/{filename}"

    # Fotograma crítico anotado con el error si ya fue procesado
    frame_error_url = None
    frame_candidate = os.path.join(FRAMES_DIR, f"critico_{evaluacion_id}.jpg")
    if os.path.exists(frame_candidate):
        frame_error_url = f"/static/frames/critico_{evaluacion_id}.jpg"

    tecnica_nombre = eval_data.get("tecnica_nombre") or "jiu-jitsu"
    practice_url = f"https://www.youtube.com/results?search_query={quote_plus(tecnica_nombre + ' jiu-jitsu tutorial')}"

    return {
        "id": eval_data["id"],
        "estado": eval_data["estado"],
        "similitud": eval_data["porcentaje_similitud"],
        "feedback": eval_data.get("feedback_gemini_es") or eval_data.get("feedback_gemini_pt"),
        "feedback_summary": eval_data.get("feedback_summary") or clean_fallback_summary(eval_data.get("feedback_gemini_es") or eval_data.get("feedback_gemini_pt")),
        "timestamp_error_segundos": timestamp_error_segundos,
        "url_video_alumno": video_alumno_url,
        "tecnica_id": eval_data["tecnica_id"],
        "tecnica_nombre": eval_data["tecnica_nombre"],
        "video_referencia_url": video_ref_url,
        "video_referencia_nombre": os.path.basename(raw_video_path) if raw_video_path else None,
        "video_referencia_profesor_nombre": eval_data.get("video_referencia_profesor_nombre"),
        "frame_error_url": frame_error_url,
        "articulaciones_criticas": articulaciones_criticas,
        "nombres_articulaciones_criticas": nombres_articulaciones_criticas,
        "practice_url": practice_url,
    }

@router.post("/evaluaciones/validar-spam", status_code=status.HTTP_200_OK)
async def validar_spam(video: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    """
    Endpoint HTTP aislado para validar tempranamente si un video es de Jiu-Jitsu (SPAM filter).
    Requiere cualquier usuario autenticado con Pase de Tatami activo.
    """
    require_active_subscription(authorization)

    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        shutil.copyfileobj(video.file, temp_video)
        temp_video_path = temp_video.name

    try:
        from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
        from corpocmente.infrastructure.ai.local_spam_filter import LocalSpamFilter

        yolo = YOLOPoseAdapter()
        filtro = LocalSpamFilter(yolo)
        es_valido = filtro.validar_es_jiujitsu(temp_video_path)
        if not es_valido:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The provided video does not appear to be related to Brazilian Jiu-Jitsu or Grappling."
            )
        return {"status": "ok", "message": "Video is valid."}
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

    if payload.alcance == "tecnica" and not payload.tecnica_id:
        raise HTTPException(status_code=422, detail="Selecciona una técnica para este material.")

    use_case = IngestKnowledgeUseCase()
    resultado = use_case.execute(
        tecnica_id=payload.tecnica_id,
        contenido_texto=payload.contenido_texto,
        profesor_id=caller.get("uid"),
        sucursal_id=caller.get("sucursal_id"),
        fuente_tipo=payload.fuente_tipo,
        fuente_nombre=payload.fuente_nombre,
        fuente_referencia=payload.fuente_referencia,
        fuente_url=str(payload.fuente_url) if payload.fuente_url else None,
        alcance=payload.alcance,
    )
    return {"status": "ok", "chunks_procesados": resultado.chunks_procesados}


@router.post("/conocimiento/fuentes/archivo", status_code=status.HTTP_201_CREATED)
async def ingerir_archivo_teoria(
    request: Request,
    background_tasks: BackgroundTasks,
    archivo: UploadFile = File(...),
    alcance: str = Form("global"),
    tecnica_id: Optional[UUID] = Form(None),
    fuente_nombre: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
    job_id: Optional[str] = None,
):
    """Guarda el original e indexa texto, imágenes y páginas visuales de documentos."""
    caller = require_auth(authorization)
    if caller.get("role") not in ("admin", "profesor"):
        raise HTTPException(status_code=403, detail="Se requieren privilegios de profesor o administrador.")
    if not isinstance(tecnica_id, UUID):
        tecnica_id = None
    if alcance not in ("global", "tecnica"):
        raise HTTPException(status_code=422, detail="El alcance debe ser global o de técnica.")
    if alcance == "tecnica" and not tecnica_id:
        raise HTTPException(status_code=422, detail="Selecciona una técnica para este material.")

    nombre_archivo = os.path.basename(archivo.filename or "manual")
    extension = os.path.splitext(nombre_archivo)[1].lower()
    if extension not in {".pdf", ".docx", ".txt", *IMAGE_MIME_TYPES}:
        raise HTTPException(
            status_code=415,
            detail="Formato no compatible. Sube PDF, Word (.docx), TXT o una imagen JPG, PNG, WEBP o TIFF.",
        )

    contenido = await archivo.read(MAX_MANUAL_BYTES + 1)
    if len(contenido) > MAX_MANUAL_BYTES:
        raise HTTPException(status_code=413, detail="El manual supera el límite de 100 MB.")

    if job_id:
        with _knowledge_jobs_lock:
            ruta_manual = Path(_knowledge_job_paths.get(job_id, ""))
        if not str(ruta_manual) or not ruta_manual.is_file():
            raise HTTPException(status_code=404, detail="Se perdió el archivo asociado a esta carga.")
    else:
        manual_id = uuid4()
        ruta_manual = MANUALES_DIR / f"{manual_id}{extension}"
        ruta_manual.write_bytes(contenido)
        job_id = str(uuid4())
        with _knowledge_jobs_lock:
            _knowledge_job_paths[job_id] = str(ruta_manual)
            _knowledge_jobs[job_id] = {
                "id": job_id, "estado": "procesando", "etapa": "Archivo recibido", "avance": 1,
                "nombre": nombre_archivo, "profesor_id": str(caller.get("uid")),
            }
        background_tasks.add_task(
            _procesar_fuente_global_background,
            request, str(ruta_manual), nombre_archivo, alcance,
            str(tecnica_id) if tecnica_id else None, fuente_nombre,
            authorization, job_id,
        )
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"status": "procesando", "job_id": job_id, "nombre": nombre_archivo},
        )
    manual_id = UUID(ruta_manual.stem.split("_imagenes")[0])
    fuente_url = f"{str(request.base_url).rstrip('/')}/api/v1/conocimiento/archivos/{ruta_manual.name}"

    texto = ""
    paginas = []
    paginas_escaneadas = []
    paginas_visual = []
    imagenes_docx = []
    _set_knowledge_progress(job_id, 3, "Preparando documento")
    try:
        if extension == ".txt":
            texto = contenido.decode("utf-8-sig")
        elif extension in IMAGE_MIME_TYPES:
            imagenes_docx.append({
                "label": f"Imagen de conocimiento: {nombre_archivo}",
                "media_path": str(ruta_manual),
                "media_url": f"/api/v1/conocimiento/media/imagenes/{quote(ruta_manual.name)}",
                "imagen_hash": hashlib.sha256(contenido).hexdigest(),
                "bytes": contenido,
                "mime_type": IMAGE_MIME_TYPES[extension],
                "texto": (fuente_nombre or nombre_archivo).strip(),
                "pagina": None,
            })
        elif extension == ".docx":
            _set_knowledge_progress(job_id, 8, "Leyendo texto e imágenes del documento")
            with zipfile.ZipFile(io.BytesIO(contenido)) as docx:
                root = ET.fromstring(docx.read("word/document.xml"))
                media_dir = MANUALES_DIR / f"{manual_id}_imagenes"
                hashes_imagenes = set()
                for media_name in docx.namelist():
                    if not media_name.startswith("word/media/"):
                        continue
                    media_bytes = docx.read(media_name)
                    image_hash = hashlib.sha256(media_bytes).hexdigest()
                    if image_hash in hashes_imagenes:
                        continue
                    hashes_imagenes.add(image_hash)
                    mime_type = {
                        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                        ".webp": "image/webp", ".bmp": "image/bmp", ".tif": "image/tiff", ".tiff": "image/tiff",
                    }.get(Path(media_name).suffix.lower())
                    if not mime_type:
                        logger.info("Se omite una imagen Word con formato no compatible: %s", media_name)
                        continue
                    media_dir.mkdir(parents=True, exist_ok=True)
                    media_path = media_dir / f"figura_{len(imagenes_docx) + 1:04d}_{image_hash[:10]}{Path(media_name).suffix.lower()}"
                    media_path.write_bytes(media_bytes)
                    imagenes_docx.append({
                        "label": f"Imagen del manual Word, {os.path.basename(media_name)}",
                        "media_path": str(media_path),
                        "media_url": f"/api/v1/conocimiento/media/imagenes/{quote(media_path.relative_to(MANUALES_DIR).as_posix(), safe='/')}",
                        "imagen_hash": image_hash,
                        "bytes": media_bytes,
                        "mime_type": mime_type,
                        "texto": f"Figura del manual {fuente_nombre or nombre_archivo}: {os.path.basename(media_name)}",
                        "pagina": None,
                    })
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            texto = "\n".join(
                "".join(node.text or "" for node in paragraph.findall(".//w:t", ns))
                for paragraph in root.findall(".//w:p", ns)
            )
        else:
            import fitz
            documento = fitz.open(stream=contenido, filetype="pdf")
            total_paginas = max(1, len(documento))
            _set_knowledge_progress(job_id, 5, "Leyendo páginas del PDF", paginas_procesadas=0, total_paginas=len(documento))
            for numero, pagina in enumerate(documento, start=1):
                texto_pagina = pagina.get_text("text").strip()
                tiene_imagenes = bool(pagina.get_images())
                es_escaneada = len(texto_pagina) < 40

                if es_escaneada:
                    paginas_escaneadas.append(numero)
                else:
                    paginas.append(f"[Página {numero}]\n{texto_pagina}")

                # Indexar como imagen visual las páginas con fotos/diagramas o páginas escaneadas
                if tiene_imagenes or es_escaneada:
                    paginas_visual.append({
                        "label": f"Página {numero} del manual PDF",
                        "media_path": str(ruta_manual),
                        "media_url": f"{fuente_url}#page={numero}",
                        "pagina": numero,
                        "texto": texto_pagina,
                        "documento": documento,
                    })
                _set_knowledge_progress(
                    job_id,
                    5 + round(20 * numero / total_paginas),
                    f"Leyendo página {numero} de {len(documento)}",
                    paginas_procesadas=numero,
                    total_paginas=len(documento),
                )
            texto = "\n\n".join(paginas)
    except HTTPException:
        raise
    except ModuleNotFoundError as error:
        if error.name == "fitz":
            raise HTTPException(
                status_code=503,
                detail=(
                    "Falta instalar PyMuPDF para procesar archivos PDF. "
                    "Activa el entorno virtual del backend y ejecuta: pip install -r requirements.txt. "
                    "El archivo original quedó guardado; vuelve a subirlo después de instalar la dependencia."
                ),
            ) from error
        logger.exception("No se pudo procesar el manual %s", nombre_archivo)
        raise HTTPException(status_code=503, detail="Falta una dependencia del backend para procesar el documento.") from error
    except Exception as error:
        logger.exception("No se pudo extraer el texto del manual %s", nombre_archivo)
        raise HTTPException(status_code=422, detail=f"No se pudo leer el documento: {error}")

    medios_visuales = paginas_visual + imagenes_docx
    if not texto.strip() and not medios_visuales:
        raise HTTPException(status_code=422, detail="No se encontró texto legible en el documento.")

    worker_url = settings.COLAB_TUNNEL_URL
    use_local_qwen = getattr(settings, "USE_LOCAL_QWEN", False)
    use_drive = False
    drive_client = None

    if not use_local_qwen:
        try:
            from corpocmente.infrastructure.storage.google_drive_client import GoogleDriveDataLakeClient
            drive_client = GoogleDriveDataLakeClient()
            use_drive = drive_client.token_file.exists()
        except Exception:
            use_drive = False

    if (texto.strip() or medios_visuales) and not use_local_qwen and not use_drive and (not worker_url or "placeholder" in worker_url):
        raise HTTPException(
            status_code=503,
            detail="El archivo quedó guardado, pero para vectorizar su contenido debes iniciar el worker Qwen en Colab o activar USE_LOCAL_QWEN=true.",
        )

    nombre_fuente = (fuente_nombre or nombre_archivo).strip()
    use_case = IngestKnowledgeUseCase()
    chunks_procesados = 0
    texto_embeddings = None
    imagenes_embeddings = []

    if texto.strip():
        if use_local_qwen:
            try:
                from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
                # Si hay worker configurado, evitar importar MLX/Metal antes del fallback.
                qwen_local = QwenEmbeddingAdapter(use_local=not bool(worker_url), colab_url=worker_url)
                bloques_texto = [texto[i:i + 8000] for i in range(0, len(texto), 8000)]
                texto_embeddings = {"chunks": [], "embeddings": [], "dimension": 2048}
                for indice, bloque in enumerate(bloques_texto, start=1):
                    emb = qwen_local.generar_embedding_texto(bloque)
                    texto_embeddings["chunks"].append(bloque)
                    texto_embeddings["embeddings"].append(emb)
                    avance = 30 + round(23 * indice / len(bloques_texto))
                    _set_knowledge_progress(job_id, avance, f"Vectorizando texto con Qwen local: bloque {indice} de {len(bloques_texto)}", bloques_texto_procesados=indice, total_bloques_texto=len(bloques_texto))
            except Exception as error:
                logger.exception("Error vectorizando texto con Qwen local: %s", error)
                raise HTTPException(status_code=500, detail=f"Error en inferencia local Qwen: {error}") from error
        elif use_drive:
            try:
                _set_knowledge_progress(job_id, 35, "Enviando texto al worker Qwen vía Google Drive...")
                datos_texto = drive_client.vectorizar_texto_qwen(texto=texto, job_id=job_id)
                texto_embeddings = {
                    "chunks": datos_texto.get("chunks", []),
                    "embeddings": datos_texto.get("embeddings", []),
                    "dimension": datos_texto.get("dimension", 2048)
                }
                _set_knowledge_progress(job_id, 53, "Texto vectorizado con éxito por Qwen en Colab")
            except Exception as error:
                logger.exception("Error vectorizando texto vía Drive: %s", error)
                raise HTTPException(
                    status_code=503,
                    detail=f"Qwen no pudo vectorizar el texto del manual vía Drive ({error}). Revisa que la Celda 4 de Colab esté activa."
                ) from error
        else:
            try:
                # Lotes acotados permiten informar avance durante la vectorización de libros largos.
                bloques_texto = [texto[i:i + 8000] for i in range(0, len(texto), 8000)]
                texto_embeddings = {"chunks": [], "embeddings": [], "dimension": 2048}
                for indice, bloque in enumerate(bloques_texto, start=1):
                    respuesta_texto = requests.post(
                        f"{worker_url.rstrip('/')}/embed_text",
                        data={"texto": bloque},
                        headers=WORKER_HEADERS,
                        timeout=240,
                    )
                    respuesta_texto.raise_for_status()
                    datos_texto = respuesta_texto.json()
                    texto_embeddings["chunks"].extend(datos_texto.get("chunks", []))
                    texto_embeddings["embeddings"].extend(datos_texto.get("embeddings", []))
                    avance = 30 + round(23 * indice / len(bloques_texto))
                    _set_knowledge_progress(job_id, avance, f"Vectorizando texto: bloque {indice} de {len(bloques_texto)}", bloques_texto_procesados=indice, total_bloques_texto=len(bloques_texto))
            except requests.exceptions.RequestException as error:
                raise HTTPException(status_code=503, detail="Qwen no pudo vectorizar el texto del manual. Revisa que el worker de Colab siga activo.") from error

    # Las páginas PDF se indexan como imagen junto a su texto; las escaneadas van como imagen sola. No se hace OCR.
    if medios_visuales:
        lotes = [medios_visuales[i:i + 4] for i in range(0, len(medios_visuales), 4)]
        _set_knowledge_progress(job_id, 54 if texto.strip() else 30, "Preparando páginas e imágenes", elementos_visuales_procesados=0, total_elementos_visuales=len(medios_visuales))
        for indice_lote, lote in enumerate(lotes, start=1):
            if use_local_qwen:
                try:
                    import io
                    from PIL import Image
                    from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
                    # Si hay worker configurado, evitar importar MLX/Metal antes del fallback.
                    qwen_local = QwenEmbeddingAdapter(use_local=not bool(worker_url), colab_url=worker_url)
                    lote_embs = []
                    for item in lote:
                        if item.get("pagina"):
                            pixmap = item["documento"][item["pagina"] - 1].get_pixmap(dpi=120, alpha=False)
                            image_bytes = pixmap.tobytes("jpeg")
                        else:
                            image_bytes = item["bytes"]
                        item["imagen_hash"] = item.get("imagen_hash") or hashlib.sha256(image_bytes).hexdigest()
                        img_pil = Image.open(io.BytesIO(image_bytes))
                        emb = qwen_local.generar_embedding_imagen(
                            img_pil,
                            prompt=f"{item.get('label', 'Página/Imagen')}. {item.get('texto', '')[:6000]}",
                        )
                        lote_embs.append(emb)
                    datos_imagen = {
                        "chunks": [f"[Imagen: {item['label']}]" for item in lote],
                        "embeddings": lote_embs,
                        "dimension": 2048
                    }
                    imagenes_embeddings.append((lote, datos_imagen))
                    avance = 54 + round(34 * indice_lote / len(lotes)) if texto.strip() else 30 + round(58 * indice_lote / len(lotes))
                    _set_knowledge_progress(job_id, avance, f"Vectorizando imágenes con Qwen local: {min(indice_lote * 4, len(medios_visuales))} de {len(medios_visuales)}", elementos_visuales_procesados=min(indice_lote * 4, len(medios_visuales)), total_elementos_visuales=len(medios_visuales))
                except Exception as error:
                    logger.exception("Error vectorizando imágenes con Qwen local: %s", error)
                    raise HTTPException(status_code=500, detail=f"Error en inferencia local Qwen para imágenes: {error}") from error
            elif use_drive:
                try:
                    import base64
                    lote_payload = []
                    for item in lote:
                        if item.get("pagina"):
                            pixmap = item["documento"][item["pagina"] - 1].get_pixmap(dpi=120, alpha=False)
                            image_bytes = pixmap.tobytes("jpeg")
                        else:
                            image_bytes = item["bytes"]
                        item["imagen_hash"] = item.get("imagen_hash") or hashlib.sha256(image_bytes).hexdigest()
                        b64_str = base64.b64encode(image_bytes).decode("utf-8")
                        lote_payload.append({
                            "label": item.get("label", "Página/Imagen"),
                            "b64": b64_str
                        })

                    datos_imagen = drive_client.vectorizar_imagenes_qwen(
                        lote_imagenes=lote_payload,
                        job_id=f"{job_id}_img_{indice_lote}"
                    )
                    imagenes_embeddings.append((lote, datos_imagen))
                    avance = 54 + round(34 * indice_lote / len(lotes)) if texto.strip() else 30 + round(58 * indice_lote / len(lotes))
                    _set_knowledge_progress(job_id, avance, f"Vectorizando imágenes: {min(indice_lote * 4, len(medios_visuales))} de {len(medios_visuales)}", elementos_visuales_procesados=min(indice_lote * 4, len(medios_visuales)), total_elementos_visuales=len(medios_visuales))
                except Exception as error:
                    logger.exception("Falló la vectorización multimodal de imágenes vía Drive: %s", error)
                    raise HTTPException(
                        status_code=503,
                        detail="El archivo original quedó guardado, pero Qwen no pudo vectorizar parte de sus imágenes en Drive. Revisa que el worker de Colab siga activo.",
                    ) from error
            else:
                archivos = []
                try:
                    page_numbers = []
                    for item in lote:
                        if item.get("pagina"):
                            page_numbers.append(item["pagina"])
                            pixmap = item["documento"][item["pagina"] - 1].get_pixmap(dpi=120, alpha=False)
                            image_bytes = pixmap.tobytes("jpeg")
                            filename, mime_type = f"pagina-{item['pagina']}.jpg", "image/jpeg"
                        else:
                            image_bytes = item["bytes"]
                            filename = os.path.basename(item["media_path"])
                            mime_type = item["mime_type"]
                        archivos.append(("files", (filename, image_bytes, mime_type)))
                        item["imagen_hash"] = item.get("imagen_hash") or hashlib.sha256(image_bytes).hexdigest()
                    respuesta_imagen = requests.post(
                        f"{worker_url.rstrip('/')}/embed_images",
                        data={
                            "page_numbers": ",".join(map(str, page_numbers)),
                            "labels": "\n".join(item["label"] for item in lote),
                            "texts_json": json.dumps([item.get("texto", "") for item in lote], ensure_ascii=False),
                        },
                        files=archivos,
                        headers=WORKER_HEADERS,
                        timeout=240,
                    )
                    if respuesta_imagen.status_code == 404:
                        raise HTTPException(
                            status_code=503,
                            detail="El archivo quedó guardado, pero tu worker de Colab todavía no tiene /embed_images. Actualiza y vuelve a ejecutar el notebook Colab.",
                        )
                    respuesta_imagen.raise_for_status()
                    datos_imagen = respuesta_imagen.json()
                    if "embeddings" not in datos_imagen:
                        raise ValueError("El worker no devolvió embeddings de las imágenes.")
                    imagenes_embeddings.append((lote, datos_imagen))
                    avance = 54 + round(34 * indice_lote / len(lotes)) if texto.strip() else 30 + round(58 * indice_lote / len(lotes))
                    _set_knowledge_progress(job_id, avance, f"Vectorizando imágenes: {min(indice_lote * 4, len(medios_visuales))} de {len(medios_visuales)}", elementos_visuales_procesados=min(indice_lote * 4, len(medios_visuales)), total_elementos_visuales=len(medios_visuales))
                except HTTPException:
                    raise
                except requests.exceptions.RequestException as error:
                    logger.exception("Falló la vectorización multimodal de imágenes %s", [item["label"] for item in lote])
                    raise HTTPException(
                        status_code=503,
                        detail="El archivo original quedó guardado, pero Qwen no pudo vectorizar parte de sus imágenes. Revisa que el worker actualizado siga activo.",
                    ) from error
                finally:
                    archivos.clear()

    datos_ingesta = {
        "tecnica_id": str(tecnica_id) if tecnica_id else None,
        "profesor_id": caller.get("uid"),
        "sucursal_id": caller.get("sucursal_id"),
        "fuente_tipo": "manual",
        "fuente_nombre": nombre_fuente,
        "fuente_url": fuente_url,
        "alcance": alcance,
    }
    total_chunks_por_guardar = max(
        1,
        (len(texto_embeddings.get("chunks", [])) if texto_embeddings else 0)
        + sum(len(datos.get("chunks", [])) for _, datos in imagenes_embeddings),
    )
    chunks_guardados = 0

    def reportar_guardado(_hechos: int, _total: int):
        nonlocal chunks_guardados
        chunks_guardados += 1
        _set_knowledge_progress(
            job_id,
            90 + round(9 * chunks_guardados / total_chunks_por_guardar),
            f"Guardando fragmentos: {chunks_guardados} de {total_chunks_por_guardar}",
            chunks_guardados=chunks_guardados,
            total_chunks=total_chunks_por_guardar,
        )

    # Persistir solamente cuando Qwen terminó todos los embeddings, evitando una ingesta parcial.
    if texto_embeddings:
        _set_knowledge_progress(job_id, 90, "Guardando vectores y referencias")
        resultado_texto = use_case.execute(
            contenido_texto=texto,
            fuente_referencia="Texto del documento; las páginas están indicadas en cada fragmento",
            embedding_data=texto_embeddings,
            progress_callback=reportar_guardado,
            **datos_ingesta,
        )
        chunks_procesados += resultado_texto.chunks_procesados
    for lote, datos_imagen in imagenes_embeddings:
        etiquetas = datos_imagen.get("chunks") or [f"[Imagen: {item['label']}]" for item in lote]
        resultado_imagen = use_case.execute(
            contenido_texto="\n".join(etiquetas),
            fuente_referencia="; ".join(item["label"] for item in lote),
            embedding_data=datos_imagen,
            metadata_por_chunk=[
                {
                    "modalidad": "multimodal",
                    "media_path": item["media_path"],
                    "media_url": item.get("media_url"),
                    "imagen_hash": item.get("imagen_hash"),
                    "texto_asociado": item.get("texto", "")[:4000],
                    **({"pagina": item["pagina"]} if item.get("pagina") else {}),
                }
                for item in lote
            ],
            progress_callback=reportar_guardado,
            **datos_ingesta,
        )
        chunks_procesados += resultado_imagen.chunks_procesados

    _set_knowledge_progress(job_id, 99, "Finalizando registro de la fuente")

    return {
        "status": "ok",
        "nombre": nombre_archivo,
        "paginas_texto_indexadas": len(paginas) if extension == ".pdf" else None,
        "paginas_imagen_indexadas": len(paginas_visual),
        "imagenes_word_indexadas": len(imagenes_docx),
        "imagenes_indexadas": len(imagenes_docx),
        "chunks_procesados": chunks_procesados,
    }


class _SavedUpload:
    """Adaptador pequeño para reutilizar el procesador existente desde la tarea background."""
    def __init__(self, path: str, filename: str):
        self.filename = filename
        self._path = path

    async def read(self, limit: int):
        with open(self._path, "rb") as source:
            return source.read(limit)


def _procesar_fuente_global_background(request, path, filename, alcance, tecnica_id, fuente_nombre, authorization, job_id):
    import asyncio
    try:
        result = asyncio.run(ingerir_archivo_teoria(
            request=request,
            background_tasks=BackgroundTasks(),
            archivo=_SavedUpload(path, filename),
            alcance=alcance,
            tecnica_id=UUID(tecnica_id) if tecnica_id else None,
            fuente_nombre=fuente_nombre,
            authorization=authorization,
            job_id=job_id,
        ))
        with _knowledge_jobs_lock:
            _knowledge_jobs[job_id] = {**_knowledge_jobs[job_id], **result, "estado": "completado", "etapa": "Indexación terminada", "avance": 100}
    except Exception as error:
        logger.exception("Falló la ingesta de la fuente %s", job_id)
        detail = error.detail if isinstance(error, HTTPException) else "No se pudo procesar el documento. Revisa los logs del backend."
        with _knowledge_jobs_lock:
            _knowledge_jobs[job_id] = {**_knowledge_jobs.get(job_id, {}), "estado": "error", "etapa": "No se pudo indexar", "error": detail}


@router.get("/conocimiento/fuentes/procesamiento/{job_id}")
async def estado_procesamiento_fuente(job_id: str, authorization: Optional[str] = Header(None)):
    caller = require_auth(authorization)
    with _knowledge_jobs_lock:
        job = _knowledge_jobs.get(job_id)
    if not job or (caller.get("role") != "admin" and job.get("profesor_id") != str(caller.get("uid"))):
        raise HTTPException(status_code=404, detail="No se encontró ese proceso de carga.")
    return job


@router.get("/conocimiento/archivos/{nombre_archivo}")
async def descargar_archivo_conocimiento(
    nombre_archivo: str,
    authorization: Optional[str] = Header(None),
):
    require_auth(authorization)
    nombre_seguro = os.path.basename(nombre_archivo)
    ruta = MANUALES_DIR / nombre_seguro
    if ruta.parent != MANUALES_DIR or not ruta.is_file():
        raise HTTPException(status_code=404, detail="Archivo de conocimiento no encontrado.")
    return FileResponse(ruta, filename=nombre_seguro)


@router.get("/conocimiento/media/imagenes/{asset_path:path}")
async def servir_imagen_conocimiento(
    asset_path: str,
    authorization: Optional[str] = Header(None),
):
    """Sirve una imagen de conocimiento solo si permanece dentro del almacenamiento de manuales."""
    require_auth(authorization)
    root = MANUALES_DIR.resolve()
    candidate = (root / asset_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ruta de imagen inválida.") from exc
    if candidate.suffix.lower() not in IMAGE_MIME_TYPES or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Imagen de conocimiento no encontrada.")
    return FileResponse(candidate, media_type=IMAGE_MIME_TYPES[candidate.suffix.lower()])


class BibliotecaBuscarRequest(BaseModel):
    query: str
    idioma: Optional[str] = "es"
    limit: Optional[int] = 10
    imagen_url: Optional[str] = None


def resolver_ruta_imagen_local(imagen_url: Optional[str]) -> Optional[Path]:
    """Resuelve la ruta física en disco de una URL de imagen para búsqueda visual multimodal."""
    if not imagen_url or not isinstance(imagen_url, str):
        return None
    url_clean = imagen_url.strip()
    if not url_clean:
        return None

    if "://" in url_clean:
        from urllib.parse import urlparse
        parsed = urlparse(url_clean)
        url_path = parsed.path
    else:
        url_path = url_clean

    repo_root = Path(__file__).resolve().parents[4]

    # 1. Fotogramas críticos de error (/static/frames/...)
    if "/static/frames/" in url_path:
        fname = os.path.basename(url_path)
        candidate = Path("/tmp/corpocmente_frames") / fname
        if candidate.exists() and candidate.is_file():
            return candidate

    # 2. Fotogramas de manuales (/api/v1/conocimiento/media/paginas/...)
    if "conocimiento/media/paginas/" in url_path:
        subpath = url_path.split("conocimiento/media/paginas/")[-1]
        candidate = repo_root / "backend" / "storage" / "manuales" / "paginas" / subpath
        if candidate.exists() and candidate.is_file():
            return candidate

    # 3. Path directo en filesystem
    candidate_direct = Path(url_clean)
    if candidate_direct.exists() and candidate_direct.is_file():
        return candidate_direct

    # 4. En /tmp
    if url_path.startswith("/tmp/") or url_path.startswith("/private/tmp/"):
        cand_tmp = Path(url_path)
        if cand_tmp.exists() and cand_tmp.is_file():
            return cand_tmp

    # 5. Descarga remota si es URL externa
    if url_clean.startswith("http://") or url_clean.startswith("https://"):
        try:
            import requests
            resp = requests.get(url_clean, timeout=5)
            if resp.status_code == 200:
                tmp_dir = Path("/tmp/corpocmente_frames")
                tmp_dir.mkdir(parents=True, exist_ok=True)
                tmp_file = tmp_dir / f"dl_{os.path.basename(url_path) or 'frame.jpg'}"
                with open(tmp_file, "wb") as f_dl:
                    f_dl.write(resp.content)
                return tmp_file
        except Exception as e_dl:
            logger.warning("Fallo al descargar imagen remota %s: %s", url_clean, e_dl)

    return None


@router.post("/conocimiento/biblioteca/buscar", status_code=status.HTTP_200_OK)
async def buscar_en_biblioteca(
    req: BibliotecaBuscarRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Búsqueda semántica multimodal en la biblioteca de manuales de Jiu-Jitsu.
    Soporta búsqueda por texto y búsqueda visual multimodal si se provee imagen_url.
    Cualquier usuario autenticado con suscripción activa puede buscar.
    """
    require_auth(authorization)
    from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
    from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter
    from corpocmente.domain.glossary.glossary_service import expandir_query_con_glosario

    query_limpia = (req.query or "").strip()
    if not query_limpia and not req.imagen_url:
        return {
            "query": "",
            "idioma": req.idioma or "es",
            "imagen_url": None,
            "imagen_procesada": None,
            "busqueda_multimodal": False,
            "total": 0,
            "resultados": []
        }

    # Búsqueda Cognitiva: Reescribir query para diferenciar conceptos de ataque vs defensa
    try:
        from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
        vlm = LocalVLMAdapter()
        query_cognitiva = vlm.reescribir_query_cognitiva(query_limpia) if query_limpia else ""
    except Exception as e_cog:
        logger.warning("Fallo en reescritura cognitiva con VLM: %s", e_cog)
        query_cognitiva = query_limpia

    query_expandida = expandir_query_con_glosario(query_cognitiva or query_limpia) if (query_cognitiva or query_limpia) else ""

    qwen = QwenEmbeddingAdapter()
    query_vector = qwen.generar_embedding_texto(query_expandida or query_cognitiva or query_limpia or "jiu-jitsu")

    # Resolución de imagen para búsqueda visual multimodal
    ruta_img = resolver_ruta_imagen_local(req.imagen_url) if req.imagen_url else None
    busqueda_multimodal = False
    img_procesada_str = None

    rag = QdrantRAGAdapter()

    if ruta_img and ruta_img.exists():
        try:
            img_vector = qwen.generar_embedding_imagen(str(ruta_img), prompt=query_limpia or "tecnica")
            resultados = rag.buscar_biblioteca_multimodal(query_vector, img_vector, alpha=0.5, limit=req.limit or 10)
            busqueda_multimodal = True
            img_procesada_str = str(ruta_img)
        except Exception as e_img:
            logger.warning("Fallo al generar embedding visual para %s (%s). Fallback a búsqueda textual.", ruta_img, e_img)
            resultados = rag.buscar_biblioteca(query_vector, limit=req.limit or 10)
    else:
        resultados = rag.buscar_biblioteca(query_vector, limit=req.limit or 10)

    return {
        "query": query_limpia,
        "query_cognitiva": query_cognitiva,
        "query_expandida": query_expandida,
        "idioma": req.idioma or "es",
        "imagen_url": req.imagen_url,
        "imagen_procesada": img_procesada_str,
        "busqueda_multimodal": busqueda_multimodal,
        "total": len(resultados),
        "resultados": resultados,
    }


@router.get("/conocimiento/manuales", status_code=status.HTTP_200_OK)
async def listar_manuales_pdf(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None
):
    """
    Retorna la lista de manuales en formato PDF disponibles en la biblioteca.
    Devuelve una lista JSON con los nombres de los PDFs disponibles en backend/storage/manuales.
    Requiere autenticación.
    """
    auth_header = authorization or (f"Bearer {token}" if token else None)
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    require_auth(auth_header)
    repo_root = Path(__file__).resolve().parents[4]
    search_dirs = [
        repo_root / "backend" / "storage" / "manuales"
    ]
    manuales_dict = {}
    for d in search_dirs:
        if d.exists() and d.is_dir():
            for p in d.glob("*.pdf"):
                if p.is_file() and p.stat().st_size > 1000 and not p.name.startswith("."):
                    if p.name not in manuales_dict:
                        manuales_dict[p.name] = p

    resultado = [nom for nom in sorted(manuales_dict.keys()) if "matplotlib" not in str(manuales_dict[nom])]
    return resultado


@router.get("/conocimiento/manuales/{filename}")
async def servir_manual_pdf(
    filename: str,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None
):
    """
    Sirve un archivo de manual en PDF para visualización en el visor embebido (iframe) o descarga.
    """
    auth_header = authorization or (f"Bearer {token}" if token else None)
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    require_auth(auth_header)

    safe_name = os.path.basename(filename)
    repo_root = Path(__file__).resolve().parents[4]
    candidates = [
        repo_root / "backend" / "storage" / "manuales" / safe_name,
    ]
    encontrado = next((c for c in candidates if c.exists() and c.is_file()), None)
    if not encontrado:
        raise HTTPException(status_code=404, detail="Manual PDF no encontrado.")

    return FileResponse(
        str(encontrado),
        media_type="application/pdf",
        filename=safe_name,
        headers={"Content-Disposition": f"inline; filename=\"{safe_name}\""}
    )


@router.get("/conocimiento/media/paginas/{asset_path:path}")
async def servir_pagina_manual(
    asset_path: str,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None
):
    """Sirve los JPG persistentes de páginas PDF generados por la ingesta multimodal."""
    auth_header = authorization or (f"Bearer {token}" if token else None)
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    require_auth(auth_header)
    root = PDF_PAGE_IMAGES_DIR.resolve()
    candidate = (root / asset_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ruta de página inválida.") from exc
    if candidate.suffix.lower() not in {".jpg", ".jpeg"} or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Página del manual no encontrada.")
    return FileResponse(candidate, media_type="image/jpeg")


@router.get("/conocimiento/media/{tecnica_id}/{filename}")
async def servir_frame_rag_conocimiento(tecnica_id: str, filename: str):
    """Sirve fotogramas muestreados de videos del profesor para RAG multimodal."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Filename inválido.")
    if ".." in tecnica_id or "/" in tecnica_id or "\\" in tecnica_id:
        raise HTTPException(status_code=400, detail="Tecnica ID inválido.")
    from corpocmente.application.services.rag_video_ingestion import STORAGE_DIR
    path = (STORAGE_DIR / tecnica_id / filename).resolve()
    if not str(path).startswith(str(STORAGE_DIR.resolve())) or not path.is_file():
        raise HTTPException(status_code=404, detail="Frame no encontrado.")
    return FileResponse(path)


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


@router.get("/conocimiento/fuentes/globales", status_code=status.HTTP_200_OK)
async def listar_fuentes_globales(authorization: Optional[str] = Header(None)):
    caller = require_auth(authorization)
    if caller.get("role") not in ("admin", "profesor"):
        raise HTTPException(status_code=403, detail="Se requieren privilegios de profesor o administrador.")
    try:
        return PostgrestClient().rpc("admin_list_fuentes_globales", {}) or []
    except Exception as error:
        logger.exception("No se pudieron listar las fuentes globales")
        raise HTTPException(
            status_code=503,
            detail=(
                "No se pudieron consultar las fuentes globales. Verifica que PostgREST esté activo "
                "y que se haya aplicado codigo_fuente/database/11_conocimiento_global_mensaje_tecnica.sql."
            ),
        ) from error


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


def _bbox_iou(b1: list, b2: list) -> float:
    x1 = max(b1[0], b2[0])
    y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2])
    y2 = min(b1[3], b2[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = a1 + a2 - inter
    return inter / union if union > 0 else 0.0


def _bbox_iomin(b1: list, b2: list) -> float:
    x1 = max(b1[0], b2[0])
    y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2])
    y2 = min(b1[3], b2[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    m = min(a1, a2)
    return inter / m if m > 0 else 0.0


def _limpiar_candidatos_bboxes(candidates: list, w_img: int, h_img: int) -> list:
    """
    Filtra y deduplica detecciones de personas en el primer frame para la selección del usuario.
    Elimina:
    1. Quimeras/fantasmas (cajas intermedias solapadas con dos cuerpos independientes).
    2. Duplicados directos de la misma persona por NMS imperfecto (IoU > 0.50, proximidad < 40px).
    """
    if len(candidates) <= 1:
        return candidates

    # Paso 0: Filtrar reflejos (espejos) y figuras diminutas en el fondo
    # Si una caja delimitadora tiene un área menor al 10% de la caja más grande del frame, descartarla
    areas = []
    for c in candidates:
        min_x, min_y, max_x, max_y = c["bbox_raw"]
        area = max(0.0, max_x - min_x) * max(0.0, max_y - min_y)
        areas.append(area)
    max_area = max(areas) if areas else 0.0
    if max_area > 0.0:
        sin_reflejos = [c for c, a in zip(candidates, areas) if a >= 0.10 * max_area]
        if sin_reflejos:
            candidates = sin_reflejos

    if len(candidates) <= 1:
        return candidates

    # Paso 1: Si hay >= 3 candidatos, detectar y eliminar quimeras
    if len(candidates) >= 3:
        sin_quimeras = []
        for i, c in enumerate(candidates):
            es_quimera = False
            for j in range(len(candidates)):
                if i == j:
                    continue
                for k in range(j + 1, len(candidates)):
                    if i == k:
                        continue
                    a, b = candidates[j], candidates[k]
                    # Si A y B son dos cuerpos independientes
                    if _bbox_iou(a["bbox_raw"], b["bbox_raw"]) < 0.30:
                        overlap_a = _bbox_iomin(c["bbox_raw"], a["bbox_raw"]) > 0.50 or _bbox_iou(c["bbox_raw"], a["bbox_raw"]) > 0.35
                        overlap_b = _bbox_iomin(c["bbox_raw"], b["bbox_raw"]) > 0.50 or _bbox_iou(c["bbox_raw"], b["bbox_raw"]) > 0.35
                        if overlap_a and overlap_b:
                            es_quimera = True
                            logger.info("Descartando candidato quimera/fantasma idx=%s por solapamiento con %s y %s",
                                        c["idx"], a["idx"], b["idx"])
                            break
                if es_quimera:
                    break
            if not es_quimera:
                sin_quimeras.append(c)
        candidates = sin_quimeras

    # Paso 2: Deduplicación de candidatos restantes (mismo cuerpo detectado dos veces)
    cands_sorted = sorted(candidates, key=lambda c: (c["confianza"], c["keypoints_validos"]), reverse=True)
    dedup = []
    for c in cands_sorted:
        is_dup = False
        for d in dedup:
            iou_val = _bbox_iou(c["bbox_raw"], d["bbox_raw"])
            d_cent = np.linalg.norm(c["center"] - d["center"])
            d_head = np.linalg.norm(c["head"] - d["head"]) if c["head"] is not None and d["head"] is not None else float("inf")
            d_pelv = np.linalg.norm(c["pelvis"] - d["pelvis"]) if c["pelvis"] is not None and d["pelvis"] is not None else float("inf")

            # Reglas de duplicado:
            # - IoU > 0.50
            # - Centros a menos de 40px
            # - Cabezas a menos de 40px con solapamiento
            # - Pelvis a menos de 40px con solapamiento
            # - Alto IoMin (> 0.70) y cabeza compartida
            if iou_val > 0.50:
                is_dup = True
                break
            if d_cent < 40.0:
                is_dup = True
                break
            if d_head < 40.0 and (d_pelv < 80.0 or iou_val > 0.25):
                is_dup = True
                break
            if d_pelv < 40.0 and iou_val > 0.35:
                is_dup = True
                break
            iomin_val = _bbox_iomin(c["bbox_raw"], d["bbox_raw"])
            if iomin_val > 0.70 and (d_head < 100.0 or (c["head"] is not None and d["head"] is not None and abs(c["head"][0] - d["head"][0]) < 50.0)):
                is_dup = True
                break

        if not is_dup:
            dedup.append(c)

    return sorted(dedup, key=lambda c: c["idx"])


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
            detail="Unsupported file format. Must be a video (MP4, AVI, MOV, MKV)."
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
                candidates = []
                for idx, p in enumerate(valid_personas):
                    mask = (p[:, 2] > 0.3) & (p[:, 0] > 0)
                    pts = p[mask, :2]
                    min_x, min_y = float(pts[:, 0].min()), float(pts[:, 1].min())
                    max_x, max_y = float(pts[:, 0].max()), float(pts[:, 1].max())
                    center = np.array([(min_x + max_x) / 2.0, (min_y + max_y) / 2.0])
                    pelvis = p[[11, 12], :2].mean(axis=0) if ((p[[11, 12], 2] > 0.3).all() and (p[[11, 12], 0] > 0).all()) else None
                    head = p[0, :2] if (p[0, 2] > 0.3 and p[0, 0] > 0) else None
                    conf = float(p[mask, 2].mean())
                    candidates.append({
                        "idx": idx,
                        "pose": p,
                        "bbox_raw": [min_x, min_y, max_x, max_y],
                        "confianza": round(conf, 3),
                        "keypoints_validos": int(np.count_nonzero(mask)),
                        "center": center,
                        "pelvis": pelvis,
                        "head": head,
                    })

                candidatos_limpios = _limpiar_candidatos_bboxes(candidates, frame.shape[1], frame.shape[0])
                if not candidatos_limpios:
                    continue

                frame_idx_encontrado = target
                frame_encontrado = frame
                h_img, w_img = frame.shape[:2]

                for c in candidatos_limpios:
                    min_x, min_y, max_x, max_y = c["bbox_raw"]
                    pad_x = (max_x - min_x) * 0.15
                    pad_y = (max_y - min_y) * 0.15

                    x1 = max(0.0, min_x - pad_x)
                    y1 = max(0.0, min_y - pad_y)
                    x2 = min(float(w_img), max_x + pad_x)
                    y2 = min(float(h_img), max_y + pad_y)

                    personas_encontradas.append({
                        "idx": c["idx"],
                        "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        "confianza": c["confianza"],
                        "keypoints_validos": c["keypoints_validos"]
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
                detail="No valid persons detected in the first video frames."
            )

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        ret, buffer = cv2.imencode('.jpg', frame_encontrado, encode_param)
        if not ret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error encoding frame to JPEG."
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must specify persona_idx.")

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



