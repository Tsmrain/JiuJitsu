#!/usr/bin/env python3
"""
prepare_combined_americana_dataset.py
Construye el dataset balanceado 70/30 (Replay Buffer) para entrenar con FINCH:
- 70% Poses de técnicas antiguas (Gold Standard BJJ + Continuous Dataset)
- 30% Poses de la nueva técnica ("Americana desde la montada")
"""

import os
import shutil
import random
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

AMERICANA_DIR = DATA_DIR / "americana"
CONTINUOUS_DIR = DATA_DIR / "continuous_dataset"
BJJ_GOLD_DIR = BASE_DIR / "backend" / "storage" / "datasets" / "bjj_pose_yolo"

COMBINED_DIR = DATA_DIR / "combined_americana"
TRAIN_IMG = COMBINED_DIR / "images" / "train"
VAL_IMG = COMBINED_DIR / "images" / "val"
TRAIN_LBL = COMBINED_DIR / "labels" / "train"
VAL_LBL = COMBINED_DIR / "labels" / "val"

AMERICANA_VAL_DIR = DATA_DIR / "americana_val"
AMERICANA_VAL_IMG = AMERICANA_VAL_DIR / "images" / "val"
AMERICANA_VAL_LBL = AMERICANA_VAL_DIR / "labels" / "val"

