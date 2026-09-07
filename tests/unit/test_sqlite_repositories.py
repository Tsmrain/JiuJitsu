import uuid
import pytest
from datetime import datetime
from uuid import UUID

from src.infrastructure.repositories import SQLiteDB, TecnicaMaestraRepository, AnalisisRepository
from src.domain.entities import TecnicaMaestra, ReglaBiomecanica, AnalisisBiomecanico, FotogramaAnotado
from src.domain.value_objects import ErrorBiomecanico


class TestSQLiteRepositories:
    """Pruebas unitarias para persistencia relacional SQLite (Mannino)."""

    def test_sqlite_foreign_keys_activas(self):
        """Verifica que SQLite tenga habilitada la integridad referencial (PRAGMA foreign_keys = ON)."""
        db = SQLiteDB()
        cursor = db.get_cursor()
        cursor.execute("PRAGMA foreign_keys;")
        row = cursor.fetchone()
        assert row[0] == 1, "Las Foreign Keys deben estar activadas en SQLite (Mannino)."

    def test_tecnica_maestra_guardar_y_recuperar(self):
        """Verifica que TecnicaMaestraRepository persista y recupere técnicas con sus reglas asociadas."""
        repo = TecnicaMaestraRepository()
        t_id = uuid.uuid4()
        regla = ReglaBiomecanica(articulacion_clave="codo_der", umbral_angular_tolerado=15.0, descripcion_error="Codo abierto")
        tecnica = TecnicaMaestra(
            id=t_id,
            nombre="Armbar desde Guardia",
            categoria="Finalización",
            posicion_origen="Guardia Cerrada",
            video_url="uploads/maestro_armbar.mp4",
            ventana_sakoe_chiba=0.15,
            reglas=[regla]
        )

        repo.guardar(tecnica)
        recuperada = repo.obtener_por_id(t_id)

        assert recuperada is not None
        assert recuperada.id == t_id
        assert recuperada.nombre == "Armbar desde Guardia"
        assert len(recuperada.reglas) == 1
        assert recuperada.reglas[0].articulacion_clave == "codo_der"

    def test_analisis_guardar_y_recuperar(self):
        """Verifica que AnalisisRepository persista fotogramas anotados y lista de errores."""
        repo = AnalisisRepository()
        a_id = uuid.uuid4()
        v_id = uuid.uuid4()

        fotograma = FotogramaAnotado(
            imagen_url="resultados/fotogramas/error_01.jpg",
            coordenada_error_x=320,
            coordenada_error_y=240,
            explicacion_causa="Desviación angular excesiva"
        )
        error = ErrorBiomecanico(
            articulacion="rodilla_izq",
            angulo_alumno=90.0,
            angulo_maestro=120.0,
            diferencia=30.0,
            frame=15,
            mensaje="Rodilla no extendida"
        )

        analisis = AnalisisBiomecanico(
            id=a_id,
            video_id=v_id,
            desviacion_angular_maxima=30.0,
            articulacion_afectada="rodilla_izq",
            estado_computo="completado",
            fotograma_anotado=fotograma,
            errores=[error]
        )

        repo.guardar(analisis)
        recuperado = repo.obtener_por_id(a_id)

        assert recuperado is not None
        assert recuperado.id == a_id
        assert recuperado.desviacion_angular_maxima == 30.0
        assert recuperado.fotograma_anotado is not None
        assert recuperado.fotograma_anotado.coordenada_error_x == 320
        assert len(recuperado.errores) == 1
        assert recuperado.errores[0].articulacion == "rodilla_izq"
