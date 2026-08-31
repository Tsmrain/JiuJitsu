"""
Pruebas Unitarias - Repositorios Concretos (TDD con SQLite en Memoria)

Pruebas de integración para los repositorios de persistencia usando
SQLAlchemy 2.0 con SQLite en memoria (:memory:). Valida el mapeo
dominio↔ORM, restricciones CHECK (Mannino) y CASCADE DELETE.

IMPORTANTE: Se habilita PRAGMA foreign_keys=ON para que SQLite
            respete las restricciones de integridad referencial.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from src.domain.models import (
    AnalisisBiomecanico,
    ReglaBiomecanica,
    TecnicaMaestra,
    VideoEjecucion,
)
from src.infrastructure.database.models import (
    AnalisisBiomecanicoDB,
    Base,
    ReglaBiomecanicaDB,
    TecnicaMaestraDB,
    VideoEjecucionDB,
)
from src.infrastructure.repositories.analisis_repository import (
    AnalisisBiomecanicoRepository,
)
from src.infrastructure.repositories.tecnica_repository import (
    TecnicaMaestraRepository,
)
from src.infrastructure.repositories.video_repository import (
    VideoEjecucionRepository,
)


# ──────────────────────────────────────────────
#  Fixtures
# ──────────────────────────────────────────────


@pytest.fixture
def db_session():
    """Crea una sesión SQLAlchemy con SQLite en memoria para cada test.

    - Habilita PRAGMA foreign_keys=ON para CASCADE DELETE.
    - Crea todas las tablas antes del test.
    - Hace rollback y cierra la sesión después del test.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()
    engine.dispose()


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────


def _crear_tecnica_con_reglas() -> TecnicaMaestra:
    """Crea una TecnicaMaestra de dominio con 2 reglas biomecánicas."""
    tecnica = TecnicaMaestra(
        nombre="Armbar",
        categoria="Sumisión",
        posicion_origen="Guardia Cerrada",
        video_url="https://obs.example.com/armbar_ref.mp4",
        ventana_sakoe_chiba=0.15,
    )

    tecnica.agregar_regla(ReglaBiomecanica(
        articulacion_clave="codo_derecho",
        umbral_angular_tolerado=180.0,
        descripcion_error="Hiperextensión del codo derecho",
    ))
    tecnica.agregar_regla(ReglaBiomecanica(
        articulacion_clave="hombro_derecho",
        umbral_angular_tolerado=90.0,
        descripcion_error="Rotación excesiva del hombro",
    ))

    return tecnica


def _crear_video_valido() -> VideoEjecucion:
    """Crea un VideoEjecucion dentro de los límites."""
    return VideoEjecucion(
        duracion_segundos=5.0,
        peso_mb=4.5,
        video_url="https://obs.example.com/ejecucion_001.mp4",
    )


# ──────────────────────────────────────────────
#  TecnicaMaestraRepository
# ──────────────────────────────────────────────


class TestTecnicaMaestraRepository:
    """Pruebas para el repositorio de técnicas maestras."""

    def test_tecnica_repository_guardar_y_obtener(
        self, db_session: Session
    ) -> None:
        """Guarda una técnica con reglas y la recupera con relaciones intactas."""
        repo = TecnicaMaestraRepository(db_session)
        tecnica = _crear_tecnica_con_reglas()

        repo.guardar(tecnica)

        # Recuperar por ID
        recuperada = repo.obtener_por_id(str(tecnica.id_tecnica))

        assert recuperada is not None
        assert recuperada.nombre == "Armbar"
        assert recuperada.categoria == "Sumisión"
        assert recuperada.posicion_origen == "Guardia Cerrada"
        assert recuperada.ventana_sakoe_chiba == pytest.approx(0.15)
        assert len(recuperada.reglas) == 2

        # Verificar reglas cargadas
        articulaciones = {r.articulacion_clave for r in recuperada.reglas}
        assert articulaciones == {"codo_derecho", "hombro_derecho"}

    def test_tecnica_repository_obtener_inexistente(
        self, db_session: Session
    ) -> None:
        """Obtener técnica inexistente retorna None."""
        repo = TecnicaMaestraRepository(db_session)
        resultado = repo.obtener_por_id(str(uuid.uuid4()))
        assert resultado is None

    def test_tecnica_repository_listar_todas(
        self, db_session: Session
    ) -> None:
        """Listar técnicas retorna todas las registradas."""
        repo = TecnicaMaestraRepository(db_session)

        tecnica1 = _crear_tecnica_con_reglas()
        tecnica2 = TecnicaMaestra(
            nombre="Triangle Choke",
            categoria="Sumisión",
            posicion_origen="Guardia Cerrada",
            video_url="https://obs.example.com/triangle_ref.mp4",
        )

        repo.guardar(tecnica1)
        repo.guardar(tecnica2)

        todas = repo.listar_todas()
        assert len(todas) == 2
        nombres = {t.nombre for t in todas}
        assert nombres == {"Armbar", "Triangle Choke"}

    def test_tecnica_repository_eliminar_cascade(
        self, db_session: Session
    ) -> None:
        """Eliminar técnica → CASCADE elimina sus reglas biomecánicas."""
        repo = TecnicaMaestraRepository(db_session)
        tecnica = _crear_tecnica_con_reglas()
        repo.guardar(tecnica)

        # Verificar que las reglas existen en la BD
        reglas_antes = db_session.query(ReglaBiomecanicaDB).all()
        assert len(reglas_antes) == 2

        # Eliminar técnica
        eliminada = repo.eliminar(str(tecnica.id_tecnica))
        assert eliminada is True

        # Verificar que las reglas se eliminaron por CASCADE
        reglas_despues = db_session.query(ReglaBiomecanicaDB).all()
        assert len(reglas_despues) == 0

        # Verificar que la técnica ya no existe
        assert repo.obtener_por_id(str(tecnica.id_tecnica)) is None

    def test_tecnica_repository_eliminar_inexistente(
        self, db_session: Session
    ) -> None:
        """Eliminar técnica inexistente retorna False."""
        repo = TecnicaMaestraRepository(db_session)
        resultado = repo.eliminar(str(uuid.uuid4()))
        assert resultado is False


