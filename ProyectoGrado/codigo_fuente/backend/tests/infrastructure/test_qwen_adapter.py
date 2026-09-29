import pytest
from unittest.mock import patch, MagicMock
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter

def test_qwen_embedding_adapter_fallback():
    # Arrange
    adapter = QwenEmbeddingAdapter(colab_url="")
    
    # Act
    embedding = adapter.generar_embedding("dummy_frame.jpg")
    
    # Assert
    assert len(embedding) == 2048
    assert embedding == [0.05] * 2048

@patch("corpocmente.infrastructure.ai.qwen_adapter.requests.post")
def test_qwen_embedding_adapter_colab_success(mock_post):
    # Arrange
    adapter = QwenEmbeddingAdapter(colab_url="http://fake-colab.com")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"embeddings": [[0.1] * 2048]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    # Act
    embedding = adapter.generar_embedding("dummy_frame.jpg")
    
    # Assert
    assert len(embedding) == 2048
    assert embedding == [0.1] * 2048
    mock_post.assert_called_once()

@patch("corpocmente.infrastructure.ai.qwen_adapter.requests.post")
def test_generar_embedding_texto_usa_form_data(mock_post):
    """
    Regression test C11.4: generar_embedding_texto debe enviar
    `data={"texto": ...}` (form-data) al Worker de Colab, NO `json={"text": ...}`.
    """
    # Arrange
    adapter = QwenEmbeddingAdapter(colab_url="http://fake-colab.com")
    mock_response = MagicMock()
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

