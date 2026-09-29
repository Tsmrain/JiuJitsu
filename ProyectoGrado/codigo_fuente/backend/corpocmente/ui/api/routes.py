import os
import shutil
import tempfile
from uuid import UUID, uuid4
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel

from corpocmente.infrastructure.ai.adapters import GeminiApiAdapter
from corpocmente.application.use_cases.ingest_knowledge_use_case import IngestKnowledgeUseCase
from corpocmente.application.dtos.knowledge_dtos import IngestionRequest
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.ui.api.auth_routes import require_auth, require_admin
from corpocmente.config import settings

router = APIRouter(prefix="/api/v1", tags=["Evaluaciones", "Conocimiento"])

class ResultadoWorkerDTO(BaseModel):
    similitud: float
    feedback: str
    estado: str


VIDEOS_DIR = "/tmp/corpocmente_videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

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

@router.post("/evaluaciones/analizar", status_code=status.HTTP_200_OK)
async def analizar_video(
    tecnica_id: UUID = Form(...),
    tecnica_nombre: str = Form(...),
    profesor_id: Optional[UUID] = Form(None),
    video: UploadFile = File(...),
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

    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado. Debe ser un video (MP4, AVI, MOV, MKV)."
        )

    eval_id = str(uuid4())
    video_path = os.path.join(VIDEOS_DIR, f"{eval_id}.mp4")

    # Guardar video en directorio persistente para el worker
    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    db = get_db()

    # Buscar el video de referencia del PROFESOR ESPECÍFICO si se proveyó
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
    except Exception:
        videos_ref = []

    if not videos_ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay video de referencia para esta técnica, por lo que no se puede evaluar."
        )
    video_ref_id = videos_ref[0]["id"]

    try:
        created = db.rpc("create_evaluacion", {
            "p_id": eval_id,
            "p_alumno_id": str(alumno_id),
            "p_tecnica_id": str(tecnica_id),
            "p_video_referencia_id": str(video_ref_id),
            "p_url_video_alumno": video_path
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando evaluación: {e}")

    if not created:
        raise HTTPException(status_code=500, detail="Error creando evaluación")

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

    return {
        "id": eval_data["id"],
        "estado": eval_data["estado"],
        "similitud": eval_data["porcentaje_similitud"],
        "feedback": eval_data["feedback_gemini_es"] or eval_data["feedback_gemini_pt"],
        "tecnica_id": eval_data["tecnica_id"],
        "tecnica_nombre": eval_data["tecnica_nombre"],
        "video_referencia_url": video_ref_url,
        "video_referencia_profesor_nombre": eval_data.get("video_referencia_profesor_nombre"),
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



