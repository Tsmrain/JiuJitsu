# demo_e2e.py
"""
Script de Validación End-to-End (E2E) para el Asistente de Visión Artificial BJJ.
Permite verificar la conectividad real con Google Colab (YOLO26x Pose + Depth)
y con la API local FastAPI sin utilizar mocks.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

COLAB_URL = os.getenv("COLAB_TUNNEL_URL")
LOCAL_API = os.getenv("LOCAL_API_URL", "http://localhost:8000")

def test_colab_directo():
    """Prueba directa al backend remoto en Google Colab para verificar YOLO26."""
    if not COLAB_URL or "ngrok" not in COLAB_URL:
        print("⚠️ AVISO: COLAB_TUNNEL_URL no está configurada con una URL activa de Ngrok en .env")
        print(f"   Valor actual: '{COLAB_URL}'")
        print("   👉 Para probar Colab real, inicia colab_backend.ipynb en Colab y copia la URL de Ngrok en .env")
        return
    
    print(f"\n🔍 Probando conexión directa a Colab: {COLAB_URL}/inferir")
    video_fixture = "tests/fixtures/test_video.mp4"
    try:
        if os.path.exists(video_fixture):
            print(f"   Enviando video de prueba: {video_fixture}")
            with open(video_fixture, "rb") as f:
                files = {"file": ("test_video.mp4", f, "video/mp4")}
                resp = requests.post(f"{COLAB_URL}/inferir", files=files, timeout=45)
        else:
            print("   Verificando respuesta del endpoint (sin payload de video)...")
            resp = requests.post(f"{COLAB_URL}/inferir", timeout=10)
            
        print(f"   Respuesta Colab: Código {resp.status_code} - {resp.text[:120]}...")
        if resp.status_code == 200:
            print("   ✅ Conexión con YOLO26x en Colab exitosa.")
        elif resp.status_code == 400:
            print("   ℹ️ El endpoint respondió correctamente validando la estructura del archivo.")
    except Exception as e:
        print(f"   ❌ Falló la conexión directa a Colab: {e}")

def test_api_local_asincrona():
    """Prueba el flujo completo vía FastAPI local (Worker y Persistencia)."""
    print(f"\n🔍 Probando API Local: {LOCAL_API}")
    payload = {
        "id_tecnica": "armbar_guardia",
        "video_url_o_path": "tests/fixtures/test_video.mp4",
        "id_alumno": "demo_user"
    }
    try:
        resp = requests.post(f"{LOCAL_API}/api/v1/evaluaciones/evaluar-asincrono", json=payload, timeout=10)
        if resp.status_code == 200:
            tarea_id = resp.json().get("tarea_id")
            print(f"   ✅ Tarea asíncrona despachada: {tarea_id}")
            
            # Consultar estado de la tarea
            status_resp = requests.get(f"{LOCAL_API}/api/v1/evaluaciones/tareas/{tarea_id}", timeout=10)
            print(f"   Estado de la Tarea: {status_resp.json()}")

            # Consultar progreso del alumno (CU-04)
            prog_resp = requests.get(f"{LOCAL_API}/api/v1/alumnos/demo_user/progreso", timeout=10)
            if prog_resp.status_code == 200:
                print(f"   ✅ Consulta de Progreso Histórico: {prog_resp.json()}")
            else:
                print(f"   ℹ️ Consulta de Progreso: {prog_resp.status_code}")
        else:
            print(f"   ❌ Error en API Local: {resp.status_code} - {resp.text}")
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️ La API local no está corriendo en {LOCAL_API}.")
        print("   💡 Puedes levantarla con:")
        print("      .venv/bin/uvicorn src.presentation.api:app --host 0.0.0.0 --port 8000")
        print("      o vía Docker: docker compose up -d")
    except Exception as e:
        print(f"   ❌ Fallo al conectar con la API Local: {e}")

if __name__ == "__main__":
    print("==================================================")
    print("🥋 ASISTENTE BJJ: VALIDACIÓN REAL END-TO-END")
    print("==================================================")
    test_colab_directo()
    test_api_local_asincrona()
    print("==================================================")
    print("🏁 FIN DE LA VALIDACIÓN")
    print("==================================================")
