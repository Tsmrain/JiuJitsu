import psycopg2

def fix_sucursales():
    conn = psycopg2.connect(dbname='corpocmente', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()

    print("Sincronizando sucursales...")
    # 1. Asignar a Mike (profesor) y Santi (alumno) a la sucursal Knockout
    cur.execute("""
        UPDATE usuarios 
        SET sucursal_id = 'b1000000-0000-0000-0000-000000000001' 
        WHERE username IN ('mike', 'santi');
    """)

    # 2. Limpiar o reasignar usuarios huérfanos a la Casa Matriz
    cur.execute("""
        UPDATE usuarios 
        SET sucursal_id = 'b3000000-0000-0000-0000-000000000003' 
        WHERE sucursal_id IS NULL OR sucursal_id NOT IN (
            'b1000000-0000-0000-0000-000000000001', 
            'b2000000-0000-0000-0000-000000000002', 
            'b3000000-0000-0000-0000-000000000003'
        );
    """)

    conn.commit()

    # 3. Verificar que se hayan guardado
    cur.execute("SELECT username, sucursal_id, rol, estado_suscripcion FROM usuarios WHERE username IN ('mike', 'santi', 'admin', 'milton');")
    for row in cur.fetchall():
        print(f"Usuario: {row[0]} | Rol: {row[2]} | Sucursal ID: {row[1]} | Estado: {row[3]}")

    cur.close()
    conn.close()
    print("✅ Datos sincronizados.")

if __name__ == "__main__":
    fix_sucursales()
