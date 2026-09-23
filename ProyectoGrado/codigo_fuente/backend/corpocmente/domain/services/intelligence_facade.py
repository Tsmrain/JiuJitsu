from corpocmente.domain.entities.models import AnalisisResultDTO
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
from corpocmente.domain.strategies.prompt_strategies import PortuguesePromptStrategy, SpanishPromptStrategy
from uuid import UUID

class IntelligenceAnalysisFacade:
    def __init__(self, 
                 yolo_adapter: YOLOPoseAdapter, 
                 qdrant_adapter: QdrantVectorAdapter, 
                 gemini_adapter: GeminiApiAdapter):
        self.yolo = yolo_adapter
        self.qdrant = qdrant_adapter
        self.gemini = gemini_adapter

    def ejecutar_analisis_completo(self, video_path: str, tecnica_id: UUID, idioma: str) -> AnalisisResultDTO:
        # 1. Extraer esqueleto con YOLO
        esqueletos = self.yolo.extraer_keypoints(video_path)
        if not esqueletos:
            raise ValueError("No se pudo detectar el esqueleto biomecánico.")
            
        vector_alumno = esqueletos[0].to_vector_array()

        # 2. Buscar similitud en Qdrant
        resultado_vector = self.qdrant.buscar_similitud_pose(vector_alumno, tecnica_id)

        # 3. Seleccionar estrategia de idioma
        if idioma == 'pt':
            strategy = PortuguesePromptStrategy()
        else:
            strategy = SpanishPromptStrategy()
            
        prompt = strategy.construir_prompt_evaluacion(resultado_vector.discrepancias)

        # 4. Generar feedback con Gemini API
        feedback_texto = self.gemini.generar_texto_feedback(prompt, resultado_vector.frame_path)

        return AnalisisResultDTO(
            similitud=resultado_vector.score,
            feedback=feedback_texto
        )
