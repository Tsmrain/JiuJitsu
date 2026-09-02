"""
Prueba de Integración Real (Sin Mocks) para RTMPose3D con Videos Reales.

Valida el modelo rbarac/rtmpose3d ejecutando inferencia real sobre los videos reales de entrenamiento:
1. Videos/Maestro.mp4 (Video patrón del Head Coach)
2. Videos/Alumno.mp4 (Video de ejecución del practicante)

Utiliza marcadores de pytest (@pytest.mark.real_model y @pytest.mark.integration)
para permitir la ejecución condicionada en Google Colab (GPU A100/CUDA) y la
omisión automática en entornos locales de desarrollo (Dell).
"""

import os
import unittest
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None

from src.domain.interfaces import KeypointFrame
from src.infrastructure.inference.hardware_detector import get_device
from src.infrastructure.inference.rtmpose3d_adapter import RTMPose3DAdapter


def _pytest_marker(mark_name):
    """Aplica un marcador pytest si la librería está disponible."""
    if pytest is not None:
        return getattr(pytest.mark, mark_name)
    return lambda func_or_cls: func_or_cls


@_pytest_marker("integration")
@_pytest_marker("real_model")
class TestRTMPose3DRealModelIntegration(unittest.TestCase):
    """
    Pruebas de integración end-to-end con el modelo real de HuggingFace/OpenMMLab
    utilizando los videos reales de Jiu-Jitsu como Ground Truth.
    """

    def setUp(self):
        """Verifica la presencia de dependencias reales y videos antes de ejecutar."""
        # 1. Comprobar si rtmpose3d está instalado en el entorno
        try:
            import rtmpose3d  # noqa: F401
        except ImportError:
            msg = "Librería rtmpose3d no instalada. Esta prueba requiere un entorno con GPU (Google Colab o Windows GPU)."
            if pytest is not None:
                pytest.skip(msg)
            else:
                self.skipTest(msg)

        # 2. Comprobar si PyTorch está disponible
        try:
            import torch
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        except ImportError:
            msg = "PyTorch no está instalado. Omitiendo prueba de modelo real."
            if pytest is not None:
                pytest.skip(msg)
            else:
                self.skipTest(msg)

        # 3. Rutas a los videos reales de Ground Truth
        # tests/integration -> raíz del proyecto -> Videos
        root_dir = Path(__file__).resolve().parent.parent.parent
        self.teacher_video_path = str(root_dir / "Videos" / "Maestro.mp4")
        self.student_video_path = str(root_dir / "Videos" / "Alumno.mp4")

    def test_real_inference_extracts_keypoints_from_teacher_video(self):
        """
        Ejecuta el modelo rbarac/rtmpose3d real sobre 'Videos/Maestro.mp4'.
        Valida que la salida del extractor produzca objetos KeypointFrame con 133 landmarks 3D
        y scores de confianza en el rango [0.0, 1.0].
        """
        if not os.path.isfile(self.teacher_video_path):
            self.skipTest(f"No se encontró el video del maestro en: {self.teacher_video_path}")

        adapter = RTMPose3DAdapter(device=self.device)
        frames = adapter.extract_keypoints(self.teacher_video_path)

        # Validaciones sobre el pipeline real
        self.assertIsInstance(frames, list, "El resultado debe ser una lista de fotogramas")
        self.assertGreater(len(frames), 0, "Debe haberse extraído al menos un fotograma del video del maestro")

        first_frame = frames[0]
        self.assertIsInstance(first_frame, KeypointFrame, "Cada elemento debe ser una instancia de KeypointFrame")
        self.assertEqual(len(first_frame.keypoints), 133, "La topología RTMPose3D Halpe/Wholebody debe contener 133 keypoints")

        # Validar coordenadas y rango de scores
        for kp in first_frame.keypoints:
            self.assertIsInstance(kp.x, float)
            self.assertIsInstance(kp.y, float)
            self.assertIsInstance(kp.z, float)
            self.assertGreaterEqual(kp.score, 0.0, f"El score {kp.score} no puede ser menor a 0.0")
            self.assertLessEqual(kp.score, 1.0, f"El score {kp.score} no puede ser mayor a 1.0")

        # Validar que al menos un keypoint tenga score > 0
        has_positive_score = any(kp.score > 0.0 for kp in first_frame.keypoints)
        self.assertTrue(has_positive_score, "Debe haber keypoints detectados con score positivo")

    def test_real_inference_extracts_keypoints_from_student_video(self):
        """
        Ejecuta el modelo rbarac/rtmpose3d real sobre 'Videos/Alumno.mp4'.
        Valida que la salida del extractor produzca objetos KeypointFrame con 133 landmarks 3D
        y scores de confianza en el rango [0.0, 1.0].
        """
        if not os.path.isfile(self.student_video_path):
            self.skipTest(f"No se encontró el video del alumno en: {self.student_video_path}")

        adapter = RTMPose3DAdapter(device=self.device)
        frames = adapter.extract_keypoints(self.student_video_path)

        # Validaciones sobre el pipeline real
        self.assertIsInstance(frames, list, "El resultado debe ser una lista de fotogramas")
        self.assertGreater(len(frames), 0, "Debe haberse extraído al menos un fotograma del video del alumno")

        first_frame = frames[0]
        self.assertIsInstance(first_frame, KeypointFrame, "Cada elemento debe ser una instancia de KeypointFrame")
        self.assertEqual(len(first_frame.keypoints), 133, "La topología RTMPose3D Halpe/Wholebody debe contener 133 keypoints")

        # Validar coordenadas y rango de scores
        for kp in first_frame.keypoints:
            self.assertIsInstance(kp.x, float)
            self.assertIsInstance(kp.y, float)
            self.assertIsInstance(kp.z, float)
            self.assertGreaterEqual(kp.score, 0.0, f"El score {kp.score} no puede ser menor a 0.0")
            self.assertLessEqual(kp.score, 1.0, f"El score {kp.score} no puede ser mayor a 1.0")

        has_positive_score = any(kp.score > 0.0 for kp in first_frame.keypoints)
        self.assertTrue(has_positive_score, "Debe haber keypoints detectados con score positivo")


if __name__ == "__main__":
    unittest.main()
