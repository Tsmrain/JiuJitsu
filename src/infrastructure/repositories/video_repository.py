"""
Repositorio Concreto - VideoEjecucion (Patrón Repository)

Implementación concreta de IVideoEjecucionRepository usando
SQLAlchemy 2.0. Encapsula la persistencia de metadatos de
videos de ejecución subidos por los practicantes.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain.models import VideoEjecucion
from src.infrastructure.database.models import VideoEjecucionDB
from src.infrastructure.interfaces import IVideoEjecucionRepository


class VideoEjecucionRepository(IVideoEjecucionRepository):
    """Repositorio concreto para VideoEjecucion con SQLAlchemy.

    La tabla subyacente incluye CHECK constraints (RF-07) que
    refuerzan la validación de negocio a nivel de base de datos.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, video: VideoEjecucion) -> None:
        """Persiste los metadatos de un video de ejecución.

        Raises:
            sqlalchemy.exc.IntegrityError: Si peso_mb > 5.0 o
                duracion_segundos > 6.0 (CHECK constraint).
        """
        db_video = self._dominio_a_orm(video)
        self._session.merge(db_video)
        self._session.commit()

    # ── Mapper: Dominio → ORM ──

    @staticmethod
    def _dominio_a_orm(video: VideoEjecucion) -> VideoEjecucionDB:
        """Convierte una entidad de dominio a modelo ORM."""
        return VideoEjecucionDB(
            id=video.id_video,
            duracion_segundos=video.duracion_segundos,
            peso_mb=video.peso_mb,
            video_url=video.video_url,
        )
