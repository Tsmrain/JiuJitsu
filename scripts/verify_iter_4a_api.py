import requests
import json
import psycopg2
from uuid import UUID

BASE_URL = "http://localhost:8000"

def reset_and_test():
    # 1. Resetear a Carlos como alumno con suscripción pendiente
    conn = psycopg2.connect(dbname='corpocmente', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET estado_suscripcion = 'pendiente', fecha_expiracion = NULL WHERE username = 'carlos';")
    conn.commit()
    cur.close()
    conn.close()

    print("\n=======================================================")
    print("FASE 4.1: PRUEBA DE FUEGO API / CANDADO DE SEGURIDAD")
    print("=======================================================")

    # A. Login Carlos (alumno pendiente)
    print("\n>>> PASO 1: Login de Alumno con Pase Pendiente (carlos)...")
    res_login_carlos = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username_or_email": "carlos",
        "password": "password123"
    })
    print(f"HTTP Status: {res_login_carlos.status_code}")
    carlos_data = res_login_carlos.json()
    print("Response JSON:")
    print(json.dumps(carlos_data, indent=2))
    assert res_login_carlos.status_code == 200
    assert carlos_data["estado_suscripcion"] == "pendiente"
    carlos_token = carlos_data["token"]
    carlos_id = carlos_data["user_id"]

    # B. Intentar analizar evaluación (Bloqueo 403 Forbidden)
    print("\n>>> PASO 2: Alumno intenta llamar a /api/v1/evaluaciones/analizar...")
    res_analizar_blocked = requests.post(
        f"{BASE_URL}/api/v1/evaluaciones/analizar",
        headers={"Authorization": f"Bearer {carlos_token}"},
        data={
            "tecnica_id": "d3b07384-d9a4-4f6c-947b-11347076a5b6",
            "tecnica_nombre": "Armbar",
            "alumno_id": carlos_id
        },
        files={"video": ("dummy.mp4", b"\x00\x00\x00\x18ftypmp42", "video/mp4")}
    )
    print(f"HTTP Status (Esperado 403): {res_analizar_blocked.status_code}")
    print("Response JSON:")
    print(json.dumps(res_analizar_blocked.json(), indent=2))
    assert res_analizar_blocked.status_code == 403
    assert "Suscripción inactiva" in res_analizar_blocked.json()["detail"]

    # C. Login Profesor Mike y ver lista de pendientes
    print("\n>>> PASO 3: Login de Profesor (mike)...")
    res_login_mike = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username_or_email": "mike",
        "password": "password123"
    })
    assert res_login_mike.status_code == 200
    mike_data = res_login_mike.json()
    mike_token = mike_data["token"]
    print(f"Profesor autenticado: {mike_data['nombre_completo']} ({mike_data['rol']})")

    print("\n>>> PASO 4: Profesor consulta GET /api/v1/auth/alumnos/pendientes...")
    res_pendientes = requests.get(
        f"{BASE_URL}/api/v1/auth/alumnos/pendientes",
        headers={"Authorization": f"Bearer {mike_token}"}
    )
    print(f"HTTP Status: {res_pendientes.status_code}")
    pendientes = res_pendientes.json()
    print(f"Alumnos pendientes encontrados: {len(pendientes)}")
    for p in pendientes:
        print(f" - [{p['id']}] {p['nombre_completo']} (@{p['username']}) -> {p['estado_suscripcion']}")
    assert any(p["id"] == carlos_id for p in pendientes)

    # D. Profesor activa Pase de Tatami de Carlos
    print(f"\n>>> PASO 5: Profesor activa pase: POST /api/v1/auth/alumnos/{carlos_id}/activar...")
    res_activar = requests.post(
        f"{BASE_URL}/api/v1/auth/alumnos/{carlos_id}/activar",
        headers={"Authorization": f"Bearer {mike_token}"},
        json={"dias": 30}
    )
    print(f"HTTP Status (Esperado 200): {res_activar.status_code}")
    act_data = res_activar.json()
    print("Response JSON:")
    print(json.dumps(act_data, indent=2))
    assert res_activar.status_code == 200
    assert act_data["success"] is True
    assert act_data["estado_suscripcion"] == "activo"

    # E. Alumno vuelve a intentar analizar
    print("\n>>> PASO 6: Carlos reintenta analizar con su pase activo...")
    res_analizar_allowed = requests.post(
        f"{BASE_URL}/api/v1/evaluaciones/analizar",
        headers={"Authorization": f"Bearer {carlos_token}"},
        data={
            "tecnica_id": "d3b07384-d9a4-4f6c-947b-11347076a5b6",
            "tecnica_nombre": "Armbar",
            "alumno_id": carlos_id
        },
        files={"video": ("dummy.mp4", b"dummy video content", "video/mp4")}
    )
    print(f"HTTP Status tras pase activo: {res_analizar_allowed.status_code}")
    print("Response JSON:")
    print(json.dumps(res_analizar_allowed.json(), indent=2))
    # Ya no es 403 Forbidden! Pasó el candado!
    assert res_analizar_allowed.status_code != 403, f"Fallo: retornó 403 a pesar de estar activo"

    print("\n✅ PASO 4.1 COMPLETADO CON ÉXITO: CANDADO DE SEGURIDAD VALIDADO EMPÍRICAMENTE.")

if __name__ == "__main__":
    reset_and_test()

