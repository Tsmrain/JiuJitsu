import os
import shutil
import logging
from pathlib import Path
from uuid import UUID, uuid4
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Header, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from corpocmente.config import settings
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.ui.api.auth_routes import require_auth, require_admin, require_staff

router = APIRouter(prefix="/api/v1/tecnicas", tags=["Técnicas"])
logger = logging.getLogger(__name__)


class TecnicaCreate(BaseModel):
    nombre: str
    nivel_cinturon: str
    mensaje_profesor: str = ""


class TecnicaResponse(TecnicaCreate):
    id: UUID
    tiene_video: bool = False
    tiene_patron: bool = False
    video_url: Optional[str] = None


UPLOAD_DIR = "/tmp/corpocmente_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
RAG_VIDEO_FRAMES_DIR = settings.video_frames_dir
RAG_VIDEO_FRAMES_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    return PostgrestClient()


def require_staff(authorization: Optional[str]) -> dict:
    """Permite admin o profesor."""
    caller = require_auth(authorization)
    if caller.get("role") not in ("admin", "profesor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor or administrator privileges required."
        )
    return caller


@router.get("", response_model=List[TecnicaResponse], status_code=status.HTTP_200_OK)
async def listar_tecnicas(profesor_id: Optional[UUID] = None):
    """
    Lista todas las técnicas del catálogo global (público).
    Si se provee profesor_id, marca las que ese profesor ya tiene con video.
    """
    db = get_db()
    try:
        rows = db.rpc("get_tecnicas_with_videos", {})
    except Exception as error:
        logger.exception("No se pudo consultar el catálogo de técnicas")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not query catalog. Please check database connection.",
        ) from error

    # Agrupar por técnica (una técnica puede tener varios videos de distintos profesores)
    tecnicas_map: dict = {}
    for r in rows:
        tid = r["id"]
        if tid not in tecnicas_map:
            tecnicas_map[tid] = {
                "id": tid,
                "nombre": r["nombre"],
                "nivel_cinturon": r["nivel_cinturon"],
                "mensaje_profesor": r.get("mensaje_profesor") or "",
                "tiene_patron": bool(r.get("tiene_patron", False)),
                "videos": []
            }
        if r.get("video_id"):
            tecnicas_map[tid]["videos"].append({
                "profesor_id": r.get("video_profesor_id"),
                "url": r.get("video_url")
            })

    resultados = []
    for t in tecnicas_map.values():
        tiene_video = t["tiene_patron"]
        video_url = None
        if profesor_id:
            videos_profesor = [v for v in t["videos"] if str(v["profesor_id"]) == str(profesor_id)]
            # Puede haber referencias históricas duplicadas. Usa el último archivo
            # que realmente exista y tenga contenido, no un registro de prueba vacío.
            video_path = next((
                os.path.join(UPLOAD_DIR, os.path.basename(v["url"]))
                for v in reversed(videos_profesor)
                if v.get("url")
                and os.path.isfile(os.path.join(UPLOAD_DIR, os.path.basename(v["url"])))
                and os.path.getsize(os.path.join(UPLOAD_DIR, os.path.basename(v["url"]))) > 1024
            ), None)
            if video_path:
                tiene_video = True
                filename = os.path.basename(video_path)
                video_url = f"http://localhost:8000/static/videos/{filename}"

        resultados.append(TecnicaResponse(
            id=UUID(t["id"]),
            nombre=t["nombre"],
            nivel_cinturon=t["nivel_cinturon"],
            mensaje_profesor=t["mensaje_profesor"],
            tiene_video=tiene_video,
            tiene_patron=t["tiene_patron"],
            video_url=video_url
        ))

    return resultados


