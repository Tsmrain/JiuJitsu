import json
import psycopg2
import requests

API_URL = "http://localhost:8000/api/v1"

def reset_carlos():
    conn = psycopg2.connect(dbname='corpocmente', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET estado_suscripcion = 'pendiente', fecha_expiracion = NULL WHERE username = 'carlos';")
    conn.commit()
    cur.close()
    conn.close()

def run_test():
    reset_carlos()
    print("=" * 70)
    print("FASE 1: PRUEBA DE FUEGO - FIX DE SEGURIDAD EN ACTUALIZACIÓN DE PERFIL")
    print("=" * 70)

    # 1. Login como alumno pendiente
    print("\n1. Iniciando sesión como alumno 'carlos' (pendiente)...")
    res_login = requests.post(f"{API_URL}/auth/login", json={
        "username_or_email": "carlos",
        "password": "password123"
    })
    print(f"Status: {res_login.status_code}")
    login_data = res_login.json()
    token = login_data["token"]
    user_id = login_data["user_id"]
    print("Login Response:")
    print(json.dumps({
        "user_id": user_id,
        "username": login_data["username"],
        "rol": login_data["rol"],
        "estado_suscripcion": login_data.get("estado_suscripcion"),
        "fecha_expiracion": login_data.get("fecha_expiracion")
    }, indent=2))
    assert login_data.get("estado_suscripcion") == "pendiente", "Error: Se esperaba estado_suscripcion 'pendiente'"

    # 2. PUT /auth/usuarios/{id} cambiando avatar_url y nombre
    print("\n2. Ejecutando PUT /auth/usuarios/{user_id} para actualizar avatar y nombre...")
    res_put = requests.put(
        f"{API_URL}/auth/usuarios/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nombre_completo": "Carlos Alumno Actualizado",
            "avatar_url": "https://example.com/new_avatar.jpg",
            "idioma_preferido": "pt"
        }
    )
    print(f"Status: {res_put.status_code}")
    put_data = res_put.json()
    new_token = put_data.get("token") or token
    print("PUT Response:")
    print(json.dumps({
        "user_id": put_data["user_id"],
        "nombre_completo": put_data["nombre_completo"],
        "avatar_url": put_data.get("avatar_url"),
        "idioma_preferido": put_data.get("idioma_preferido"),
        "estado_suscripcion": put_data.get("estado_suscripcion"),
        "fecha_expiracion": put_data.get("fecha_expiracion")
    }, indent=2))
    assert put_data.get("estado_suscripcion") == "pendiente", "FALLO CRÍTICO: PUT /usuarios alteró estado_suscripcion a activo!"

    # 3. GET /auth/me
    print("\n3. Verificando GET /auth/me con el nuevo token...")
    res_me = requests.get(
        f"{API_URL}/auth/me",
        headers={"Authorization": f"Bearer {new_token}"}
    )
    print(f"Status: {res_me.status_code}")
    me_data = res_me.json()
    print("GET /auth/me Response:")
    print(json.dumps({
        "user_id": me_data["user_id"],
        "username": me_data["username"],
        "nombre_completo": me_data["nombre_completo"],
        "estado_suscripcion": me_data.get("estado_suscripcion"),
        "fecha_expiracion": me_data.get("fecha_expiracion")
    }, indent=2))
    assert me_data.get("estado_suscripcion") == "pendiente", "FALLO CRÍTICO: GET /auth/me reporta estado no pendiente!"

    # 4. Verificación directa en base de datos PostgreSQL
    print("\n4. Verificación directa en PostgreSQL (tabla usuarios)...")
    conn = psycopg2.connect(dbname='corpocmente', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()
    cur.execute("SELECT id, username, nombre_completo, estado_suscripcion, fecha_expiracion FROM usuarios WHERE id = %s;", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    db_res = {
        "id": row[0],
        "username": row[1],
        "nombre_completo": row[2],
        "estado_suscripcion": row[3],
        "fecha_expiracion": str(row[4]) if row[4] else None
    }
    print("PostgreSQL Raw Query:")
    print(json.dumps(db_res, indent=2))
    assert db_res["estado_suscripcion"] == "pendiente", "FALLO CRÍTICO: La BD tiene estado no pendiente!"
    assert db_res["fecha_expiracion"] is None, "FALLO CRÍTICO: La BD tiene fecha_expiracion asignada!"

    print("\n" + "=" * 70)
    print("✅ PRUEBA DE FUEGO FASE 1 SUPERADA EXITOSAMENTE: CERO FALSOS POSITIVOS.")
    print("=" * 70)

if __name__ == "__main__":
    run_test()

