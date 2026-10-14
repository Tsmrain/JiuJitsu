import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
import io

from corpocmente.main import app

pytestmark = pytest.mark.skip(reason="Pendiente migración a PostgREST")

client = TestClient(app)

def test_analizar_video_crea_evaluacion_pendiente():
    video_content = b"fake video content"
    video_file = io.BytesIO(video_content)
    tecnica_id = str(uuid4())
    
    data = {
        "tecnica_id": tecnica_id,
        "tecnica_nombre": "Armbar",
        "idioma": "es"
    }
    files = {"video": ("test_video.mp4", video_file, "video/mp4")}
    
    response = client.post("/api/v1/evaluaciones/analizar", data=data, files=files)
    
    assert response.status_code == 200
    response_data = response.json()
    assert "evaluacion_id" in response_data
    assert response_data["estado"] == "procesando"
    
    # Verificar en la base de datos
    eval_id = response_data["evaluacion_id"]
    # assert eval_id in EVALUACIONES_DB
    # assert EVALUACIONES_DB[eval_id]["tecnica_nombre"] == "Armbar"

def test_flujo_completo_worker():
    # 1. Subir video
    video_content = b"fake video content for worker"
    video_file = io.BytesIO(video_content)
    tecnica_id = str(uuid4())
    
    data = {
        "tecnica_id": tecnica_id,
        "tecnica_nombre": "Kimura",
        "idioma": "pt"
    }
    files = {"video": ("test_video2.mp4", video_file, "video/mp4")}
    
    response = client.post("/api/v1/evaluaciones/analizar", data=data, files=files)
    assert response.status_code == 200
    eval_id = response.json()["evaluacion_id"]
    
    # 2. GET /pendientes
    response_pendientes = client.get("/api/v1/evaluaciones/pendientes")
    assert response_pendientes.status_code == 200
    tarea = response_pendientes.json()
    assert tarea["id"] == eval_id
    assert tarea["estado"] == "en_progreso_worker"
    
    # 3. GET /video/{id}
    response_video = client.get(f"/api/v1/evaluaciones/video/{eval_id}")
    assert response_video.status_code == 200
    assert response_video.content == video_content
    
    # 4. POST /resultado/{id}
    resultado_data = {
        "similitud": 95.5,
        "feedback": "Excelente ejecución.",
        "estado": "completado"
    }
    response_resultado = client.post(f"/api/v1/evaluaciones/resultado/{eval_id}", json=resultado_data)
    assert response_resultado.status_code == 200
    
    # 5. GET /{id}
    response_final = client.get(f"/api/v1/evaluaciones/{eval_id}")
    assert response_final.status_code == 200
    eval_final = response_final.json()
    assert eval_final["estado"] == "completado"
    assert eval_final["similitud"] == 95.5
    assert eval_final["feedback"] == "Excelente ejecución."

def test_analizar_video_formato_invalido():
    video_content = b"fake txt content"
    video_file = io.BytesIO(video_content)

    tecnica_id = str(uuid4())
    data = {
        "tecnica_id": tecnica_id,
        "tecnica_nombre": "Kimura",
        "idioma": "es"
    }
    
    files = {
        "video": ("test_file.txt", video_file, "text/plain")
    }

    response = client.post("/api/v1/evaluaciones/analizar", data=data, files=files)

    assert response.status_code == 400
    assert "Formato de archivo no soportado" in response.json()["detail"]
