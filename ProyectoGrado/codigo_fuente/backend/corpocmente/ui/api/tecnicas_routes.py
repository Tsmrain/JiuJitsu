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

import json

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
    },
    {
        "id": UUID("a1b2c3d4-e5f6-4a5b-8c9d-0123456789ab"),
        "nombre": "Salir de 100 kilos",
        "nivel_cinturon": "Blanco"
    }
]

# Tabla asociativa: Un profesor sube un video para una técnica
VIDEOS_REFERENCIA_DB = []

# Para guardar temporalmente videos en desarrollo
UPLOAD_DIR = "/tmp/corpocmente_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
DB_FILE = "/tmp/corpocmente_tecnicas_db.json"

# Auto-detectar video subido previo
_existing_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".mp4") or f.endswith(".mov") or f.endswith(".webm")]
if _existing_files:
    _video_file_path = os.path.join(UPLOAD_DIR, _existing_files[0])
    VIDEOS_REFERENCIA_DB.append({
        "id": UUID("f1e2d3c4-b5a6-4f7e-8d9c-0123456789cd"),
        "tecnica_id": UUID("a1b2c3d4-e5f6-4a5b-8c9d-0123456789ab"),
        "profesor_id": UUID("7e455a7d-cbc8-4190-9a10-3b959f6425fc"), # Profesor Mike
        "url_video_local": _video_file_path,
        "vector_qdrant_id": UUID("11111111-2222-3333-4444-555555555555")
    })

def _save_db():
    try:
        data = {
            "tecnicas": [{**t, "id": str(t["id"])} for t in TECNICAS_DB],
            "videos": [{**v, "id": str(v["id"]), "tecnica_id": str(v["tecnica_id"]), "profesor_id": str(v["profesor_id"])} for v in VIDEOS_REFERENCIA_DB]
        }
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Error saving DB:", e)

def _load_db():
    global TECNICAS_DB, VIDEOS_REFERENCIA_DB
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                if data.get("tecnicas"):
                    TECNICAS_DB = [{**t, "id": UUID(t["id"])} for t in data["tecnicas"]]
                if data.get("videos"):
                    VIDEOS_REFERENCIA_DB = [
                        {**v, "id": UUID(v["id"]), "tecnica_id": UUID(v["tecnica_id"]), "profesor_id": UUID(v["profesor_id"])}
                        for v in data["videos"]
                    ]
        except Exception as e:
            print("Error loading DB:", e)

_load_db()

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
    _save_db()
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
            _save_db()
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
    _save_db()
    
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
    _save_db()
    
    return {"status": "ok", "message": "Video de referencia actualizado.", "video_id": str(nuevo_video["id"])}
