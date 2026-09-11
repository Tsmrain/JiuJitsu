# tests/test_iteracion3.py
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from src.presentation.api import app, container, TAREAS_ESTADO
from src.application.controllers import EvaluacionController
from src.application.pattern_controller import RegistrarTecnicaController
from src.infrastructure.rag_ingestion import IngestorRAG
from src.infrastructure.mocks import MockYOLOEngine, MockGeminiService, MockTecnicaRepository

@pytest.fixture
def api_client():
    """Configura el cliente de prueba limpiando el estado de tareas."""
    TAREAS_ESTADO.clear()
    container["evaluacion_controller"] = EvaluacionController(
        inference_engine=MockYOLOEngine(desviacion_grados=5.0),
        generation_service=MockGeminiService(),
        tecnica_repository=MockTecnicaRepository()
    )
    yield TestClient(app)
    TAREAS_ESTADO.clear()
    container.clear()

def test_flujo_asincrono_crea_tarea_y_consulta_estado(api_client):
    payload = {"id_tecnica": "armbar_guardia", "video_url_o_path": "video_test.mp4"}
    
    # 1. Solicitar procesamiento asíncrono
    response_post = api_client.post("/api/v1/evaluaciones/evaluar-asincrono", json=payload)
    assert response_post.status_code == 200
    data_post = response_post.json()
    assert "tarea_id" in data_post
    tarea_id = data_post["tarea_id"]
    
    # 2. Consultar estado de la tarea (TestClient ejecuta background tasks en el ciclo de vida de la petición)
    response_get = api_client.get(f"/api/v1/evaluaciones/tareas/{tarea_id}")
    assert response_get.status_code == 200
    data_get = response_get.json()
    assert data_get["estado"] in ["PENDIENTE", "PROCESANDO", "COMPLETADO"]
    if data_get["estado"] == "COMPLETADO":
        assert data_get["resultado"] is not None
        assert "consejo_pedagogico" in data_get["resultado"]

def test_consulta_tarea_inexistente_retorna_404(api_client):
    response = api_client.get("/api/v1/evaluaciones/tareas/tarea_fantasma_12345")
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"].lower()

class TestRegistrarTecnicaController:
    @patch("psycopg2.connect")
    def test_registrar_patron_exitoso(self, mock_connect):
        # Simular conexión y cursor de PostgreSQL
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn

        controller = RegistrarTecnicaController(
            inference_engine=MockYOLOEngine(desviacion_grados=0.0),
            db_url="postgresql://test:test@localhost:5432/testdb"
        )
        
        resultado = controller.registrar_patron(
            id_tecnica="triangulo_guardia",
            nombre="Triángulo desde Guardia",
            descripcion="Técnica de estrangulación con piernas",
            video_maestro_path="tests/fixtures/test_video.mp4"
        )
        
        assert resultado is True
        assert mock_cursor.execute.called
        # Verificar que se intentó insertar en tecnicas_patron
        args, _ = mock_cursor.execute.call_args
        assert "INSERT INTO tecnicas_patron" in args[0]
        assert "triangulo_guardia" in args[1]

class TestIngestorRAG:
    @patch("psycopg2.connect")
    def test_indexar_documento_fragmentacion_y_guardado(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn

        # Mock adapter para simular generación de embedding
        class MockGeminiEmbed:
            def generate_embedding(self, texto: str):
                return [0.05] * 768

        ingestor = IngestorRAG(
            db_url="postgresql://test:test@localhost:5432/testdb",
            gemini_adapter=MockGeminiEmbed()
        )

        texto_largo = "Jiu Jitsu Brasileño es un arte marcial enfocado en la lucha en el suelo. " * 20
        total_insertados = ingestor.indexar_documento(
            titulo="Manual de Fundamentos BJJ",
            texto_completo=texto_largo,
            tamano_chunk=100
        )

        assert total_insertados > 1
        assert mock_cursor.execute.call_count == total_insertados
        args, _ = mock_cursor.execute.call_args
        assert "INSERT INTO recursos_didacticos" in args[0]
