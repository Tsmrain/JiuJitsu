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

    def test_pipeline_exportar_e_importar_colab(self, tmp_path):
        """Prueba: generación de manifiesto Colab y posterior análisis de keypoints JSON devueltos."""
        import os
        dest_payload = tmp_path / "colab_payload.json"
        res_payload = self.pipeline.exportar_payload_colab("Videos/Maestro.mp4", "Videos/Alumno.mp4", str(dest_payload))
        assert os.path.exists(res_payload)

        colab_data = {
            "version": "2.0-hybrid",
            "keypoints_maestro": np.ones((5, 17, 2)).tolist(),
            "keypoints_alumno": np.ones((5, 17, 2)).tolist()
        }
        self.mock_angle_calculator.extraer_angulos.return_value = {'codo_izq': 90.0}
        self.mock_dtw_comparator.comparar_articulacion.return_value = (
            0.0, [(i, i) for i in range(5)], [90.0] * 5, [90.0] * 5
        )
        self.mock_storage.guardar_csv.return_value = str(tmp_path / "test.csv")

        resultado = self.pipeline.ejecutar_desde_colab_json(colab_data)
        assert resultado is not None
        assert resultado.estado_computo == "completado"

    def test_pipeline_procesar_resultado_colab_json(self, tmp_path):
        """Prueba: Ingesta del JSON exportado por Colab con persistencia en SQLite (Mannino)."""
        import json
        json_file = tmp_path / "colab_results.json"
        payload = {
            "errores": [
                {
                    "articulacion": "codo_der",
                    "angulo_alumno": 85.0,
                    "angulo_maestro": 110.0,
                    "diferencia": 25.0,
                    "frame": 10,
                    "mensaje": "Desviación de 25.00° en codo_der"
                }
            ]
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        res = self.pipeline.procesar_resultado_colab(
            str(json_file),
            video_id="550e8400-e29b-41d4-a716-446655440000",
            tecnica_id="123e4567-e89b-12d3-a456-426614174000"
        )
        assert res is not None
        assert res.desviacion_angular_maxima == 25.0
        assert res.articulacion_afectada == "codo_der"
        assert len(res.errores) == 1
