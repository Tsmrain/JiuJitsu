import sys
from pathlib import Path
import numpy as np
import cv2
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter

PROMPT = (
    "Describe en una sola oración, en inglés, qué acción realizan las personas "
    "visibles en esta imagen. Si no hay personas, di 'no persons visible'."
)

adapter = LocalVLMAdapter()

# Extraer frame real del Alumno.mp4 (en la raíz del proyecto)
cap = cv2.VideoCapture("/Users/santiago/Desktop/JiuJitsu-main/Alumno.mp4")
cap.set(cv2.CAP_PROP_POS_FRAMES, 200)
ok, frame = cap.read()
cap.release()
if not ok:
    print("ERROR: no se pudo extraer frame de Alumno.mp4")
    sys.exit(1)
frame_real = "/tmp/frame_real_test.jpg"
cv2.imwrite(frame_real, frame)
print(f"Imagen real: {frame_real}")

# Imagen negra del mismo tamaño
img_negra = np.zeros_like(frame)
frame_negra = "/tmp/frame_negra_test.jpg"
cv2.imwrite(frame_negra, img_negra)
print(f"Imagen negra: {frame_negra}")

print("\n=== CON IMAGEN REAL ===")
res_real = adapter.generar_texto_feedback(PROMPT, frame_real)
print(f"summary: {res_real['summary']}")
print(f"correction: {res_real['correction'][:200]}")

print("\n=== CON IMAGEN NEGRA ===")
res_negra = adapter.generar_texto_feedback(PROMPT, frame_negra)
print(f"summary: {res_negra['summary']}")
print(f"correction: {res_negra['correction'][:200]}")

print("\n=== VEREDICTO ===")
if res_real == res_negra:
    print("❌ FALSO POSITIVO: el VLM NO usa la imagen (output idéntico).")
    sys.exit(1)
elif "no persons" in (res_real.get("correction", "") + res_negra.get("correction", "")).lower() or "no persons" in (res_real.get("summary", "") + res_negra.get("summary", "")).lower():
    print("✅ El VLM diferencia imagen real de negra y detecta 'no persons'. Las imágenes SÍ se usan.")
else:
    print("⚠️ Output diferente, pero sin 'no persons'. Verificar manualmente.")

