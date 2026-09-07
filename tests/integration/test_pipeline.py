import pytest
from unittest.mock import Mock
import numpy as np

from src.application.pipeline import BiomechanicsPipeline
from src.domain.interfaces import (
    IPoseExtractor, IAngleCalculator, IDTWComparator,
    IFrameAnnotator, IStorageProvider
)


class TestPipelineIntegration:
    """Pruebas de integración del controlador de caso de uso (TDD - Craig Larman)."""

    def setup_method(self):
        self.mock_pose_extractor = Mock(spec=IPoseExtractor)
        self.mock_angle_calculator = Mock(spec=IAngleCalculator)
        self.mock_dtw_comparator = Mock(spec=IDTWComparator)
        self.mock_frame_annotator = Mock(spec=IFrameAnnotator)
        self.mock_storage = Mock(spec=IStorageProvider)

        self.pipeline = BiomechanicsPipeline(
            pose_extractor=self.mock_pose_extractor,
            angle_calculator=self.mock_angle_calculator,
            dtw_comparator=self.mock_dtw_comparator,
            frame_annotator=self.mock_frame_annotator,
            storage=self.mock_storage
        )

    def test_pipeline_detecta_error_maximo(self):
        """Prueba: el pipeline detecta el error máximo correctamente."""
        frames_m = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(10)]
        frames_a = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(10)]

        self.mock_pose_extractor.extraer_keypoints.side_effect = [
            (np.random.rand(10, 17, 2), frames_m),
            (np.random.rand(10, 17, 2), frames_a)
        ]

        # Simular ángulos: frame 5 del alumno tiene error de 45° en codo_izq
        angulos_maestro = [{'codo_izq': 90.0, 'rodilla_izq': 180.0} for _ in range(10)]
        angulos_alumno = [
            {'codo_izq': 90.0, 'rodilla_izq': 180.0} if i != 5 else {'codo_izq': 45.0, 'rodilla_izq': 180.0}
            for i in range(10)
        ]

        self.mock_angle_calculator.extraer_angulos.side_effect = angulos_maestro + angulos_alumno
        self.mock_dtw_comparator.comparar_articulacion.return_value = (
            10.0, [(i, i) for i in range(10)], [90.0] * 10, [90.0] * 10
        )
        self.mock_frame_annotator.anotar_error.return_value = frames_a[5]
        self.mock_storage.guardar_imagen.return_value = "resultados/fotogramas/error.jpg"
        self.mock_storage.guardar_csv.return_value = "resultados/csv/data.csv"

        resultado = self.pipeline.ejecutar("maestro.mp4", "alumno.mp4")

        assert resultado.desviacion_angular_maxima == pytest.approx(45.0, 0.1)
        assert resultado.articulacion_afectada == "codo_izq"
        assert resultado.estado_computo == "completado"
        assert resultado.fotograma_anotado is not None
        assert resultado.fotograma_anotado.imagen_url == "resultados/fotogramas/error.jpg"

    def test_pipeline_maneja_vacio_sin_personas(self):
        """Prueba: manejo elegante cuando no se detectan poses en el video."""
        self.mock_pose_extractor.extraer_keypoints.return_value = (np.array([]), [])

        with pytest.raises(ValueError, match="No se detectaron poses"):
            self.pipeline.ejecutar("maestro.mp4", "alumno.mp4")
