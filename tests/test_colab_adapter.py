# tests/test_colab_adapter.py
from unittest.mock import patch, MagicMock
import pytest
from src.infrastructure.colab_adapter import ColabYOLOAdapter
from src.domain.models import MatrizEsqueletica, Punto3D

class TestColabYOLOAdapter:
    @patch("requests.post")
    def test_inferir_esqueleto_3d_formato_colab(self, mock_post):
        # Simular respuesta JSON exacta de colab_backend.ipynb
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "keypoints_3d": {
                "6": {"x": 150.0, "y": 200.0, "z": 2.0},
                "8": {"x": 180.0, "y": 230.0, "z": 2.3},
                "10": {"x": 210.0, "y": 260.0, "z": 2.6}
            },
            "frame_base64": "data:image/jpeg;base64,mockbase64encodedframe"
        }
        mock_post.return_value = mock_response

        adapter = ColabYOLOAdapter(colab_tunnel_url="https://test-ngrok-tunnel.ngrok-free.app")
        matriz = adapter.inferir_esqueleto_3d("tests/fixtures/test_video.mp4")

        assert isinstance(matriz, MatrizEsqueletica)
        punto_codo = matriz.obtener_punto(8)
        assert isinstance(punto_codo, Punto3D)
        assert punto_codo.x == 180.0
        assert punto_codo.y == 230.0
        assert punto_codo.z == 2.3
        assert adapter.ultimo_frame_base64 == "data:image/jpeg;base64,mockbase64encodedframe"

        # Verificar que la llamada HTTP se hizo al endpoint /inferir con multipart file
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://test-ngrok-tunnel.ngrok-free.app/inferir"
        assert "files" in kwargs
        assert "file" in kwargs["files"]
