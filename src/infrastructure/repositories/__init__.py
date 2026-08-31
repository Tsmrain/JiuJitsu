"""Módulo de repositorios de infraestructura."""

from src.infrastructure.repositories.analisis_repository import AnalisisBiomecanicoRepository
from src.infrastructure.repositories.tecnica_repository import TecnicaMaestraRepository
from src.infrastructure.repositories.video_repository import VideoEjecucionRepository

__all__ = [
    "AnalisisBiomecanicoRepository",
    "TecnicaMaestraRepository",
    "VideoEjecucionRepository",
]