@router.post("", response_model=TecnicaResponse, status_code=status.HTTP_201_CREATED)
async def crear_tecnica(req: TecnicaCreate, authorization: Optional[str] = Header(None)):
    """
    Agrega una nueva técnica al catálogo global.
    Requiere token de admin o profesor. Usa RPC SECURITY DEFINER.
    """
    require_staff(authorization)
    db = get_db()
    created = db.rpc("admin_create_tecnica", {
        "p_nombre": req.nombre,
        "p_nivel_cinturon": req.nivel_cinturon,
        "p_mensaje_profesor": req.mensaje_profesor,
    })
    if not created:
        raise HTTPException(status_code=500, detail="Error creating technique.")
    c = created[0] if isinstance(created, list) else created
    return TecnicaResponse(
        id=UUID(c["id"]),
        nombre=c["nombre"],
        nivel_cinturon=c["nivel_cinturon"],
        mensaje_profesor=c.get("mensaje_profesor") or req.mensaje_profesor,
    )


@router.put("/{tecnica_id}", response_model=TecnicaResponse, status_code=status.HTTP_200_OK)
async def actualizar_tecnica(tecnica_id: UUID, req: TecnicaCreate, authorization: Optional[str] = Header(None)):
    """
    Edita una técnica del catálogo. Requiere token de admin o profesor.
    """
    require_staff(authorization)
    db = get_db()
    updated = db.rpc("admin_update_tecnica", {
        "p_tecnica_id": str(tecnica_id),
        "p_nombre": req.nombre,
        "p_nivel_cinturon": req.nivel_cinturon,
        "p_mensaje_profesor": req.mensaje_profesor,
    })
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technique not found.")
    c = updated[0] if isinstance(updated, list) else updated
    return TecnicaResponse(
        id=UUID(c["id"]),
        nombre=c["nombre"],
        nivel_cinturon=c["nivel_cinturon"],
        mensaje_profesor=c.get("mensaje_profesor") or req.mensaje_profesor,
    )


