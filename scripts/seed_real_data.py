import random
import uuid
import psycopg2
import requests
import re
from datetime import datetime, timedelta, timezone

def expand_maps_url(url: str):
    """
    Expande enlaces de Google Maps y extrae coordenadas (lat, lng).
    Si falla la conexión de red o no hay URL, devuelve None.
    """
    if not url:
        return None
    try:
        resp = requests.head(url, allow_redirects=True, timeout=5)
        final_url = resp.url
        at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if at_match:
            return float(at_match.group(1)), float(at_match.group(2))
        pin_match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", final_url)
        if pin_match:
            return float(pin_match.group(1)), float(pin_match.group(2))
    except Exception as e:
        print(f"Nota: No se pudo expandir link remoto ({url}): {e}")
    return None

NOMBRES_LATINOS = [
    ("Mateo", "Fernandez"), ("Lucas", "Silva"), ("Thiago", "Oliveira"), ("Gabriel", "Santos"),
    ("Rodrigo", "Souza"), ("Alejandro", "Morales"), ("Carlos", "Rojas"), ("Diego", "Suarez"),
    ("Javier", "Alvarez"), ("Nicolas", "Castro"), ("Sebastian", "Chavez"), ("Bruno", "Pereira"),
    ("Rafael", "Lima"), ("Felipe", "Ferreira"), ("Sofia", "Rodriguez"), ("Camila", "Garcia"),
    ("Valentina", "Martinez"), ("Isabella", "Lopez"), ("Mariana", "Gonzalez"), ("Luciana", "Perez"),
    ("Natalia", "Sanchez"), ("Daniel", "Romero"), ("Leonardo", "Torres"), ("Andre", "Flores"),
    ("Fernando", "Ramos"), ("Gonzalo", "Baigorria"), ("Joaquin", "Mendoza"), ("Ricardo", "Paz"),
    ("Eduardo", "Guzman"), ("Esteban", "Vaca"), ("Gustavo", "Ribera"), ("Marcos", "Justiniano"),
    ("Pablo", "Antelo"), ("Martin", "Saucedo"), ("Victor", "Montero"), ("Adrian", "Serrano"),
    ("Alvaro", "Soliz"), ("Claudio", "Terrazas"), ("Emilio", "Villagomez"), ("Hugo", "Zeballos"),
    ("Ignacio", "Aguilera"), ("Manuel", "Barba"), ("Oscar", "Cuellar"), ("Patricio", "Daza"),
    ("Ramiro", "Eguez"), ("Sergio", "Franco"), ("Tomas", "Hurtado"), ("Vicente", "Landivar"),
    ("Guilherme", "Costa"), ("Vinicius", "Almeida"), ("Pedro", "Ribeiro"), ("Renato", "Carvalho"),
    ("Marcelo", "Gomes"), ("Fabio", "Martins"), ("Caua", "Rocha"), ("Leandro", "Cardoso"),
    ("Guillermo", "Pinto"), ("Julio", "Cabrera"), ("Hector", "Navarro"), ("Mauricio", "Mercado"),
    ("Enrique", "Terceros"), ("Raul", "Banegas"), ("Jaime", "Añez"), ("Felix", "Parada")
]

