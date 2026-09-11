"""Capa de Infraestructura (Infrastructure Layer).

Contiene adaptadores, repositorios y servicios externos (o sus simulaciones/mocks)
implementando los contratos definidos en la capa de dominio.
"""

from src.infrastructure.persistence import PostgresTecnicaRepository
from src.infrastructure.history_repository import PostgresHistorialRepository
from src.infrastructure.gemini_adapter import GeminiServiceAdapter
from src.infrastructure.colab_adapter import ColabYOLOAdapter
from src.infrastructure.rag_ingestion import IngestorRAG

__all__ = [
    "PostgresTecnicaRepository",
    "PostgresHistorialRepository",
    "GeminiServiceAdapter",
    "ColabYOLOAdapter",
    "IngestorRAG",
]