# ──────────────────────────────────────────────
#  VideoEjecucionRepository
# ──────────────────────────────────────────────


class TestVideoEjecucionRepository:
    """Pruebas para el repositorio de videos de ejecución."""

    def test_video_repository_guardar_exitoso(
        self, db_session: Session
    ) -> None:
        """Guarda un video dentro de los límites sin errores."""
        repo = VideoEjecucionRepository(db_session)
        video = _crear_video_valido()

        repo.guardar(video)

        # Verificar persistencia directa
        db_video = db_session.get(VideoEjecucionDB, video.id_video)
        assert db_video is not None
        assert db_video.peso_mb == pytest.approx(4.5)
        assert db_video.duracion_segundos == pytest.approx(5.0)

    def test_video_repository_check_constraint_peso(
        self, db_session: Session
    ) -> None:
        """Video con peso_mb > 5.0 → IntegrityError por CHECK constraint.

        Defensa en profundidad (Mannino): la BD rechaza datos inválidos
        incluso si la validación del dominio fue omitida.
        """
        repo = VideoEjecucionRepository(db_session)
        video = VideoEjecucion(
            duracion_segundos=5.0,
            peso_mb=6.0,  # Excede el CHECK constraint
            video_url="https://obs.example.com/video_grande.mp4",
        )

        with pytest.raises(IntegrityError):
            repo.guardar(video)

    def test_video_repository_check_constraint_duracion(
        self, db_session: Session
    ) -> None:
        """Video con duracion > 6.0 → IntegrityError por CHECK constraint."""
        repo = VideoEjecucionRepository(db_session)
        video = VideoEjecucion(
            duracion_segundos=7.0,  # Excede el CHECK constraint
            peso_mb=4.0,
            video_url="https://obs.example.com/video_largo.mp4",
        )

        with pytest.raises(IntegrityError):
            repo.guardar(video)


# ──────────────────────────────────────────────
#  AnalisisBiomecanicoRepository + CASCADE DELETE
# ──────────────────────────────────────────────


class TestAnalisisBiomecanicoRepository:
    """Pruebas para el repositorio de análisis biomecánicos."""

    def test_analisis_repository_guardar_y_obtener(
        self, db_session: Session
    ) -> None:
        """Guarda un análisis asociado a un video y lo recupera."""
        video_repo = VideoEjecucionRepository(db_session)
        analisis_repo = AnalisisBiomecanicoRepository(db_session)

        # Primero crear el video (FK)
        video = _crear_video_valido()
        video_repo.guardar(video)

        # Crear y guardar análisis
        analisis = AnalisisBiomecanico(
            desviacion_angular_maxima=12.5,
            articulacion_afectada="codo_derecho",
            estado_computo="EXITOSO",
            video_id=video.id_video,
        )
        analisis_repo.guardar(analisis)

        # Recuperar
        recuperado = analisis_repo.obtener_por_id(str(analisis.id_analisis))

        assert recuperado is not None
        assert recuperado.desviacion_angular_maxima == pytest.approx(12.5)
        assert recuperado.articulacion_afectada == "codo_derecho"
        assert recuperado.estado_computo == "EXITOSO"
        assert recuperado.video_id == video.id_video

    def test_analisis_repository_cascade_delete(
        self, db_session: Session
    ) -> None:
        """Eliminar video → CASCADE elimina sus análisis asociados.

        Verifica la integridad referencial automática definida
        por el FK con ON DELETE CASCADE (Mannino).
        """
        video_repo = VideoEjecucionRepository(db_session)
        analisis_repo = AnalisisBiomecanicoRepository(db_session)

        # Crear video y análisis asociado
        video = _crear_video_valido()
        video_repo.guardar(video)

        analisis = AnalisisBiomecanico(
            desviacion_angular_maxima=8.3,
            articulacion_afectada="rodilla_izquierda",
            estado_computo="EXITOSO",
            video_id=video.id_video,
        )
        analisis_repo.guardar(analisis)

        # Verificar que el análisis existe
        assert analisis_repo.obtener_por_id(str(analisis.id_analisis)) is not None

        # Eliminar el video → CASCADE debe eliminar el análisis
        db_video = db_session.get(VideoEjecucionDB, video.id_video)
        db_session.delete(db_video)
        db_session.commit()

        # Verificar que el análisis fue eliminado en cascada
        assert analisis_repo.obtener_por_id(str(analisis.id_analisis)) is None

        # Verificar que no quedan registros huérfanos
        analisis_restantes = db_session.query(AnalisisBiomecanicoDB).all()
        assert len(analisis_restantes) == 0
