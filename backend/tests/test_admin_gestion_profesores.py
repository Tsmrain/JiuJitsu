from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from corpocmente.main import app
from corpocmente.ui.api.auth_routes import _sign_token


client = TestClient(app)


def _auth_header(role: str, uid: str | None = None) -> dict:
    token = _sign_token({
        "uid": uid or str(uuid4()),
        "role": role,
        "email": f"{role}@test.com",
        "sucursal_id": "8b315b4e-43f2-4ca1-904d-dec87242f347",
    })
    return {"Authorization": f"Bearer {token}"}


def test_crear_profesor_requiere_admin():
    sucursal_id = str(uuid4())
    payload = {
        "nombre_completo": "Prof Prueba",
        "username": "prof_prueba",
        "password": "password123",
        "email": "prof_prueba@corpocmente.com",
        "sucursal_id": sucursal_id,
    }
    res_unauth = client.post("/api/v1/auth/profesores", json=payload)
    assert res_unauth.status_code == 401

    res_alumno = client.post("/api/v1/auth/profesores", json=payload, headers=_auth_header("alumno"))
    assert res_alumno.status_code == 403

    res_prof = client.post("/api/v1/auth/profesores", json=payload, headers=_auth_header("profesor"))
    assert res_prof.status_code == 403


def test_crear_profesor_exito_y_duplicado():
    sucursal_id = str(uuid4())
    prof_id = str(uuid4())
    mock_db = MagicMock()
    mock_db.get.return_value = [{"id": sucursal_id, "nombre": "Sede Central"}]
    mock_db.rpc.return_value = [{
        "id": prof_id,
        "nombre_completo": "Carlos Gracie",
        "username": "carlos_bjj",
        "email": "carlos@corpocmente.com",
        "rol": "profesor",
        "avatar_url": None,
        "sucursal_id": sucursal_id,
        "sucursal_nombre": "Sede Central",
        "idioma_preferido": "pt",
        "estado_suscripcion": "activo",
        "fecha_expiracion": None,
    }]

    with patch("corpocmente.ui.api.auth_routes.get_db", return_value=mock_db):
        res = client.post(
            "/api/v1/auth/profesores",
            json={
                "nombre_completo": "Carlos Gracie",
                "username": "carlos_bjj",
                "password": "password123",
                "email": "carlos@corpocmente.com",
                "sucursal_id": sucursal_id,
                "idioma_preferido": "pt",
            },
            headers=_auth_header("admin"),
        )

    assert res.status_code == 201
    data = res.json()
    assert data["rol"] == "profesor"
    assert data["estado_suscripcion"] == "activo"
    assert data["idioma_preferido"] == "pt"
    mock_db.rpc.assert_called_once()

    # Caso duplicado (23505)
    mock_db.rpc.side_effect = Exception("23505 duplicate key value violates unique constraint")
    with patch("corpocmente.ui.api.auth_routes.get_db", return_value=mock_db):
        res_dup = client.post(
            "/api/v1/auth/profesores",
            json={
                "nombre_completo": "Carlos Gracie",
                "username": "carlos_bjj",
                "password": "password123",
                "sucursal_id": sucursal_id,
            },
            headers=_auth_header("admin"),
        )
    assert res_dup.status_code == 400


def test_crear_profesor_validaciones_negocio():
    sucursal_id = str(uuid4())
    mock_db = MagicMock()
    mock_db.get.return_value = []  # Sucursal inexistente

    with patch("corpocmente.ui.api.auth_routes.get_db", return_value=mock_db):
        res_missing_branch = client.post(
            "/api/v1/auth/profesores",
            json={
                "nombre_completo": "Sin Sede",
                "username": "sin_sede",
                "password": "password123",
                "sucursal_id": sucursal_id,
            },
            headers=_auth_header("admin"),
        )
    assert res_missing_branch.status_code == 404

    res_short_pw = client.post(
        "/api/v1/auth/profesores",
        json={
            "nombre_completo": "Clave Corta",
            "username": "clave_corta",
            "password": "123",
            "sucursal_id": sucursal_id,
        },
        headers=_auth_header("admin"),
    )
    assert res_short_pw.status_code == 400


def test_modificar_profesor_admin():
    admin_id = str(uuid4())
    prof_id = str(uuid4())
    sucursal_id = str(uuid4())
    mock_db = MagicMock()
    mock_db.get.return_value = [{"id": sucursal_id, "nombre": "Sede Norte"}]
    mock_db.rpc.return_value = [{
        "id": prof_id,
        "nombre_completo": "Carlos Gracie Actualizado",
        "username": "carlos_bjj",
        "email": "carlos.nuevo@corpocmente.com",
        "rol": "profesor",
        "avatar_url": None,
        "sucursal_id": sucursal_id,
        "sucursal_nombre": "Sede Norte",
        "idioma_preferido": "en",
        "estado_suscripcion": "activo",
        "fecha_expiracion": None,
    }]

    with patch("corpocmente.ui.api.auth_routes.get_db", return_value=mock_db):
        res = client.put(
            f"/api/v1/auth/profesores/{prof_id}",
            json={
                "nombre_completo": "Carlos Gracie Actualizado",
                "email": "carlos.nuevo@corpocmente.com",
                "sucursal_id": sucursal_id,
                "idioma_preferido": "en",
            },
            headers=_auth_header("admin", uid=admin_id),
        )

    assert res.status_code == 200
    body = res.json()
    assert body["nombre_completo"] == "Carlos Gracie Actualizado"
    assert body["sucursal_nombre"] == "Sede Norte"
    assert body["idioma_preferido"] == "en"

    # Admin no puede cambiar su propio rol
    res_self = client.put(
        f"/api/v1/auth/profesores/{admin_id}",
        json={"rol": "profesor"},
        headers=_auth_header("admin", uid=admin_id),
    )
    assert res_self.status_code == 400
