import unittest
import numpy as np
from src.angle_calculator import AngleCalculator


class TestAngleCalculator(unittest.TestCase):
    def test_calcular_angulo_recto(self):
        """Verifica que un triángulo rectángulo arroje exactamente 90 grados."""
        a = [0.0, 1.0]
        b = [0.0, 0.0]
        c = [1.0, 0.0]
        angulo = AngleCalculator.calcular_angulo(a, b, c)
        self.assertAlmostEqual(angulo, 90.0, places=2)

    def test_calcular_angulo_llano(self):
        """Verifica que puntos colineales opuestos arrojen 180 grados."""
        a = [-1.0, 0.0]
        b = [0.0, 0.0]
        c = [1.0, 0.0]
        angulo = AngleCalculator.calcular_angulo(a, b, c)
        self.assertAlmostEqual(angulo, 180.0, places=2)

    def test_calcular_angulo_colineal(self):
        """Verifica que vectores en la misma dirección arrojen 0 grados."""
        a = [1.0, 0.0]
        b = [0.0, 0.0]
        c = [2.0, 0.0]
        angulo = AngleCalculator.calcular_angulo(a, b, c)
        self.assertAlmostEqual(angulo, 0.0, places=2)

    def test_calcular_angulo_punto_degenerado(self):
        """Verifica que un vector con longitud cero retorne 0.0 sin excepción."""
        a = [0.0, 0.0]
        b = [0.0, 0.0]
        c = [1.0, 0.0]
        angulo = AngleCalculator.calcular_angulo(a, b, c)
        self.assertEqual(angulo, 0.0)

    def test_extraer_angulos_coco_completo(self):
        """Verifica extracción de ángulos a partir de matriz sintética COCO de 17 puntos."""
        # Matriz de 17 puntos COCO con coordenadas no nulas
        keypoints = np.zeros((17, 2), dtype=np.float64)
        # Hombro izq (5), Codo izq (7), Muñeca izq (9) formando 90°
        keypoints[5] = [100.0, 100.0]
        keypoints[7] = [100.0, 150.0]
        keypoints[9] = [150.0, 150.0]

        # Cadera izq (11), Rodilla izq (13), Tobillo izq (15) formando 180°
        keypoints[11] = [100.0, 200.0]
        keypoints[13] = [100.0, 250.0]
        keypoints[15] = [100.0, 300.0]

        angulos = AngleCalculator.extraer_angulos(keypoints)
        self.assertIn('codo_izq', angulos)
        self.assertAlmostEqual(angulos['codo_izq'], 90.0, places=1)
        self.assertIn('rodilla_izq', angulos)
        self.assertAlmostEqual(angulos['rodilla_izq'], 180.0, places=1)

    def test_extraer_angulos_puntos_ocultos(self):
        """Verifica que no se calculen ángulos para articulaciones con puntos en cero."""
        keypoints = np.zeros((17, 2), dtype=np.float64)
        angulos = AngleCalculator.extraer_angulos(keypoints)
        self.assertEqual(len(angulos), 0)


if __name__ == '__main__':
    unittest.main()
