#!/usr/bin/env python3
"""
train_americana_finch.py
Entrenamiento continuo supervisado con Replay Buffer 70/30, Congelamiento de Backbone (freeze=10)
y tasa de aprendizaje adaptativa inspirada en FINCH (arXiv:2605.20005).
"""

import os
import sys
import json
import shutil
from pathlib import Path
import torch

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "scripts"))

from finch_callback import FINCHScheduler
from ultralytics import YOLO

def main():
    print("=" * 70)
    print("INICIO: CONTINUAL LEARNING CON PROTOCOLO FINCH Y REPLAY BUFFER (70/30)")
    print("=" * 70)

    dataset_yaml = BASE_DIR / "data" / "combined_americana" / "dataset.yaml"
    if not dataset_yaml.exists():
        print(f"❌ Error: {dataset_yaml} no existe. Ejecuta prepare_combined_americana_dataset.py primero.")
        sys.exit(1)

    base_model_path = BASE_DIR / "yolo26n-pose.pt"
    if not base_model_path.exists():
        base_model_path = BASE_DIR / "storage" / "models" / "yolo26n-pose.pt"
    print(f"🔹 Modelo base de producción: {base_model_path}")

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"⚡ Dispositivo de aceleración: {device.upper()}")

    # 1. Cargar modelo base
    model = YOLO(str(base_model_path))

    # 2. Registrar callback FINCH (Loss-Adaptive Learning Rate)
    finch = FINCHScheduler(base_lr=0.001, min_lr=1e-5, max_lr=0.01, ref_loss=2.0, alpha=0.5)
    model.add_callback("on_train_batch_end", finch.on_train_batch_end)

    print("🛡️ Restricciones de arquitectura aplicadas:")
    print("  • freeze=10 (Preservación del backbone contra olvido catastrófico)")
    print("  • Replay Buffer: 70% poses canónicas antiguas / 30% Americana")
    print("  • FINCH Adaptive LR: lr = base_lr * (ref_loss / loss)^0.5")

    # 3. Entrenar
    epochs = 25  # Épocas suficientes para convergencia en 200 frames
    results = model.train(
        data=str(dataset_yaml.resolve()),
        epochs=epochs,
        imgsz=640,
        batch=16,
        freeze=10,  # Congelar primeras 10 capas del backbone
        device=device,
        project=str((BASE_DIR / "runs" / "pose").resolve()),
        name="americana_finch",
        exist_ok=True,
        patience=8,
        verbose=True,
        plots=True,
        val=True
    )

    # 4. Guardar pesos del modelo entrenado
    best_weights = BASE_DIR / "runs" / "pose" / "americana_finch" / "weights" / "best.pt"
    if not best_weights.exists():
        best_weights = BASE_DIR / "runs" / "pose" / "americana_finch" / "weights" / "last.pt"

    dest_weights_root = BASE_DIR / "yolo26n_americana.pt"
    dest_weights_storage = BASE_DIR / "storage" / "models" / "yolo26n_americana.pt"

    if best_weights.exists():
        shutil.copy2(best_weights, dest_weights_root)
        shutil.copy2(best_weights, dest_weights_storage)
        print(f"\n✅ Modelo entrenado guardado exitosamente en:")
        print(f"   • {dest_weights_root}")
        print(f"   • {dest_weights_storage}")

    # 5. Exportar historial FINCH
    finch_log_path = BASE_DIR / "runs" / "pose" / "americana_finch" / "finch_trajectory.json"
    finch_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(finch_log_path, "w", encoding="utf-8") as f_hist:
        json.dump(finch.history, f_hist, indent=2)
    print(f"📊 Historial de adaptación FINCH guardado en: {finch_log_path}")

    print("=" * 70)
    print("ENTRENAMIENTO FINCH FINALIZADO EXITOSAMENTE")
    print("=" * 70)

if __name__ == "__main__":
    main()

