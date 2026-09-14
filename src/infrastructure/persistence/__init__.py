"""Adaptadores de Persistencia (Infrastructure Persistence).

Repositorios concretos que implementan los contratos de dominio (IProfesorRepository,
ITecnicaRepository, IFuenteConocimientoRepository) sobre PostgreSQL + pgvector.
Diseño normalizado hasta BCNF (Mannino, 7th Ed., Cap. 6-8).
"""

from src.infrastructure.persistence.postgres_repository import (
    PostgresTecnicaRepository,
    PostgresProfesorRepository,
    PostgresFuenteConocimientoRepository,
)
from src.infrastructure.persistence.history_repository import PostgresHistorialRepository
from src.infrastructure.persistence.rag_ingestion import IngestorRAG, PipelineIngestaRAG

__all__ = [
    "PostgresTecnicaRepository",
    "PostgresProfesorRepository",
    "PostgresFuenteConocimientoRepository",
    "PostgresHistorialRepository",
    "IngestorRAG",
    "PipelineIngestaRAG",
]
