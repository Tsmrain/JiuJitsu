"""Capa de Infraestructura (Infrastructure Layer).

Contiene adaptadores, repositorios y servicios externos implementando
los contratos definidos en la capa de dominio (Larman, Proceso Unificado).

Estructura interna:
    adapters/    — Adaptadores para YOLO26x (Colab), Gemini AI, Qwen embeddings y Qdrant
    persistence/ — Repositorios SQL (PostgreSQL BCNF) y pipeline RAG con Qdrant
    mocks.py     — Dobles de prueba para TDD sin dependencias externas
"""

# Adapters
from src.infrastructure.adapters import (
    ColabYOLOAdapter,
    GeminiServiceAdapter,
    AdaptadorYOLO,
    QwenEmbeddingAdapter,
    QdrantAdapter,
)

# Persistence
from src.infrastructure.persistence import (
    PostgresTecnicaRepository,
    PostgresProfesorRepository,
    PostgresFuenteConocimientoRepository,
    PostgresHistorialRepository,
    PipelineIngestaRAG,
)

__all__ = [
    # Adapters
    "ColabYOLOAdapter",
    "GeminiServiceAdapter",
    "AdaptadorYOLO",
    "QwenEmbeddingAdapter",
    "QdrantAdapter",
    # Persistence
    "PostgresTecnicaRepository",
    "PostgresProfesorRepository",
    "PostgresFuenteConocimientoRepository",
    "PostgresHistorialRepository",
    "PipelineIngestaRAG",
]

