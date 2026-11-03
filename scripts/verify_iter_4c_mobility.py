import json
import psycopg2
import requests

API_URL = "http://localhost:8000/api/v1"

KNOCKOUT_ID = "b1000000-0000-0000-0000-000000000001"
UFC_GYM_ID = "b2000000-0000-0000-0000-000000000002"

def run_test():
    print("=" * 75)
    print("FASE 2: PRUEBA DE MOVILIDAD MULTI-ACADEMIA E INTEGRIDAD HISTÓRICA")
    print("=" * 75)

    # 1. Login como admin
    print("\n1. Autenticando como Admin...")
    res_admin = requests.post(f"{API_URL}/auth/login", json={
        "username_or_email": "admin",
        "password": "admin123"
    })
    assert res_admin.status_code == 200, f"Error en login admin: {res_admin.text}"
    admin_token = res_admin.json()["token"]
    print("✅ Admin autenticado exitosamente.")

    # 2. Obtener datos de alumno 'santi'
    conn = psycopg2.connect(dbname='corpocmente', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()
    cur.execute("SELECT id, username, sucursal_id, estado_suscripcion FROM usuarios WHERE username = 'santi';")
    santi_user = cur.fetchone()
    santi_id = santi_user[0]
    print(f"\n2. Alumno Santi ID: {santi_id}")
    print(f"   Sucursal Inicial: {santi_user[2]}")

    # 3. Consultar evaluaciones históricas de Santi en la base de datos
    cur.execute("""
        SELECT e.id, e.sucursal_id, s.nombre, e.fecha_evaluacion
        FROM evaluaciones_alumnos e
        JOIN sucursales s ON s.id = e.sucursal_id
        WHERE e.alumno_id = %s
        LIMIT 3;
    """, (santi_id,))
    evals_before = cur.fetchall()
    print(f"\n3. Evaluaciones históricas congeladas antes del traslado:")
    for ev in evals_before:
        print(f"   Eval ID: {ev[0]} | Sucursal Congelada: {ev[1]} ({ev[2]}) | Fecha: {ev[3]}")
        assert str(ev[1]) == KNOCKOUT_ID, f"Error: Sucursal esperada {KNOCKOUT_ID}, encontrada {ev[1]}"

    # 4. Trasladar alumno de Knockout a UFC Gym
    print(f"\n4. Ejecutando PUT /auth/usuarios/{santi_id}/cambiar-sucursal a UFC Gym ({UFC_GYM_ID})...")
    res_cambio = requests.put(
        f"{API_URL}/auth/usuarios/{santi_id}/cambiar-sucursal",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"nueva_sucursal_id": UFC_GYM_ID}
    )
    print(f"Status Code: {res_cambio.status_code}")
    print("Respuesta API:", json.dumps(res_cambio.json(), indent=2))
    assert res_cambio.status_code == 200, f"Error en cambio de sucursal: {res_cambio.text}"
    assert res_cambio.json()["sucursal_nueva_id"] == UFC_GYM_ID

    # 5. Verificar que el perfil actual del alumno ahora es UFC Gym
    cur.execute("SELECT u.id, u.username, u.sucursal_id, s.nombre FROM usuarios u JOIN sucursales s ON s.id = u.sucursal_id WHERE u.id = %s;", (santi_id,))
    perfil_actual = cur.fetchone()
    print(f"\n5. Perfil actual del alumno tras el traslado:")
    print(f"   Alumno: {perfil_actual[1]} | Sucursal Actual: {perfil_actual[2]} ({perfil_actual[3]})")
    assert str(perfil_actual[2]) == UFC_GYM_ID

    # 6. VERIFICACIÓN CRÍTICA: Las evaluaciones históricas DEBEN SEGUIR CONGELADAS en Knockout
    cur.execute("""
        SELECT e.id, e.sucursal_id, s.nombre, e.fecha_evaluacion
        FROM evaluaciones_alumnos e
        JOIN sucursales s ON s.id = e.sucursal_id
        WHERE e.alumno_id = %s
        LIMIT 3;
    """, (santi_id,))
    evals_after = cur.fetchall()
    print(f"\n6. Evaluaciones históricas verificadas tras el traslado:")
    for ev in evals_after:
        print(f"   Eval ID: {ev[0]} | Sucursal Congelada: {ev[1]} ({ev[2]})")
        assert str(ev[1]) == KNOCKOUT_ID, f"VIOLACIÓN DE INTEGRIDAD: La evaluación {ev[0]} cambió a {ev[1]} en vez de permanecer en {KNOCKOUT_ID}!"

    # 7. Verificar RPC admin_list_evaluaciones_alumno
    cur.execute("SELECT id, sucursal_id, sucursal_nombre FROM admin_list_evaluaciones_alumno(%s) LIMIT 2;", (santi_id,))
    rpc_rows = cur.fetchall()
    print(f"\n7. Verificando salida del Stored Procedure admin_list_evaluaciones_alumno:")
    for rpc_row in rpc_rows:
        print(f"   Eval: {rpc_row[0]} | sucursal_id: {rpc_row[1]} | sucursal_nombre: {rpc_row[2]}")
        assert str(rpc_row[1]) == KNOCKOUT_ID
        assert "Knock Out" in rpc_row[2]

    # 8. Restaurar alumno a Knockout
    print("\n8. Restaurando sucursal original para mantener base de datos limpia...")
    requests.put(
        f"{API_URL}/auth/usuarios/{santi_id}/cambiar-sucursal",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"nueva_sucursal_id": KNOCKOUT_ID}
    )
    cur.execute("SELECT sucursal_id FROM usuarios WHERE id = %s;", (santi_id,))
    restaurado = cur.fetchone()[0]
    assert str(restaurado) == KNOCKOUT_ID
    print(f"✅ Alumno restaurado a {KNOCKOUT_ID}.")

    cur.close()
    conn.close()

    print("\n" + "=" * 75)
    print("✅ PRUEBA DE MOVILIDAD MULTI-ACADEMIA COMPLETADA EXITOSAMENTE (0 REGRESIONES)")
    print("=" * 75)

if __name__ == "__main__":
    run_test()
