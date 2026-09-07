import pytest
import numpy as np
from uuid import UUID

from src.domain.value_objects import Keypoint, Frame, AnguloArticular, ErrorBiomecanico
from src.domain.entities import TecnicaMaestra, AnalisisBiomecanico, FotogramaAnotado


class TestValueObjects:
    """Pruebas unitarias para objetos de valor inmutables y entidades (TDD - Craig Larman)."""

    def test_keypoint_inmutabilidad(self):
        """Prueba: Keypoint es inmutable y convertible a array NumPy."""
        kp = Keypoint(x=100.0, y=150.0, confianza=0.98)
        assert kp.x == 100.0
        assert kp.y == 150.0
        arr = kp.to_array()
        assert isinstance(arr, np.ndarray)
        assert arr.tolist() == [100.0, 150.0]

        with pytest.raises((AttributeError, TypeError)):
            kp.x = 200.0

    def test_frame_acceso_keypoints(self):
        """Prueba: Frame indexa y recupera keypoints correctamente."""
        kp0 = Keypoint(x=5.0, y=5.0)
        kp1 = Keypoint(x=15.0, y=15.0)
        frame = Frame(index=3, keypoints=[kp0, kp1])

        assert frame.index == 3
        assert frame.get_keypoint_by_index(0) == kp0
        assert frame.get_keypoint_by_index(1) == kp1
        assert frame.get_keypoint_by_index(2) is None

    def test_angulo_articular_diferencia(self):
        """Prueba: AnguloArticular valida rangos y computa diferencia angular."""
        a1 = AnguloArticular(articulacion="codo_der", valor=90.0, frame=1)
        a2 = AnguloArticular(articulacion="codo_der", valor=120.0, frame=1)

        assert a1.es_valido()
        assert not AnguloArticular(articulacion="codo_der", valor=-5.0, frame=1).es_valido()
        assert a1.diferencia(a2) == pytest.approx(30.0, 0.01)

    def test_error_biomecanico_es_critico(self):
        """Prueba: ErrorBiomecanico clasifica correctamente errores críticos."""
        err = ErrorBiomecanico(
            articulacion="rodilla_izq", angulo_alumno=178.0,
            angulo_maestro=90.0, diferencia=88.0, frame=51
        )
        assert err.es_critico(umbral=15.0)
        assert not ErrorBiomecanico(
            articulacion="rodilla_izq", angulo_alumno=92.0,
            angulo_maestro=90.0, diferencia=2.0, frame=1
        ).es_critico(umbral=15.0)

    def test_analisis_biomecanico_entidad(self):
        """Prueba: Entidad AnalisisBiomecanico mantiene identidad y relaciones."""
        analisis = AnalisisBiomecanico(
            desviacion_angular_maxima=178.37,
            articulacion_afectada="rodilla_izq",
            fotograma_anotado=FotogramaAnotado(
                imagen_url="resultados/fotogramas/test.jpg",
                coordenada_error_x=100, coordenada_error_y=200,
                explicacion_causa="Desviación crítica en rodilla"
            )
        )
        assert isinstance(analisis.id, UUID)
        assert analisis.estado_computo == "completado"
        assert analisis.desviacion_angular_maxima == 178.37
