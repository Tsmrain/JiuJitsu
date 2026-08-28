"""
Pruebas Unitarias Simuladas (Mocks) para HuaweiOBSStorageAdapter (Craig Larman / TDD).
Verifica la interacción con Huawei Cloud OBS sin requerir credenciales ni red externa.
"""

import unittest
from unittest.mock import MagicMock
from src.infrastructure.storage.obs_adapter import (
    HuaweiOBSStorageAdapter,
    StorageOperationError,
)


class TestHuaweiOBSStorageAdapter(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_client = MagicMock()
        self.server = "obs.la-south-2.myhuaweicloud.com"
        self.bucket_in = "bjj-videos-input"
        self.bucket_out = "bjj-reports-output"

        # Adaptador inyectado con cliente simulado
        self.adapter = HuaweiOBSStorageAdapter(
            ak="MOCK_AK_TEST",
            sk="MOCK_SK_TEST",
            server=self.server,
            bucket_input=self.bucket_in,
            bucket_output=self.bucket_out,
            client=self.mock_client,
        )

    def test_subir_video_exitoso(self) -> None:
        """Prueba 1: Sube video simulado y comprueba llamada a putObject con argumentos correctos y retorno de URL."""
        video_dummy = b"\x00\x00\x00 ftypmp42\x00\x00\x00\x00isommp42"
        object_key = "atletas/estudiante_01/armbar.mp4"

        # Simular respuesta exitosa de OBS (status 200)
        mock_resp = MagicMock()
        mock_resp.status = 200
        self.mock_client.putObject.return_value = mock_resp

        url_resultado = self.adapter.subir_video(video_dummy, object_key)

        # Verificación de invocación
        self.mock_client.putObject.assert_called_once()
        args, kwargs = self.mock_client.putObject.call_args

        self.assertEqual(kwargs["bucketName"], self.bucket_in)
        self.assertEqual(kwargs["objectKey"], object_key)
        self.assertEqual(kwargs["content"], video_dummy)

        # Verificación del formato de URL HTTPS resultante
        self.assertIsInstance(url_resultado, str)
        self.assertEqual(
            url_resultado,
            f"https://{self.bucket_in}.{self.server}/{object_key}",
        )

    def test_subir_fotograma_exitoso(self) -> None:
        """Prueba 2: Sube fotograma JPG simulado y verifica Content-Type 'image/jpeg'."""
        foto_dummy = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        object_key = "reportes/analisis_789_annotated.jpg"

        mock_resp = MagicMock()
        mock_resp.status = 200
        self.mock_client.putObject.return_value = mock_resp

        url_resultado = self.adapter.subir_fotograma(foto_dummy, object_key)

        self.mock_client.putObject.assert_called_once()
        args, kwargs = self.mock_client.putObject.call_args

        self.assertEqual(kwargs["bucketName"], self.bucket_out)
        self.assertEqual(kwargs["objectKey"], object_key)
        self.assertEqual(kwargs["content"], foto_dummy)

        # Verificar headers con Content-Type
        headers = kwargs.get("headers")
        self.assertIsNotNone(headers)
        # PutObjectHeader puede ser diccionario o tener atributo contentType
        content_type = headers.get("contentType") if isinstance(headers, dict) else getattr(headers, "contentType", None)
        self.assertEqual(content_type, "image/jpeg")

        self.assertEqual(
            url_resultado,
            f"https://{self.bucket_out}.{self.server}/{object_key}",
        )

    def test_descargar_objeto_exitoso(self) -> None:
        """Prueba 3: Descarga objeto y comprueba retorno de bytes crudos."""
        contenido_esperado = b"CONTENIDO_BINARIO_VIDEO_O_IMAGEN"
        object_key = "armbar_patron_master.mp4"

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.body.read.return_value = contenido_esperado
        self.mock_client.getObject.return_value = mock_resp

        resultado = self.adapter.descargar_objeto(object_key, self.bucket_in)

        self.mock_client.getObject.assert_called_once_with(
            bucketName=self.bucket_in, objectKey=object_key
        )
        self.assertEqual(resultado, contenido_esperado)

    def test_error_en_subida_lanza_excepcion_personalizada(self) -> None:
        """Prueba 4: Simula fallo de OBS y comprueba que se capture y levante StorageOperationError."""
        # Caso A: Excepción directa lanzada por el cliente de red
        self.mock_client.putObject.side_effect = Exception("Conexión rehusada por timeout en endpoint OBS")

        with self.assertRaises(StorageOperationError) as contexto:
            self.adapter.subir_video(b"bytes_de_prueba", "falla_conexion.mp4")

        self.assertIn("Error inesperado al subir video a Huawei OBS", str(contexto.exception))

        # Caso B: Respuesta HTTP con código de error (ej. 403 Forbidden o 404 Bucket Not Found)
        self.mock_client.putObject.side_effect = None
        mock_resp_error = MagicMock()
        mock_resp_error.status = 403
        mock_resp_error.reason = "Forbidden"
        self.mock_client.putObject.return_value = mock_resp_error

        with self.assertRaises(StorageOperationError) as contexto_http:
            self.adapter.subir_fotograma(b"bytes_foto", "falla_permisos.jpg")

        self.assertIn("Fallo al subir fotograma", str(contexto_http.exception))


if __name__ == "__main__":
    unittest.main()
