import pytest
from src.application.analitica_controller import AnaliticaController

class MockHistorialRepository:
    def __init__(self):
        self.datos = [
            {
                "id_evaluacion": "1",
                "id_tecnica": "armbar",
                "es_valido": True,
                "consejo_estructurado": {
                    "desviaciones": [
                        {"articulacion": "Codo Derecho", "desviacion": 15.0},
                        {"articulacion": "Cadera", "desviacion": 5.0}
                    ]
                }
            },
            {
                "id_evaluacion": "2",
                "id_tecnica": "armbar",
                "es_valido": False,
                "consejo_estructurado": {
                    "desviaciones": [
                        {"articulacion": "Codo Derecho", "desviacion": 25.0},
                        {"articulacion": "Hombro Izquierdo", "desviacion": 10.0}
                    ]
                }
            },
            {
                "id_evaluacion": "3",
                "id_tecnica": "otra",
                "es_valido": True,
                "consejo_estructurado": None # Simulando compatibilidad retroactiva
            }
        ]

    def listar_todas(self, id_tecnica=None):
        if id_tecnica:
            return [d for d in self.datos if d["id_tecnica"] == id_tecnica]
        return self.datos

def test_analitica_controller_calcula_metricas_correctas():
    repo = MockHistorialRepository()
    controller = AnaliticaController(historial_repository=repo)
    
    res = controller.obtener_debilidades_grupales("armbar")
    
    assert res["total_evaluaciones"] == 2
    assert res["tasa_aprobacion"] == 50.0
    assert len(res["debilidades_grupales"]) == 3
    # Codo Derecho aparece 2 veces
    codo = next(d for d in res["debilidades_grupales"] if d["articulacion"] == "Codo Derecho")
    assert codo["frecuencia"] == 2
    assert codo["promedio_desviacion"] == 20.0 # (15+25)/2

from fastapi.testclient import TestClient
from src.presentation.api import app, container

client = TestClient(app)

def get_mock_repo():
    return MockHistorialRepository()

def test_endpoint_analitica():
    # Setup the mock repository inside the DI container
    container["historial_repository"] = get_mock_repo()
    
    response = client.get("/api/v1/instructor/analitica?id_tecnica=armbar")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_evaluaciones"] == 2
    assert "debilidades_grupales" in data

