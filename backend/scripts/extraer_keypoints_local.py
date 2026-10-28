#!/usr/bin/env python3
"""
Extrae keypoints YOLO de un video LOCALMENTE (sin Colab).
SOLO para desarrollo del algoritmo DTW: los keypoints se guardan en JSON
y se usan offline para validar la matemática antes de integrar con Colab.

Incluye tracking por continuidad temporal para seleccionar consistentemente
al mismo practicante a lo largo de todos los fotogramas (evita saltos entre personas).
"""
import argparse
import json
import os
import sys

import numpy as np
import torch
_orig_torch_load = torch.load
def _safe_torch_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _orig_torch_load(*args, **kwargs)
torch.load = _safe_torch_load

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ultralytics import YOLO

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--model", default="yolo26n-pose.pt")
    ap.add_argument("--conf", type=float, default=0.3)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Device: {device}")
    print(f"[INFO] Modelo: {args.model}")
    print(f"[INFO] Video:  {args.video}")

    model = YOLO(args.model)
    results = model.predict(
        source=args.video, device=device, stream=False,
        verbose=False, conf=args.conf,
    )

    esqueletos = []
    persona_anterior = None

    for frame_idx, r in enumerate(results):
        if r.keypoints is None or len(r.keypoints.data) == 0:
            continue

        raw_personas = r.keypoints.data.cpu().numpy()
        # Filtrar personas válidas con shape exacto (17, 3) y al menos 3 keypoints detectados
        personas = [p for p in raw_personas if p.shape == (17, 3) and np.count_nonzero(p[:, :2]) >= 3]

        # YOLO26 es NMS-free: filtramos personas con < 8 keypoints de alta confianza (> 0.3)
        personas = [
            p for p in personas
            if np.count_nonzero((p[:, 2] > 0.3) & (p[:, 0] > 0)) >= 8
        ]
        if not personas:
            continue

        if persona_anterior is not None:
            # Distancia euclidiana media entre articulaciones detectadas
            distancias = [
                float(np.mean(np.linalg.norm(p[:, :2] - persona_anterior[:, :2], axis=1)))
                for p in personas
            ]
            idx = int(np.argmin(distancias))
        else:
            # Primera detección: seleccionar la persona con mayor confianza media
            confianzas = [float(p[:, 2].mean()) for p in personas]
            idx = int(np.argmax(confianzas))

        persona_actual = personas[idx]
        persona_anterior = persona_actual

        kpts = persona_actual.flatten().tolist()
        if len(kpts) < 133:
            kpts.extend([0.0] * (133 - len(kpts)))
        else:
            kpts = kpts[:133]

        esqueletos.append({
            "frame_idx": frame_idx,
            "keypoints133": kpts,
            "angulos_articulares": {}
        })

    with open(args.output, "w") as f:
        json.dump({
            "total_frames_procesados": len(results),
            "total_esqueletos": len(esqueletos),
            "esqueletos": esqueletos,
        }, f)

    print(f"[OK] {len(esqueletos)} esqueletos con tracking temporal → {args.output}")

if __name__ == "__main__":
    main()
