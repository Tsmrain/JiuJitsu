import sys
import logging
from pathlib import Path

# Configurar logging para capturar las líneas de info con los ratios reales
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.infrastructure.ai.local_spam_filter import LocalSpamFilter

# Videos que SÍ pasan por el filtro (alumnos subiendo ejecuciones para evaluación)
VIDEOS_ALUMNO = [
    "/Users/santiago/Desktop/JiuJitsu-main/Alumno.mp4",
    "/Users/santiago/Desktop/JiuJitsu-main/Alumno_Gaetamo.mp4",
]

# Videos que NO pasan por el filtro (profesores registrando patrón técnico de referencia)
VIDEOS_PROFESOR = [
    "/Users/santiago/Desktop/JiuJitsu-main/Maestro.mp4",
    "/Users/santiago/Desktop/JiuJitsu-main/Escape de 100 kilos brazo por debajo.mp4",
    "/Users/santiago/Desktop/JiuJitsu-main/Profesor dill pasaje de guardia abierta.mp4",
    "/Users/santiago/Desktop/JiuJitsu-main/profesor salida de Guardia Parandose.mp4",
    "/Users/santiago/Desktop/JiuJitsu-main/Profesor ensena 1 escape de guardia cerrada.mp4",
]

VIDEOS_NO_BJJ = [
    "storage/control_bailarinas.mp4",
    "storage/control_yoga.mp4",
    "storage/control_boxeo.mp4",
]

yolo = YOLOPoseAdapter()
filtro = LocalSpamFilter(yolo)

print("=== VIDEOS PROFESOR (Registran patrón de referencia — NO aplican al filtro anti-spam) ===")
for v in VIDEOS_PROFESOR:
    p = Path(v)
    existe = "✓ Existe" if p.exists() else "✗ No existe"
    print(f"  {p.name}: [EXENTO DEL FILTRO - Flujo Maestro] ({existe})")

print("\n=== VIDEOS ALUMNO (Evaluación de técnica — SÍ pasan por el filtro anti-spam, esperado: True) ===")
for v in VIDEOS_ALUMNO:
    p = Path(v)
    if not p.exists():
        print(f"  SKIP: no existe {v}")
        continue
    resultado = filtro.validar_es_jiujitsu(str(p))
    print(f"  {p.name}: {resultado} {'✅' if resultado else '❌ FALSO NEGATIVO'}")

print("\n=== NO-BJJ / CONTROLES NEGATIVOS (esperado: False) ===")
for v in VIDEOS_NO_BJJ:
    p = Path(v)
    if not p.is_absolute():
        p = Path(__file__).resolve().parents[1] / v
    if not p.exists():
        print(f"  SKIP: no existe {p}")
        continue
    resultado = filtro.validar_es_jiujitsu(str(p))
    print(f"  {p.name}: {resultado} {'❌ FALSO POSITIVO' if resultado else '✅'}")
