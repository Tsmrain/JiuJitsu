import pytest
from unittest.mock import MagicMock, patch
from corpocmente.infrastructure.ai.adapters import GeminiApiAdapter, GeminiRateLimitError
from google.genai.errors import APIError

@pytest.fixture
def mock_genai_client():
    with patch("corpocmente.infrastructure.ai.adapters.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        yield mock_instance

def test_validar_es_jiujitsu_exitoso(mock_genai_client, tmp_path):
    # Crear un archivo de prueba temporal
    fake_video = tmp_path / "test_video.mp4"
    fake_video.write_bytes(b"fake video content")

    # Configurar Mocks
    mock_file = MagicMock()
    mock_file.name = "files/12345"
    mock_genai_client.files.upload.return_value = mock_file
    
    mock_response = MagicMock()
    mock_response.text = "SI, el video muestra un pasaje de guardia de Jiu-Jitsu."
    mock_genai_client.models.generate_content.return_value = mock_response

    adapter = GeminiApiAdapter(api_key="fake_key")
    es_valido = adapter.validar_es_jiujitsu(str(fake_video))

    assert es_valido is True
    mock_genai_client.files.upload.assert_called_once()
    mock_genai_client.files.delete.assert_called_once_with(name="files/12345")

def test_validar_es_jiujitsu_contenido_invalido(mock_genai_client, tmp_path):
    fake_video = tmp_path / "fake_dance.mp4"
    fake_video.write_bytes(b"fake content")

    mock_file = MagicMock(name="files/67890")
    mock_genai_client.files.upload.return_value = mock_file
    
    mock_response = MagicMock()
    mock_response.text = "NO, el video es un baile."
    mock_genai_client.models.generate_content.return_value = mock_response

    adapter = GeminiApiAdapter(api_key="fake_key")
    es_valido = adapter.validar_es_jiujitsu(str(fake_video))

    assert es_valido is False

def test_generar_texto_feedback_rate_limit(mock_genai_client, tmp_path):
    fake_frame = tmp_path / "frame.jpg"
    fake_frame.write_bytes(b"fake image data")

    import requests
    mock_requests_response = MagicMock(spec=requests.Response)
    mock_requests_response.json.return_value = {"error": {"message": "RESOURCE_EXHAUSTED", "code": 429}}
    api_error = APIError(code=429, response=mock_requests_response)
    mock_genai_client.models.generate_content.side_effect = api_error

    adapter = GeminiApiAdapter(api_key="fake_key")

    with pytest.raises(GeminiRateLimitError):
        adapter.generar_texto_feedback("Prompt de prueba", str(fake_frame))
