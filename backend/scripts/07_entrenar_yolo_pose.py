import sys
import time
from pathlib import Path
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DATA_YAML = "storage/datasets/bjj_pose_yolo/data.yaml"
PROJECT = "storage/models"
NAME = "yolo26n_bjj_pose"

print("=" * 60)
print("Fine-tuning de YOLO26-pose con ViCoS")
print("=" * 60)

t0 = time.time()

model = YOLO("yolo26n-pose.pt")

results = model.train(
    data=DATA_YAML,
    epochs=80,
    imgsz=640,
    batch=16,
    device="mps",
    workers=4,
    freeze=10,
    patience=20,
    project=PROJECT,
    name=NAME,
    exist_ok=True,
    verbose=True,
)

elapsed = time.time() - t0
print(f"\n=== ENTRENAMIENTO COMPLETADO en {elapsed/60:.1f} min ===")

best = Path(PROJECT) / NAME / "weights" / "best.pt"
if best.exists():
    print(f"Modelo guardado: {best}")
    print(f"Tamaño: {best.stat().st_size / 1024 / 1024:.1f} MB")
else:
    print("ERROR: no se encontró weights/best.pt")
    sys.exit(1)

