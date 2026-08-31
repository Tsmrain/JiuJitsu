"""
Repositorio Concreto - AnalisisBiomecanico (Patrón Repository)

Implementación concreta de IAnalisisBiomecanicoRepository usando
SQLAlchemy 2.0. Encapsula la persistencia de los resultados del
análisis biomecánico generados por el pipeline.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from src.domain.models import AnalisisBiomecanico
from src.infrastructure.database.models import AnalisisBiomecanicoDB
from src.infrastructure.interfaces import IAnalisisBiomecanicoRepository


class AnalisisBiomecanicoRepository(IAnalisisBiomecanicoRepository):
    """Repositorio concreto para AnalisisBiomecanico con SQLAlchemy.

    La tabla tiene una FK con CASCADE DELETE hacia video_ejecucion:
    al eliminar un video, sus análisis asociados se eliminan
    automáticamente.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, analisis: AnalisisBiomecanico) -> None:
        """Persiste un resultado de análisis biomecánico."""
        db_analisis = self._dominio_a_orm(analisis)
        self._session.merge(db_analisis)
        self._session.commit()

    def obtener_por_id(
        self, id_analisis: str
    ) -> Optional[AnalisisBiomecanico]:
        """Recupera un análisis por su identificador único."""
        analisis_uuid = uuid.UUID(id_analisis)
        db_analisis = self._session.get(AnalisisBiomecanicoDB, analisis_uuid)

        if db_analisis is None:
            return None

        return self._orm_a_dominio(db_analisis)

    # ── Mappers: Dominio ↔ ORM ──

    @staticmethod
    def _dominio_a_orm(
        analisis: AnalisisBiomecanico,
    ) -> AnalisisBiomecanicoDB:
        """Convierte una entidad de dominio a modelo ORM."""
        return AnalisisBiomecanicoDB(
            id=analisis.id_analisis,
            video_id=analisis.video_id,
            fecha_procesamiento=analisis.fecha_procesamiento,
            desviacion_angular_maxima=analisis.desviacion_angular_maxima,
            articulacion_afectada=analisis.articulacion_afectada,
            estado_computo=analisis.estado_computo,
        )

    @staticmethod
    def _orm_a_dominio(
        db_analisis: AnalisisBiomecanicoDB,
    ) -> AnalisisBiomecanico:
        """Convierte un modelo ORM a entidad de dominio."""
        return AnalisisBiomecanico(
            id_analisis=db_analisis.id,
            video_id=db_analisis.video_id,
            fecha_procesamiento=db_analisis.fecha_procesamiento,
            desviacion_angular_maxima=float(
                db_analisis.desviacion_angular_maxima
            ),
            articulacion_afectada=db_analisis.articulacion_afectada,
            estado_computo=db_analisis.estado_computo,
        )
