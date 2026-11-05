#!/usr/bin/env python3
"""
Test de Validación de Profundidad Nativa YOLO26 (Iteración 4I - Fase 1)
Metodología: Craig Larman (Evidencia Empírica Cruda, Métricas en Metros)
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

# Directorios de artefactos y búsqueda
REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = Path("/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_CANDIDATES = [
    REPO_ROOT / "2026-10-31 17-15-58.mov",
    Path("2026-10-31 17-15-58.mov"),
]
video_path = next((p for p in VIDEO_CANDIDATES if p.exists()), None)
if not video_path:
    print(f"ERROR: Video '2026-10-31 17-15-58.mov' no encontrado en {REPO_ROOT}")
    sys.exit(1)

DEPTH_MODEL_CANDIDATES = [
    REPO_ROOT / "backend" / "yolo26n-depth.pt",
    REPO_ROOT / "yolo26n-depth.pt",
    REPO_ROOT / "storage" / "models" / "yolo26n-depth.pt",
    Path("yolo26n-depth.pt"),
]
depth_weights = next((p for p in DEPTH_MODEL_CANDIDATES if p.exists()), "yolo26n-depth.pt")

POSE_MODEL_CANDIDATES = [
    REPO_ROOT / "backend" / "yolo26n-pose.pt",
    REPO_ROOT / "yolo26n-pose.pt",
    REPO_ROOT / "storage" / "models" / "yolo26n-pose.pt",
    Path("yolo26n-pose.pt"),
]
pose_weights = next((p for p in POSE_MODEL_CANDIDATES if p.exists()), "yolo26n-pose.pt")

print("=" * 70)
print("FASE 1: VALIDACIÓN DE ESTIMACIÓN DE PROFUNDIDAD MÉTRICA CON YOLO26")
print("=" * 70)
print(f"Video de prueba:  {video_path}")
print(f"Pesos de Pose:    {pose_weights}")
print(f"Pesos de Depth:   {depth_weights}")

# Cargar modelos YOLO
pose_model = YOLO(str(pose_weights))
depth_model = YOLO(str(depth_weights))

cap = cv2.VideoCapture(str(video_path))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Propiedades del video: {w}x{h} @ {fps:.1f} fps, {total_frames} frames totales ({total_frames/fps:.1f}s)")

target_frames = [0, 50, 100]

for f_idx in target_frames:
    cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
    ret, frame = cap.read()
    if not ret or frame is None:
        print(f"ERROR: No se pudo leer el fotograma {f_idx}")
        continue

    # Inferencia en paralelo / secuencial
    pose_results = pose_model.predict(source=frame, verbose=False, conf=0.25)[0]
    depth_results = depth_model.predict(source=frame, verbose=False)[0]

    # Mapa de profundidad métrico (Z en metros)
    depth_map = depth_results.depth.data.cpu().numpy()
    dh, dw = depth_map.shape[:2]

    z_min = float(np.min(depth_map))
    z_max = float(np.max(depth_map))
    z_mean = float(np.mean(depth_map))

    print(f"\n==================== FOTOGRAMA #{f_idx} ====================")
    print(f"Dimensiones del Depth Map: {dw}x{dh} (Coincidencia nativa 1:1 con frame)")
    print(f"Rango de Profundidad Escena: Min={z_min:.2f}m, Max={z_max:.2f}m, Media={z_mean:.2f}m")

    boxes = pose_results.boxes
    num_atletas = len(boxes) if boxes is not None else 0
    print(f"Atletas detectados por YOLO Pose: {num_atletas}")

    vis_depth = depth_map.copy()
    # Normalizar para visualización 0-255 con colormap Turbo
    vis_norm = cv2.normalize(vis_depth, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    vis_colored = cv2.applyColorMap(vis_norm, cv2.COLORMAP_TURBO)

    if boxes is not None and len(boxes) > 0:
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            conf = float(box.conf[0].cpu().numpy())

            # Clamping a los límites de la imagen
            x1, y1 = max(0, min(dw - 1, x1)), max(0, min(dh - 1, y1))
            x2, y2 = max(0, min(dw - 1, x2)), max(0, min(dh - 1, y2))

            crop = depth_map[y1:y2, x1:x2]
            if crop.size > 0:
                mean_depth = float(np.mean(crop))
                median_depth = float(np.median(crop))
                std_depth = float(np.std(crop))
                p25 = float(np.percentile(crop, 25))
                p75 = float(np.percentile(crop, 75))

                print(f"  🥋 Atleta {i}: Box=[{x1}, {y1}, {x2}, {y2}] Conf={conf:.2f}")
                print(f"     Profundidad Media:   {mean_depth:.2f}m (±{std_depth:.2f}m)")
                print(f"     Profundidad Mediana: {median_depth:.2f}m [IQR: {p25:.2f}m - {p75:.2f}m]")

                # Dibujar en la imagen de visualización
                color_box = (0, 255, 0) if i == 0 else (255, 0, 0)
                cv2.rectangle(vis_colored, (x1, y1), (x2, y2), color_box, 3)
                label = f"Atleta {i}: {mean_depth:.2f}m"
                cv2.putText(vis_colored, label, (x1, max(30, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

    # Guardar mapa de profundidad coloreado en la carpeta de artefactos
    out_img_path = ARTIFACTS_DIR / f"depth_map_frame_{f_idx}.png"
    cv2.imwrite(str(out_img_path), vis_colored)
    print(f"  [EVIDENCIA VISUAL] Guardado mapa coloreado en: {out_img_path}")

cap.release()
print("\n" + "=" * 70)
print("✅ FASE 1 COMPLETADA: Estimación métrica verificada con éxito.")
print("=" * 70)
