import pytest
import numpy as np
from src.domain.services.angle_calculator import AngleCalculatorImpl


class TestAngleCalculator:
    """Pruebas unitarias para el calculador de ángulos articulares (TDD - Craig Larman)."""

    def setup_method(self):
        self.calculator = AngleCalculatorImpl()

    def test_calcular_angulo_90_grados(self):
        """Prueba: ángulo recto de 90° entre tres puntos (Information Expert)."""
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 0.0])
        c = np.array([1.0, 1.0])
        angulo = self.calculator.calcular_angulo(a, b, c)
        assert angulo == pytest.approx(90.0, 0.1)

    def test_calcular_angulo_180_grados(self):
        """Prueba: ángulo llano de 180° (extensión articular completa)."""
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 0.0])
        c = np.array([2.0, 0.0])
        angulo = self.calculator.calcular_angulo(a, b, c)
        assert angulo == pytest.approx(180.0, 0.1)

    def test_calcular_angulo_0_grados_colineal(self):
        """Prueba: vectores superpuestos en la misma dirección retornan 0°."""
        a = np.array([2.0, 0.0])
        b = np.array([0.0, 0.0])
        c = np.array([3.0, 0.0])
        angulo = self.calculator.calcular_angulo(a, b, c)
        assert angulo == pytest.approx(0.0, 0.1)

    def test_calcular_angulo_punto_degenerado(self):
        """Prueba: vectores con norma cero retornan 0.0 sin excepción."""
        a = np.array([0.0, 0.0])
        b = np.array([0.0, 0.0])
        c = np.array([1.0, 0.0])
        angulo = self.calculator.calcular_angulo(a, b, c)
        assert angulo == 0.0

    def test_extraer_angulos_codos(self):
        """Prueba: extracción de ángulos articulares de codos desde keypoints COCO."""
        keypoints = np.zeros((17, 2), dtype=np.float64)
        # Hombro izq (5), Codo izq (7), Muñeca izq (9) formando 90°
        keypoints[5] = [10.0, 10.0]
        keypoints[7] = [20.0, 10.0]
        keypoints[9] = [20.0, 20.0]

        angulos = self.calculator.extraer_angulos(keypoints)
        assert 'codo_izq' in angulos
        assert angulos['codo_izq'] == pytest.approx(90.0, 0.1)

    def test_extraer_angulos_rodillas(self):
        """Prueba: extracción de ángulo de rodilla (11 cadera, 13 rodilla, 15 tobillo)."""
        keypoints = np.zeros((17, 2), dtype=np.float64)
        keypoints[11] = [10.0, 0.0]
        keypoints[13] = [10.0, 50.0]
        keypoints[15] = [10.0, 100.0]

        angulos = self.calculator.extraer_angulos(keypoints)
        assert 'rodilla_izq' in angulos
        assert angulos['rodilla_izq'] == pytest.approx(180.0, 0.1)

    def test_keypoints_invalidos_retorna_dict_vacio(self):
        """Prueba: keypoints incompletos o nulos no producen excepciones (Robustez)."""
        keypoints = np.zeros((10, 2), dtype=np.float64)  # Menos de 17 puntos
        angulos = self.calculator.extraer_angulos(keypoints)
        assert angulos == {}
