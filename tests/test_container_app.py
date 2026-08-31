"""
Pruebas Unitarias - Adaptador de Entrada HTTP para Custom Container (TDD)

Verifica los endpoints requeridos por Huawei Cloud FunctionGraph Custom Container:
- GET /health: Liveness probe retornando {"status": "healthy"} y código 200.
- POST /init: Mitigación de Cold Start retornando {"status": "initialized"} y código 200.
- POST /invoke: Delegación estricta hacia functiongraph_handler con transformación de evento APIG.
- Propagación de códigos de error (400, 500).

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.infrastructure.serverless.container_app import app


class TestContainerApp(unittest.TestCase):
    """Batería de pruebas para el servidor FastAPI del contenedor."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_check(self) -> None:
        """Prueba 1: GET /health retorna 200 y {"status": "healthy"}."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_init_endpoint(self) -> None:
        """Prueba 2: POST /init retorna 200 y {"status": "initialized", "model_loaded": True}."""
        response = self.client.post("/init")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "initialized")
        self.assertTrue(data.get("model_loaded"))


    @patch("src.infrastructure.serverless.container_app.handler")
    def test_invoke_delegation(self, mock_handler) -> None:
        """Prueba 3: POST /invoke transforma la petición y delega en functiongraph_handler."""
        mock_handler.return_value = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "estado_computo": "EXITOSO",
                "distancia_dtw": 0.42,
                "articulacion_afectada": "codo_derecho",
            }),
            "isBase64Encoded": False,
        }

        payload = {
            "video_base64": "AAAAIGZ0eXBtcDQyAAAAAGlzb21tcDQy",
            "tecnica_id": "test-armbar-uuid",
        }

        response = self.client.post(
            "/invoke?tecnica_id=test-armbar-uuid",
            json=payload,
            headers={"X-Custom-Auth": "SecretToken123"},
        )

        # Verificar respuesta HTTP
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["estado_computo"], "EXITOSO")
        self.assertEqual(data["distancia_dtw"], 0.42)
        self.assertEqual(data["articulacion_afectada"], "codo_derecho")

        # Verificar que el handler fue llamado con la estructura de evento de API Gateway
        mock_handler.assert_called_once()
        event_recibido = mock_handler.call_args[0][0]

        self.assertIn("body", event_recibido)
        self.assertIn("headers", event_recibido)
        self.assertIn("queryStringParameters", event_recibido)
        self.assertFalse(event_recibido["isBase64Encoded"])
        self.assertEqual(event_recibido["queryStringParameters"].get("tecnica_id"), "test-armbar-uuid")

    @patch("src.infrastructure.serverless.container_app.handler")
    def test_invoke_error_handling(self, mock_handler) -> None:
        """Prueba 4: POST /invoke propaga correctamente códigos de error como HTTP 400."""
        mock_handler.return_value = {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "estado_computo": "ERROR_VALIDACION",
                "error": "RF-07 Violado: El video supera los 5MB permitidos",
            }),
            "isBase64Encoded": False,
        }

        response = self.client.post("/invoke", json={"video_bytes": "too_large"})

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["estado_computo"], "ERROR_VALIDACION")
        self.assertIn("RF-07 Violado", data["error"])


if __name__ == "__main__":
    unittest.main()
