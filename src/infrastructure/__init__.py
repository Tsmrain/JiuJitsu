"""Capa de Infraestructura (Infrastructure Layer).

Contiene adaptadores, repositorios y servicios externos implementando
los contratos definidos en la capa de dominio (Larman, Proceso Unificado).

Estructura interna:
    adapters/    — Adaptadores para YOLO26x (Colab), Gemini AI y embeddings
    persistence/ — Repositorios SQL (PostgreSQL + pgvector) y pipeline RAG
    mocks.py     — Dobles de prueba para TDD sin dependencias externas
"""

# Adapters
from src.infrastructure.adapters import (
    ColabYOLOAdapter,
    GeminiServiceAdapter,
    AdaptadorYOLO,
    AdaptadorGemini,
    GeminiEmbedding2Adapter,
)

# Persistence
from src.infrastructure.persistence import (
    PostgresTecnicaRepository,
    PostgresProfesorRepository,
    PostgresFuenteConocimientoRepository,
    PostgresHistorialRepository,
    IngestorRAG,
    PipelineIngestaRAG,
)

__all__ = [
    # Adapters
    "ColabYOLOAdapter",
    "GeminiServiceAdapter",
    "AdaptadorYOLO",
    "AdaptadorGemini",
    "GeminiEmbedding2Adapter",
    # Persistence
    "PostgresTecnicaRepository",
    "PostgresProfesorRepository",
    "PostgresFuenteConocimientoRepository",
    "PostgresHistorialRepository",
    "IngestorRAG",
    "PipelineIngestaRAG",
]
