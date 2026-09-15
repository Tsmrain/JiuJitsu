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

def test_evaluacion_completa_persiste_jsonb_con_4_claves():
    """Prueba de integración: Simula una evaluación completa y verifica que se guarda en Postgres un JSONB válido con las 4 claves."""
    from unittest.mock import MagicMock, patch
    from psycopg2.extras import Json
    from src.infrastructure.persistence.history_repository import PostgresHistorialRepository
    from src.infrastructure.adapters.gemini_adapter import GeminiServiceAdapter
    from src.domain.models import DesviacionArticular

    # 1. Simular respuesta estructurada de Gemini 2.5 Flash
    adapter = GeminiServiceAdapter(api_key="fake-key")
    mock_genai_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '''{
        "analisis_postural": "Ángulo de codo derecho en 78 grados, por debajo de los 90 requeridos.",
        "riesgo_lesion": "Mayor estrés en la articulación del codo.",
        "paso_a_paso": "1. Ajusta la base.\\n2. Extiende el brazo a 90 grados.",
        "resumen_ejecutivo": "Buen intento. Ajusta el ángulo del codo."
    }'''
    mock_genai_client.models.generate_content.return_value = mock_response
    adapter._client = mock_genai_client

    # 2. Obtener consejo estructurado del adaptador
    desviaciones = [DesviacionArticular("Codo Derecho", 90.0, 78.0, 12.0)]
    consejo_result = adapter.generar_consejo("armbar_guardia", desviaciones)
    assert isinstance(consejo_result, dict)
    for clave in ["analisis_postural", "riesgo_lesion", "paso_a_paso", "resumen_ejecutivo"]:
        assert clave in consejo_result

    # 3. Ejecutar controlador con el adaptador
    controller = EvaluacionController(
        inference_engine=MockYOLOEngine(desviacion_grados=12.0),
        generation_service=adapter,
        tecnica_repository=MockTecnicaRepository()
    )
    resultado_eval = controller.evaluar_ejecucion("tests/fixtures/test_video.mp4", "armbar_guardia")

    assert "consejo_estructurado" in resultado_eval
    assert "Buen intento. Ajusta el ángulo del codo." in resultado_eval["consejo_pedagogico"]

    # 4. Persistir a través de PostgresHistorialRepository y validar inserción en JSONB
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_connect.return_value.__enter__.return_value = mock_conn

        repo = PostgresHistorialRepository("postgresql://test:test@localhost:5432/testdb")
        id_eval = repo.guardar_evaluacion("alumno_test_42", "armbar_guardia", resultado_eval)

        assert id_eval is not None
        assert mock_cur.execute.called
        sql, params = mock_cur.execute.call_args[0]
        assert "INSERT INTO evaluaciones_alumno" in sql
        
        # Validar que el parámetro para consejo_pedagogico es un objeto Json con las 4 claves
        json_param = params[6]
        assert isinstance(json_param, Json)
        adapted_dict = json_param.adapted
        assert isinstance(adapted_dict, dict)
        assert adapted_dict["analisis_postural"] == "Ángulo de codo derecho en 78 grados, por debajo de los 90 requeridos."
        assert adapted_dict["riesgo_lesion"] == "Mayor estrés en la articulación del codo."
        assert adapted_dict["paso_a_paso"] == "1. Ajusta la base.\n2. Extiende el brazo a 90 grados."
        assert adapted_dict["resumen_ejecutivo"] == "Buen intento. Ajusta el ángulo del codo."

