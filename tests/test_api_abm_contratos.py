# tests/test_api_abm_contratos.py
"""Pruebas de contratos de API Backend para operaciones ABM y segmentación de roles (Larman UP).

Valida estrictamente a nivel de servidor (HTTP / JSON / Códigos de estado):
1. Operación PUT /api/v1/profesores/{id} y /api/v1/instructor/profesores/{id} (200, 400, 404, 422).
2. Segmentación lógica de rutas de Instructor (/api/v1/instructor/*).
3. Segmentación lógica de rutas de Alumno (/api/v1/alumno/*).
4. Contrato de reglas de validación (/api/v1/validation-rules).
5. Contrato de streaming de video patrón (/api/v1/tecnicas/{id}/stream).

NOTA METODOLÓGICA: Este archivo NO realiza scraping de DOM, simulación de navegador ni
pruebas de frontend. La validación es 100% lógica de servidor mediante pytest y TestClient.
"""

import io
import os
import uuid
import pytest
from fastapi.testclient import TestClient

from src.presentation.api import app, container
from src.application.controllers import EvaluacionController
from src.infrastructure.mocks import (
    MockYOLOEngine,
    MockGeminiService,
    MockTecnicaRepository,
    InMemoryProfesorRepository,
    InMemoryTecnicaRepository,
)
from src.application.profesor_controller import ProfesorController
from src.application.tecnica_controller import TecnicaController


@pytest.fixture
def client():
    mock_tec_repo = InMemoryTecnicaRepository()
    mock_prof_repo = InMemoryProfesorRepository(tecnica_repository=mock_tec_repo)
    container["evaluacion_controller"] = EvaluacionController(
        inference_engine=MockYOLOEngine(desviacion_grados=10.0),
        generation_service=MockGeminiService(),
        tecnica_repository=mock_tec_repo,
    )
    prof_ctrl = ProfesorController(
        repository=mock_prof_repo,
        tecnica_repository=mock_tec_repo,
    )
    container["profesor_controller"] = prof_ctrl
    container["tecnica_controller"] = TecnicaController(
        repository=mock_tec_repo,
        profesor_repository=mock_prof_repo,
    )

    yield TestClient(app)
    container.clear()


# ==============================================================================
# 1. PRUEBAS DE OPERACIÓN "ACTUALIZAR" (PUT - CRUD COMPLETO PROFESORES)
# ==============================================================================

def test_actualizar_profesor_exitoso(client):
    """PUT /api/v1/profesores/{id} actualiza nombre y email con HTTP 200 y JSON correcto."""
    uid = uuid.uuid4().hex[:6]
    id_prof = f"prof_{uid}"

    # 1. Crear profesor
    post_res = client.post(
        "/api/v1/instructor/profesores",
        json={
            "id_profesor": id_prof,
            "nombre": "Prof. Carlson Gracie",
            "email": f"carlson_{uid}@bjjbiomechanics.com"
        }
    )
    assert post_res.status_code == 200

    # 2. Actualizar datos (vía ruta de instructor o alias)
    nuevo_nombre = "Mestre Carlson Gracie Senior"
    nuevo_email = f"carlson_master_{uid}@bjjbiomechanics.com"
    put_res = client.put(
        f"/api/v1/instructor/profesores/{id_prof}",
        json={
            "nombre": nuevo_nombre,
            "email": nuevo_email
        }
    )
    assert put_res.status_code == 200
    datos = put_res.json()
    assert datos["id_profesor"] == id_prof
    assert datos["nombre"] == nuevo_nombre
    assert datos["email"] == nuevo_email
    assert "exitosamente" in datos["message"].lower()

    # 3. Comprobar que GET refleja los cambios
    get_res = client.get("/api/v1/instructor/profesores")
    assert get_res.status_code == 200
    profesores = get_res.json()
    prof_actualizado = next((p for p in profesores if p["id_profesor"] == id_prof), None)
    assert prof_actualizado is not None
    assert prof_actualizado["nombre"] == nuevo_nombre
    assert prof_actualizado["email"] == nuevo_email


def test_actualizar_profesor_no_existente_retorna_404(client):
    """PUT a un ID inexistente retorna 404 Not Found."""
    resp = client.put(
        "/api/v1/profesores/prof_fantasma_inexistente",
        json={
            "nombre": "Fantasma Gracie",
            "email": "fantasma@bjjbiomechanics.com"
        }
    )
    assert resp.status_code == 404
    assert "no encontrado" in resp.json()["detail"].lower()


def test_actualizar_profesor_email_duplicado_retorna_400(client):
    """PUT intentando asignar el email de otro profesor existente retorna 400 Bad Request."""
    uid1 = uuid.uuid4().hex[:6]
    uid2 = uuid.uuid4().hex[:6]

    email1 = f"prof1_{uid1}@bjjbiomechanics.com"
    email2 = f"prof2_{uid2}@bjjbiomechanics.com"

    # Registrar 2 profesores
    client.post("/api/v1/profesores", json={"id_profesor": f"p1_{uid1}", "nombre": "Prof Uno", "email": email1})
    client.post("/api/v1/profesores", json={"id_profesor": f"p2_{uid2}", "nombre": "Prof Dos", "email": email2})

    # Intentar actualizar el profesor 2 asignándole el email del profesor 1
    resp = client.put(
        f"/api/v1/profesores/p2_{uid2}",
        json={
            "nombre": "Prof Dos Renombrado",
            "email": email1
        }
    )
    assert resp.status_code == 400
    assert "ya se encuentra registrado" in resp.json()["detail"].lower()


