import os
import sys
import time
import json
from pathlib import Path
import cv2
import numpy as np

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
from ultralytics import YOLO

def main():
    print("=" * 75)
    print("FASE 1: BENCHMARK COMPARATIVO — YOLO POSE DIRECTO VS YOLO SEGMENTATION")
    print("=" * 75)

    video_path = Path("profesor salida de Guardia Parandose.mp4")
    if not video_path.exists():
        video_path = Path("../profesor salida de Guardia Parandose.mp4")
    if not video_path.exists():
        print(f"Error: No se encuentra {video_path}")
        sys.exit(1)

    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 464)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 832)
    cap.release()

    print(f"Video: {video_path.name} ({total_frames} frames, {w}x{h} @ {fps:.1f} fps)")

    _orig = torch.load
    def _safe_load(*a, **kw):
        kw["weights_only"] = False
        return _orig(*a, **kw)
    torch.load = _safe_load

    _device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Dispositivo de aceleración: {_device.upper()}")

    # -------------------------------------------------------------
    # MODO 1: YOLO Pose Directo (Baseline)
    # -------------------------------------------------------------
    print("\n--- MODO 1: YOLO Pose Directo (yolo26n-pose.pt) ---")
    pose_model = YOLO("yolo26n-pose.pt")

    t0 = time.time()
    results_direct = pose_model.predict(source=str(video_path), stream=True, verbose=False, conf=0.10, device=_device)

    frames_con_persona_direct = 0
    frames_2_personas_direct = 0
    frames_eval_direct = 0
    kpts_conf_list_direct = []

    for r in results_direct:
        frames_eval_direct += 1
        n_cands = 0
        if r.keypoints is not None and len(r.keypoints.data) > 0:
            raw = r.keypoints.data.cpu().numpy()
            cands = [p for p in raw if p.shape == (17, 3) and (p[:, 2] > 0.3).sum() >= 4]
            n_cands = len(cands)
            for c in cands:
                kpts_conf_list_direct.append(float(c[c[:, 2] > 0.3, 2].mean()))

        if n_cands >= 1:
            frames_con_persona_direct += 1
        if n_cands == 2:
            frames_2_personas_direct += 1

    t_direct = time.time() - t0
    cobertura_direct = (frames_con_persona_direct / total_frames) * 100
    fps_direct = total_frames / max(0.001, t_direct)
    avg_conf_direct = np.mean(kpts_conf_list_direct) if kpts_conf_list_direct else 0.0

    print(f"Frames con persona:     {frames_con_persona_direct}/{total_frames} ({cobertura_direct:.2f}%)")
    print(f"Frames con 2 personas:  {frames_2_personas_direct}/{total_frames} ({frames_2_personas_direct/total_frames*100:.2f}%)")
    print(f"Confianza media kpts:   {avg_conf_direct:.4f}")
    print(f"Tiempo total:           {t_direct:.2f}s ({fps_direct:.1f} FPS)")

    # -------------------------------------------------------------
    # MODO 2: Multi-Stage Segmentation + Pose (yolo26n-seg + yolo26n-pose)
    # -------------------------------------------------------------
    print("\n--- MODO 2: Multi-Stage Segmentation + Pose (yolo26n-seg -> yolo26n-pose) ---")
    seg_model = YOLO("yolo26n-seg.pt")

    cap = cv2.VideoCapture(str(video_path))
    t0 = time.time()

    frames_con_persona_seg = 0
    frames_2_personas_seg = 0
    frames_eval_seg = 0
    kpts_conf_list_seg = []

    # Procesar frames
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        frames_eval_seg += 1

        # 1. Segmentar personas con yolo26n-seg (clase 0 = person)
        seg_res = seg_model.predict(source=frame, verbose=False, conf=0.15, classes=[0], device=_device)
        
        candidatos_frame = []
        if seg_res and len(seg_res[0].boxes) > 0:
            boxes = seg_res[0].boxes.xyxy.cpu().numpy()
            
            for b in boxes:
                x1, y1, x2, y2 = b
                # Añadir margen del 10% para asegurar visibilidad de articulaciones extremas
                bw = x2 - x1
                bh = y2 - y1
                pad_x = bw * 0.10
                pad_y = bh * 0.10
                
                cx1 = int(max(0, x1 - pad_x))
                cy1 = int(max(0, y1 - pad_y))
                cx2 = int(min(w, x2 + pad_x))
                cy2 = int(min(h, y2 + pad_y))
                
                crop = frame[cy1:cy2, cx1:cx2]
                if crop.size == 0 or crop.shape[0] < 20 or crop.shape[1] < 20:
                    continue

                # 2. Inferencia de pose en el crop
                p_res = pose_model.predict(source=crop, verbose=False, conf=0.10, device=_device)
                if p_res and p_res[0].keypoints is not None and len(p_res[0].keypoints.data) > 0:
                    k_data = p_res[0].keypoints.data.cpu().numpy()
                    for person_k in k_data:
                        # Mapear coordenadas locales del crop a globales del frame
                        global_k = person_k.copy()
                        global_k[:, 0] += cx1
                        global_k[:, 1] += cy1
                        
                        if (global_k[:, 2] > 0.3).sum() >= 4:
                            candidatos_frame.append(global_k)
                            kpts_conf_list_seg.append(float(global_k[global_k[:, 2] > 0.3, 2].mean()))

        n_cands_seg = len(candidatos_frame)
        if n_cands_seg >= 1:
            frames_con_persona_seg += 1
        if n_cands_seg == 2:
            frames_2_personas_seg += 1

    cap.release()
    t_seg = time.time() - t0
    cobertura_seg = (frames_con_persona_seg / total_frames) * 100
    fps_seg = total_frames / max(0.001, t_seg)
    avg_conf_seg = np.mean(kpts_conf_list_seg) if kpts_conf_list_seg else 0.0

    print(f"Frames con persona:     {frames_con_persona_seg}/{total_frames} ({cobertura_seg:.2f}%)")
    print(f"Frames con 2 personas:  {frames_2_personas_seg}/{total_frames} ({frames_2_personas_seg/total_frames*100:.2f}%)")
    print(f"Confianza media kpts:   {avg_conf_seg:.4f}")
    print(f"Tiempo total:           {t_seg:.2f}s ({fps_seg:.1f} FPS)")

    # -------------------------------------------------------------
    # TABLA COMPARATIVA Y DECISIÓN LARMAN
    # -------------------------------------------------------------
    print("\n" + "=" * 75)
    print("TABLA COMPARATIVA DE PRUEBA DE FUEGO (CRAIG LARMAN):")
    print("=" * 75)
    print(f"{'Métrica':<30} | {'YOLO Pose Directo':<18} | {'Multi-Stage Seg+Pose':<20}")
    print("-" * 75)
    print(f"{'Cobertura Tracking (%)':<30} | {cobertura_direct:>17.2f}% | {cobertura_seg:>19.2f}%")
    print(f"{'Frames con 2 personas':<30} | {frames_2_personas_direct:>17} | {frames_2_personas_seg:>19}")
    print(f"{'Confianza Media Kpts':<30} | {avg_conf_direct:>18.4f} | {avg_conf_seg:>20.4f}")
    print(f"{'FPS de Procesamiento':<30} | {fps_direct:>18.1f} | {fps_seg:>20.1f}")
    print(f"{'Latencia por frame (ms)':<30} | {t_direct/total_frames*1000:>16.1f}ms | {t_seg/total_frames*1000:>18.1f}ms")
    print("-" * 75)

    delta_cobertura = cobertura_seg - cobertura_direct
    print(f"\nDelta de Cobertura: {delta_cobertura:+.2f}%")
    print(f"Detección de 2 personas: {frames_2_personas_seg - frames_2_personas_direct:+d} frames")

    if delta_cobertura >= 5.0:
        print("DECISIÓN DE ARQUITECTURA: La segmentación mejora la cobertura >= 5%. Habilitar por defecto.")
    else:
        print("DECISIÓN DE ARQUITECTURA: La segmentación NO mejora la cobertura en al menos +5%.")
        print("GUARDRAIL LARMAN: Mantener USE_SEGMENTATION=False por defecto para preservar alta velocidad")
        print("y dejar el modo Segmentation como flag configurable opcional de alta precisión.")
    print("=" * 75)

if __name__ == "__main__":
    main()

