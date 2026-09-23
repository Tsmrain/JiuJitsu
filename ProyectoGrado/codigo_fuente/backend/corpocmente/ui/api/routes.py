import os
import shutil
import tempfile
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel

from corpocmente.domain.controllers.video_analysis_controller import VideoAnalysisController
from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter

router = APIRouter(prefix="/api/v1/evaluaciones", tags=["Evaluaciones"])

# Instanciación e inyección de dependencias (Singleton / Service Locator pattern en API Layer)
yolo_adapter = YOLOPoseAdapter()
qdrant_adapter = QdrantVectorAdapter()
gemini_adapter = GeminiApiAdapter()

facade = IntelligenceAnalysisFacade(
    yolo_adapter=yolo_adapter,
    qdrant_adapter=qdrant_adapter,
    gemini_adapter=gemini_adapter
)

controller = VideoAnalysisController(intelligence_facade=facade)

class AnalisisResponse(BaseModel):
    similitud: float
    feedback: str
    estado: str = "completado"

@router.post("/analizar", response_model=AnalisisResponse, status_code=status.HTTP_200_OK)
async def analizar_video(
    tecnica_id: UUID = Form(...),
    idioma: str = Form("es"),
    video: UploadFile = File(...)
):
    """
    Endpoint HTTP para procesar y analizar la ejecución de una técnica de Jiu-Jitsu.
    Recibe el archivo de video Multipart, lo almacena temporalmente y ejecuta el controlador.
    """
    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado. Debe ser un video (MP4, AVI, MOV, MKV)."
        )

    # Guardar video en un archivo temporal seguro
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        shutil.copyfileobj(video.file, temp_video)
        temp_video_path = temp_video.name

    try:
        resultado = controller.procesar_evaluacion_video(
            video_path=temp_video_path,
            tecnica_id=tecnica_id,
            idioma=idioma
        )
        return AnalisisResponse(
            similitud=resultado.similitud,
            feedback=resultado.feedback
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno procesando el video: {str(e)}"
        )
    finally:
        # Limpieza del archivo temporal local
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)

@router.post("/validar-spam", status_code=status.HTTP_200_OK)
async def validar_spam(video: UploadFile = File(...)):
    """
    Endpoint HTTP aislado para validar tempranamente si un video es de Jiu-Jitsu (SPAM filter).
    """
    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        shutil.copyfileobj(video.file, temp_video)
        temp_video_path = temp_video.name

    try:
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
