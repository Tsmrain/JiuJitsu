"""
Pruebas Unitarias TDD para GeometryUtils (Cálculos Cinemáticos 3D).

Valida el cálculo de ángulos articulares tridimensionales usando álgebra vectorial pura.
"""

import unittest
from src.domain.geometry_utils import GeometryUtils
from src.domain.interfaces import Keypoint


class TestGeometryUtils(unittest.TestCase):
    """Suite de pruebas para utilidades de geometría y trigonometría 3D."""

    def test_calculate_3d_angle_90_degrees(self):
        """Verifica que dos vectores ortogonales en el plano XY formen exactamente 90.0°."""
        p1 = (1.0, 0.0, 0.0)
        p2 = (0.0, 0.0, 0.0)  # Vértice
        p3 = (0.0, 1.0, 0.0)

        angle = GeometryUtils.calculate_3d_angle(p1, p2, p3)
        self.assertAlmostEqual(angle, 90.0, places=2)

    def test_calculate_3d_angle_180_degrees(self):
        """Verifica que tres puntos colineales opuestos formen 180.0° (brazo extendido)."""
        p1 = (1.0, 0.0, 0.0)
        p2 = (0.0, 0.0, 0.0)  # Vértice
        p3 = (-1.0, 0.0, 0.0)

        angle = GeometryUtils.calculate_3d_angle(p1, p2, p3)
        self.assertAlmostEqual(angle, 180.0, places=2)

    def test_calculate_3d_angle_45_degrees(self):
        """Verifica el cálculo de un ángulo de 45.0°."""
        p1 = (1.0, 1.0, 0.0)
        p2 = (0.0, 0.0, 0.0)  # Vértice
        p3 = (1.0, 0.0, 0.0)

        angle = GeometryUtils.calculate_3d_angle(p1, p2, p3)
        self.assertAlmostEqual(angle, 45.0, places=2)

    def test_calculate_3d_angle_handles_identical_points_gracefully(self):
        """Verifica que puntos superpuestos (norma cero) retornen 0.0° sin ZeroDivisionError."""
        p1 = (0.0, 0.0, 0.0)
        p2 = (0.0, 0.0, 0.0)  # Vértice idéntico a p1
        p3 = (1.0, 0.0, 0.0)

        angle = GeometryUtils.calculate_3d_angle(p1, p2, p3)
        self.assertEqual(angle, 0.0)

    def test_calculate_3d_angle_with_keypoint_objects(self):
        """Verifica que calculate_3d_angle acepte instancias de Keypoint del dominio."""
        shoulder = Keypoint(x=0.0, y=1.0, z=0.0, name="left_shoulder")
        elbow = Keypoint(x=0.0, y=0.0, z=0.0, name="left_elbow")
        wrist = Keypoint(x=1.0, y=0.0, z=0.0, name="left_wrist")

        angle = GeometryUtils.calculate_3d_angle(shoulder, elbow, wrist)
        self.assertAlmostEqual(angle, 90.0, places=2)

    def test_calculate_3d_angle_in_3d_space(self):
        """Verifica el cálculo de ángulos en espacio 3D real con componente Z."""
        p1 = (0.0, 0.0, 1.0)
        p2 = (0.0, 0.0, 0.0)
        p3 = (1.0, 0.0, 0.0)

        angle = GeometryUtils.calculate_3d_angle(p1, p2, p3)
        self.assertAlmostEqual(angle, 90.0, places=2)


if __name__ == "__main__":
    unittest.main()
