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


def test_feedback_envia_frame_del_alumno_y_evidencia_visual_a_gemini(mock_genai_client, tmp_path, monkeypatch):
    import corpocmente.infrastructure.ai.adapters as gemini_module
    monkeypatch.setattr(gemini_module, "RAG_MEDIA_STORAGE_ROOTS", (tmp_path,))
    frame_alumno = tmp_path / "alumno.jpg"
    frame_referencia = tmp_path / "profesor.jpg"
    frame_alumno.write_bytes(b"student-image")
    frame_referencia.write_bytes(b"teacher-image")
    mock_genai_client.models.generate_content.return_value.text = "Ajusta la cadera hacia el compañero."

    adapter = GeminiApiAdapter(api_key="fake_key")
    adapter.generar_texto_feedback(
        "Corrige el error principal.",
        str(frame_alumno),
        evidencias_visuales=[{"payload": {"media_path": str(frame_referencia)}}],
    )

    contents = mock_genai_client.models.generate_content.call_args.kwargs["contents"]
    assert len(contents) == 3
    assert contents[-1] == "Corrige el error principal."


def test_feedback_ignora_evidencia_fuera_del_storage_y_limita_imagenes(mock_genai_client, tmp_path, monkeypatch):
    import corpocmente.infrastructure.ai.adapters as gemini_module
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    monkeypatch.setattr(gemini_module, "RAG_MEDIA_STORAGE_ROOTS", (allowed_dir,))

    frame_alumno = allowed_dir / "alumno.jpg"
    frame_alumno.write_bytes(b"student")
    inside_paths = []
    for index in range(4):
        path = allowed_dir / f"ref-{index}.jpg"
        path.write_bytes(b"reference")
        inside_paths.append(path)
    outside = outside_dir / "private.jpg"
    outside.write_bytes(b"private")
    mock_genai_client.models.generate_content.return_value.text = "Respuesta breve."

    adapter = GeminiApiAdapter(api_key="fake_key")
    adapter.generar_texto_feedback(
        "Evalúa el movimiento.",
        str(frame_alumno),
        evidencias_visuales=[
            {"payload": {"media_path": str(path)}} for path in inside_paths
        ] + [{"payload": {"media_path": str(outside)}}],
    )
    contents = mock_genai_client.models.generate_content.call_args.kwargs["contents"]
    assert len(contents) == 5  # Fotograma alumno + máximo 3 referencias + prompt.
