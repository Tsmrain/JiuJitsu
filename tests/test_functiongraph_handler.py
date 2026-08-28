"""
Pruebas Unitarias para el Handler Serverless de FunctionGraph (Craig Larman / TDD).
"""

import base64
import json
import unittest
from uuid import uuid4

from src.infrastructure.serverless.functiongraph_handler import handler


class TestFunctionGraphHandler(unittest.TestCase):

    def setUp(self) -> None:
        self.video_bytes_dummy = b"\x00\x00\x00 ftypmp42\x00\x00\x00\x00isommp42DUMMY_DATA"
        self.video_b64 = base64.b64encode(self.video_bytes_dummy).decode("utf-8")

        self.tecnica_data = {
            "id": str(uuid4()),
            "nombre": "Armbar desde Guardia Cerrada",
            "categoria_tecnica": "Llave de Brazo",
            "posicion_origen": "Guardia Cerrada",
            "ventana_sakoe_chiba": 0.15,
            "video_url": "https://obs.huawei.com/patron.mp4",
            "reglas": [
                {
                    "id": str(uuid4()),
                    "articulacion_clave": "codo_derecho",
                    "umbral_angular_tolerado": 15.0,
                    "descripcion_error": "Brazo hiper-extendido",
                }
            ],
        }

    def test_handler_invocacion_directa_exitosa(self) -> None:
        """Prueba 1: Invocación con payload dict válido retorna 200 y JSON estructurado."""
        event = {
            "video_base64": self.video_b64,
            "tecnica_maestra": self.tecnica_data,
        }

        response = handler(event)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["headers"]["Content-Type"], "application/json")

        body = json.loads(response["body"])
        self.assertIn("estado_computo", body)
        self.assertIn("desviacion_maxima", body)
        self.assertIn("articulacion_afectada", body)
        self.assertIn("explicacion_error", body)
        self.assertIn("fotograma_base64", body)

    def test_handler_invocacion_con_body_string_api_gateway(self) -> None:
        """Prueba 2: Simula petición proveniente de API Gateway con 'body' como string JSON."""
        event = {
            "body": json.dumps({
                "video_base64": self.video_b64,
                "tecnica_maestra": self.tecnica_data,
            })
        }

        response = handler(event)

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["estado_computo"], "SIN_FALLAS")

    def test_handler_falta_video_retorna_bad_request_400(self) -> None:
        """Prueba 3: Solicitud sin 'video_base64' retorna HTTP 400 Bad Request."""
        event = {
            "tecnica_maestra": self.tecnica_data,
        }

        response = handler(event)

        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertEqual(body["estado_computo"], "ERROR_SOLICITUD")

    def test_handler_error_interno_retorna_500(self) -> None:
        """Prueba 4: Datos corruptos en base64 capturados limpiamente con HTTP 500."""
        event = {
            "video_base64": "ESTO_NO_ES_BASE64_VALIDO_!@#$",
            "tecnica_maestra": self.tecnica_data,
        }

        response = handler(event)

        self.assertEqual(response["statusCode"], 500)
        body = json.loads(response["body"])
        self.assertEqual(body["estado_computo"], "ERROR_SERVIDOR")


if __name__ == "__main__":
    unittest.main()
