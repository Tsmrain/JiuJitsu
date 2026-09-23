import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4, UUID
import io

from corpocmente.main import app

client = TestClient(app)

@patch("corpocmente.ui.api.routes.controller.procesar_evaluacion_video")
def test_analizar_video_success(mock_procesar):
    # Configurar el mock
    mock_resultado = MagicMock()
    mock_resultado.similitud = 85.5
    mock_resultado.feedback = "Buen trabajo, mejora la postura de los brazos."
    mock_procesar.return_value = mock_resultado

    # Simular archivo de video
    video_content = b"fake video content"
    video_file = io.BytesIO(video_content)
    
    # Datos del formulario
    tecnica_id = str(uuid4())
    data = {
        "tecnica_id": tecnica_id,
        "idioma": "es"
    }
    
    # Archivos a enviar
    files = {
        "video": ("test_video.mp4", video_file, "video/mp4")
    }

    response = client.post("/api/v1/evaluaciones/analizar", data=data, files=files)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["similitud"] == 85.5
    assert response_data["feedback"] == "Buen trabajo, mejora la postura de los brazos."
    assert response_data["estado"] == "completado"
    
    mock_procesar.assert_called_once()
    _, kwargs = mock_procesar.call_args
    assert kwargs["tecnica_id"] == UUID(tecnica_id)
    assert kwargs["idioma"] == "es"
    assert "video_path" in kwargs

def test_analizar_video_formato_invalido():
    video_content = b"fake txt content"
    video_file = io.BytesIO(video_content)

    tecnica_id = str(uuid4())
    data = {
        "tecnica_id": tecnica_id,
        "idioma": "es"
    }
    
    files = {
        "video": ("test_file.txt", video_file, "text/plain")
    }

    response = client.post("/api/v1/evaluaciones/analizar", data=data, files=files)

    assert response.status_code == 400
    assert "Formato de archivo no soportado" in response.json()["detail"]

@patch("corpocmente.ui.api.routes.controller.procesar_evaluacion_video")
def test_analizar_video_error_procesamiento(mock_procesar):
    mock_procesar.side_effect = ValueError("El video es demasiado corto para extraer keypoints.")

    video_content = b"fake video content"
    video_file = io.BytesIO(video_content)

    tecnica_id = str(uuid4())
    data = {
        "tecnica_id": tecnica_id,
        "idioma": "es"
    }
    
    files = {
        "video": ("test_video.mp4", video_file, "video/mp4")
    }

    response = client.post("/api/v1/evaluaciones/analizar", data=data, files=files)

    assert response.status_code == 422
    assert "El video es demasiado corto" in response.json()["detail"]
