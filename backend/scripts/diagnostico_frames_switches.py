#!/usr/bin/env python3
"""
Para cada frame donde ocurre un ID switch (o pérdida de track),
extraer el frame a disco y reportar:
  - ¿Cuántas personas detecta YOLO sin tracker?
  - ¿En qué posición está cada una?
  - ¿Cuál es el área de bbox del track principal antes/después?
"""
import json
from pathlib import Path

import cv2
from ultralytics import YOLO

GALERIA = Path.home() / "Desktop" / "Galeria"
OUT = Path("/tmp/galeria_report/diagnostico")
OUT.mkdir(parents=True, exist_ok=True)

# Casos a diagnosticar (de los logs v3, total 12 frames x 3 deltas = 36 muestras)
CASOS = [
    ("Americana/AlumnaAmericana.mov", [98, 148, 164], "Alumno"),
    ("Americana/MaestroAmericana.mov", [648, 650], "Maestro"),
    ("Llave de Brazo/ProfLlavebRAZO.mov", [1522, 1546], "Maestro"),
    ("Escape 100 kg/Maestro.mp4", [688, 716, 734], "Maestro"),
    ("Llave de Brazo/ArmbarStudent.mov", [124, 156], "Alumno"),
]


def analizar(video_rel: str, frames: list[int], rol: str) -> dict:
    video = GALERIA / video_rel
    model = YOLO(str(Path(__file__).resolve().parents[1] / "yolo26n-pose.pt"))
    cap = cv2.VideoCapture(str(video))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    info = {
        "video": video_rel,
        "rol": rol,
        "total_frames": total,
        "resolucion": f"{width}x{height}",
        "frames": [],
    }

    for f_idx in frames:
        for delta in [-10, 0, 10]:
            target = max(0, min(total - 1, f_idx + delta))
            cap.set(cv2.CAP_PROP_POS_FRAMES, target)
            ok, frame = cap.read()
            if not ok:
                continue
            out_img = OUT / f"{video.stem}_f{target}_{rol}.jpg"
            cv2.imwrite(str(out_img), frame)

            results = model.predict(frame, imgsz=416, conf=0.10, verbose=False)
            n_personas = 0
            bboxes = []
            if results and results[0].boxes is not None:
                for box in results[0].boxes:
                    if int(box.cls) == 0:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        area = (x2 - x1) * (y2 - y1)
                        bboxes.append(
                            {
                                "xyxy": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                                "area": round(area, 1),
                                "area_pct": round(area / max(1, width * height) * 100, 2),
                                "conf": round(float(box.conf), 4),
                            }
                        )
                        n_personas += 1

            info["frames"].append(
                {
                    "switch_ref": f_idx,
                    "delta": delta,
                    "frame_idx": target,
                    "img_path": str(out_img),
                    "n_personas_yolo": n_personas,
                    "bboxes": bboxes,
                    "es_negro": bool(frame.mean() < 5),
                }
            )

    cap.release()
    return info


def main():
    resultados = []
    for video, frames, rol in CASOS:
        print(f"\n=== {video} ({rol}) — switches {frames} ===", flush=True)
        try:
            r = analizar(video, frames, rol)
            for f in r["frames"]:
                areas = [b["area_pct"] for b in f["bboxes"]]
                confs = [b["conf"] for b in f["bboxes"]]
                print(
                    f"  ref={f['switch_ref']:5d} (delta={f['delta']:+3d}) frame={f['frame_idx']:5d} "
                    f"| personas={f['n_personas_yolo']} | areas%={areas} | confs={confs} "
                    f"| negro={f['es_negro']} | img={f['img_path']}",
                    flush=True,
                )
            resultados.append(r)
        except Exception as e:
            print(f"ERROR: {e}", flush=True)
            resultados.append({"video": video, "error": str(e)})

    (OUT / "diagnostico.json").write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] {OUT / 'diagnostico.json'}", flush=True)


if __name__ == "__main__":
    main()
