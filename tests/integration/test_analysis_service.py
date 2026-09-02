"""
Pruebas de Integración para el Servicio de Aplicación (Use Case Controller).

Valida la orquestación end-to-end entre Almacenamiento, Inferencia de Pose,
Comparador Biomecánico y Anotación Gráfica de Errores.
"""

import math
import unittest
from unittest.mock import MagicMock

from src.application.analysis_service import TechniqueAnalysisService
from src.domain.comparator import BiomechanicsComparator
from src.domain.interfaces import IPoseEstimator, IStorageProvider, Keypoint, KeypointFrame
from src.infrastructure.vision.frame_annotator import FrameAnnotator


class DummyImage:
    """Objeto representativo de imagen matricial para pruebas ligeras sin dependencias pesadas."""

    def __init__(self, shape=(480, 640, 3)):
        self.shape = shape

    def copy(self):
        return DummyImage(shape=self.shape)


class TestTechniqueAnalysisService(unittest.TestCase):
    """Suite de pruebas de integración para TechniqueAnalysisService."""

    def setUp(self):
        """Configura los mocks de infraestructura y las instancias reales de dominio."""
        self.mock_storage = MagicMock(spec=IStorageProvider)
        self.mock_estimator = MagicMock(spec=IPoseEstimator)
        self.comparator = BiomechanicsComparator()
        self.annotator = FrameAnnotator()

        self.service = TechniqueAnalysisService(
            storage=self.mock_storage,
            estimator=self.mock_estimator,
            comparator=self.comparator,
            annotator=self.annotator,
        )

    def _create_mock_arm_frame(self, frame_idx: int, elbow_angle_deg: float) -> KeypointFrame:
        """Genera un fotograma de prueba con el ángulo de codo especificado."""
        rad = math.radians(elbow_angle_deg)
        wrist_x = math.sin(rad)
        wrist_y = math.cos(rad)

        keypoints = [Keypoint(x=0.0, y=0.0, z=0.0) for _ in range(133)]
        keypoints[5] = Keypoint(x=0.0, y=1.0, z=0.0, name="left_shoulder")
        keypoints[7] = Keypoint(x=100.0, y=150.0, z=0.0, name="left_elbow")  # Vértice 2D en (100, 150)
        keypoints[9] = Keypoint(x=100.0 + wrist_x, y=150.0 + wrist_y, z=0.0, name="left_wrist")

        return KeypointFrame(frame_idx=frame_idx, timestamp_ms=frame_idx * 33.33, keypoints=keypoints)

    def test_analyze_technique_with_biomechanical_error_annotates_frame(self):
        """
        Verifica el flujo completo ante un error técnico:
        1. Detecta la discrepancia angular (45° de error en frame 2, codo izquierdo kp 7).
        2. Solicita el frame 2 al almacenamiento.
        3. Genera la anotación visual del error.
        """
        teacher_frames = [self._create_mock_arm_frame(i, elbow_angle_deg=90.0) for i in range(3)]
        student_frames = [
            self._create_mock_arm_frame(0, elbow_angle_deg=90.0),
            self._create_mock_arm_frame(1, elbow_angle_deg=90.0),
            self._create_mock_arm_frame(2, elbow_angle_deg=45.0),  # Error de 45°
        ]

        self.mock_estimator.extract_keypoints.side_effect = [teacher_frames, student_frames]
        dummy_frame = DummyImage(shape=(480, 640, 3))
        self.mock_storage.get_frame.return_value = dummy_frame

        result = self.service.analyze_technique(
            teacher_video_path="Videos/Maestro.mp4",
            student_video_path="Videos/Alumno.mp4",
            technique_name="Upa Escape",
            threshold_degrees=15.0,
        )

        # Verificaciones de orquestación
        self.assertFalse(result["is_correct"], "La técnica debe ser clasificada como incorrecta")
        self.assertAlmostEqual(result["max_deviation_angle"], 45.0, places=1)
        self.assertEqual(result["error_frame_index"], 2)
        self.assertEqual(result["error_keypoint_index"], 7)
        self.assertIsNotNone(result["annotated_frame"], "Debe retornarse el fotograma con el error anotado")

        # Verificar que el almacenamiento extrajo el fotograma específico
        self.mock_storage.get_frame.assert_called_once_with("Videos/Alumno.mp4", 2)

    def test_analyze_technique_correct_execution_does_not_annotate(self):
        """
        Verifica que una ejecución correcta (sin errores) retorne is_correct=True
        y no invoque la extracción ni anotación de fotogramas de error.
        """
        teacher_frames = [self._create_mock_arm_frame(i, elbow_angle_deg=90.0) for i in range(3)]
        student_frames = [self._create_mock_arm_frame(i, elbow_angle_deg=90.0) for i in range(3)]

        self.mock_estimator.extract_keypoints.side_effect = [teacher_frames, student_frames]

        result = self.service.analyze_technique(
            teacher_video_path="Videos/Maestro.mp4",
            student_video_path="Videos/Alumno.mp4",
            technique_name="Upa Escape",
            threshold_degrees=15.0,
        )

        self.assertTrue(result["is_correct"])
        self.assertAlmostEqual(result["max_deviation_angle"], 0.0, places=1)
        self.assertIsNone(result["annotated_frame"], "No debe generarse fotograma de error en técnica correcta")
        self.mock_storage.get_frame.assert_not_called()


if __name__ == "__main__":
    unittest.main()