def test_actualizar_profesor_email_invalido_retorna_400(client):
    """PUT con email que no cumple el regex de dominio retorna 400 Bad Request."""
    uid = uuid.uuid4().hex[:6]
    id_prof = f"p_{uid}"
    client.post("/api/v1/profesores", json={"id_profesor": id_prof, "nombre": "Prof Test", "email": f"test_{uid}@bjj.com"})

    resp = client.put(
        f"/api/v1/profesores/{id_prof}",
        json={
            "nombre": "Prof Test",
            "email": "correo-invalido-sin-arroba"
        }
    )
    assert resp.status_code == 400
    assert "inválido" in resp.json()["detail"].lower()


def test_actualizar_profesor_campos_incompletos_retorna_422(client):
    """PUT con payload Pydantic incompleto retorna 422 Unprocessable Entity."""
    resp = client.put(
        "/api/v1/profesores/prof_123",
        json={"nombre": "Solo Nombre"}
    )
    assert resp.status_code == 422


# ==============================================================================
# 2. PRUEBAS DE RUTAS SEGMENTADAS: ACTOR INSTRUCTOR
# ==============================================================================

def test_rutas_instructor_profesores(client):
    """Verifica contratos HTTP para gestión de profesores por parte del Instructor."""
    uid = uuid.uuid4().hex[:6]

    # GET /api/v1/instructor/profesores
    res_get = client.get("/api/v1/instructor/profesores")
    assert res_get.status_code == 200
    assert isinstance(res_get.json(), list)

    # POST /api/v1/instructor/profesores
    res_post = client.post(
        "/api/v1/instructor/profesores",
        json={
            "id_profesor": f"prof_inst_{uid}",
            "nombre": "Instructor Marcelo Garcia",
            "email": f"marcelo_{uid}@bjjbiomechanics.com"
        }
    )
    assert res_post.status_code == 200
    assert res_post.json()["id_profesor"] == f"prof_inst_{uid}"

    # DELETE /api/v1/instructor/profesores/{id}
    res_del = client.delete(f"/api/v1/instructor/profesores/prof_inst_{uid}")
    assert res_del.status_code == 200
    assert "eliminado" in res_del.json()["message"].lower()


def test_rutas_instructor_tecnicas(client):
    """Verifica contratos HTTP para gestión de técnicas patrón por parte del Instructor."""
    # GET /api/v1/instructor/tecnicas
    res_get = client.get("/api/v1/instructor/tecnicas")
    assert res_get.status_code == 200
    assert isinstance(res_get.json(), list)

    # POST /api/v1/instructor/tecnicas sin video retorna 422 o 400
    res_post_invalido = client.post(
        "/api/v1/instructor/tecnicas",
        data={"nombre": "Triángulo", "id_profesor": "prof_demo"}
    )
    assert res_post_invalido.status_code in (400, 422)


def test_rutas_instructor_fuentes_requiere_pdf(client):
    """POST /api/v1/instructor/fuentes rechaza archivos que no sean PDF con 400 Bad Request."""
    archivo_falso = io.BytesIO(b"texto plano no pdf")
    res = client.post(
        "/api/v1/instructor/fuentes",
        data={"id_instructor": "prof_demo", "titulo": "Manual Invalido"},
        files={"archivo": ("archivo.txt", archivo_falso, "text/plain")}
    )
    assert res.status_code == 400
    assert "pdf" in res.json()["detail"].lower()


# ==============================================================================
# 3. PRUEBAS DE RUTAS SEGMENTADAS: ACTOR ALUMNO
# ==============================================================================

def test_rutas_alumno_progreso(client):
    """GET /api/v1/alumno/progreso y /api/v1/alumno/{id}/progreso retornan estructura de progreso."""
    res_default = client.get("/api/v1/alumno/progreso")
    assert res_default.status_code == 200
    data = res_default.json()
    assert "id_alumno" in data
    assert "historial" in data

    res_especifico = client.get("/api/v1/alumno/alumno_123/progreso")
    assert res_especifico.status_code == 200
    assert res_especifico.json()["id_alumno"] == "alumno_123"


def test_rutas_alumno_recursos(client):
    """GET /api/v1/alumno/recursos retorna lista de técnicas y recursos disponibles."""
    res = client.get("/api/v1/alumno/recursos")
    assert res.status_code == 200
    data = res.json()
    assert "recursos" in data
    assert "total_recursos" in data
    assert isinstance(data["recursos"], list)


def test_rutas_alumno_evaluaciones_valida_entrada(client):
    """POST /api/v1/alumno/evaluaciones exige archivo de video o payload válido."""
    res_vacio = client.post("/api/v1/alumno/evaluaciones", data={})
    assert res_vacio.status_code in (400, 422)


# ==============================================================================
# 4. PRUEBAS DE CONTRATO DE VALIDACIÓN Y STREAMING
# ==============================================================================

def test_contrato_validation_rules(client):
    """GET /api/v1/validation-rules retorna constantes canónicas del dominio."""
    res = client.get("/api/v1/validation-rules")
    assert res.status_code == 200
    data = res.json()
    assert "email_regex" in data
    assert "categorias_validas" in data
    assert "max_video_mb" in data
    assert data["max_video_mb"] == 50
    assert "Guardia" in data["categorias_validas"]


def test_contrato_streaming_video(client):
    """GET /api/v1/tecnicas/{id}/stream sirve video o fallback con cabeceras de streaming."""
    res = client.get("/api/v1/tecnicas/armbar_guardia/stream")
    # Puede ser 200 OK con chunked transfer si existe el video
    if res.status_code == 200:
        assert res.headers.get("content-type") == "video/mp4"
        assert res.headers.get("accept-ranges") == "bytes"
    else:
        # Si no hay video en disco en entorno CI, retorna 404 limpio
        assert res.status_code == 404
