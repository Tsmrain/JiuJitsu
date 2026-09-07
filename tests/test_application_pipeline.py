import unittest
from unittest.mock import MagicMock
import numpy as np
from uuid import uuid4

from src.domain.interfaces import (
    IPoseExtractor, IAngleCalculator, IDTWComparator,
    IFrameAnnotator, IStorageProvider
)
from src.domain.entities import AnalisisBiomecanico, TecnicaMaestra
from src.application.pipeline import BiomechanicsPipeline
from src.application.services import AnalysisAppService


class TestApplicationPipeline(unittest.TestCase):
    def test_pipeline_dependency_injection(self):
        """Verifica la ejecución del controlador de caso de uso con inyección de dependencias."""
        mock_extractor = MagicMock(spec=IPoseExtractor)
        mock_angle_calc = MagicMock(spec=IAngleCalculator)
        mock_dtw = MagicMock(spec=IDTWComparator)
        mock_annotator = MagicMock(spec=IFrameAnnotator)
        mock_storage = MagicMock(spec=IStorageProvider)

        # Configuración de mocks
        kpts_m = np.zeros((5, 17, 2), dtype=np.float64)
        kpts_a = np.zeros((5, 17, 2), dtype=np.float64)
        frames_m = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(5)]
        frames_a = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(5)]

        mock_extractor.extraer_keypoints.side_effect = [
            (kpts_m, frames_m),
            (kpts_a, frames_a)
        ]

        # Simular ángulos: frame 2 tiene error crítico en rodilla_izq (180 vs 90)
        mock_angle_calc.extraer_angulos.side_effect = [
            # 5 frames maestro
            {'rodilla_izq': 180.0}, {'rodilla_izq': 180.0}, {'rodilla_izq': 180.0}, {'rodilla_izq': 180.0}, {'rodilla_izq': 180.0},
            # 5 frames alumno
            {'rodilla_izq': 180.0}, {'rodilla_izq': 180.0}, {'rodilla_izq': 90.0}, {'rodilla_izq': 180.0}, {'rodilla_izq': 180.0}
        ]

        mock_dtw.comparar_articulacion.return_value = (90.0, [(0, 0)], [180.0]*5, [180.0, 180.0, 90.0, 180.0, 180.0])
        mock_annotator.anotar_error.return_value = frames_a[2]
        mock_storage.guardar_imagen.return_value = "resultados/fotogramas/frame_error.jpg"
        mock_storage.guardar_csv.return_value = "resultados/csv/data.csv"

        pipeline = BiomechanicsPipeline(
            pose_extractor=mock_extractor,
            angle_calculator=mock_angle_calc,
            dtw_comparator=mock_dtw,
            frame_annotator=mock_annotator,
            storage=mock_storage
        )

        analisis = pipeline.ejecutar("maestro.mp4", "alumno.mp4")

        self.assertIsInstance(analisis, AnalisisBiomecanico)
        self.assertEqual(analisis.articulacion_afectada, "rodilla_izq")
        self.assertAlmostEqual(analisis.desviacion_angular_maxima, 90.0, places=1)
        self.assertIsNotNone(analisis.fotograma_anotado)
        self.assertEqual(analisis.fotograma_anotado.imagen_url, "resultados/fotogramas/frame_error.jpg")

    def test_analysis_app_service(self):
        """Verifica la coordinación del servicio de aplicación con repositorios."""
        mock_pipeline = MagicMock(spec=BiomechanicsPipeline)
        mock_analisis_repo = MagicMock()
        mock_tecnica_repo = MagicMock()

        t_id = uuid4()
        tecnica = TecnicaMaestra(id=t_id, nombre="Pasaje Torreando")
        mock_tecnica_repo.obtener_por_id.return_value = tecnica

        mock_analisis = AnalisisBiomecanico(desviacion_angular_maxima=25.0)
        mock_pipeline.ejecutar.return_value = mock_analisis

        app_service = AnalysisAppService(
            pipeline=mock_pipeline,
            analisis_repo=mock_analisis_repo,
            tecnica_repo=mock_tecnica_repo
        )

        res = app_service.analizar_ejecucion("maestro.mp4", "alumno.mp4", tecnica_id=t_id)

        self.assertEqual(res, mock_analisis)
        mock_tecnica_repo.obtener_por_id.assert_called_once_with(t_id)
        mock_analisis_repo.guardar.assert_called_once_with(mock_analisis)


if __name__ == '__main__':
    unittest.main()
