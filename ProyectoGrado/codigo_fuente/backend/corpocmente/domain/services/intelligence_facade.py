import logging
from corpocmente.domain.entities.models import AnalisisResultDTO
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
from corpocmente.domain.strategies.prompt_strategies import SpanishPromptStrategy
from uuid import UUID

logger = logging.getLogger(__name__)

class IntelligenceAnalysisFacade:
    def __init__(self, 
                 yolo_adapter: YOLOPoseAdapter, 
                 qdrant_adapter: QdrantVectorAdapter, 
                 gemini_adapter: GeminiApiAdapter,
                 qwen_adapter: QwenEmbeddingAdapter = None):
        self.yolo = yolo_adapter
        self.qdrant = qdrant_adapter
        self.gemini = gemini_adapter
        self.qwen = qwen_adapter

    def ejecutar_analisis_completo(self, video_path: str, tecnica_id: UUID, tecnica_nombre: str) -> AnalisisResultDTO:
        # 1. Extraer esqueleto con YOLO (frame a frame)
        esqueletos_frames = self.yolo.extraer_keypoints(video_path)
        if not esqueletos_frames:
            raise ValueError("No se pudo detectar el esqueleto biomecánico.")

        # 2. Buscar similitud matemática del fotograma con mayor diferencia (en Qdrant)
        resultado_comparacion = self.qdrant.buscar_maxima_diferencia(esqueletos_frames, tecnica_id)
        
        similitud = resultado_comparacion.score
        UMBRAL_ACEPTABLE = 85.0  # escala 0–100 (score ya viene multiplicado ×100)

        # 3. Lógica Condicional para evitar invocar a la IA si está bien
        if similitud >= UMBRAL_ACEPTABLE:
            feedback_texto = "¡Técnica ejecutada correctamente. Excelente trabajo!"
        else:
            # 4. Dibujar/Resaltar el error en el fotograma crítico usando YOLO
            frame_resaltado = self.yolo.dibujar_error_en_frame(
                resultado_comparacion.frame_path, 
                resultado_comparacion.discrepancias
            )

            # 5. Recuperar teoría RAG desde Qdrant usando una query textual (C11.4)
            # Se construye una query con el nombre de la técnica + las discrepancias detectadas,
            # se vectoriza con Qwen (endpoint /embed_text) y se buscan los chunks más similares.
            contexto_profundo = ""
            if self.qwen:
                try:
                    discrepancias_str = "; ".join(resultado_comparacion.discrepancias) if resultado_comparacion.discrepancias else "sin detalles específicos"
                    query_textual = (
                        f"Técnica de Jiu-Jitsu: {tecnica_nombre}. "
                        f"Errores biomecánicos detectados: {discrepancias_str}. "
                        f"¿Cuál es la forma correcta de ejecutar esta técnica y cómo corregir estos errores?"
                    )
                    logger.info(f"Construyendo query textual para RAG: {query_textual[:120]}...")
                    
                    embedding_qwen = self.qwen.generar_embedding_texto(query_textual)
                    teoria = self.qdrant.recuperar_contexto_rag(embedding_qwen, tecnica_id)
                    
                    if teoria:
                        contexto_profundo = f"\n\n[Teoría Biomecánica Recuperada (RAG)]:\n{teoria}"
                        logger.info(f"Contexto RAG recuperado: {len(teoria)} caracteres.")
                    else:
                        logger.info("Sin teoría RAG adicional para esta técnica.")
                except Exception as e:
                    logger.warning(f"Fallo en recuperación RAG (no bloqueante): {e}")

            # 6. Usar estrategia de idioma en español y pasar contexto de la técnica
            strategy = SpanishPromptStrategy()
                
            prompt = strategy.construir_prompt_evaluacion(tecnica_nombre, resultado_comparacion.discrepancias)
            if contexto_profundo:
                prompt += contexto_profundo

            # 6. Generar feedback pedagógico con Gemini API usando el frame dibujado
            feedback_texto = self.gemini.generar_texto_feedback(prompt, frame_resaltado)

        return AnalisisResultDTO(
            similitud=similitud,
            feedback=feedback_texto
        )
