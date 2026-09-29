import os
import psycopg2

def migrar_db():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_dir = os.path.join(base_dir, 'database')
    
    scripts = [
        '01_schema_3nf.sql',
        '02_auth_jwt.sql',
        '03_rls_policies.sql',
        '04_seed_data.sql',
    ]
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="corpocmente",
            user="postgres",
            password="postgres",
            port="5432"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        for script in scripts:
            script_path = os.path.join(db_dir, script)
            print(f"Ejecutando {script}...")
            with open(script_path, 'r', encoding='utf-8') as f:
                sql = f.read()
                cursor.execute(sql)
            print(f"✅ {script} ejecutado con éxito.")
            
        print("✅ Migración completada correctamente.")
        
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cursor.fetchall()
        print(f"Tablas en 'public': {tables}")
        
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='auth';")
        tables = cursor.fetchall()
        print(f"Tablas en 'auth': {tables}")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    migrar_db()
