# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from src.presentation.api import app, get_controller
from src.application.controllers import EvaluacionController
from src.infrastructure.mocks import MockYOLOEngine, MockGeminiService, MockTecnicaRepository

@pytest.fixture
def api_client():
    """Sobrescribir la dependencia para usar mocks en las pruebas de integración de la API."""
    def override_get_controller():
        return EvaluacionController(
            inference_engine=MockYOLOEngine(desviacion_grados=12.0),
            generation_service=MockGeminiService(),
            tecnica_repository=MockTecnicaRepository()
        )
    app.dependency_overrides[get_controller] = override_get_controller
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_endpoint_evaluar_retorna_200_y_estructura_valida(api_client):
    payload = {
        "id_tecnica": "armbar_guardia",
        "video_url_o_path": "tests/fixtures/test_video.mp4"
    }
    response = api_client.post("/api/v1/evaluaciones/evaluar", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id_tecnica"] == "armbar_guardia"
    assert data["es_valido"] is False
    assert data["total_desviaciones"] == 1
    assert "consejo_pedagogico" in data
    assert "desviacion" in data["desviaciones"][0]

def test_endpoint_evaluar_tecnica_no_encontrada_retorna_404(api_client):
    class MockRepoVacio(MockTecnicaRepository):
        def obtener_patron(self, id_tecnica: str):
            return None

    app.dependency_overrides[get_controller] = lambda: EvaluacionController(
        inference_engine=MockYOLOEngine(),
        generation_service=MockGeminiService(),
        tecnica_repository=MockRepoVacio()
    )
    
    payload = {
        "id_tecnica": "tecnica_inexistente",
        "video_url_o_path": "tests/fixtures/test_video.mp4"
    }
    response = api_client.post("/api/v1/evaluaciones/evaluar", json=payload)
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"]
