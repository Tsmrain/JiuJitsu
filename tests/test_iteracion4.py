# tests/test_iteracion4.py
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from src.presentation.api import app, container
from src.application.controllers import EvaluacionController
from src.infrastructure.history_repository import PostgresHistorialRepository
from src.infrastructure.mocks import MockYOLOEngine, MockGeminiService, MockTecnicaRepository

class TestFallbackRAG:
    """Pruebas del mecanismo de Fallback RAG en EvaluacionController según Larman."""

    def test_fallback_activado_cuando_similitud_baja(self):
        """Si score_similitud < 0.65, el contexto se descarta para evitar alucinaciones."""
        mock_gemini = MagicMock(wraps=MockGeminiService())
        controller = EvaluacionController(
            inference_engine=MockYOLOEngine(desviacion_grados=15.0),
            generation_service=mock_gemini,
            tecnica_repository=MockTecnicaRepository()
        )

        resultado = controller.evaluar_ejecucion(
            video_path="video_test.mp4",
            id_tecnica="armbar_guardia",
            contexto_manual="Manual BJJ: Mantener cadera elevada y codo apretado",
            score_similitud=0.40  # Similitud deficiente
        )

        # Verificar que el servicio generativo fue invocado con contexto_manual=None
        mock_gemini.generar_consejo.assert_called_once()
        _, kwargs = mock_gemini.generar_consejo.call_args
        assert kwargs.get("contexto_manual") is None

        # El resultado pedagógico no debe incluir el contexto descartado
        assert "Contexto aplicado:" not in resultado["consejo_pedagogico"]

    def test_contexto_aplicado_cuando_similitud_alta(self):
        """Si score_similitud >= 0.65, el contexto del RAG se incorpora a la IA generativa."""
        mock_gemini = MagicMock(wraps=MockGeminiService())
        controller = EvaluacionController(
            inference_engine=MockYOLOEngine(desviacion_grados=15.0),
            generation_service=mock_gemini,
            tecnica_repository=MockTecnicaRepository()
        )

        contexto_esperado = "Manual BJJ: Mantener cadera elevada y codo apretado"
        resultado = controller.evaluar_ejecucion(
            video_path="video_test.mp4",
            id_tecnica="armbar_guardia",
            contexto_manual=contexto_esperado,
            score_similitud=0.85  # Similitud alta
        )

        # Verificar que el servicio generativo recibió el contexto
        mock_gemini.generar_consejo.assert_called_once()
        _, kwargs = mock_gemini.generar_consejo.call_args
        assert kwargs.get("contexto_manual") == contexto_esperado

        # El resultado pedagógico debe reflejar la aplicación del contexto
        assert f"Contexto aplicado: {contexto_esperado}" in resultado["consejo_pedagogico"]

    def test_evaluacion_sin_contexto_manual(self):
        """Verifica la compatibilidad hacia atrás cuando no se proporciona contexto ni score."""
        mock_gemini = MagicMock(wraps=MockGeminiService())
        controller = EvaluacionController(
            inference_engine=MockYOLOEngine(desviacion_grados=0.0),
            generation_service=mock_gemini,
            tecnica_repository=MockTecnicaRepository()
        )

        resultado = controller.evaluar_ejecucion(
            video_path="video_test.mp4",
            id_tecnica="armbar_guardia"
        )

        assert resultado["es_valido"] is True
        mock_gemini.generar_consejo.assert_called_once()
        _, kwargs = mock_gemini.generar_consejo.call_args
        assert kwargs.get("contexto_manual") is None


