import pytest
from unittest.mock import patch, MagicMock
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter, NGROK_HEADERS


def test_generar_embedding_imagen_exige_worker_activo():
    adapter = QwenEmbeddingAdapter(colab_url="")
    with pytest.raises(RuntimeError):
        adapter.generar_embedding("dummy_frame.jpg")


def test_generar_embedding_texto_no_inventa_vector_si_colab_no_esta_disponible():
    adapter = QwenEmbeddingAdapter(colab_url="")
    with pytest.raises(RuntimeError, match="COLAB_TUNNEL_URL"):
        adapter.generar_embedding_texto("control de cadera")


@patch("corpocmente.infrastructure.ai.qwen_adapter.requests.post")
def test_qwen_embedding_adapter_colab_success(mock_post, tmp_path):
    # Arrange
    frame_file = tmp_path / "dummy_frame.jpg"
    frame_file.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF")

    adapter = QwenEmbeddingAdapter(colab_url="http://fake-colab.com")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embeddings": [[0.1] * 2048]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    # Act
    embedding = adapter.generar_embedding(str(frame_file))

    # Assert
    assert len(embedding) == 2048
    assert embedding == [0.1] * 2048
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["headers"]["ngrok-skip-browser-warning"] == "1"


@patch("corpocmente.infrastructure.ai.qwen_adapter.requests.post")
def test_generar_embedding_texto_usa_form_data(mock_post):
    """
    Regression test C11.4: generar_embedding_texto debe enviar
    `data={"texto": ...}` (form-data) al Worker de Colab, NO `json={"text": ...}`.
    Y debe incluir los headers de ngrok.
    """
    # Arrange
    adapter = QwenEmbeddingAdapter(colab_url="http://fake-colab.com")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embeddings": [[0.07] * 2048]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    # Act
    embedding = adapter.generar_embedding_texto("Teoría del Armbar")

    # Assert
    assert len(embedding) == 2048
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs

    # Debe usar `data=`, NO `json=`
    assert "data" in call_kwargs, "El fix C11.4 requiere enviar form-data (data=)"
    assert "json" not in call_kwargs, "El fix C11.4 prohíbe enviar JSON"
    assert call_kwargs["data"] == {"texto": "Teoría del Armbar"}, \
        "El campo debe llamarse 'texto' (como espera el endpoint /embed_text de FastAPI)"
    assert call_kwargs["headers"]["ngrok-skip-browser-warning"] == "1"
