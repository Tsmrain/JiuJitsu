# tests/test_iteracion5.py
import pytest
from fastapi.testclient import TestClient
from src.presentation.api import app, container, TAREAS_ESTADO
from src.application.controllers import EvaluacionController
from src.infrastructure.mocks import MockYOLOEngine, MockGeminiService, MockTecnicaRepository

class MockHistorialRepository:
    """Mock en memoria para verificar la persistencia automática de historial."""
    def __init__(self):
        self.registros = []

    def guardar_evaluacion(self, id_alumno: str, id_tecnica: str, resultado: dict) -> str:
        desviaciones = resultado.get("desviaciones", [])
        promedio = sum(d["desviacion"] for d in desviaciones) / len(desviaciones) if desviaciones else 0.0
        registro = {
            "id_evaluacion": f"mock-eval-{len(self.registros) + 1}",
            "id_alumno": id_alumno,
            "id_tecnica": id_tecnica,
            "es_valido": resultado.get("es_valido", False),
            "total_desviaciones": resultado.get("total_desviaciones", 0),
            "desviacion_promedio_grados": promedio,
            "consejo_pedagogico": resultado.get("consejo_pedagogico", ""),
            "fecha": "2026-09-11T12:00:00"
        }
        self.registros.append(registro)
        return registro["id_evaluacion"]

    def obtener_progreso(self, id_alumno: str):
        return [r for r in self.registros if r["id_alumno"] == id_alumno]

@pytest.fixture
def api_client_with_history():
    TAREAS_ESTADO.clear()
    mock_repo = MockHistorialRepository()
    container["historial_repository"] = mock_repo
    container["evaluacion_controller"] = EvaluacionController(
        inference_engine=MockYOLOEngine(desviacion_grados=5.0),
        generation_service=MockGeminiService(),
        tecnica_repository=MockTecnicaRepository()
    )
    yield TestClient(app), mock_repo
    TAREAS_ESTADO.clear()
    container.clear()

def test_worker_guarda_historial_automaticamente(api_client_with_history):
    client, mock_repo = api_client_with_history
    
    payload = {
        "id_tecnica": "armbar_guardia",
        "video_url_o_path": "tests/fixtures/test_video.mp4",
        "id_alumno": "alumno_prueba_01"
    }
    
    response = client.post("/api/v1/evaluaciones/evaluar-asincrono", json=payload)
    assert response.status_code == 200
    tarea_id = response.json()["tarea_id"]
    
    # TestClient de FastAPI ejecuta BackgroundTasks sincrónicamente al completar la petición HTTP
    assert len(mock_repo.registros) == 1
    registro = mock_repo.registros[0]
    assert registro["id_alumno"] == "alumno_prueba_01"
    assert registro["id_tecnica"] == "armbar_guardia"
    assert registro["total_desviaciones"] == 1
    assert "Ajustar" in registro["consejo_pedagogico"] or "desajuste" in registro["consejo_pedagogico"]
    
    # Verificar que el estado de la tarea esté en COMPLETADO
    resp_estado = client.get(f"/api/v1/evaluaciones/tareas/{tarea_id}")
    assert resp_estado.status_code == 200
    assert resp_estado.json()["estado"] == "COMPLETADO"

def test_worker_guarda_con_alumno_por_defecto(api_client_with_history):
    client, mock_repo = api_client_with_history
    
    # Petición sin campo id_alumno explícito
    payload = {
        "id_tecnica": "armbar_guardia",
        "video_url_o_path": "tests/fixtures/test_video.mp4"
    }
    
    response = client.post("/api/v1/evaluaciones/evaluar-asincrono", json=payload)
    assert response.status_code == 200
    
    assert len(mock_repo.registros) == 1
    assert mock_repo.registros[0]["id_alumno"] == "alumno_demo"

def test_flujo_completo_asincrono_y_consulta_progreso(api_client_with_history):
    client, mock_repo = api_client_with_history
    
    alumno_id = "alumno_trayectoria"
    payload = {
        "id_tecnica": "armbar_guardia",
        "video_url_o_path": "tests/fixtures/test_video.mp4",
        "id_alumno": alumno_id
    }
    
    # 1. Enviar evaluación asíncrona
    resp_post = client.post("/api/v1/evaluaciones/evaluar-asincrono", json=payload)
    assert resp_post.status_code == 200
    
    # 2. Consultar historial de progreso del alumno (CU-04)
    resp_hist = client.get(f"/api/v1/alumnos/{alumno_id}/progreso")
    assert resp_hist.status_code == 200
    data_hist = resp_hist.json()
    assert data_hist["id_alumno"] == alumno_id
    assert data_hist["total_evaluaciones"] == 1
    assert len(data_hist["historial"]) == 1
    assert data_hist["historial"][0]["id_tecnica"] == "armbar_guardia"

def test_worker_sin_historial_repository_no_falla():
    TAREAS_ESTADO.clear()
    container.clear()
    container["evaluacion_controller"] = EvaluacionController(
        inference_engine=MockYOLOEngine(desviacion_grados=0.0),
        generation_service=MockGeminiService(),
        tecnica_repository=MockTecnicaRepository()
    )
    # Sin 'historial_repository' en container
    client = TestClient(app)
    
    payload = {
        "id_tecnica": "armbar_guardia",
        "video_url_o_path": "tests/fixtures/test_video.mp4",
        "id_alumno": "alumno_sin_repo"
    }
    
    response = client.post("/api/v1/evaluaciones/evaluar-asincrono", json=payload)
    assert response.status_code == 200
    tarea_id = response.json()["tarea_id"]
    
    resp_estado = client.get(f"/api/v1/evaluaciones/tareas/{tarea_id}")
    assert resp_estado.status_code == 200
    assert resp_estado.json()["estado"] == "COMPLETADO"
