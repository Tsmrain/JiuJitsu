import logging
from uuid import UUID
from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
from corpocmente.domain.entities.models import AnalisisResultDTO

logger = logging.getLogger(__name__)

class VideoAnalysisController:
    """
    Controlador de Caso de Uso (GRASP Controller).
    
    Responsable de recibir los eventos del sistema (SSD) desde la interfaz de usuario,
    validar precondiciones y coordinar la ejecución con la Fachada de Inteligencia.
    """

    def __init__(self, intelligence_facade: IntelligenceAnalysisFacade):
        self.facade = intelligence_facade

    def procesar_evaluacion_video(self, 
                                   video_path: str, 
                                   tecnica_id: UUID,
                                   tecnica_nombre: str, 
                                   idioma: str = "es") -> AnalisisResultDTO:
        """
        Orquesta la ejecución del Caso de Uso UC1: 'Analizar Técnica y Generar Feedback'.
        
        1. Valida si el contenido corresponde a Jiu-Jitsu (Filtro de SPAM - Flujo 2a).
        2. Si es válido, delega el procesamiento multimodal e inferencia vectorial a la Fachada.
        """
        logger.info(f"Iniciando evaluación de video para técnica {tecnica_id} en idioma '{idioma}'")

        # 1. Validación de SPAM con Gemini
        es_valido = self.facade.gemini.validar_es_jiujitsu(video_path)
        if not es_valido:
            raise ValueError("El video proporcionado no corresponde a la ejecución de una técnica de Jiu-Jitsu válida.")

        # 2. Inferencia Completa (YOLO + Qdrant + Gemini Strategy Condicional)
        resultado = self.facade.ejecutar_analisis_completo(
            video_path=video_path,
            tecnica_id=tecnica_id,
            tecnica_nombre=tecnica_nombre,
            idioma=idioma
        )

        logger.info(f"Evaluación completada con éxito. Similitud: {resultado.similitud}%")
        return resultado
