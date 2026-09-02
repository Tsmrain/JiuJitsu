"""
Pruebas Unitarias TDD para la Infraestructura de Inferencia y Detección de Hardware.

Valida:
1. TestHardwareDetector: Detección elástica de hardware (CPU vs CUDA) y tolerancia a fallos ante la ausencia de PyTorch.
2. TestRTMPose3DAdapterContract: Cumplimiento de la interfaz IPoseEstimator y mapeo de la salida
   del modelo externo (rbarac/rtmpose3d) hacia las entidades de dominio KeypointFrame.
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from src.domain.interfaces import IPoseEstimator, Keypoint, KeypointFrame
from src.infrastructure.inference.hardware_detector import get_device
from src.infrastructure.inference.rtmpose3d_adapter import RTMPose3DAdapter


class TestHardwareDetector(unittest.TestCase):
    """Pruebas unitarias para el detector de aceleración de hardware."""

    def test_get_device_returns_cuda_when_available(self):
        """Verifica que get_device() retorne 'cuda:0' cuando CUDA está disponible en PyTorch."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True

        with patch.dict(sys.modules, {"torch": mock_torch}):
            device = get_device()
            self.assertEqual(device, "cuda:0")

    def test_get_device_returns_cpu_when_cuda_unavailable(self):
        """Verifica que get_device() retorne 'cpu' cuando CUDA no está disponible."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        with patch.dict(sys.modules, {"torch": mock_torch}):
            device = get_device()
            self.assertEqual(device, "cpu")

    def test_get_device_handles_import_error_gracefully(self):
        """
        Verifica el Principio de Tolerancia a Fallos:
        Si PyTorch no está instalado, get_device() debe retornar 'cpu' sin levantar excepción.
        """
        with patch.dict(sys.modules, {"torch": None}):
            # Forzar excepción de importación
            device = get_device()
            self.assertEqual(device, "cpu")


class TestRTMPose3DAdapterContract(unittest.TestCase):
    """Pruebas unitarias para el contrato del adaptador RTMPose3D."""

    def test_implements_ipose_estimator_interface(self):
        """Verifica que RTMPose3DAdapter implemente formalmente la interfaz IPoseEstimator."""
        mock_model = MagicMock()
        adapter = RTMPose3DAdapter(device="cpu", model=mock_model)
        self.assertIsInstance(adapter, IPoseEstimator)

    def test_extract_keypoints_maps_raw_output_to_domain_entities(self):
        """
        Prueba TDD Core (RF-02):
        Simula la salida cruda de rbarac/rtmpose3d con forma (1, 133, 3) en keypoints_3d,
        (1, 133, 2) en keypoints_2d y scores (1, 133).
        Verifica la traducción rigurosa a List[KeypointFrame] y Keypoint del dominio.
        """
        num_keypoints = 133
        # Generar datos sintéticos de prueba
        simulated_keypoints_3d = [
            [[float(i) * 0.1, float(i) * 0.2, float(i) * 0.3] for i in range(num_keypoints)]
        ]  # Forma: (1, 133, 3)
        simulated_keypoints_2d = [
            [[float(i) * 10.0, float(i) * 20.0] for i in range(num_keypoints)]
        ]  # Forma: (1, 133, 2)
        simulated_scores = [
            [0.98 for _ in range(num_keypoints)]
        ]  # Forma: (1, 133)

        raw_model_output = {
            "keypoints_3d": simulated_keypoints_3d,
            "keypoints_2d": simulated_keypoints_2d,
            "scores": simulated_scores,
        }

        # Mock del modelo RTMPose3D
        mock_model = MagicMock()
        mock_model.predict.return_value = raw_model_output

        adapter = RTMPose3DAdapter(device="cpu", model=mock_model)
        result_frames = adapter.extract_keypoints("sample_test_video.mp4")

        # Validaciones estructurales del dominio
        self.assertIsInstance(result_frames, list)
        self.assertEqual(len(result_frames), 1)

        frame = result_frames[0]
        self.assertIsInstance(frame, KeypointFrame)
        self.assertEqual(frame.frame_idx, 0)
        self.assertEqual(len(frame.keypoints), num_keypoints)

        # Validación del primer keypoint
        first_kp = frame.keypoints[0]
        self.assertIsInstance(first_kp, Keypoint)
        self.assertAlmostEqual(first_kp.x, 0.0)
        self.assertAlmostEqual(first_kp.y, 0.0)
        self.assertAlmostEqual(first_kp.z, 0.0)
        self.assertAlmostEqual(first_kp.score, 0.98)
        self.assertEqual(first_kp.name, "kp_0")

        # Validación del segundo keypoint
        second_kp = frame.keypoints[1]
        self.assertAlmostEqual(second_kp.x, 0.1)
        self.assertAlmostEqual(second_kp.y, 0.2)
        self.assertAlmostEqual(second_kp.z, 0.3)
        self.assertAlmostEqual(second_kp.score, 0.98)
        self.assertEqual(second_kp.name, "kp_1")

        # Verificar que el método predict del modelo fue invocado con la ruta del video
        mock_model.predict.assert_called_once_with("sample_test_video.mp4")

    def test_extract_keypoints_raises_runtime_error_when_model_uninitialized(self):
        """Verifica que se lance RuntimeError si el modelo no está cargado ni disponible."""
        adapter = RTMPose3DAdapter(device="cpu", model=None)
        # Asegurar que model permanezca None
        adapter.model = None

        with self.assertRaises(RuntimeError) as ctx:
            adapter.extract_keypoints("test_video.mp4")

        self.assertIn("no está disponible", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
