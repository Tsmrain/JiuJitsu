import os
import sys
import time
import json
from pathlib import Path
import cv2

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from ultralytics import YOLO
import torch

def diagnostico():
    video_path = Path("profesor salida de Guardia Parandose.mp4")
    if not video_path.exists():
        video_path = Path("../profesor salida de Guardia Parandose.mp4")
    if not video_path.exists():
        print(f"Error: No se encuentra {video_path}")
        sys.exit(1)

    print("=" * 70)
    print("FASE 1: DIAGNÓSTICO EN 'profesor salida de Guardia Parandose.mp4'")
    print("=" * 70)

    cap = cv2.VideoCapture(str(video_path))
    total_cap_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)
    duracion_s = total_cap_frames / fps
    cap.release()

    print(f"Video: {video_path.name}")
    print(f"Resolución: {w}x{h} | FPS: {fps:.2f} | Frames totales: {total_cap_frames} | Duración: {duracion_s:.2f}s")

    # 1. Ejecutar YOLOPoseAdapter actual
    adapter = YOLOPoseAdapter()
    t0 = time.time()
    res_adapter = adapter.extraer_secuencia(str(video_path))
    t_adapter = time.time() - t0

    print("\n--- RESULTADO DE YOLOPoseAdapter ACTUAL ---")
    print(f"Total frames evaluados: {res_adapter['total_frames']}")
    print(f"Frames con persona:     {res_adapter['frames_con_persona']}")
    print(f"Cobertura:              {res_adapter['cobertura'] * 100:.2f}%")
    print(f"Tiempo de inferencia:   {t_adapter:.2f}s ({res_adapter['total_frames']/max(0.001, t_adapter):.1f} FPS)")

    # 2. Conteo detallado de personas por frame con YOLO Pose estándar
    _orig = torch.load
    def _safe_load(*a, **kw):
        kw["weights_only"] = False
        return _orig(*a, **kw)
    torch.load = _safe_load

    _device = "mps" if torch.backends.mps.is_available() else "cpu"
    pose_model = YOLO("yolo26n-pose.pt")
    
    conteos_personas = {0: 0, 1: 0, 2: 0, "3+": 0}
    frames_2_personas = []
    
    results = pose_model.predict(source=str(video_path), stream=True, verbose=False, conf=0.10, device=_device)
    for f_idx, r in enumerate(results):
        n_cands = 0
        if r.keypoints is not None and len(r.keypoints.data) > 0:
            raw = r.keypoints.data.cpu().numpy()
            candidatos = [
                p for p in raw
                if p.shape == (17, 3) and (p[:, 2] > 0.3).sum() >= 4
            ]
            n_cands = len(candidatos)
        
        if n_cands == 0:
            conteos_personas[0] += 1
        elif n_cands == 1:
            conteos_personas[1] += 1
        elif n_cands == 2:
            conteos_personas[2] += 1
            frames_2_personas.append(f_idx)
        else:
            conteos_personas["3+"] += 1

    print("\n--- DETECCIÓN DE PERSONAS POR FRAME (YOLO Pose) ---")
    print(f"Frames con 0 personas:  {conteos_personas[0]:>4} ({conteos_personas[0]/total_cap_frames*100:.1f}%)")
    print(f"Frames con 1 persona:   {conteos_personas[1]:>4} ({conteos_personas[1]/total_cap_frames*100:.1f}%)")
    print(f"Frames con 2 personas:  {conteos_personas[2]:>4} ({conteos_personas[2]/total_cap_frames*100:.1f}%)")
    print(f"Frames con 3+ personas: {conteos_personas['3+']:>4} ({conteos_personas['3+']/total_cap_frames*100:.1f}%)")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    diagnostico()

