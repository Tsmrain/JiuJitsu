"""
Pruebas Unitarias TDD para el Comparador Biomecánico Basado en Ángulos 3D.

Valida el cálculo de discrepancias angulares entre las poses del Maestro y del Alumno
frente al umbral de tolerancia de 15°.
"""

import unittest
from src.domain.comparator import BiomechanicsComparator
from src.domain.entities import ComparisonResult
from src.domain.interfaces import Keypoint, KeypointFrame


class TestBiomechanicsComparator(unittest.TestCase):
    """Suite de pruebas unitarias para BiomechanicsComparator."""

    def setUp(self):
        """Inicializa el comparador de dominio."""
        self.comparator = BiomechanicsComparator()

    def _create_mock_arm_frame(self, frame_idx: int, elbow_angle_deg: float) -> KeypointFrame:
        """
        Crea un KeypointFrame con un brazo en los keypoints estándar (5: Hombro, 7: Codo, 9: Muñeca).
        Hombro en (0, 1, 0), Codo en (0, 0, 0) como vértice.
        La muñeca se posiciona según el ángulo deseado respecto al hombro.
        """
        import math

        rad = math.radians(elbow_angle_deg)
        # Muñeca calculada a partir del ángulo con el hombro (que está en +Y)
        # Vector hombro-codo = (0, 1, 0).
        # Vector muñeca-codo = (sin(rad), cos(rad), 0)
        wrist_x = math.sin(rad)
        wrist_y = math.cos(rad)

        keypoints = [Keypoint(x=0.0, y=0.0, z=0.0) for _ in range(133)]
        keypoints[5] = Keypoint(x=0.0, y=1.0, z=0.0, name="left_shoulder")
        keypoints[7] = Keypoint(x=0.0, y=0.0, z=0.0, name="left_elbow")  # Vértice
        keypoints[9] = Keypoint(x=wrist_x, y=wrist_y, z=0.0, name="left_wrist")

        # Rellenar los otros tripletes por defecto con ángulos rectos idénticos
        keypoints[6] = Keypoint(x=0.0, y=1.0, z=0.0, name="right_shoulder")
        keypoints[8] = Keypoint(x=0.0, y=0.0, z=0.0, name="right_elbow")
        keypoints[10] = Keypoint(x=1.0, y=0.0, z=0.0, name="right_wrist")

        keypoints[11] = Keypoint(x=0.0, y=1.0, z=0.0, name="left_hip")
        keypoints[13] = Keypoint(x=0.0, y=0.0, z=0.0, name="left_knee")
        keypoints[15] = Keypoint(x=1.0, y=0.0, z=0.0, name="left_ankle")

        keypoints[12] = Keypoint(x=0.0, y=1.0, z=0.0, name="right_hip")
        keypoints[14] = Keypoint(x=0.0, y=0.0, z=0.0, name="right_knee")
        keypoints[16] = Keypoint(x=1.0, y=0.0, z=0.0, name="right_ankle")

        return KeypointFrame(frame_idx=frame_idx, timestamp_ms=frame_idx * 33.33, keypoints=keypoints)

    def test_compare_identical_angles_returns_is_correct_true(self):
        """
        Verifica que comparar secuencias con ángulos idénticos retorne
        is_correct=True y una desviación máxima de 0.0°.
        """
        teacher_frames = [self._create_mock_arm_frame(i, elbow_angle_deg=90.0) for i in range(3)]
        student_frames = [self._create_mock_arm_frame(i, elbow_angle_deg=90.0) for i in range(3)]

        result = self.comparator.compare(teacher_frames, student_frames, threshold_degrees=15.0)

        self.assertIsInstance(result, ComparisonResult)
        self.assertTrue(result.is_correct, "La ejecución con ángulos idénticos debe ser calificada como correcta")
        self.assertAlmostEqual(result.max_deviation_angle, 0.0, places=2)

    def test_compare_divergent_angle_returns_error_frame_and_vertex(self):
        """
        Verifica que cuando un ángulo articular (ej. codo izquierdo en 45°) se desvía
        del maestro (90°) superando el umbral de 15°, se marque is_correct=False y
        se identifiquen el frame del error y el keypoint del vértice (7 = codo izquierdo).
        """
        # Maestro mantiene codo a 90.0° en los 3 frames
        teacher_frames = [self._create_mock_arm_frame(i, elbow_angle_deg=90.0) for i in range(3)]

        # Alumno ejecuta bien en frames 0 y 1, pero en frame 2 cierra el codo a 45.0° (diferencia de 45.0°)
        student_frames = [
            self._create_mock_arm_frame(0, elbow_angle_deg=90.0),
            self._create_mock_arm_frame(1, elbow_angle_deg=90.0),
            self._create_mock_arm_frame(2, elbow_angle_deg=45.0),
        ]

        result = self.comparator.compare(
            teacher_frames,
            student_frames,
            threshold_degrees=15.0,
            triplets=[(5, 7, 9)],  # Brazo izquierdo
        )

        self.assertIsInstance(result, ComparisonResult)
        self.assertFalse(result.is_correct, "La ejecución con desviación angular de 45° (>15°) debe ser incorrecta")
        self.assertAlmostEqual(result.max_deviation_angle, 45.0, places=1)
        self.assertEqual(result.error_frame_index, 2, "Debe identificar el frame 2 como el punto del error")
        self.assertEqual(result.error_keypoint_index, 7, "Debe identificar el keypoint 7 (codo) como el vértice del fallo")

    def test_compare_within_threshold_returns_is_correct_true(self):
        """
        Verifica que una discrepancia angular menor (ej. 10.0°) por debajo del umbral (15.0°)
        sea aprobada como técnica válida.
        """
        teacher_frames = [self._create_mock_arm_frame(0, elbow_angle_deg=90.0)]
        student_frames = [self._create_mock_arm_frame(0, elbow_angle_deg=80.0)]  # Desviación de 10.0°

        result = self.comparator.compare(
            teacher_frames,
            student_frames,
            threshold_degrees=15.0,
            triplets=[(5, 7, 9)],
        )

        self.assertTrue(result.is_correct)
        self.assertAlmostEqual(result.max_deviation_angle, 10.0, places=1)
        self.assertEqual(result.error_frame_index, 0)
        self.assertEqual(result.error_keypoint_index, 7)

    def test_compare_empty_sequences_returns_safe_default(self):
        """Verifica el comportamiento seguro ante listas de fotogramas vacías."""
        result = self.comparator.compare([], [])
        self.assertFalse(result.is_correct)
        self.assertEqual(result.max_deviation_angle, 0.0)


if __name__ == "__main__":
    unittest.main()
