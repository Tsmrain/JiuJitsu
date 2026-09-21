# tests/test_analitica_cu04.py
import pytest
from fastapi.testclient import TestClient
from src.presentation.api import app, container
from src.application.analitica_controller import AnaliticaController
from src.infrastructure.mocks import MockHistorialRepository, InMemoryTecnicaRepository
from src.domain.models import TecnicaPatron, MatrizEsqueletica

@pytest.fixture
def setup_teardown():
    container.clear()
    
    mock_historial = MockHistorialRepository()
    mock_tecnica = InMemoryTecnicaRepository()
    mock_tecnica.registrar_patron(TecnicaPatron(
        id_tecnica="armbar_guardia",
        id_profesor="inst_santiago",
        nombre="Armbar Guardia",
        categoria="Finalización",
        matriz_esqueletica=MatrizEsqueletica(puntos_3d={}),
    ))
    
    ctrl = AnaliticaController(mock_historial, mock_tecnica)
    container["analitica_controller"] = ctrl
    
    yield
    container.clear()

def test_listar_top_tecnicas(setup_teardown):
    client = TestClient(app)
    response = client.get("/api/v1/analitica/tecnicas/top?limite=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "id_tecnica" in data[0]
    assert "total_evaluaciones" in data[0]

def test_obtener_analitica_tecnica_existente(setup_teardown):
    client = TestClient(app)
    response = client.get("/api/v1/analitica/tecnicas/armbar_guardia")
    assert response.status_code == 200
    data = response.json()
    assert data["id_tecnica"] == "armbar_guardia"
    assert "articulaciones_criticas" in data
    assert "tasa_aprobacion" in data
    assert data["total_evaluaciones"] > 0

def test_obtener_analitica_tecnica_inexistente(setup_teardown):
    client = TestClient(app)
    response = client.get("/api/v1/analitica/tecnicas/tecnica_falsa")
    assert response.status_code == 404
