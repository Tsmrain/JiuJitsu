import pytest
from fastapi.testclient import TestClient
import io

from src.presentation.api import app

client = TestClient(app)

def test_registrar_tecnica_bug_formdata():
    """
    Simula la petición POST a /api/v1/instructor/tecnicas 
    con los parámetros que envía app.js.
    """
    url = "/api/v1/instructor/tecnicas"
    
    data = {
        "nombre": "Ezequiel Choke",
        "categoria": "General",
        "id_profesor": "inst_santiago",
        "descripcion": "Descripción de prueba"
    }
    
    files = {
        "file": ("video.mp4", io.BytesIO(b"dummy video content"), "video/mp4")
    }

    # Create professor to avoid 400 error
    client.post("/api/v1/profesores", json={"id_profesor": "inst_santiago", "nombre": "Santiago", "email": "santi@test.com"})

    response = client.post(url, data=data, files=files)
    
    assert response.status_code == 200, f"Error: {response.text}"
    json_response = response.json()
    assert "message" in json_response or "id_tecnica" in json_response
