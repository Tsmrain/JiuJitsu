import os
import shutil
from uuid import UUID, uuid4
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Header
from pydantic import BaseModel

from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.ui.api.auth_routes import require_auth, require_admin, require_staff

router = APIRouter(prefix="/api/v1/tecnicas", tags=["Técnicas"])


class TecnicaCreate(BaseModel):
    nombre: str
    nivel_cinturon: str


class TecnicaResponse(TecnicaCreate):
    id: UUID
    tiene_video: bool = False
    video_url: Optional[str] = None


UPLOAD_DIR = "/tmp/corpocmente_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    return PostgrestClient()


def require_staff(authorization: Optional[str]) -> dict:
    """Permite admin o profesor."""
    caller = require_auth(authorization)
    if caller.get("role") not in ("admin", "profesor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de profesor o administrador."
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
    except Exception:
        rows = []

    # Agrupar por técnica (una técnica puede tener varios videos de distintos profesores)
    tecnicas_map: dict = {}
    for r in rows:
        tid = r["id"]
        if tid not in tecnicas_map:
            tecnicas_map[tid] = {
                "id": tid,
                "nombre": r["nombre"],
                "nivel_cinturon": r["nivel_cinturon"],
                "videos": []
            }
        if r.get("video_id"):
            tecnicas_map[tid]["videos"].append({
                "profesor_id": r.get("video_profesor_id"),
                "url": r.get("video_url")
            })

    resultados = []
    for t in tecnicas_map.values():
        tiene_video = False
        video_url = None
        if profesor_id:
            vid = next((v for v in t["videos"] if str(v["profesor_id"]) == str(profesor_id)), None)
            if vid:
                tiene_video = True
                filename = os.path.basename(vid["url"])
                video_url = f"http://localhost:8000/static/videos/{filename}"

        resultados.append(TecnicaResponse(
            id=UUID(t["id"]),
            nombre=t["nombre"],
            nivel_cinturon=t["nivel_cinturon"],
            tiene_video=tiene_video,
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
        "p_nivel_cinturon": req.nivel_cinturon
    })
    if not created:
        raise HTTPException(status_code=500, detail="Error creando técnica")
    c = created[0] if isinstance(created, list) else created
    return TecnicaResponse(
        id=UUID(c["id"]),
        nombre=c["nombre"],
        nivel_cinturon=c["nivel_cinturon"]
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
        "p_nivel_cinturon": req.nivel_cinturon
    })
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnica no encontrada.")
    c = updated[0] if isinstance(updated, list) else updated
    return TecnicaResponse(
        id=UUID(c["id"]),
        nombre=c["nombre"],
        nivel_cinturon=c["nivel_cinturon"]
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnica no encontrada.")
    return None


@router.post("/{tecnica_id}/video", status_code=status.HTTP_200_OK)
async def subir_video_referencia(
    tecnica_id: UUID,
    profesor_id: UUID = Form(...),
    video: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Sube un video de referencia para una técnica.
    Requiere token de profesor o admin. Un profesor solo puede subir sus propios videos.
    """
    caller = require_staff(authorization)

    # Autorización: profesor solo puede subir videos a su propio nombre
    if caller.get("role") != "admin" and str(caller.get("uid")) != str(profesor_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes subir videos a nombre de otro profesor."
        )

    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.webm')):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de video no soportado.")

    db = get_db()

    # Verificar que la técnica existe vía RPC
    try:
        exists = db.rpc("tecnica_exists", {"p_tecnica_id": str(tecnica_id)})
    except Exception:
        exists = False

    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnica no encontrada en el catálogo.")

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
        raise HTTPException(status_code=500, detail=f"Error guardando referencia de video: {e}")

    if not result:
        raise HTTPException(status_code=500, detail="Error guardando referencia de video.")

    video_id = result[0]["video_id"] if isinstance(result, list) else result["video_id"]
    return {"status": "ok", "message": "Video de referencia actualizado.", "video_id": video_id}