@router.delete("/{tecnica_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_tecnica(tecnica_id: UUID, authorization: Optional[str] = Header(None)):
    """
    Elimina una técnica del catálogo. Requiere token de admin o profesor.
    """
    require_staff(authorization)
    db = get_db()
    deleted_ok = db.rpc("admin_delete_tecnica", {"p_tecnica_id": str(tecnica_id)})
    if not deleted_ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technique not found.")
    return None


from corpocmente.application.services.rag_video_ingestion import indexar_frames_video_rag


def auto_ingerir_video_rag_background(
    tecnica_id: UUID,
    video_path: str = None,
    tecnica_nombre: str = "Técnica",
    profesor_id: Optional[str] = None,
    sucursal_id: Optional[str] = None,
):
    """
    Ingesta en segundo plano del video de referencia:
    1. Índices biomecánicos de poses (133 dims)
    2. Evidencia visual multimodal (frames -> Qwen -> Qdrant)
    """
    # Soporta tanto (tecnica_id, video_path, tecnica_nombre) como (tecnica_id, tecnica_nombre, video_path)
    if isinstance(video_path, str) and not os.path.exists(video_path) and isinstance(tecnica_nombre, str) and os.path.exists(tecnica_nombre):
        video_path, tecnica_nombre = tecnica_nombre, video_path

    # 1. Índices biomecánicos de poses (133 dims)
    try:
        from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
        from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter

        qdrant = QdrantVectorAdapter()
        yolo = YOLOPoseAdapter()

        qdrant.asegurar_poses_referencia(
            tecnica_id=tecnica_id,
            video_referencia_path=video_path,
            yolo_adapter=yolo,
            tecnica_nombre=tecnica_nombre,
        )
    except Exception as exc:
        logger.warning("No se pudieron indexar poses de referencia: %s", exc)

    # 2. Evidencia visual multimodal (frames -> Qwen -> Qdrant)
    try:
        indexar_frames_video_rag(
            tecnica_id=tecnica_id,
            video_path=video_path,
            tecnica_nombre=tecnica_nombre,
            profesor_id=str(profesor_id) if profesor_id else None,
            sucursal_id=str(sucursal_id) if sucursal_id else None,
            sample_seconds=2.0,
            max_frames=30,
        )
    except Exception as exc:
        logger.warning("No se pudieron indexar frames visuales para RAG: %s", exc)


def auto_ingerir_referencia_background(tecnica_id: UUID, video_path: str):
    auto_ingerir_video_rag_background(tecnica_id=tecnica_id, video_path=video_path)


@router.post("/{tecnica_id}/video", status_code=status.HTTP_200_OK, deprecated=True)
async def subir_video_referencia(
    tecnica_id: UUID,
    background_tasks: BackgroundTasks,
    profesor_id: UUID = Form(...),
    video: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """[DEPRECATED] Sube una referencia de video heredada sin activar un patrón biomecánico.

    Se conserva para compatibilidad con integraciones existentes. Los clientes nuevos deben
    usar /evaluaciones/primer-frame, seleccionar persona y registrar /{tecnica_id}/patron.
    Sube un video de referencia para una técnica.
    Requiere token de profesor o admin. Un profesor solo puede subir sus propios videos.
    """
    caller = require_staff(authorization)

    # Autorización: profesor solo puede subir videos a su propio nombre
    if caller.get("role") != "admin" and str(caller.get("uid")) != str(profesor_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot upload videos on behalf of another instructor."
        )

    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.webm')):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported video format.")

    db = get_db()

    # Verificar que la técnica existe vía RPC
    try:
        exists = db.rpc("tecnica_exists", {"p_tecnica_id": str(tecnica_id)})
    except Exception:
        exists = False

    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technique not found in catalog.")

    file_path = os.path.join(UPLOAD_DIR, f"{uuid4()}_{video.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    # Guardar vía RPC (upsert: borra el anterior del mismo profesor y crea uno nuevo)
    try:
        result = db.rpc("admin_save_video_referencia", {
            "p_tecnica_id": str(tecnica_id),
            "p_profesor_id": str(profesor_id),
            "p_url_video": file_path
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving video reference: {e}")

    if not result:
        raise HTTPException(status_code=500, detail="Error saving video reference.")

    video_id = result[0]["video_id"] if isinstance(result, list) else result["video_id"]

    # Iniciar auto-ingesta de poses del profesor en segundo plano para Qdrant
    background_tasks.add_task(auto_ingerir_referencia_background, tecnica_id, file_path)

    return {"status": "ok", "message": "Video de referencia actualizado.", "video_id": video_id}


@router.get("/{tecnica_id}/patron", status_code=status.HTTP_200_OK)
async def consultar_patron_activo(
    tecnica_id: UUID,
    authorization: Optional[str] = Header(None)
):
    """
    Retorna los datos del patrón activo de la técnica.
    """
    require_auth(authorization)
    from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
    qdrant = QdrantVectorAdapter()
    patron_id = qdrant._get_patron_activo_db(tecnica_id)
    if not patron_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The technique does not have an active pattern registered.")

    secuencia = qdrant.obtener_secuencia_referencia(tecnica_id, patron_id=patron_id)
    return {
        "status": "ok",
        "tecnica_id": str(tecnica_id),
        "patron_id": str(patron_id),
        "total_frames": len(secuencia),
        "keypoint_schema_version": "coco17_v1"
    }


@router.post("/{tecnica_id}/patron", status_code=status.HTTP_201_CREATED)
async def registrar_patron_tecnica(
    tecnica_id: UUID,
    background_tasks: BackgroundTasks,
    session_id: Optional[str] = Form(None),
    persona_idx: Optional[int] = Form(None),
    video: Optional[UploadFile] = File(None),
    authorization: Optional[str] = Header(None)
):
    """
    Registra el patrón biomecánico de una técnica a partir del video del profesor.
    Requiere rol profesor o admin (alumno recibe 403).
    Sigue el flujo de 5 pasos verificables con gestión de fallos parciales:
      1. Extraer y validar secuencia (cobertura >= 70%).
      2. Insertar nuevo patrón en Qdrant (133 dims).
      3. Verificar recuperación completa y ordenada.
      4. Activar patrón en PostgreSQL (fuente de verdad).
      5. Limpiar patrón anterior en Qdrant.
    """
    caller = require_staff(authorization)
    profesor_id = caller.get("uid") or UUID("7e455a7d-cbc8-4190-9a10-3b959f6425fc")

    db = get_db()
    # 0. Validar existencia de la técnica en PostgreSQL
    try:
        exists = db.rpc("tecnica_exists", {"p_tecnica_id": str(tecnica_id)})
    except Exception:
        exists = False

    if not exists:
        try:
            import psycopg2
            from corpocmente.config import settings
            db_url = getattr(settings, "DATABASE_URL", "postgres://postgres:postgres@localhost:5432/corpocmente")
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM tecnicas WHERE id = %s", (str(tecnica_id),))
            exists = cur.fetchone() is not None
            cur.close()
            conn.close()
        except Exception:
            pass

    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technique not found in catalog.")

    # Resolver video_path y persona_idx a través de session_id o upload directo
    from corpocmente.domain.services.session_manager import (
        SessionStateManager, SessionState, SessionConflictError, SessionNotFoundError, SessionExpiredError
    )
    sesion = None
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
                detail=f"Session is in state '{sesion.get('estado')}'. State 'PERSONA_SELECTED' is required."
            )
        target_persona_idx = sesion.get("persona_idx_seleccionada")
        if target_persona_idx is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="persona_idx is required. Instructor must be selected in the session."
            )
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
        if not video.filename.endswith(('.mp4', '.avi', '.mov', '.webm')):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported video format.")
        if persona_idx is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="persona_idx is required to identify the instructor in the video."
            )
        target_persona_idx = persona_idx
        video_path = os.path.join(UPLOAD_DIR, f"patron_{uuid4()}_{video.filename}")
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide session_id or upload a video file."
        )

    # 1. Extraer y validar secuencia
    from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
    yolo = YOLOPoseAdapter()
    try:
        ext_res = yolo.extraer_secuencia(video_path, persona_idx_inicial=target_persona_idx)
    except Exception as e_ext:
        if session_id:
            SessionStateManager.finalizar_operacion(session_id, exito=False, error=str(e_ext))
        raise HTTPException(status_code=500, detail=f"Error extracting poses from video: {e_ext}")

    cobertura = ext_res.get("cobertura", 0.0)
    total_frames = ext_res.get("total_frames", 0)
    if total_frames == 0 or cobertura < 0.70:
        if session_id:
            SessionStateManager.finalizar_operacion(session_id, exito=False, error="Tracking insuficiente")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Insufficient tracking in pattern video: coverage {cobertura*100:.1f}% < 70% required."
        )

    secuencia_kpts = ext_res["secuencia_kpts"]
    nuevo_patron_id = uuid4()

    # 2. Insertar nuevo patrón en Qdrant
    from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
    qdrant = QdrantVectorAdapter()
    try:
        qdrant.guardar_patron_secuencia(
            tecnica_id=tecnica_id,
            patron_id=nuevo_patron_id,
            profesor_id=UUID(str(profesor_id)),
            secuencia_kpts=secuencia_kpts,
            keypoint_schema_version="coco17_v1"
        )
    except Exception as e_qdrant:
        if session_id:
            SessionStateManager.finalizar_operacion(session_id, exito=False, error=str(e_qdrant))
        raise HTTPException(status_code=500, detail=f"Failed to insert pattern in Qdrant: {e_qdrant}")

    # 3. Verificar recuperación completa y ordenada
    try:
        recuperados = qdrant.obtener_secuencia_referencia(tecnica_id, patron_id=nuevo_patron_id)
        if len(recuperados) != len(secuencia_kpts):
            qdrant.eliminar_patron(nuevo_patron_id)
            if session_id:
                SessionStateManager.finalizar_operacion(session_id, exito=False, error="Inconsistencia de frames")
            raise HTTPException(
                status_code=500,
                detail=f"Inconsistency verifying pattern in Qdrant: expected {len(secuencia_kpts)} frames, retrieved {len(recuperados)}."
            )
    except HTTPException:
        raise
    except Exception as e_verif:
        qdrant.eliminar_patron(nuevo_patron_id)
        if session_id:
            SessionStateManager.finalizar_operacion(session_id, exito=False, error=str(e_verif))
        raise HTTPException(status_code=500, detail=f"Failed verifying pattern in Qdrant: {e_verif}")

    # 4. Activar nuevo patrón en PostgreSQL
    patron_anterior_id = None
    try:
        res = db.rpc("admin_activar_patron_tecnica", {
            "p_tecnica_id": str(tecnica_id),
            "p_patron_id": str(nuevo_patron_id)
        })
        if res:
            row = res[0] if isinstance(res, list) else res
            patron_anterior_id = row.get("patron_anterior_id")
    except Exception as e_pg:
        # Rollback en Qdrant para evitar patrones huérfanos
        qdrant.eliminar_patron(nuevo_patron_id)
        if session_id:
            SessionStateManager.finalizar_operacion(session_id, exito=False, error=str(e_pg))
        raise HTTPException(status_code=500, detail=f"Failed to activate pattern in PostgreSQL: {e_pg}. Orphan pattern deleted.")

    # 5. Limpiar patrón anterior solo tras confirmación de activación
    if patron_anterior_id and str(patron_anterior_id) != str(nuevo_patron_id):
        try:
            qdrant.eliminar_patron(UUID(str(patron_anterior_id)))
        except Exception as e_clean:
            import logging
            logging.getLogger(__name__).warning(f"Error limpiando patrón anterior {patron_anterior_id}: {e_clean}")

    # Mantener disponible la demostración original para mostrarla junto al
    # fotograma crítico en los reportes. El patrón y el video son registros
    # separados; si el guardado falla, el patrón sigue siendo válido.
    video_ref_saved = False
    try:
        video_result = db.rpc("admin_save_video_referencia", {
            "p_tecnica_id": str(tecnica_id),
            "p_profesor_id": str(profesor_id),
            "p_url_video": video_path
        })
        if not video_result:
            raise RuntimeError("La base de datos no confirmó el video de referencia")
        video_ref_saved = True
    except Exception as e_video:
        import logging
        logging.getLogger(__name__).warning(
            "Patrón %s activado, pero no se pudo asociar su video de referencia: %s",
            nuevo_patron_id, e_video
        )

    if session_id:
        SessionStateManager.finalizar_operacion(session_id, exito=True, eliminar_video=False)

    if video_ref_saved:
        try:
            tecnica_rows = db.get("tecnicas", {"id": f"eq.{tecnica_id}", "select": "nombre"})
            tecnica_nombre = tecnica_rows[0].get("nombre", str(tecnica_id)) if tecnica_rows else str(tecnica_id)
        except Exception:
            tecnica_nombre = str(tecnica_id)
        background_tasks.add_task(
            auto_ingerir_video_rag_background,
            tecnica_id,
            tecnica_nombre,
            video_path,
            str(profesor_id),
            caller.get("sucursal_id"),
        )

    return {
        "status": "ok",
        "tecnica_id": str(tecnica_id),
        "patron_id": str(nuevo_patron_id),
        "patron_anterior_id": str(patron_anterior_id) if patron_anterior_id else None,
        "total_frames": total_frames,
        "cobertura": cobertura,
        "video_referencia_guardado": video_ref_saved,
        "mensaje": "Patrón biomecánico registrado y activado exitosamente."
    }


@router.get("/media/{tecnica_id}/{filename}")
async def servir_frame_rag_tecnica(tecnica_id: str, filename: str):
    """Sirve fotogramas muestreados del video de referencia para RAG multimodal."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if ".." in tecnica_id or "/" in tecnica_id or "\\" in tecnica_id:
        raise HTTPException(status_code=400, detail="Invalid technique ID.")
    from corpocmente.application.services.rag_video_ingestion import STORAGE_DIR
    path = (STORAGE_DIR / tecnica_id / filename).resolve()
    if not str(path).startswith(str(STORAGE_DIR.resolve())) or not path.is_file():
        raise HTTPException(status_code=404, detail="Frame not found.")
    return FileResponse(path)
