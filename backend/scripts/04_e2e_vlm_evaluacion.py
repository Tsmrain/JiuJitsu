import time
import json
import requests
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"
VIDEO_PATH = Path("/Users/santiago/Desktop/JiuJitsu-main/Alumno.mp4")

if not VIDEO_PATH.exists():
    raise FileNotFoundError(f"Video {VIDEO_PATH} does not exist")

print("1. Iniciar sesión como alumno santi...")
login_resp = requests.post(f"{API_BASE}/auth/login", json={
    "username_or_email": "santi",
    "password": "password123"
}, timeout=10)
assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
user_data = login_resp.json()
token = user_data["token"]
alumno_id = user_data["user_id"]
headers = {"Authorization": f"Bearer {token}"}
print(f"   Logueado OK. Alumno ID: {alumno_id}")

print("2. Obtener técnica activa...")
tecnicas_resp = requests.get(f"{API_BASE}/tecnicas", headers=headers, timeout=10)
assert tecnicas_resp.status_code == 200, f"Error listando tecnicas: {tecnicas_resp.text}"
tecnicas = tecnicas_resp.json()
tecnica = next((t for t in tecnicas if t.get("tiene_patron")), tecnicas[0])
tecnica_id = tecnica["id"]
tecnica_nombre = tecnica["nombre"]
print(f"   Técnica: {tecnica_nombre} (ID: {tecnica_id})")

print("3. Subir primer frame para sesión de detección de persona...")
with open(VIDEO_PATH, "rb") as vf:
    frame_resp = requests.post(
        f"{API_BASE}/evaluaciones/primer-frame",
        files={"video": ("Alumno.mp4", vf, "video/mp4")},
        headers=headers,
        timeout=30
    )
assert frame_resp.status_code == 200, f"Error primer-frame: {frame_resp.text}"
session_data = frame_resp.json()
session_id = session_data["session_id"]
print(f"   Sesión creada: {session_id}, personas encontradas: {len(session_data.get('personas', []))}")

print("4. Confirmar selección de persona 0...")
select_resp = requests.post(
    f"{API_BASE}/evaluaciones/{session_id}/seleccionar-persona",
    json={"persona_idx": 0},
    headers=headers,
    timeout=10
)
assert select_resp.status_code == 200, f"Error confirmando persona: {select_resp.text}"

print("5. Lanzar análisis en segundo plano (/evaluaciones/analizar)...")
t0 = time.time()
analizar_resp = requests.post(
    f"{API_BASE}/evaluaciones/analizar",
    data={
        "tecnica_id": tecnica_id,
        "tecnica_nombre": tecnica_nombre,
        "session_id": session_id,
        "alumno_id": alumno_id,
        "persona_idx": 0
    },
    headers=headers,
    timeout=10
)
assert analizar_resp.status_code == 200, f"Error al lanzar análisis: {analizar_resp.text}"
eval_id = analizar_resp.json()["evaluacion_id"]
print(f"   Evaluación lanzada ID: {eval_id}. Esperando finalización (polling)...")

eval_data = None
max_wait = 90
while time.time() - t0 < max_wait:
    time.sleep(1)
    status_resp = requests.get(f"{API_BASE}/evaluaciones/{eval_id}", headers=headers, timeout=10)
    if status_resp.status_code == 200:
        eval_data = status_resp.json()
        estado = eval_data.get("estado")
        if estado in ("completado", "error"):
            break

t1 = time.time()
tiempo_total = t1 - t0

print(f"\n=======================================================")
print(f"TIEMPO TOTAL DE ANÁLISIS: {tiempo_total:.2f} segundos")
print(f"ESTADO FINAL: {eval_data.get('estado')}")
print(f"=======================================================\n")

print("JSON DE RESPUESTA GET /api/v1/evaluaciones/{id}:")
print(json.dumps(eval_data, indent=2, ensure_ascii=False))

assert eval_data.get("estado") == "completado", f"Evaluación no completada: {eval_data}"
assert eval_data.get("feedback_summary"), "feedback_summary está vacío"
assert eval_data.get("feedback"), "feedback está vacío"
assert "nombres_articulaciones_criticas" in eval_data, "nombres_articulaciones_criticas falta en respuesta"
assert eval_data.get("frame_error_url"), "frame_error_url falta en respuesta"
assert tiempo_total < 30.0, f"El tiempo total ({tiempo_total:.2f}s) superó los 30 segundos requeridos"

print("\n✅ PRUEBA E2E MANUAL VALIDADA EXITOSAMENTE (< 30s con VLM local y feedback no vacío)")

