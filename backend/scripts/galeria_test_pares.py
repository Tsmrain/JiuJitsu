#!/usr/bin/env python3
"""Test de comparación biomecánica profesor vs alumno para 5 pares reales en ~/Desktop/Galeria."""
import json
import shutil
import sys
import time
import uuid
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpocmente.application.services.video_comparison_service import (
    crear_comparacion,
    obtener_comparacion,
    procesar_comparacion_video_a_video,
    rutas_comparacion,
)

GALERIA = Path.home() / "Desktop" / "Galeria"
OUT = Path("/tmp/galeria_report")
OUT.mkdir(parents=True, exist_ok=True)

PARES = [
    ("Americana/MaestroAmericana.mov", "Americana/AlumnaAmericana.mov", "Americana"),
    ("Escape 100 kg/Maestro.mp4", "Escape 100 kg/Alumno.mp4", "Escape100kg"),
    (
        "Escape de Guardia/profesor salida de Guardia Parandose.mp4",
        "Escape de Guardia/AlumnoSalida.mov",
        "EscapeGuardia",
    ),
    ("Llave de Brazo/ProfLlavebRAZO.mov", "Llave de Brazo/AlumLlaveBrazo.mov", "Armbar_A"),
    ("Llave de Brazo/ProfLlavebRAZO.mov", "Llave de Brazo/ArmbarStudent.mov", "Armbar_B"),
]


def _flush_mps():
    if hasattr(torch, "mps") and torch.backends.mps.is_available():
        try:
            torch.mps.synchronize()
            torch.mps.empty_cache()
        except Exception:
            pass


def main():
    results = []
    for maestro_rel, alumno_rel, tecnica in PARES:
        maestro = GALERIA / maestro_rel
        alumno = GALERIA / alumno_rel
        cid = str(uuid.uuid4())
        print(f"\n=== {tecnica} (cid={cid}) ===", flush=True)
        try:
            pa, pm, pout = rutas_comparacion(cid)
            pa.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(alumno, pa)
            shutil.copy(maestro, pm)
            crear_comparacion(
                comparacion_id=cid,
                tecnica_id=tecnica,
                idioma="es",
                persona_idx_alumno=0,
                persona_idx_maestro=0,
                alumno_id="test_galeria",
                token="dev_token",
                video_alumno_nombre=alumno.name,
                video_maestro_nombre=maestro.name,
            )
            t0 = time.time()
            procesar_comparacion_video_a_video(
                comparacion_id=cid,
                tecnica_id=tecnica,
                idioma="es",
                persona_idx_alumno=0,
                persona_idx_maestro=0,
                token="dev_token",
            )
            dt = time.time() - t0
            data = obtener_comparacion(cid, token="dev_token") or {}
            r = {
                "tecnica": tecnica,
                "maestro": maestro_rel,
                "alumno": alumno_rel,
                "comparacion_id": cid,
                "estado": data.get("estado"),
                "score_similitud": data.get("score_similitud"),
                "dtw_distance": data.get("dtw_distance"),
                "dtw_normalizado": data.get("dtw_normalizado"),
                "frame_alumno_critico": data.get("frame_alumno_critico"),
                "frame_maestro_critico": data.get("frame_maestro_critico"),
                "articulaciones_criticas": data.get("articulaciones_criticas"),
                "error_message": data.get("error_message"),
                "tiempo_total_s": round(dt, 2),
                "video_output_existe": pout.exists(),
                "video_output_path": str(pout) if pout.exists() else None,
            }
            print(json.dumps(r, indent=2, ensure_ascii=False), flush=True)
            results.append(r)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR en {tecnica}: {e}", flush=True)
            results.append({"tecnica": tecnica, "error": str(e)})
        _flush_mps()

    (OUT / "pares.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n[OK] {OUT / 'pares.json'}")


if __name__ == "__main__":
    main()
