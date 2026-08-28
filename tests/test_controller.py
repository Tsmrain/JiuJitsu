"""
Pruebas Unitarias para el Controlador de Caso de Uso AnalisisBiomecanicoController (Craig Larman / TDD).
"""

import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from src.domain.models import ReglaBiomecanica, TecnicaMaestra
from src.infrastructure.repositories.analisis_repository import AnalisisBiomecanicoRepository
from src.infrastructure.repositories.tecnica_repository import TecnicaMaestraRepository
from src.infrastructure.repositories.token_repository import TokenRepository
from src.infrastructure.storage.obs_adapter import HuaweiOBSStorageAdapter
from src.services.controllers.analisis_controller import (
    AnalisisBiomecanicoController,
    DiagnosticoDTO,
    TokenInvalidoError,
)
from src.services.pipeline_engine import PipelineBiomecanicoEngine, ResultadoPipelineDTO


class TestAnalisisBiomecanicoController(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_token_repo = MagicMock(spec=TokenRepository)
        self.mock_tecnica_repo = MagicMock(spec=TecnicaMaestraRepository)
        self.mock_analisis_repo = MagicMock(spec=AnalisisBiomecanicoRepository)
        self.mock_storage_adapter = MagicMock(spec=HuaweiOBSStorageAdapter)
        self.mock_pipeline_engine = MagicMock(spec=PipelineBiomecanicoEngine)

        self.controller = AnalisisBiomecanicoController(
            token_repo=self.mock_token_repo,
            tecnica_repo=self.mock_tecnica_repo,
            analisis_repo=self.mock_analisis_repo,
            storage_adapter=self.mock_storage_adapter,
            pipeline_engine=self.mock_pipeline_engine,
        )

        self.id_tecnica = uuid4()
        self.tecnica_dummy = TecnicaMaestra(
            id=self.id_tecnica,
            nombre="Armbar Canonico",
            categoria_tecnica="Llave de Brazo",
            posicion_origen="Guardia Cerrada",
            ventana_sakoe_chiba=0.15,
            video_url="https://obs.huawei.com/patron.mp4",
            reglas=[
                ReglaBiomecanica(
                    id=uuid4(),
                    articulacion_clave="codo_derecho",
                    umbral_angular_tolerado=15.0,
                    descripcion_error="Brazo hiper-extendido",
                )
            ],
        )
        self.mock_tecnica_repo.obtener_tecnica_y_reglas.return_value = self.tecnica_dummy

    def test_flujo_exitoso_camino_feliz(self) -> None:
        """Prueba 1 (Camino Feliz): Token válido y análisis con falla detectada sube a OBS y persiste en BD."""
        # 1. Configuración de mocks
        self.mock_token_repo.validar_token.return_value = True

        mock_resultado_pipeline = ResultadoPipelineDTO(
            estado_computo="EXITOSO",
            desviacion_maxima=38.5,
            articulacion_afectada="codo_derecho",
            explicacion_error="Brazo hiper-extendido sin control de muneca (38.5° vs 15.0°)",
            fotograma_falla_idx=18,
            imagen_jpg_bytes=b"BYTES_FOTOGRAMA_ANOTADO_JPG",
            coordenada_error_x=320,
            coordenada_error_y=240,
        )
        self.mock_pipeline_engine.ejecutar_pipeline_completo.return_value = mock_resultado_pipeline
        self.mock_storage_adapter.subir_fotograma.return_value = "https://obs.huawei.com/reports/fotograma_123.jpg"

        # 2. Invocación
        diagnostico = self.controller.ejecutar_analisis(
            token="TOKEN_VALIDO_TEST",
            video_bytes=b"VIDEO_MP4_BYTES",
            id_tecnica=self.id_tecnica,
        )

        # 3. Verificaciones
        self.mock_token_repo.validar_token.assert_called_once_with("TOKEN_VALIDO_TEST")
        self.mock_tecnica_repo.obtener_tecnica_y_reglas.assert_called_once_with(self.id_tecnica)
        self.mock_pipeline_engine.ejecutar_pipeline_completo.assert_called_once()
        self.mock_storage_adapter.subir_fotograma.assert_called_once()
        self.mock_analisis_repo.guardar_resultado.assert_called_once()

        self.assertIsInstance(diagnostico, DiagnosticoDTO)
        self.assertEqual(diagnostico.estado, "EXITOSO")
        self.assertEqual(diagnostico.imagen_url, "https://obs.huawei.com/reports/fotograma_123.jpg")
        self.assertEqual(diagnostico.articulacion_afectada, "codo_derecho")
        self.assertAlmostEqual(diagnostico.desviacion_maxima, 38.5)

    def test_zero_persistence_ante_oclusion_prolongada_rf11(self) -> None:
        """Prueba 2 (Zero-Persistence RF-11): Aborto por oclusión NO debe persistir en BD ni subir a OBS."""
        self.mock_token_repo.validar_token.return_value = True

        mock_resultado_pipeline = ResultadoPipelineDTO(
            estado_computo="ABORTADO_OCLUSION",
            desviacion_maxima=0.0,
            articulacion_afectada="",
            explicacion_error="Oclusión continua prolongada (> 45 frames). Aborto sin persistencia.",
            imagen_jpg_bytes=None,
        )
        self.mock_pipeline_engine.ejecutar_pipeline_completo.return_value = mock_resultado_pipeline

        diagnostico = self.controller.ejecutar_analisis(
            token="TOKEN_VALIDO_TEST",
            video_bytes=b"VIDEO_MP4_BYTES",
            id_tecnica=self.id_tecnica,
        )

        # Verificación estricta: OBS y Repositorio NUNCA deben ser invocados
        self.mock_storage_adapter.subir_fotograma.assert_not_called()
        self.mock_analisis_repo.guardar_resultado.assert_not_called()

        self.assertEqual(diagnostico.estado, "ABORTADO_OCLUSION")
        self.assertIsNone(diagnostico.imagen_url)
        self.assertIn("Oclusión continua prolongada", diagnostico.explicacion_error)

    def test_token_invalido_aborta_inmediatamente(self) -> None:
        """Prueba 3: Token rechazado lanza TokenInvalidoError y no consume cómputo ni almacenamiento."""
        self.mock_token_repo.validar_token.return_value = False

        with self.assertRaises(TokenInvalidoError):
            self.controller.ejecutar_analisis(
                token="TOKEN_EXPIRADO_O_FALSO",
                video_bytes=b"VIDEO_MP4_BYTES",
                id_tecnica=self.id_tecnica,
            )

        # Ни pipeline ni OBS ni BD deben ser invocados
        self.mock_pipeline_engine.ejecutar_pipeline_completo.assert_not_called()
        self.mock_storage_adapter.subir_fotograma.assert_not_called()
        self.mock_analisis_repo.guardar_resultado.assert_not_called()


if __name__ == "__main__":
    unittest.main()