class TestPostgresHistorialRepository:
    """Pruebas del repositorio de persistencia histórica con mapeo posicional de tuplas psycopg2."""

    @patch("psycopg2.connect")
    def test_guardar_evaluacion_persiste_registro(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_connect.return_value.__enter__.return_value = mock_conn

        repo = PostgresHistorialRepository("postgresql://test:test@localhost:5432/testdb")
        resultado_evaluacion = {
            "es_valido": False,
            "total_desviaciones": 1,
            "desviaciones": [{"desviacion": 12.0}],
            "consejo_pedagogico": "Ajustar ángulo del codo."
        }

        id_eval = repo.guardar_evaluacion("alumno_001", "armbar_guardia", resultado_evaluacion)

        assert isinstance(id_eval, str) and len(id_eval) > 0
        assert mock_cur.execute.called
        sql_exec, params = mock_cur.execute.call_args[0]
        assert "INSERT INTO evaluaciones_alumno" in sql_exec
        assert params[1] == "alumno_001"
        assert params[2] == "armbar_guardia"
        assert params[3] is False
        assert params[4] == 1
        assert params[5] == 12.0
        assert params[6] == "Ajustar ángulo del codo."
        assert mock_conn.commit.called

    @patch("psycopg2.connect")
    def test_obtener_progreso_mapea_tuplas_psycopg2(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_connect.return_value.__enter__.return_value = mock_conn

        fecha_test = datetime(2026, 9, 10, 18, 30, 0)
        # Tuplas nativas devueltas por el cursor por defecto de psycopg2
        mock_cur.fetchall.return_value = [
            ("eval-uuid-1", "armbar_guardia", False, 1, 14.5, "Corregir codo", fecha_test),
            ("eval-uuid-2", "armbar_guardia", True, 0, 0.0, "Excelente ejecución", fecha_test)
        ]

        repo = PostgresHistorialRepository("postgresql://test:test@localhost:5432/testdb")
        historial = repo.obtener_progreso("alumno_001")

        assert len(historial) == 2
        # Verificación del primer registro
        assert historial[0]["id_evaluacion"] == "eval-uuid-1"
        assert historial[0]["id_tecnica"] == "armbar_guardia"
        assert historial[0]["es_valido"] is False
        assert historial[0]["total_desviaciones"] == 1
        assert historial[0]["desviacion_promedio_grados"] == 14.5
        assert historial[0]["consejo_pedagogico"] == "Corregir codo"
        assert historial[0]["fecha"] == "2026-09-10T18:30:00"

        # Verificación del segundo registro
        assert historial[1]["id_evaluacion"] == "eval-uuid-2"
        assert historial[1]["es_valido"] is True


class TestApiHistorialProgreso:
    """Pruebas del endpoint GET /api/v1/alumnos/{id_alumno}/progreso."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        container.clear()
        yield
        container.clear()

    def test_obtener_progreso_alumno_exitoso(self):
        mock_repo = MagicMock()
        mock_repo.obtener_progreso.return_value = [
            {
                "id_evaluacion": "eval-1",
                "id_tecnica": "armbar_guardia",
                "es_valido": False,
                "total_desviaciones": 1,
                "desviacion_promedio_grados": 10.0,
                "consejo_pedagogico": "Cerrar codo",
                "fecha": "2026-09-10T12:00:00"
            }
        ]
        container["historial_repository"] = mock_repo

        client = TestClient(app)
        response = client.get("/api/v1/alumnos/alumno_test_99/progreso")

        assert response.status_code == 200
        data = response.json()
        assert data["id_alumno"] == "alumno_test_99"
        assert data["total_evaluaciones"] == 1
        assert len(data["historial"]) == 1
        assert data["historial"][0]["id_evaluacion"] == "eval-1"
        mock_repo.obtener_progreso.assert_called_once_with("alumno_test_99")

    def test_obtener_progreso_error_servidor_500(self):
        mock_repo = MagicMock()
        mock_repo.obtener_progreso.side_effect = Exception("Conexión a BD rechazada")
        container["historial_repository"] = mock_repo

        client = TestClient(app)
        response = client.get("/api/v1/alumnos/alumno_error/progreso")

        assert response.status_code == 500
        assert "Error consultando historial" in response.json()["detail"]
