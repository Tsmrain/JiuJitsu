import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
import tempfile
import numpy as np

from src.frame_annotator import FrameAnnotator
from src.csv_exporter import CSVExporter
from src.pipeline import BiomechanicsPipeline


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_frame_annotator(self):
        """Verifica que FrameAnnotator genere un frame anotado y lo guarde en disco."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        keypoints = np.zeros((17, 2), dtype=np.float64)
        keypoints[13] = [320.0, 240.0]  # rodilla_izq en índice 13

        anotado = FrameAnnotator.anotar_error(
            frame, keypoints, 'rodilla_izq', 45.5, 10
        )
        self.assertEqual(anotado.shape, frame.shape)

        ruta = FrameAnnotator.guardar(anotado, "test_error.jpg", self.test_dir)
        self.assertTrue(os.path.exists(ruta))
        self.assertGreater(os.path.getsize(ruta), 0)

    def test_csv_exporter(self):
        """Verifica que CSVExporter exporte correctamente dataframes a disco."""
        angulos = [{'codo_izq': 90.0, 'rodilla_izq': 180.0}]
        with patch('src.csv_exporter.CSV_DIR', self.test_dir):
            ruta_ang = CSVExporter.exportar_angulos(angulos, "test_angulos.csv")
            self.assertTrue(os.path.exists(ruta_ang))

            similitud = [95.0, 88.0, 72.0]
            ruta_sim = CSVExporter.exportar_similitud(similitud, "test_sim.csv")
            self.assertTrue(os.path.exists(ruta_sim))

    @patch('src.pipeline.PoseExtractor')
    def test_pipeline_ejecucion_sintetica(self, mock_pose_extractor_class):
        """Verifica la ejecución end-to-end del pipeline con keypoints sintéticos."""
        # Configurar extractor mock
        mock_extractor = MagicMock()
        mock_pose_extractor_class.return_value = mock_extractor

        # Crear 10 frames sintéticos
        frames_m = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(10)]
        frames_a = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(10)]

        # Keypoints donde el frame 5 del alumno tiene una desviación notable en rodilla izq
        kpts_m = np.zeros((10, 17, 2), dtype=np.float64)
        kpts_a = np.zeros((10, 17, 2), dtype=np.float64)

        for i in range(10):
            # Maestro con rodilla en 180°
            kpts_m[i, 11] = [50.0, 10.0]
            kpts_m[i, 13] = [50.0, 50.0]
            kpts_m[i, 15] = [50.0, 90.0]

            # Alumno normalmente igual, pero en frame 5 con ángulo recto (90°)
            kpts_a[i, 11] = [50.0, 10.0]
            kpts_a[i, 13] = [50.0, 50.0]
            if i == 5:
                kpts_a[i, 15] = [90.0, 50.0]  # Desviación de 90 grados
            else:
                kpts_a[i, 15] = [50.0, 90.0]

        mock_extractor.procesar_video.side_effect = [
            (kpts_m, frames_m),
            (kpts_a, frames_a)
        ]

        with patch('src.frame_annotator.FOTOGRAMAS_DIR', self.test_dir), \
             patch('src.pipeline.GRAFICAS_DIR', self.test_dir), \
             patch('src.csv_exporter.CSV_DIR', self.test_dir):
            pipeline = BiomechanicsPipeline()
            resultados = pipeline.ejecutar("dummy_maestro.mp4", "dummy_alumno.mp4")

            self.assertIsNotNone(resultados['mejor_error'])
            self.assertEqual(resultados['mejor_error']['articulacion'], 'rodilla_izq')
            self.assertEqual(resultados['mejor_error']['frame'], 5)
            self.assertAlmostEqual(resultados['mejor_error']['error'], 90.0, places=1)
            self.assertEqual(len(resultados['similitud']), 10)


if __name__ == '__main__':
    unittest.main()
