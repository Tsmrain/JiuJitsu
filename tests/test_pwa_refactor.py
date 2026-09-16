# tests/test_pwa_refactor.py
import pytest
import io
import os
from fastapi.testclient import TestClient
from src.presentation.api import app

@pytest.fixture
def client():
    return TestClient(app)

def test_login_markup_exists():
    """Verifica que index.html contenga la pantalla de login con todos sus campos requeridos."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="pantalla-login"' in html
    assert 'id="form-login"' in html
    assert 'id="login-email"' in html
    assert 'id="login-password"' in html
    assert 'id="login-error"' in html
    assert 'id="btn-cerrar-sesion"' in html
    assert 'cerrarSesion()' in html

def test_student_simplified_navigation_markup():
    """Verifica que la vista del alumno tenga los 3 botones y las 3 secciones requeridas."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Botones
    assert 'mostrarSeccionAlumno(\'evaluar\')' in html
    assert 'mostrarSeccionAlumno(\'progreso\')' in html
    assert 'mostrarSeccionAlumno(\'historial\')' in html
    assert 'Evaluar' in html
    assert 'Mi Progreso' in html
    assert 'Historial' in html

    # Secciones
    assert 'id="seccion-evaluar"' in html
    assert 'id="seccion-progreso"' in html
    assert 'id="seccion-historial"' in html
    assert 'id="contenedor-progreso"' in html
    assert 'id="contenedor-historial"' in html

def test_teacher_simplified_navigation_crud_markup():
    """Verifica que la vista del profesor tenga los 2 botones y los formularios CRUD."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Botones
    assert 'mostrarSeccionProfesor(\'tecnicas\')' in html
    assert 'mostrarSeccionProfesor(\'fuentes\')' in html
    assert 'Enseñar Técnica' in html
    assert 'Fuentes de Información' in html

    # Secciones y formularios
    assert 'id="seccion-tecnicas"' in html
    assert 'id="seccion-fuentes"' in html
    assert 'id="form-tecnica"' in html or 'id="form-tecnica-crud"' in html
    assert 'id="tecnica-id-editar"' in html
    assert 'id="tec-nombre"' in html or 'id="tecnica-nombre"' in html
    assert 'id="lista-tecnicas-profesor"' in html
    assert 'id="form-fuente-crud"' in html
    assert 'id="fuente-id-editar"' in html
    assert 'id="fuente-titulo"' in html
    assert 'id="lista-fuentes-profesor"' in html

def test_app_js_logic_integrity():
    """Verifica que app.js contenga la lógica de login, roles y CRUD."""
    with open("frontend/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    # Credenciales demo (ya no están)
    assert "localStorage.setItem('rol_usuario'" in js
    assert "function cerrarSesion()" in js

    # Alumno
    assert "function mostrarSeccionAlumno(" in js
    assert "async function cargarProgresoAlumno()" in js
    assert "async function cargarHistorialAlumno()" in js

    # Profesor CRUD
    assert "function mostrarSeccionProfesor(" in js
    assert "async function cargarTecnicasProfesor()" in js
    assert "async function editarTecnica(" in js
    assert "async function eliminarTecnica(" in js
    assert "function cancelarEdicionTecnica()" in js
    assert "async function cargarFuentesProfesor()" in js
    assert "async function editarFuente(" in js
    assert "async function eliminarFuente(" in js
    assert "function cancelarEdicionFuente()" in js

def test_backend_put_tecnica(client):
    """Verifica el endpoint PUT /api/v1/instructor/tecnicas/{id_tecnica}."""
    resp = client.put(
        "/api/v1/instructor/tecnicas/armbar_guardia",
        data={
            "nombre": "Armbar Actualizado",
            "descripcion": "Descripción actualizada para la demo",
            "id_profesor": "inst_santiago"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_tecnica"] == "armbar_guardia"
    assert data["nombre"] == "Armbar Actualizado"

def test_backend_put_fuente(client):
    """Verifica el endpoint PUT /api/v1/instructor/fuentes/{id_fuente}."""
    resp = client.put(
        "/api/v1/instructor/fuentes/fuente_demo_1",
        data={
            "titulo": "Manual Biomecánico Actualizado",
            "id_instructor": "inst_santiago"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_fuente"] == "fuente_demo_1"
    assert data["titulo"] == "Manual Biomecánico Actualizado"

def test_backend_delete_fuente(client):
    """Verifica el endpoint DELETE /api/v1/instructor/fuentes/{id_fuente}."""
    resp = client.delete("/api/v1/instructor/fuentes/fuente_demo_1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_fuente"] == "fuente_demo_1"
    assert "eliminada exitosamente" in data["message"]

def test_backend_progreso_keys(client):
    """Verifica que el progreso del alumno retorne tanto evaluaciones como historial."""
    resp = client.get("/api/v1/alumno/alumno_demo/progreso")
    assert resp.status_code == 200
    data = resp.json()
    assert "evaluaciones" in data
    assert "historial" in data
    assert "total_evaluaciones" in data

def test_descripcion_removed_from_ui():
    """Verifica que el campo descripcion haya sido eliminado del ABM de tecnicas."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert 'id="tecnica-descripcion"' not in html
    assert 'for="tecnica-descripcion"' not in html

    with open("frontend/app.js", "r", encoding="utf-8") as f:
        js = f.read()
    assert "tecnica-descripcion" not in js

def test_pdf_without_text_raises_400(client):
    """Verifica que un PDF escaneado o sin texto (< 50 caracteres) retorne 400."""
    pdf_vacio_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    files = {
        "archivo": ("vacio.pdf", io.BytesIO(pdf_vacio_bytes), "application/pdf")
    }
    data = {
        "id_instructor": "inst_santiago",
        "titulo": "Manual Escaneado Vacio"
    }
    resp = client.post("/api/v1/instructor/fuentes", files=files, data=data)
    assert resp.status_code == 400
    assert "El PDF no contiene texto extraíble" in resp.json()["detail"]

def test_qwen_and_gemini_service_adapters_syntax_and_dim():
    """Verifica que Qwen use dimensión 2048 y GeminiServiceAdapter no tenga métodos de embedding."""
    from src.infrastructure.adapters.qwen_embedding_adapter import QwenEmbeddingAdapter
    from src.infrastructure.adapters.gemini_adapter import GeminiServiceAdapter

    adapter1 = QwenEmbeddingAdapter()
    vec1 = adapter1.generar_embedding("Fundamentos de la guardia cerrada en Jiu Jitsu")
    assert len(vec1) == 2048

    adapter2 = GeminiServiceAdapter()
    assert not hasattr(adapter2, "generate_embedding")
    assert not hasattr(adapter2, "generar_embedding")