def seed_database():
    conn = psycopg2.connect(dbname='corpocmente', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()

    print("=" * 70)
    print("FASE 2 & 3: LIMPIEZA Y SEEDING DE DATOS REALES (B2B2C)")
    print("=" * 70)

    # 1. Resolver coordenadas (con fallback a las coordenadas verificadas de Santa Cruz)
    coords_knockout = expand_maps_url("https://maps.app.goo.gl/knockout") or (-17.7680, -63.1699)
    coords_ufc = expand_maps_url("https://maps.app.goo.gl/ufcgym") or (-17.8258, -63.2125)
    coords_matriz = expand_maps_url("https://maps.app.goo.gl/trespasos") or (-17.7985, -63.1462)

    # 2. Insertar o actualizar las 3 nuevas sucursales
    cur.execute("""
        INSERT INTO sucursales (id, nombre, pais, ciudad, direccion, latitud, longitud)
        VALUES 
            ('b1000000-0000-0000-0000-000000000001', 'Knockout', 'Bolivia', 'Santa Cruz de la Sierra', 'Centro Comercial Mía Plaza, 2do Anillo y Av. Alemania', %s, %s),
            ('b2000000-0000-0000-0000-000000000002', 'UFC Gym', 'Bolivia', 'Santa Cruz de la Sierra', 'Ventura Mall Sur, Doble Vía a La Guardia y 5to Anillo', %s, %s),
            ('b3000000-0000-0000-0000-000000000003', '3 Pasos al Frente (Casa Matriz)', 'Bolivia', 'Santa Cruz de la Sierra', 'Calle Romelio Antúnez N° 37, entre 4to y 5to Anillo, Av. 3 Pasos al Frente', %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            nombre = EXCLUDED.nombre,
            pais = EXCLUDED.pais,
            ciudad = EXCLUDED.ciudad,
            direccion = EXCLUDED.direccion,
            latitud = EXCLUDED.latitud,
            longitud = EXCLUDED.longitud;
    """, (coords_knockout[0], coords_knockout[1], coords_ufc[0], coords_ufc[1], coords_matriz[0], coords_matriz[1]))
    print("✅ 3 Sucursales Nuevas Creadas/Actualizadas:")
    print("   1. Knockout ->", coords_knockout)
    print("   2. UFC Gym ->", coords_ufc)
    print("   3. 3 Pasos al Frente (Casa Matriz) ->", coords_matriz)

    # 3. Reasignar cualquier referencia previa de la sucursal vieja a la nueva Casa Matriz
    cur.execute("SELECT id FROM sucursales WHERE nombre ILIKE '%MIGUEL BAIGORRIA%';")
    viejas = cur.fetchall()
    viejas_ids = [v[0] for v in viejas]

    if viejas_ids:
        print(f"\nReasignando referencias de {len(viejas_ids)} sucursal(es) antigua(s)...")
        cur.execute("UPDATE teoria_referencia SET sucursal_id = 'b3000000-0000-0000-0000-000000000003' WHERE sucursal_id = ANY(%s::uuid[]);", (viejas_ids,))
        cur.execute("UPDATE activaciones_pases SET sucursal_id = 'b3000000-0000-0000-0000-000000000003' WHERE sucursal_id = ANY(%s::uuid[]);", (viejas_ids,))
        cur.execute("UPDATE usuarios SET sucursal_id = 'b3000000-0000-0000-0000-000000000003' WHERE sucursal_id = ANY(%s::uuid[]);", (viejas_ids,))
        cur.execute("DELETE FROM sucursales WHERE id = ANY(%s::uuid[]);", (viejas_ids,))
        print("✅ Sucursal antigua 'JIU JITSU CORPO E MENTE MIGUEL BAIGORRIA' eliminada exitosamente.")

    # 4. Limpiar usuarios de prueba anteriores (manteniendo solo admin, mike, santi, milton y prefijos)
    print("\nLimpiando usuarios temporales anteriores...")
    cur.execute("""
        DELETE FROM usuarios 
        WHERE username NOT IN ('admin', 'mike', 'santi', 'milton');
    """)

    # 5. Configurar Instructores
    # Mike Baigorria -> Knockout
    cur.execute("""
        UPDATE usuarios 
        SET sucursal_id = 'b1000000-0000-0000-0000-000000000001',
            rol = 'profesor',
            estado_suscripcion = 'activo',
            fecha_expiracion = NULL
        WHERE username = 'mike';
    """)

    # Milton Flores -> 3 Pasos al Frente (Casa Matriz)
    cur.execute("SELECT id FROM usuarios WHERE username = 'milton';")
    milton_row = cur.fetchone()
    if milton_row:
        cur.execute("""
            UPDATE usuarios
            SET sucursal_id = 'b3000000-0000-0000-0000-000000000003',
                rol = 'profesor',
                estado_suscripcion = 'activo',
                fecha_expiracion = NULL,
                nombre_completo = 'Prof. Milton Flores'
            WHERE username = 'milton';
        """)
    else:
        cur.execute("""
            INSERT INTO usuarios (id, nombre_completo, username, email, password_hash, rol, sucursal_id, idioma_preferido, estado_suscripcion)
            VALUES (
                '7e455a7d-cbc8-4190-9a10-3b959f6425fd',
                'Prof. Milton Flores',
                'milton',
                'milton@corpocmente.com',
                crypt('password123', gen_salt('bf')),
                'profesor',
                'b3000000-0000-0000-0000-000000000003',
                'es',
                'activo'
            );
        """)
    print("✅ Instructores Reasignados:")
    print("   - Coach Mike Baigorria -> Knockout (profesor)")
    print("   - Prof. Milton Flores -> 3 Pasos al Frente (Casa Matriz) (profesor)")

    # Santi (alumno suite tests) -> Knockout
    cur.execute("""
        UPDATE usuarios
        SET sucursal_id = 'b1000000-0000-0000-0000-000000000001',
            rol = 'alumno',
            estado_suscripcion = 'activo',
            fecha_expiracion = CURRENT_TIMESTAMP + INTERVAL '30 days'
        WHERE username = 'santi';
    """)

    # Admin -> 3 Pasos al Frente (Casa Matriz)
    cur.execute("""
        UPDATE usuarios
        SET sucursal_id = 'b3000000-0000-0000-0000-000000000003',
            rol = 'admin',
            estado_suscripcion = 'activo',
            fecha_expiracion = NULL
        WHERE username = 'admin';
    """)

    # 6. Generación de Alumnos Reales
    print("\nGenerando alumnos reales...")
    now = datetime.now(timezone.utc)
    name_idx = 0

    def get_latin_name():
        nonlocal name_idx
        first, last = NOMBRES_LATINOS[name_idx % len(NOMBRES_LATINOS)]
        name_idx += 1
        return f"{first} {last}"

    # --- A. KNOCKOUT: 77 alumnos total (17 activos [1 santi + 16 generados], 60 expirados) ---
    print("   - Insertando alumnos para Knockout (17 activos, 60 expirados = 77 total)...")
    # 16 activos restantes (santi ya es el 1)
    for i in range(1, 17):
        name = get_latin_name()
        u_name = f"knockout_act_{i}"
        exp = now + timedelta(days=random.randint(5, 30))
        cur.execute("""
            INSERT INTO usuarios (id, nombre_completo, username, email, password_hash, rol, sucursal_id, idioma_preferido, estado_suscripcion, fecha_expiracion)
            VALUES (%s, %s, %s, %s, crypt('password123', gen_salt('bf')), 'alumno', 'b1000000-0000-0000-0000-000000000001', 'es', 'activo', %s);
        """, (str(uuid.uuid4()), name, u_name, f"{u_name}@corpocmente.com", exp))

    # 60 expirados
    for i in range(1, 61):
        name = get_latin_name()
        u_name = f"knockout_exp_{i}"
        exp = now - timedelta(days=random.randint(2, 60))
        cur.execute("""
            INSERT INTO usuarios (id, nombre_completo, username, email, password_hash, rol, sucursal_id, idioma_preferido, estado_suscripcion, fecha_expiracion)
            VALUES (%s, %s, %s, %s, crypt('password123', gen_salt('bf')), 'alumno', 'b1000000-0000-0000-0000-000000000001', 'es', 'expirado', %s);
        """, (str(uuid.uuid4()), name, u_name, f"{u_name}@corpocmente.com", exp))

    # --- B. UFC GYM: 11 alumnos activo ---
    print("   - Insertando alumnos para UFC Gym (11 activos)...")
    for i in range(1, 12):
        name = get_latin_name()
        u_name = f"ufc_act_{i}"
        exp = now + timedelta(days=random.randint(5, 30))
        cur.execute("""
            INSERT INTO usuarios (id, nombre_completo, username, email, password_hash, rol, sucursal_id, idioma_preferido, estado_suscripcion, fecha_expiracion)
            VALUES (%s, %s, %s, %s, crypt('password123', gen_salt('bf')), 'alumno', 'b2000000-0000-0000-0000-000000000002', 'es', 'activo', %s);
        """, (str(uuid.uuid4()), name, u_name, f"{u_name}@corpocmente.com", exp))

    # --- C. 3 PASOS AL FRENTE (CASA MATRIZ): 13 activos + 10 pendientes = 23 total ---
    print("   - Insertando alumnos para 3 Pasos al Frente (13 activos, 10 pendientes = 23 total)...")
    # 13 activos
    for i in range(1, 14):
        name = get_latin_name()
        u_name = f"matriz_act_{i}"
        exp = now + timedelta(days=random.randint(5, 30))
        cur.execute("""
            INSERT INTO usuarios (id, nombre_completo, username, email, password_hash, rol, sucursal_id, idioma_preferido, estado_suscripcion, fecha_expiracion)
            VALUES (%s, %s, %s, %s, crypt('password123', gen_salt('bf')), 'alumno', 'b3000000-0000-0000-0000-000000000003', 'es', 'activo', %s);
        """, (str(uuid.uuid4()), name, u_name, f"{u_name}@corpocmente.com", exp))

    # 10 pendientes
    for i in range(1, 11):
        name = get_latin_name()
        u_name = f"matriz_pend_{i}"
        cur.execute("""
            INSERT INTO usuarios (id, nombre_completo, username, email, password_hash, rol, sucursal_id, idioma_preferido, estado_suscripcion, fecha_expiracion)
            VALUES (%s, %s, %s, %s, crypt('password123', gen_salt('bf')), 'alumno', 'b3000000-0000-0000-0000-000000000003', 'es', 'pendiente', NULL);
        """, (str(uuid.uuid4()), name, u_name, f"{u_name}@corpocmente.com"))

    conn.commit()

    # Recargar schema en PostgREST
    cur.execute("NOTIFY pgrst, 'reload schema';")
    conn.commit()

    # 7. Ejecutar query de verificación de evidencia
    print("\n" + "=" * 70)
    print("EVIDENCIA DE BASE DE DATOS (OUTPUT CRUDO SQL):")
    print("=" * 70)

    cur.execute("""
        SELECT s.nombre, u.estado_suscripcion, COUNT(*)
        FROM usuarios u
        JOIN sucursales s ON u.sucursal_id = s.id
        WHERE u.rol = 'alumno'
        GROUP BY s.nombre, u.estado_suscripcion
        ORDER BY s.nombre, u.estado_suscripcion;
    """)
    rows = cur.fetchall()
    print("\n--- CONTEO POR SUCURSAL Y ESTADO DE SUSCRIPCIÓN (ALUMNOS) ---")
    for r in rows:
        print(f"Sucursal: {r[0]:<35} | Estado: {r[1]:<10} | Cantidad: {r[2]}")

    cur.execute("""
        SELECT s.nombre, COUNT(*)
        FROM usuarios u
        JOIN sucursales s ON u.sucursal_id = s.id
        WHERE u.rol = 'alumno'
        GROUP BY s.nombre
        ORDER BY s.nombre;
    """)
    totals = cur.fetchall()
    print("\n--- TOTALES EXACTOS DE ALUMNOS POR SUCURSAL ---")
    for t in totals:
        print(f"Sucursal: {t[0]:<35} | Total Alumnos: {t[1]}")

    cur.execute("SELECT id, nombre, ciudad, pais FROM sucursales ORDER BY nombre;")
    sucursales_actuales = cur.fetchall()
    print("\n--- SUCURSALES ACTIVAS EN SISTEMA ---")
    for s in sucursales_actuales:
        print(f"ID: {s[0]} | Nombre: {s[1]} | {s[2]}, {s[3]}")

    cur.close()
    conn.close()
    print("\n" + "=" * 70)
    print("✅ SEEDING Y LIMPIEZA DE DATOS COMPLETADO CON ÉXITO.")
    print("=" * 70)

if __name__ == "__main__":
    seed_database()
