"""
Modelos ORM de Base de Datos - Estándar Mannino (SQLAlchemy 2.0)

Mapeo Objeto-Relacional de las entidades de dominio al esquema
relacional normalizado. Sigue el estándar de bases de datos de
Michael Mannino para la definición de restricciones, claves
foráneas y reglas de integridad.

Las tablas incluyen:
    - CHECK constraints para validación a nivel de BD (defensa en profundidad)
    - CASCADE DELETE para integridad referencial automática
    - Restricciones NOT NULL según las reglas de negocio

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM del sistema."""
    pass


# ──────────────────────────────────────────────
#  Tabla: tecnica_maestra
# ──────────────────────────────────────────────


class TecnicaMaestraDB(Base):
    """Tabla de técnicas maestras de referencia (Mannino - Entidad Fuerte).

    Almacena las técnicas de Jiu-Jitsu que sirven como patrón
    de comparación para el análisis biomecánico.
    """

    __tablename__ = "tecnica_maestra"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    categoria: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    posicion_origen: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    ventana_sakoe_chiba: Mapped[float] = mapped_column(
        Numeric(5, 2, asdecimal=False), nullable=False, default=0.15
    )
    video_url: Mapped[str] = mapped_column(
        String(500), nullable=False
    )

    # Relación 1:N con reglas biomecánicas (CASCADE DELETE)
    reglas: Mapped[List["ReglaBiomecanicaDB"]] = relationship(
        back_populates="tecnica",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<TecnicaMaestraDB(id={self.id}, nombre='{self.nombre}')>"


# ──────────────────────────────────────────────
#  Tabla: regla_biomecanica
# ──────────────────────────────────────────────


class ReglaBiomecanicaDB(Base):
    """Tabla de reglas biomecánicas (Mannino - Entidad Débil de tecnica_maestra).

    Cada regla define un umbral angular para una articulación específica.
    La existencia de una regla depende de su técnica maestra asociada.
    """

    __tablename__ = "regla_biomecanica"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tecnica_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tecnica_maestra.id", ondelete="CASCADE"),
        nullable=False,
    )
    articulacion_clave: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    umbral_angular_tolerado: Mapped[float] = mapped_column(
        Numeric(5, 2, asdecimal=False), nullable=False
    )
    descripcion_error: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    # Relación N:1 con técnica maestra
    tecnica: Mapped["TecnicaMaestraDB"] = relationship(
        back_populates="reglas"
    )

    def __repr__(self) -> str:
        return (
            f"<ReglaBiomecanicaDB(id={self.id}, "
            f"articulacion='{self.articulacion_clave}')>"
        )


# ──────────────────────────────────────────────
#  Tabla: video_ejecucion
# ──────────────────────────────────────────────


class VideoEjecucionDB(Base):
    """Tabla de videos de ejecución (Mannino - Entidad Fuerte).

    Almacena los metadatos de los videos subidos por practicantes.
    Incluye CHECK constraints a nivel de BD como defensa en profundidad
    contra datos inválidos (RF-07).
    """

    __tablename__ = "video_ejecucion"
    __table_args__ = (
        CheckConstraint(
            "peso_mb <= 5.0",
            name="ck_video_peso_maximo",
        ),
        CheckConstraint(
            "duracion_segundos <= 6.0",
            name="ck_video_duracion_maxima",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    duracion_segundos: Mapped[float] = mapped_column(
        Numeric(5, 2, asdecimal=False), nullable=False
    )
    peso_mb: Mapped[float] = mapped_column(
        Numeric(4, 2, asdecimal=False), nullable=False
    )
    video_url: Mapped[str] = mapped_column(
        String(500), nullable=False
    )

    # Relación 1:N con análisis biomecánicos (CASCADE DELETE)
    analisis_list: Mapped[List["AnalisisBiomecanicoDB"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<VideoEjecucionDB(id={self.id}, "
            f"peso_mb={self.peso_mb}, dur={self.duracion_segundos})>"
        )


# ──────────────────────────────────────────────
#  Tabla: analisis_biomecanico
# ──────────────────────────────────────────────


class AnalisisBiomecanicoDB(Base):
    """Tabla de resultados de análisis biomecánicos (Mannino - Entidad Débil de video).

    Almacena los resultados del pipeline de análisis, incluyendo
    la desviación máxima detectada y el estado del cómputo.
    """

    __tablename__ = "analisis_biomecanico"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("video_ejecucion.id", ondelete="CASCADE"),
        nullable=False,
    )
    fecha_procesamiento: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    desviacion_angular_maxima: Mapped[float] = mapped_column(
        Numeric(5, 2, asdecimal=False), nullable=False
    )
    articulacion_afectada: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    estado_computo: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    # Relación N:1 con video de ejecución
    video: Mapped["VideoEjecucionDB"] = relationship(
        back_populates="analisis_list"
    )

    def __repr__(self) -> str:
        return (
            f"<AnalisisBiomecanicoDB(id={self.id}, "
            f"estado='{self.estado_computo}')>"
        )
