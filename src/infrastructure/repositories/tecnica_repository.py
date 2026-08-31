"""
Repositorio Concreto - TecnicaMaestra (Patrón Repository)

Implementación concreta de ITecnicaMaestraRepository usando
SQLAlchemy 2.0. Encapsula toda la lógica de acceso a datos
para la entidad TecnicaMaestra, manteniendo alta cohesión.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from src.domain.models import ReglaBiomecanica, TecnicaMaestra
from src.infrastructure.database.models import (
    ReglaBiomecanicaDB,
    TecnicaMaestraDB,
)
from src.infrastructure.interfaces import ITecnicaMaestraRepository


class TecnicaMaestraRepository(ITecnicaMaestraRepository):
    """Repositorio concreto para TecnicaMaestra con SQLAlchemy.

    Encapsula el mapeo bidireccional entre el modelo de dominio
    (TecnicaMaestra) y el modelo ORM (TecnicaMaestraDB).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_id(self, id_tecnica: str) -> Optional[TecnicaMaestra]:
        """Recupera una técnica con sus reglas biomecánicas asociadas."""
        tecnica_uuid = uuid.UUID(id_tecnica)
        db_tecnica = self._session.get(TecnicaMaestraDB, tecnica_uuid)

        if db_tecnica is None:
            return None

        return self._orm_a_dominio(db_tecnica)

    def listar_todas(self) -> List[TecnicaMaestra]:
        """Lista todas las técnicas maestras con carga eager de reglas."""
        db_tecnicas = self._session.query(TecnicaMaestraDB).all()
        return [self._orm_a_dominio(t) for t in db_tecnicas]

    def guardar(self, tecnica: TecnicaMaestra) -> None:
        """Persiste una técnica maestra y sus reglas biomecánicas."""
        db_tecnica = self._dominio_a_orm(tecnica)
        self._session.merge(db_tecnica)
        self._session.commit()

    def eliminar(self, id_tecnica: str) -> bool:
        """Elimina una técnica (CASCADE elimina sus reglas automáticamente)."""
        tecnica_uuid = uuid.UUID(id_tecnica)
        db_tecnica = self._session.get(TecnicaMaestraDB, tecnica_uuid)

        if db_tecnica is None:
            return False

        self._session.delete(db_tecnica)
        self._session.commit()
        return True

    # ── Mappers: Dominio ↔ ORM ──

    @staticmethod
    def _dominio_a_orm(tecnica: TecnicaMaestra) -> TecnicaMaestraDB:
        """Convierte una entidad de dominio a modelo ORM."""
        db_reglas = [
            ReglaBiomecanicaDB(
                id=regla.id_regla,
                tecnica_id=tecnica.id_tecnica,
                articulacion_clave=regla.articulacion_clave,
                umbral_angular_tolerado=regla.umbral_angular_tolerado,
                descripcion_error=regla.descripcion_error,
            )
            for regla in tecnica.reglas
        ]

        return TecnicaMaestraDB(
            id=tecnica.id_tecnica,
            nombre=tecnica.nombre,
            categoria=tecnica.categoria,
            posicion_origen=tecnica.posicion_origen,
            ventana_sakoe_chiba=tecnica.ventana_sakoe_chiba,
            video_url=tecnica.video_url,
            reglas=db_reglas,
        )

    @staticmethod
    def _orm_a_dominio(db_tecnica: TecnicaMaestraDB) -> TecnicaMaestra:
        """Convierte un modelo ORM a entidad de dominio."""
        tecnica = TecnicaMaestra(
            id_tecnica=db_tecnica.id,
            nombre=db_tecnica.nombre,
            categoria=db_tecnica.categoria,
            posicion_origen=db_tecnica.posicion_origen,
            ventana_sakoe_chiba=float(db_tecnica.ventana_sakoe_chiba),
            video_url=db_tecnica.video_url,
        )

        for db_regla in db_tecnica.reglas:
            regla = ReglaBiomecanica(
                id_regla=db_regla.id,
                articulacion_clave=db_regla.articulacion_clave,
                umbral_angular_tolerado=float(db_regla.umbral_angular_tolerado),
                descripcion_error=db_regla.descripcion_error,
            )
            tecnica.agregar_regla(regla)

        return tecnica
