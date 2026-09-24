import os
import shutil
import tempfile
from uuid import UUID, uuid4
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/tecnicas", tags=["Técnicas"])

# --- Modelos Pydantic ---
class TecnicaCreate(BaseModel):
    nombre: str
    nivel_cinturon: str

class TecnicaResponse(TecnicaCreate):
    id: UUID
    # Campos dinámicos en base a los videos que haya subido el profesor
    tiene_video: bool = False
    video_url: Optional[str] = None

# --- Mock Databases en Memoria (Hasta conectar Postgres) ---
TECNICAS_DB = [
    {
        "id": UUID("d3b07384-d9a4-4f6c-947b-11347076a5b6"),
        "nombre": "Armbar (Llave de Brazo)",
        "nivel_cinturon": "Blanco"
    },
    {
        "id": UUID("e8b15394-d9a4-4f6c-947b-11347076a5b7"),
        "nombre": "Triângulo",
        "nivel_cinturon": "Blanco"
    }
]

# Tabla asociativa: Un profesor sube un video para una técnica
VIDEOS_REFERENCIA_DB = []

# Para guardar temporalmente videos en desarrollo
UPLOAD_DIR = "/tmp/corpocmente_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_model=List[TecnicaResponse], status_code=status.HTTP_200_OK)
async def listar_tecnicas(profesor_id: Optional[UUID] = None):
    """
    Lista todas las técnicas del catálogo global.
    Si se provee profesor_id, cruza la información para indicar si el profesor ya subió un video para la técnica.
    """
    resultados = []
    for t in TECNICAS_DB:
        tecnica_resp = TecnicaResponse(**t)
        
        # Verificar si el profesor tiene un video para esta técnica
        if profesor_id:
            video_ref = next((v for v in VIDEOS_REFERENCIA_DB if v["tecnica_id"] == t["id"] and v["profesor_id"] == profesor_id), None)
            if video_ref:
                tecnica_resp.tiene_video = True
                filename = os.path.basename(video_ref["url_video_local"])
                tecnica_resp.video_url = f"http://localhost:8000/static/videos/{filename}"
        
        resultados.append(tecnica_resp)
        
    return resultados

@router.post("", response_model=TecnicaResponse, status_code=status.HTTP_201_CREATED)
async def crear_tecnica(req: TecnicaCreate):
    """
    Agrega una nueva técnica al catálogo global.
    """
    nueva_tecnica = {
        "id": uuid4(),
        **req.model_dump()
    }
    TECNICAS_DB.append(nueva_tecnica)
    return TecnicaResponse(**nueva_tecnica)

@router.put("/{tecnica_id}", response_model=TecnicaResponse, status_code=status.HTTP_200_OK)
async def actualizar_tecnica(tecnica_id: UUID, req: TecnicaCreate):
    """
    Edita el catálogo de una técnica.
    """
    for index, t in enumerate(TECNICAS_DB):
        if t["id"] == tecnica_id:
            actualizada = {
                "id": tecnica_id,
                **req.model_dump()
            }
            TECNICAS_DB[index] = actualizada
            return TecnicaResponse(**actualizada)
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnica no encontrada.")

@router.delete("/{tecnica_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_tecnica(tecnica_id: UUID):
    """
    Elimina una técnica del catálogo y sus videos asociados en memoria.
    """
    global TECNICAS_DB
    global VIDEOS_REFERENCIA_DB
    
    if not any(t["id"] == tecnica_id for t in TECNICAS_DB):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnica no encontrada.")
        
    TECNICAS_DB = [t for t in TECNICAS_DB if t["id"] != tecnica_id]
    VIDEOS_REFERENCIA_DB = [v for v in VIDEOS_REFERENCIA_DB if v["tecnica_id"] != tecnica_id]
    
    return None

@router.post("/{tecnica_id}/video", status_code=status.HTTP_200_OK)
async def subir_video_referencia(
    tecnica_id: UUID,
    profesor_id: UUID = Form(...),
    video: UploadFile = File(...)
):
    """
    Sube un video de referencia para una técnica por parte de un profesor.
    (Relación M:N entre Profesores y Técnicas a través del video de referencia)
    """
    if not any(t["id"] == tecnica_id for t in TECNICAS_DB):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnica no encontrada en el catálogo.")
        
    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.webm')):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de video no soportado.")

    # Almacenar en disco local para previsualización MVP
    file_path = os.path.join(UPLOAD_DIR, f"{uuid4()}_{video.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
        
    # Remover video anterior si el profesor ya tenía uno para esta técnica
    global VIDEOS_REFERENCIA_DB
    VIDEOS_REFERENCIA_DB = [v for v in VIDEOS_REFERENCIA_DB if not (v["tecnica_id"] == tecnica_id and v["profesor_id"] == profesor_id)]
    
    nuevo_video = {
        "id": uuid4(),
        "tecnica_id": tecnica_id,
        "profesor_id": profesor_id,
        "url_video_local": file_path,
        "vector_qdrant_id": uuid4() # Simulado
    }
    VIDEOS_REFERENCIA_DB.append(nuevo_video)
    
    return {"status": "ok", "message": "Video de referencia actualizado.", "video_id": str(nuevo_video["id"])}
