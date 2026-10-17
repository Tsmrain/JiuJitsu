import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from corpocmente.application.services.video_comparison_service import (
    crear_comparacion,
    obtener_comparacion,
    procesar_comparacion_video_a_video,
    rutas_comparacion,
)
from corpocmente.ui.api.auth_routes import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comparaciones", tags=["comparaciones"])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MAX_VIDEO_BYTES = 300 * 1024 * 1024  # 300 MB por video


def _ext_valido(filename: str) -> bool:
    return Path(filename or "").suffix.lower() in ALLOWED_EXTENSIONS


async def _guardar_upload(file: UploadFile, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)

    size = 0
    with open(dest, "wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break

            size += len(chunk)
            if size > MAX_VIDEO_BYTES:
                try:
                    out.close()
                except Exception:
                    pass

                if dest.exists():
                    dest.unlink(missing_ok=True)

                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="El video supera el límite de 300 MB.",
                )

            out.write(chunk)


@router.post("/video-a-video", status_code=status.HTTP_202_ACCEPTED)
async def comparar_video_a_video(
    background_tasks: BackgroundTasks,
    video_alumno: UploadFile = File(...),
    video_maestro: UploadFile = File(...),
    tecnica_id: Optional[str] = Form(None),
    persona_idx_alumno: int = Form(0),
    persona_idx_maestro: int = Form(0),
    idioma: str = Form("es"),
    video_maestro_nombre: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
):
    if not _ext_valido(video_alumno.filename or ""):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Video del alumno en formato no soportado. Usa MP4, MOV, AVI, MKV o WEBM.",
        )

    if not _ext_valido(video_maestro.filename or ""):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Video del maestro en formato no soportado. Usa MP4, MOV, AVI, MKV o WEBM.",
        )

    usuario = require_auth(authorization)
    token = authorization.split(" ", 1)[1].strip()

    comparacion_id = str(uuid.uuid4())

    path_alumno, path_maestro, _ = rutas_comparacion(comparacion_id)

    await _guardar_upload(video_alumno, path_alumno)
    await _guardar_upload(video_maestro, path_maestro)

    crear_comparacion(
        comparacion_id=comparacion_id,
        tecnica_id=tecnica_id,
        idioma=idioma,
        persona_idx_alumno=persona_idx_alumno,
        persona_idx_maestro=persona_idx_maestro,
        alumno_id=usuario["uid"],
        token=token,
        video_alumno_nombre=video_alumno.filename,
        video_maestro_nombre=video_maestro_nombre or video_maestro.filename,
    )

    background_tasks.add_task(
        procesar_comparacion_video_a_video,
        comparacion_id=comparacion_id,
        tecnica_id=tecnica_id,
        idioma=idioma,
        persona_idx_alumno=persona_idx_alumno,
        persona_idx_maestro=persona_idx_maestro,
        token=token,
    )

    return {
        "comparacion_id": comparacion_id,
        "estado": "procesando",
        "mensaje": "Comparación encolada. Consulta el estado en GET /api/v1/comparaciones/{comparacion_id}.",
    }


@router.get("/{comparacion_id}")
async def leer_comparacion(comparacion_id: str, authorization: Optional[str] = Header(None)):
    usuario = require_auth(authorization)
    data = obtener_comparacion(comparacion_id, token=authorization.split(" ", 1)[1].strip())

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparación no encontrada.",
        )
    if data.get("alumno_id") != usuario["uid"] and usuario.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a esta comparación.")

    return data


@router.get("/{comparacion_id}/video")
async def descargar_video_comparacion(comparacion_id: str, authorization: Optional[str] = Header(None)):
    usuario = require_auth(authorization)
    data = obtener_comparacion(comparacion_id, token=authorization.split(" ", 1)[1].strip())

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparación no encontrada.",
        )
    if data.get("alumno_id") != usuario["uid"] and usuario.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a esta comparación.")

    if data.get("estado") != "completado":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La comparación aún no está completada.",
        )

    if not data.get("video_disponible"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El video comparativo no está disponible.",
        )

    _, _, path_output = rutas_comparacion(comparacion_id)

    if not path_output.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo de video comparativo no existe en disco.",
        )

    return FileResponse(
        path=str(path_output),
        media_type="video/mp4",
        filename=f"comparacion_{comparacion_id}.mp4",
    )
