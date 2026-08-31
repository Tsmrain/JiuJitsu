"""
Pruebas Unitarias - Handler Serverless de FunctionGraph (TDD)

Verifica:
- Evento sin body retorna 400 Bad Request.
- Evento con isBase64Encoded: True se decodifica y procesa correctamente con código 200.
- Manejo de ValueError retornando código 400.
- Inyección de dependencias (mock controller).

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import base64
import json
import unittest
from unittest.mock import MagicMock

from src.infrastructure.serverless.functiongraph_handler import handler


class TestFunctionGraphHandler(unittest.TestCase):
    """Batería de pruebas unitarias para functiongraph_handler."""

    def setUp(self) -> None:
        self.mock_controller = MagicMock()
        self.video_bytes_dummy = b"\x00" * 1024  # 1 KB
        self.video_b64 = base64.b64encode(self.video_bytes_dummy).decode("utf-8")

    def test_handler_sin_body_retorna_400(self) -> None:
        """Prueba que un evento sin 'body' o con body None retorna 400 Bad Request."""
        event_sin_body = {
            "httpMethod": "POST",
            "queryStringParameters": {"tecnica_id": "armbar-123"},
        }

        response = handler(event_sin_body, controller=self.mock_controller)

        self.assertEqual(response["statusCode"], 400)
        self.assertFalse(response["isBase64Encoded"])
        self.assertEqual(response["headers"]["Content-Type"], "application/json")

        body = json.loads(response["body"])
        self.assertEqual(body["estado_computo"], "ERROR_VALIDACION")
        self.assertIn("body", body["error"])
        self.mock_controller.ejecutar_analisis.assert_not_called()

    def test_handler_evento_base64_decodifica_y_retorna_200(self) -> None:
        """Prueba que un evento con isBase64Encoded: True se decodifica y retorna 200."""
        self.mock_controller.ejecutar_analisis.return_value = {
            "estado_computo": "EXITOSO",
            "distancia_dtw": 0.85,
            "articulacion_afectada": "codo_derecho",
            "pico_desviacion": 18.5,
            "video_url": "https://obs.huaweicloud.com/bjj-videos-input/ejecucion_armbar.mp4",
        }

        event = {
            "httpMethod": "POST",
            "body": self.video_b64,
            "isBase64Encoded": True,
            "headers": {"Content-Type": "application/json"},
            "queryStringParameters": {"tecnica_id": "armbar-123"},
        }

        response = handler(event, controller=self.mock_controller)

        self.assertEqual(response["statusCode"], 200)
        self.assertFalse(response["isBase64Encoded"])
        self.assertEqual(response["headers"]["Content-Type"], "application/json")

        body = json.loads(response["body"])
        self.assertEqual(body["estado_computo"], "EXITOSO")
        self.assertEqual(body["distancia_dtw"], 0.85)
        self.assertEqual(body["articulacion_afectada"], "codo_derecho")

        # Verificar que el controlador recibió los bytes decodificados
        self.mock_controller.ejecutar_analisis.assert_called_once()
        args, kwargs = self.mock_controller.ejecutar_analisis.call_args
        self.assertEqual(kwargs["video_bytes"], self.video_bytes_dummy)
        self.assertEqual(kwargs["id_tecnica"], "armbar-123")

    def test_handler_value_error_retorna_400(self) -> None:
        """Prueba que errores de validación de negocio (ValueError) retornan 400."""
        self.mock_controller.ejecutar_analisis.side_effect = ValueError(
            "RF-07 Violado: El video supera los 5MB permitidos"
        )

        event = {
            "httpMethod": "POST",
            "body": self.video_b64,
            "isBase64Encoded": True,
            "queryStringParameters": {"tecnica_id": "armbar-123"},
        }

        response = handler(event, controller=self.mock_controller)

        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertEqual(body["estado_computo"], "ERROR_VALIDACION")
        self.assertIn("RF-07 Violado", body["error"])

    def test_handler_excepcion_inesperada_retorna_500(self) -> None:
        """Prueba que errores inesperados del sistema retornan 500 Internal Server Error."""
        self.mock_controller.ejecutar_analisis.side_effect = RuntimeError(
            "Fallo irrecuperable en GPU/CPU"
        )

        event = {
            "httpMethod": "POST",
            "body": self.video_b64,
            "isBase64Encoded": True,
            "queryStringParameters": {"tecnica_id": "armbar-123"},
        }

        response = handler(event, controller=self.mock_controller)

        self.assertEqual(response["statusCode"], 500)
        body = json.loads(response["body"])
        self.assertEqual(body["estado_computo"], "ERROR_SERVIDOR")
        self.assertIn("Error interno en FunctionGraph", body["error"])


if __name__ == "__main__":
    unittest.main()
