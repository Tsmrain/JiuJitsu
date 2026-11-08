#!/usr/bin/env python3
"""
extract_and_label_americana.py
Extrae fotogramas de los videos de 'Americana desde la montada' (alumna y maestro)
y aplica pseudo-etiquetado Teacher-Student usando el modelo maestro yolo26x-pose.pt.
"""

import os
import sys
from pathlib import Path
import cv2
import torch

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parents[1]
VIDEO_ALUMNA = BASE_DIR / "AlumnaAmericana.mov"
VIDEO_MAESTRO = BASE_DIR / "MaestroAmericana.mov"

OUTPUT_DIR = BASE_DIR / "data" / "americana"
IMAGES_DIR = OUTPUT_DIR / "images"
LABELS_DIR = OUTPUT_DIR / "labels"

MASTER_MODEL_PATH = BASE_DIR / "storage" / "models" / "yolo26x-pose.pt"

def extract_frames(video_path: Path, prefix: str, every_n: int = 5):
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    idx = 0
    saved = 0
    extracted_paths = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % every_n == 0:
            frame_name = f"{prefix}_frame_{idx:05d}.jpg"
            save_path = IMAGES_DIR / frame_name
            cv2.imwrite(str(save_path), frame)
            extracted_paths.append(save_path)
            saved += 1
        idx += 1
    cap.release()
    print(f"✅ Extraídos {saved} frames de {video_path.name}")
    return extracted_paths

def label_frames_with_master(frame_paths):
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    _orig = torch.load
    def _safe_load(*a, **kw):
        kw["weights_only"] = False
        return _orig(*a, **kw)
    torch.load = _safe_load

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"🧠 Cargando modelo maestro {MASTER_MODEL_PATH.name} en {device.upper()}...")
    master = YOLO(str(MASTER_MODEL_PATH))

    labeled_count = 0
    discarded_empty = 0

    for img_path in frame_paths:
        results = master.predict(
            source=str(img_path),
            device=device,
            verbose=False,
            conf=0.20
        )
        r = results[0]
        img_h, img_w = r.orig_shape
        lineas_yolo = []

        if r.boxes is not None and r.keypoints is not None:
            boxes_data = r.boxes.xywhn.cpu().numpy()
            kpts_data = r.keypoints.data.cpu().numpy()

            for b_idx in range(len(boxes_data)):
                bx, by, bw, bh = boxes_data[b_idx]
                kpts = kpts_data[b_idx]

                linea_parts = [f"0 {bx:.6f} {by:.6f} {bw:.6f} {bh:.6f}"]
                for k in range(17):
                    kx, ky, kconf = kpts[k]
                    norm_kx = max(0.0, min(1.0, kx / img_w))
                    norm_ky = max(0.0, min(1.0, ky / img_h))

                    if kconf >= 0.40 and 0.0 <= norm_kx <= 1.0 and 0.0 <= norm_ky <= 1.0:
                        v = 2
                    elif kconf >= 0.10:
                        v = 1
                    else:
                        v = 0
                        norm_kx = 0.0
                        norm_ky = 0.0

                    linea_parts.append(f"{norm_kx:.6f} {norm_ky:.6f} {v}")

                lineas_yolo.append(" ".join(linea_parts))

        label_path = LABELS_DIR / f"{img_path.stem}.txt"
        with open(label_path, "w", encoding="utf-8") as f_lbl:
            if lineas_yolo:
                f_lbl.write("\n".join(lineas_yolo) + "\n")
                labeled_count += 1
            else:
                discarded_empty += 1

    print(f"🎯 Pseudo-etiquetado completado: {labeled_count} frames con atletas, {discarded_empty} vacíos.")

def main():
    print("=" * 70)
    print("EXTRACCIÓN Y PSEUDO-ETIQUETADO: AMERICANA DESDE LA MONTADA")
    print("=" * 70)
    frames_alumna = extract_frames(VIDEO_ALUMNA, "americana_alumna", every_n=5)
    frames_maestro = extract_frames(VIDEO_MAESTRO, "americana_maestro", every_n=5)
    all_frames = frames_alumna + frames_maestro
    label_frames_with_master(all_frames)
    print("=" * 70)

if __name__ == "__main__":
    main()

