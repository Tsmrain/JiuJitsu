import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from corpocmente.main import app

client = TestClient(app)

def test_actualizar_perfil_no_altera_estado_suscripcion_pendiente():
    """
    Test de regresión de seguridad (Iteración 4B):
    Al actualizar avatar, nombre o idioma, un alumno en estado 'pendiente'
    NUNCA debe ser activado a 'activo'.
    Usa un usuario temporal y lo elimina al finalizar para mantener la BD limpia.
    """
    temp_user = f"temp_pend_{uuid4().hex[:8]}"
    signup_res = client.post("/api/v1/auth/signup", json={
        "nombre_completo": "Alumno Pendiente Temp",
        "username": temp_user,
        "password": "password123",
        "rol": "alumno"
    })
    assert signup_res.status_code == 201
    user_data = signup_res.json()
    assert user_data["estado_suscripcion"] == "pendiente"
    user_id = user_data["user_id"]
    token = user_data["token"]

    try:
        # Ejecutar PUT /auth/usuarios/{user_id}
        put_res = client.put(
            f"/api/v1/auth/usuarios/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nombre_completo": "Nombre Actualizado Test",
                "avatar_url": "https://example.com/avatar.png",
                "idioma_preferido": "es"
            }
        )
        assert put_res.status_code == 200
        updated_data = put_res.json()

        # Invariante de seguridad: El estado debe permanecer 'pendiente'
        assert updated_data["estado_suscripcion"] == "pendiente"
        assert updated_data["fecha_expiracion"] is None

        # Verificar que GET /auth/me también reporta 'pendiente'
        me_res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {updated_data['token']}"}
        )
        assert me_res.status_code == 200
        assert me_res.json()["estado_suscripcion"] == "pendiente"
    finally:
        import psycopg2
        conn = psycopg2.connect(dbname='corpocmente', user='postgres', password='postgres', host='localhost', port=5432)
        cur = conn.cursor()
        cur.execute("DELETE FROM usuarios WHERE username = %s;", (temp_user,))
        conn.commit()
        conn.close()
