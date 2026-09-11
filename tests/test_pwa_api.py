# tests/test_pwa_api.py
import io
import pytest
from fastapi.testclient import TestClient
from src.presentation.api import app, container, TAREAS_ESTADO
from src.application.controllers import EvaluacionController
from src.infrastructure.mocks import MockYOLOEngine, MockGeminiService, MockTecnicaRepository

class MockHistorialRepository:
    def __init__(self):
        self.registros = []

    def guardar_evaluacion(self, id_alumno: str, id_tecnica: str, resultado: dict) -> str:
        self.registros.append({"id_alumno": id_alumno, "id_tecnica": id_tecnica, "resultado": resultado})
        return "eval-pwa-123"

    def obtener_progreso(self, id_alumno: str):
        return [r for r in self.registros if r["id_alumno"] == id_alumno]

@pytest.fixture
def client_pwa():
    TAREAS_ESTADO.clear()
    mock_repo = MockHistorialRepository()
    container["historial_repository"] = mock_repo
    container["evaluacion_controller"] = EvaluacionController(
        inference_engine=MockYOLOEngine(desviacion_grados=10.0),
        generation_service=MockGeminiService(),
        tecnica_repository=MockTecnicaRepository()
    )
    yield TestClient(app), mock_repo
    TAREAS_ESTADO.clear()
    container.clear()

def test_servir_pwa_html_raiz(client_pwa):
    client, _ = client_pwa
    response = client.get("/")
    assert response.status_code == 200
    assert "BJJ Biomechanics" in response.text
    assert "text/html" in response.headers["content-type"]

def test_servir_assets_estaticos_pwa(client_pwa):
    client, _ = client_pwa
    
    # CSS
    resp_css = client.get("/static/style.css")
    assert resp_css.status_code == 200
    assert "--color-primary" in resp_css.text

    # JS
    resp_js = client.get("/static/app.js")
    assert resp_js.status_code == 200
    assert "selectRole" in resp_js.text

    # Manifest
    resp_manifest = client.get("/static/manifest.json")
    assert resp_manifest.status_code == 200
    assert "BJJ Bio" in resp_manifest.json()["short_name"]

    # Service Worker
    resp_sw = client.get("/static/service-worker.js")
    assert resp_sw.status_code == 200
    assert "bjj-bio-cache" in resp_sw.text

def test_subir_video_multipart_y_evaluar_asincrono(client_pwa):
    client, mock_repo = client_pwa
    
    # Simular archivo de video multipart
    video_dummy_bytes = b"fake-mp4-video-content-for-testing"
    files = {
        "file": ("prueba_alumno.mp4", io.BytesIO(video_dummy_bytes), "video/mp4")
    }
    data = {
        "id_tecnica": "armbar_guardia",
        "id_alumno": "alumno_pwa_01"
    }

    response = client.post("/api/v1/evaluaciones/evaluar-asincrono", files=files, data=data)
    assert response.status_code == 200
    res_json = response.json()
    assert "tarea_id" in res_json
    tarea_id = res_json["tarea_id"]

    # BackgroundTasks se ejecuta sincrónicamente en TestClient
    assert len(mock_repo.registros) == 1
    assert mock_repo.registros[0]["id_alumno"] == "alumno_pwa_01"
    assert mock_repo.registros[0]["id_tecnica"] == "armbar_guardia"

    # Consultar estado de tarea
    resp_estado = client.get(f"/api/v1/evaluaciones/tareas/{tarea_id}")
    assert resp_estado.status_code == 200
    assert resp_estado.json()["estado"] == "COMPLETADO"

def test_servir_pwa_html_contiene_roles_y_pestana_instructor(client_pwa):
    client, _ = client_pwa
    response = client.get("/")
    assert response.status_code == 200
    # Verificaciones de elementos de roles y vista de instructor y alumno con pestañas
    assert 'id="pantalla-rol"' in response.text
    assert "seleccionarRol('alumno')" in response.text or 'seleccionarRol("alumno")' in response.text
    assert "seleccionarRol('instructor')" in response.text or 'seleccionarRol("instructor")' in response.text
    assert 'id="vista-instructor"' in response.text
    assert 'id="vista-alumno"' in response.text
    assert 'id="form-tecnica"' in response.text

def test_listar_tecnicas_endpoint(client_pwa):
    client, _ = client_pwa
    response = client.get("/api/v1/tecnicas")
    assert response.status_code == 200
    tecnicas = response.json()
    assert isinstance(tecnicas, list)
    assert len(tecnicas) >= 1
    assert any(t["id_tecnica"] == "armbar_guardia" for t in tecnicas)

def test_registrar_tecnica_patron_multipart(client_pwa):
    client, _ = client_pwa
    
    class MockPatternController:
        def __init__(self):
            self.patrones_guardados = []
        def registrar_patron(self, id_tecnica, nombre, descripcion, video_path):
            self.patrones_guardados.append({
                "id_tecnica": id_tecnica,
                "nombre": nombre,
                "descripcion": descripcion,
                "video_path": video_path
            })
            return True

    mock_pattern_ctrl = MockPatternController()
    container["pattern_controller"] = mock_pattern_ctrl

    video_bytes = b"fake-master-video-content"
    files = {
        "file": ("video_maestro.mp4", io.BytesIO(video_bytes), "video/mp4")
    }
    data = {
        "id_tecnica": "kimura_norte_sur",
        "nombre": "Kimura desde Norte-Sur",
        "descripcion": "Llave articular de hombro con rotación externa"
    }

    response = client.post("/api/v1/tecnicas/registrar", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert res["message"] == "Técnica patrón registrada"
    assert res["id"] == "kimura_norte_sur"
    assert len(mock_pattern_ctrl.patrones_guardados) == 1
    assert mock_pattern_ctrl.patrones_guardados[0]["nombre"] == "Kimura desde Norte-Sur"

def test_registrar_tecnica_patron_archivo_no_video_retorna_400(client_pwa):
    client, _ = client_pwa
    txt_bytes = b"este es un archivo de texto no permitido"
    files = {
        "file": ("documento.txt", io.BytesIO(txt_bytes), "text/plain")
    }
    data = {
        "id_tecnica": "tecnica_invalida",
        "nombre": "Invalida",
        "descripcion": "Test"
    }

    response = client.post("/api/v1/tecnicas/registrar", files=files, data=data)
    assert response.status_code == 400
    assert "Solo se aceptan archivos de video" in response.text

