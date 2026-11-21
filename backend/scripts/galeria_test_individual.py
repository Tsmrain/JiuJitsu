#!/usr/bin/env python3
"""Test individual: por cada video de ~/Desktop/Galeria -> personas detectadas + clasificación JJ + keypoints."""
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpocmente.application.services.jiujitsu_classifier import clasificar_video_jiujitsu
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
from corpocmente.ui.api.routes import _limpiar_candidatos_bboxes

GALERIA = Path.home() / "Desktop" / "Galeria"
OUT = Path("/tmp/galeria_report")
OUT.mkdir(parents=True, exist_ok=True)
TRIM_DIR = Path("/tmp/galeria_trimmed")
TRIM_DIR.mkdir(parents=True, exist_ok=True)

MAX_SECONDS = 30
FRAME_STRIDE = 2


def _flush_mps():
    if hasattr(torch, "mps") and torch.backends.mps.is_available():
        try:
            torch.mps.synchronize()
            torch.mps.empty_cache()
        except Exception:
            pass
    try:
        import mlx.core as mx
        if hasattr(mx, "clear_cache"):
            mx.clear_cache()
    except Exception:
        pass


def _trim_if_needed(video: Path) -> tuple[Path, bool, float, int]:
    cap = cv2.VideoCapture(str(video))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    dur = (total_frames / fps) if fps > 0 else 0.0
    if dur <= MAX_SECONDS or total_frames <= 0:
        cap.release()
        return video, False, fps, total_frames

    max_frames = int(MAX_SECONDS * fps)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
    safe_name = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in video.name)
    out_path = TRIM_DIR / f"trim30s_{safe_name}.mp4"
    writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    count = 0
    while count < max_frames:
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        writer.write(frame)
        count += 1
    writer.release()
    cap.release()
    return out_path, True, fps, total_frames


def _contar_personas_muestreo(adapter: YOLOPoseAdapter, video: Path, n_samples: int = 8) -> dict:
    model = adapter._get_model()
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    cap = cv2.VideoCapture(str(video))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    counts_raw = []
    counts_clean = []
    primer_frame_personas = 0

    try:
        if total <= 0:
            return {"primer_frame_personas": 0, "personas_max_raw": 0, "personas_max_clean": 0}
        sample_idxs = sorted({min(total - 1, int(i * total / n_samples)) for i in range(n_samples)})
        if 0 not in sample_idxs:
            sample_idxs.insert(0, 0)
        with torch.inference_mode():
            for idx in sample_idxs:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue
                res = model.predict(source=frame, conf=0.15, verbose=False, imgsz=416, half=True, device=device)
                if not res or res[0].keypoints is None or len(res[0].keypoints.data) == 0:
                    counts_raw.append(0)
                    counts_clean.append(0)
                    continue
                raw_kpts = res[0].keypoints.data.cpu().numpy()
                cands = []
                for p_i, p in enumerate(raw_kpts):
                    mask = (p[:, 2] > 0.3) & (p[:, 0] > 0)
                    if p.shape == (17, 3) and int(np.count_nonzero(mask)) >= 4:
                        pts = p[mask, :2]
                        min_x, min_y = float(pts[:, 0].min()), float(pts[:, 1].min())
                        max_x, max_y = float(pts[:, 0].max()), float(pts[:, 1].max())
                        cands.append({
                            "idx": p_i,
                            "pose": p,
                            "bbox_raw": [min_x, min_y, max_x, max_y],
                            "confianza": float(p[mask, 2].mean()),
                            "keypoints_validos": int(np.count_nonzero(mask)),
                            "center": np.array([(min_x + max_x) / 2.0, (min_y + max_y) / 2.0]),
                            "pelvis": p[[11, 12], :2].mean(axis=0) if ((p[[11, 12], 2] > 0.3).all() and (p[[11, 12], 0] > 0).all()) else None,
                            "head": p[0, :2] if (p[0, 2] > 0.3 and p[0, 0] > 0) else None,
                        })
                limpios = _limpiar_candidatos_bboxes(cands, frame.shape[1], frame.shape[0]) if cands else []
                counts_raw.append(len(cands))
                counts_clean.append(len(limpios))
                if idx == 0 or (primer_frame_personas == 0 and len(limpios) > 0):
                    primer_frame_personas = len(limpios)
    finally:
        cap.release()

    return {
        "primer_frame_personas": primer_frame_personas,
        "personas_max_raw": max(counts_raw) if counts_raw else 0,
        "personas_max_clean": max(counts_clean) if counts_clean else 0,
        "muestras_clean": counts_clean,
    }


def analizar(video: Path, adapter: YOLOPoseAdapter, vlm_adapter: LocalVLMAdapter) -> dict:
    proc_path, recortado, fps, orig_frames = _trim_if_needed(video)

    t0 = time.time()
    person_stats = _contar_personas_muestreo(adapter, proc_path)
    seq = adapter.extraer_secuencia(
        str(proc_path),
        persona_idx_inicial=0,
        frame_stride=FRAME_STRIDE,
    )
    dt_yolo = time.time() - t0
    _flush_mps()

    t1 = time.time()
    clf = clasificar_video_jiujitsu(video, vlm_adapter=vlm_adapter, n_frames=6)
    dt_vlm = time.time() - t1
    _flush_mps()

    frames_procesados = len(seq.get("frame_idxs", [])) if isinstance(seq, dict) else 0
    return {
        "video": str(video.relative_to(GALERIA)),
        "fps": round(fps, 2),
        "frames_totales_video": orig_frames,
        "recortado_a_30s": recortado,
        "frames_procesados": frames_procesados,
        "cobertura_tracking": seq.get("cobertura", 0.0) if isinstance(seq, dict) else 0.0,
        "personas_primer_frame": person_stats["primer_frame_personas"],
        "personas_max_detectadas": person_stats["personas_max_clean"],
        "personas_max_raw": person_stats["personas_max_raw"],
        "muestras_personas_clean": person_stats["muestras_clean"],
        "clasificacion_jj": clf,
        "tiempo_yolo_s": round(dt_yolo, 2),
        "tiempo_vlm_s": round(dt_vlm, 2),
        "tiempo_analisis_s": round(dt_yolo + dt_vlm, 2),
    }


def main():
    adapter = YOLOPoseAdapter(colab_url="")
    vlm_adapter = LocalVLMAdapter()
    videos = sorted(GALERIA.rglob("*.mov")) + sorted(GALERIA.rglob("*.mp4"))
    results = []
    for v in videos:
        print(f"\n=== {v.relative_to(GALERIA)} ===", flush=True)
        try:
            r = analizar(v, adapter, vlm_adapter)
            print(json.dumps(r, indent=2, ensure_ascii=False), flush=True)
            results.append(r)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR: {e}", flush=True)
            results.append({"video": str(v.relative_to(GALERIA)), "error": str(e)})
        _flush_mps()
    (OUT / "individual.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n[OK] Resultados: {OUT / 'individual.json'}")


if __name__ == "__main__":
    main()
