"""Sincroniza el mensaje editorial del instructor con el índice RAG."""
import logging

from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter

logger = logging.getLogger(__name__)


def sincronizar_mensaje_profesor(tecnica_id: str, mensaje_profesor: str) -> int:
    """Reemplaza (no acumula) la instrucción vigente de una técnica en Qdrant."""
    rag = QdrantRAGAdapter()
    rag.eliminar_mensaje_profesor(tecnica_id)
    texto = (mensaje_profesor or "").strip()
    if not texto:
        logger.info("Mensaje de profesor eliminado de RAG para técnica %s", tecnica_id)
        return 0

    embedding = QwenEmbeddingAdapter().generar_embedding_texto(texto)
    rag.ingestar_desde_respuesta(
        {"chunks": [texto], "embeddings": [embedding]},
        tecnica_id=str(tecnica_id),
        fuente_tipo="instructor_message",
        fuente_nombre="Mensaje del profesor",
        alcance="tecnica",
        metadata_por_chunk=[{"media_path": None, "media_url": None, "modalidad": "texto"}],
    )
    logger.info("Mensaje de profesor indexado para técnica %s", tecnica_id)
    return 1