def main():
    print("=" * 70)
    print("CONSTRUCCIÓN DE DATASET COMBINADO: REPLAY BUFFER 70/30 (LARMAN & FINCH)")
    print("=" * 70)

    # Limpiar o recrear directorios
    if COMBINED_DIR.exists():
        shutil.rmtree(COMBINED_DIR)
    for d in [TRAIN_IMG, VAL_IMG, TRAIN_LBL, VAL_LBL]:
        d.mkdir(parents=True, exist_ok=True)

    if AMERICANA_VAL_DIR.exists():
        shutil.rmtree(AMERICANA_VAL_DIR)
    for d in [AMERICANA_VAL_IMG, AMERICANA_VAL_LBL]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Recolectar frames antiguos (Gold Standard + Flywheel)
    old_train_pairs = []

    # De continuous_dataset
    c_img_dir = CONTINUOUS_DIR / "images" / "train"
    c_lbl_dir = CONTINUOUS_DIR / "labels" / "train"
    if c_img_dir.exists():
        for img in sorted(c_img_dir.glob("*.jpg")):
            lbl = c_lbl_dir / f"{img.stem}.txt"
            if lbl.exists():
                old_train_pairs.append((img, lbl))

    # De bjj_pose_yolo (muestreo balanceado y determinista)
    bjj_img_dir = BJJ_GOLD_DIR / "train" / "images"
    bjj_lbl_dir = BJJ_GOLD_DIR / "train" / "labels"
    if bjj_img_dir.exists():
        all_bjj_imgs = sorted(bjj_img_dir.glob("*.jpg"))
        random.seed(42)
        sampled_bjj = random.sample(all_bjj_imgs, min(120, len(all_bjj_imgs)))
        for img in sampled_bjj:
            lbl = bjj_lbl_dir / f"{img.stem}.txt"
            if lbl.exists():
                old_train_pairs.append((img, lbl))

    print(f"📦 Total frames antiguos seleccionados: {len(old_train_pairs)}")

    # 2. Recolectar frames de Americana
    americana_pairs = []
    ame_img_dir = AMERICANA_DIR / "images"
    ame_lbl_dir = AMERICANA_DIR / "labels"
    for img in sorted(ame_img_dir.glob("*.jpg")):
        lbl = ame_lbl_dir / f"{img.stem}.txt"
        if lbl.exists() and lbl.stat().st_size > 0:
            americana_pairs.append((img, lbl))

    random.seed(42)
    random.shuffle(americana_pairs)

    # Calcular proporción exacta 70/30
    # n_old = len(old_train_pairs) -> n_new = int(n_old * 3 / 7)
    n_old = len(old_train_pairs)
    n_new = int(n_old * 0.3 / 0.7)
    print(f"⚖️ Proporción Replay Buffer: {n_old} antiguos (70%) + {n_new} nuevos (30%)")

    selected_americana_train = americana_pairs[:n_new]
    selected_americana_val = americana_pairs[n_new:n_new + 40]

    # Copiar al set de entrenamiento combinado
    for img, lbl in old_train_pairs:
        dest_img = TRAIN_IMG / f"old_{img.name}"
        dest_lbl = TRAIN_LBL / f"old_{lbl.name}"
        shutil.copy2(img, dest_img)
        shutil.copy2(lbl, dest_lbl)

    for img, lbl in selected_americana_train:
        dest_img = TRAIN_IMG / f"new_{img.name}"
        dest_lbl = TRAIN_LBL / f"new_{lbl.name}"
        shutil.copy2(img, dest_img)
        shutil.copy2(lbl, dest_lbl)

    # 3. Preparar set de validación antiguo en combined_americana
    c_val_img = CONTINUOUS_DIR / "images" / "val"
    c_val_lbl = CONTINUOUS_DIR / "labels" / "val"
    val_count = 0
    if c_val_img.exists():
        for img in sorted(c_val_img.glob("*.jpg")):
            lbl = c_val_lbl / f"{img.stem}.txt"
            if lbl.exists():
                shutil.copy2(img, VAL_IMG / f"old_val_{img.name}")
                shutil.copy2(lbl, VAL_LBL / f"old_val_{lbl.name}")
                val_count += 1

    bjj_val_img = BJJ_GOLD_DIR / "val" / "images"
    bjj_val_lbl = BJJ_GOLD_DIR / "val" / "labels"
    if bjj_val_img.exists():
        all_bjj_val = sorted(bjj_val_img.glob("*.jpg"))
        random.seed(42)
        sampled_val = random.sample(all_bjj_val, min(20, len(all_bjj_val)))
        for img in sampled_val:
            lbl = bjj_val_lbl / f"{img.stem}.txt"
            if lbl.exists():
                shutil.copy2(img, VAL_IMG / f"bjj_val_{img.name}")
                shutil.copy2(lbl, VAL_LBL / f"bjj_val_{lbl.name}")
                val_count += 1

    # 4. Preparar set de validación exclusivo de Americana
    for img, lbl in selected_americana_val:
        shutil.copy2(img, AMERICANA_VAL_IMG / img.name)
        shutil.copy2(lbl, AMERICANA_VAL_LBL / lbl.name)

    # Crear dataset.yaml para combined_americana
    combined_yaml = {
        "path": str(COMBINED_DIR.resolve()),
        "train": "images/train",
        "val": "images/val",
        "kpt_shape": [17, 3],
        "flip_idx": [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15],
        "names": {0: "person"}
    }
    with open(COMBINED_DIR / "dataset.yaml", "w", encoding="utf-8") as f:
        yaml.dump(combined_yaml, f, sort_keys=False)

    # Crear dataset.yaml para americana_val
    americana_yaml = {
        "path": str(AMERICANA_VAL_DIR.resolve()),
        "train": "images/val",  # dummy
        "val": "images/val",
        "kpt_shape": [17, 3],
        "flip_idx": [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15],
        "names": {0: "person"}
    }
    with open(AMERICANA_VAL_DIR / "dataset.yaml", "w", encoding="utf-8") as f:
        yaml.dump(americana_yaml, f, sort_keys=False)

    print("\n✅ DATASET COMBINADO PREPARADO CON ÉXITO:")
    print(f"  • Imágenes train:        {len(list(TRAIN_IMG.glob('*')))} (70% antiguas, 30% Americana)")
    print(f"  • Imágenes val (antiguas): {val_count} (para medir no-olvido)")
    print(f"  • Imágenes val (Americana): {len(selected_americana_val)} (para medir aprendizaje de técnica nueva)")
    print(f"  • Configuración:          {COMBINED_DIR / 'dataset.yaml'}")
    print("=" * 70)

if __name__ == "__main__":
    main()

