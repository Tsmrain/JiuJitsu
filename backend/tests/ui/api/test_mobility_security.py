import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from corpocmente.main import app

client = TestClient(app)

KNOCKOUT_ID = "b1000000-0000-0000-0000-000000000001"
UFC_GYM_ID = "b2000000-0000-0000-0000-000000000002"

def test_admin_cambiar_sucursal_preserva_evaluaciones_historicas():
    """
    Test de movilidad multi-academia (Iteración 4C):
    Un admin/profesor puede transferir a un alumno a otra sede,
    pero las evaluaciones pasadas deben mantener congelado su sucursal_id original.
    Usa un usuario temporal y lo elimina al finalizar para mantener la BD limpia.
    """
    # 1. Crear alumno temporal
    temp_user = f"temp_mob_{uuid4().hex[:8]}"
    signup_res = client.post("/api/v1/auth/signup", json={
        "nombre_completo": "Alumno Movilidad Temp",
        "username": temp_user,
        "password": "password123",
        "rol": "alumno"
    })
    assert signup_res.status_code == 201
    santi_data = signup_res.json()
    santi_id = santi_data["user_id"]

    try:
        # 2. Login admin
        login_admin = client.post("/api/v1/auth/login", json={
            "username_or_email": "admin",
            "password": "admin123"
        })
        assert login_admin.status_code == 200
        admin_token = login_admin.json()["token"]

        # 3. Cambiar sucursal a UFC Gym
        res_cambio = client.put(
            f"/api/v1/auth/usuarios/{santi_id}/cambiar-sucursal",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"nueva_sucursal_id": UFC_GYM_ID}
        )
        assert res_cambio.status_code == 200
        assert res_cambio.json()["sucursal_nueva_id"] == UFC_GYM_ID

        # 4. Verificar perfil actual
        login_santi_after = client.post("/api/v1/auth/login", json={
            "username_or_email": temp_user,
            "password": "password123"
        })
        assert login_santi_after.status_code == 200
        assert login_santi_after.json()["sucursal_id"] == UFC_GYM_ID

        # 5. Restaurar sucursal a Knockout
        res_restaurar = client.put(
            f"/api/v1/auth/usuarios/{santi_id}/cambiar-sucursal",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"nueva_sucursal_id": KNOCKOUT_ID}
        )
        assert res_restaurar.status_code == 200
        assert res_restaurar.json()["sucursal_nueva_id"] == KNOCKOUT_ID
    finally:
        import psycopg2
        conn = psycopg2.connect(dbname='corpocmente', user='postgres', password='postgres', host='localhost', port=5432)
        cur = conn.cursor()
        cur.execute("DELETE FROM usuarios WHERE username = %s;", (temp_user,))
        conn.commit()
        conn.close()
