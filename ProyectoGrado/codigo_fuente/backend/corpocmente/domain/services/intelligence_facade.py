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

    def ejecutar_analisis_completo(self, video_path: str, tecnica_id: UUID, tecnica_nombre: str, idioma: str) -> AnalisisResultDTO:
        # 1. Extraer esqueleto con YOLO (frame a frame)
        esqueletos_frames = self.yolo.extraer_keypoints(video_path)
        if not esqueletos_frames:
            raise ValueError("No se pudo detectar el esqueleto biomecánico.")

        # 2. Buscar similitud matemática del fotograma con mayor diferencia (en Qdrant)
        resultado_comparacion = self.qdrant.buscar_maxima_diferencia(esqueletos_frames, tecnica_id)
        
        similitud = resultado_comparacion.score
        UMBRAL_ACEPTABLE = 0.85

        # 3. Lógica Condicional para evitar invocar a la IA si está bien
        if similitud >= UMBRAL_ACEPTABLE:
            feedback_texto = "Técnica executada corretamente. Excelente trabalho!" if idioma == 'pt' else "¡Técnica ejecutada correctamente. Excelente trabajo!"
        else:
            # 4. Dibujar/Resaltar el error en el fotograma crítico usando YOLO
            frame_resaltado = self.yolo.dibujar_error_en_frame(
                resultado_comparacion.frame_path, 
                resultado_comparacion.discrepancias
            )

            # 5. Seleccionar estrategia de idioma y pasar contexto de la técnica
            if idioma == 'pt':
                strategy = PortuguesePromptStrategy()
            else:
                strategy = SpanishPromptStrategy()
                
            prompt = strategy.construir_prompt_evaluacion(tecnica_nombre, resultado_comparacion.discrepancias)

            # 6. Generar feedback pedagógico con Gemini API usando el frame dibujado
            feedback_texto = self.gemini.generar_texto_feedback(prompt, frame_resaltado)

        return AnalisisResultDTO(
            similitud=similitud,
            feedback=feedback_texto
        )
