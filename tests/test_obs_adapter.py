"""
Pruebas Unitarias - HuaweiOBSStorageAdapter (TDD)

Verifica la interacción con el SDK esdk-obs-python, validación de Information Expert:
- RF-07: Rechazo estricto si el video supera 5 MB sin llamar a OBS.
- RP-02: Rechazo estricto si el fotograma supera 100 KB sin llamar a OBS.
- Mapeo de errores a StorageOperationError.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.storage.obs_adapter import (
    HuaweiOBSStorageAdapter,
    StorageOperationError,
)


class TestHuaweiOBSStorageAdapter(unittest.TestCase):
    """Batería de pruebas con mocks para HuaweiOBSStorageAdapter."""

    def setUp(self) -> None:
        self.mock_client = MagicMock()
        self.server = "obs.la-south-2.myhuaweicloud.com"
        self.bucket_in = "bjj-videos-input"
        self.bucket_out = "bjj-reports-output"

        self.adapter = HuaweiOBSStorageAdapter(
            ak="MOCK_AK_TEST",
            sk="MOCK_SK_TEST",
            server=self.server,
            bucket_input=self.bucket_in,
            bucket_output=self.bucket_out,
            client=self.mock_client,
        )

    def test_subir_video_exitoso(self) -> None:
        """Prueba de caso feliz: sube un video <= 5MB y comprueba URL HTTPS retornada."""
        video_dummy = b"\x00" * (1024 * 1024)  # 1 MB
        video_id = "ejecucion_001.mp4"

        mock_resp = MagicMock()
        mock_resp.status = 200
        self.mock_client.putObject.return_value = mock_resp

        url_resultado = self.adapter.subir_video(video_dummy, video_id)

        self.mock_client.putObject.assert_called_once()
        _, kwargs = self.mock_client.putObject.call_args

        self.assertEqual(kwargs["bucketName"], self.bucket_in)
        self.assertEqual(kwargs["objectKey"], video_id)
        self.assertEqual(kwargs["content"], video_dummy)

        self.assertEqual(
            url_resultado,
            f"https://{self.bucket_in}.{self.server}/{video_id}",
        )

    def test_subir_video_rechaza_video_mayor_a_5mb_sin_llamar_sdk(self) -> None:
        """Prueba crítica (RF-07): Video de 6MB lanza ValueError y NO llama a putObject."""
        video_grande = b"\x00" * (6 * 1024 * 1024)  # 6 MB (> 5 MB)
        video_id = "ejecucion_grande.mp4"

        with self.assertRaises(ValueError) as ctx:
            self.adapter.subir_video(video_grande, video_id)

        self.assertIn("RF-07 Violado", str(ctx.exception))
        # El SDK de OBS NUNCA debe haber sido llamado
        self.mock_client.putObject.assert_not_called()

    def test_subir_fotograma_exitoso(self) -> None:
        """Prueba de caso feliz: sube fotograma <= 100KB y comprueba URL HTTPS retornada."""
        frame_dummy = b"\xff\xd8\xff\xe0" + b"\x00" * (80 * 1024)  # ~80 KB
        analisis_id = "analisis_001.jpg"

        mock_resp = MagicMock()
        mock_resp.status = 200
        self.mock_client.putObject.return_value = mock_resp

        url_resultado = self.adapter.subir_fotograma(frame_dummy, analisis_id)

        self.mock_client.putObject.assert_called_once()
        _, kwargs = self.mock_client.putObject.call_args

        self.assertEqual(kwargs["bucketName"], self.bucket_out)
        self.assertEqual(kwargs["objectKey"], analisis_id)
        self.assertEqual(kwargs["content"], frame_dummy)
        self.assertEqual(
            url_resultado,
            f"https://{self.bucket_out}.{self.server}/{analisis_id}",
        )

    def test_subir_fotograma_rechaza_frame_mayor_a_100kb_sin_llamar_sdk(self) -> None:
        """Prueba crítica (RP-02): Fotograma de 150KB lanza ValueError y NO llama a putObject."""
        frame_grande = b"\x00" * (150 * 1024)  # 150 KB (> 100 KB)
        analisis_id = "analisis_pesado.jpg"

        with self.assertRaises(ValueError) as ctx:
            self.adapter.subir_fotograma(frame_grande, analisis_id)

        self.assertIn("RP-02 Violado", str(ctx.exception))
        self.mock_client.putObject.assert_not_called()

    def test_descargar_objeto_exitoso(self) -> None:
        """Prueba descarga de objeto y comprueba retorno de bytes crudos."""
        contenido_esperado = b"CONTENIDO_BINARIO_VIDEO_MP4"
        object_key = "armbar_ref.mp4"

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.body.read.return_value = contenido_esperado
        self.mock_client.getObject.return_value = mock_resp

        resultado = self.adapter.descargar_objeto(object_key)

        self.mock_client.getObject.assert_called_once_with(
            bucketName=self.bucket_in, objectKey=object_key
        )
        self.assertEqual(resultado, contenido_esperado)

    def test_error_en_obs_lanza_storage_operation_error(self) -> None:
        """Prueba que fallos de red/cliente OBS son encapsulados en StorageOperationError."""
        self.mock_client.putObject.side_effect = Exception("Conexión rechazada por timeout")

        with self.assertRaises(StorageOperationError) as ctx:
            self.adapter.subir_video(b"\x00" * 1024, "video_error.mp4")

        self.assertIn("Error inesperado al subir video", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
