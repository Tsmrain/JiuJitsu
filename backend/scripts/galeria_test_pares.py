#!/usr/bin/env python3
"""Test de comparación biomecánica profesor vs alumno para 5 pares reales en ~/Desktop/Galeria."""
import json
import shutil
import subprocess
import sys
import threading
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


class ThermalMonitor:
    def __init__(self, interval_s: float = 1.0):
        self.samples = []
        self._stop = False
        self._interval = interval_s
        self._t = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._t.start()

    def _run(self):
        while not self._stop:
            try:
                out = subprocess.check_output(["pmset", "-g", "therm"], text=True, timeout=2)
                ts = round(time.time(), 2)
                presion = "warning" if "warning" in out.lower() and "no thermal warning" not in out.lower() else "nominal"
                self.samples.append({"t": ts, "presion": presion, "raw": out.strip()})
            except Exception:
                pass
            time.sleep(self._interval)

    def stop(self):
        self._stop = True
        self._t.join(timeout=2)
        return self.samples


def _sample_powermetrics() -> str:
    try:
        out = subprocess.check_output(
            ["sudo", "-n", "powermetrics", "--samplers", "smc", "-n", "1", "-i", "1000"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
        )
        lines = [ln for ln in out.splitlines() if any(k in ln.lower() for k in ("temp", "power", "gpu"))]
        return "\n".join(lines).strip() or "no disponible"
    except Exception:
        return "no disponible (sudo -n powermetrics requiere contraseña)"


def _flush_mps():
    if hasattr(torch, "mps") and torch.backends.mps.is_available():
        try:
            torch.mps.synchronize()
            torch.mps.empty_cache()
        except Exception:
            pass


def main():
    results = []
    thermal_lines = [f"[POWERMETRICS ANTES]\n{_sample_powermetrics()}\n"]

    for maestro_rel, alumno_rel, tecnica in PARES:
        maestro = GALERIA / maestro_rel
        alumno = GALERIA / alumno_rel
        cid = str(uuid.uuid4())
        print(f"\n=== {tecnica} (cid={cid}) ===", flush=True)
        mon = ThermalMonitor(interval_s=1.0)
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
            mon.start()
            try:
                procesar_comparacion_video_a_video(
                    comparacion_id=cid,
                    tecnica_id=tecnica,
                    idioma="es",
                    persona_idx_alumno=0,
                    persona_idx_maestro=0,
                    token="dev_token",
                )
            finally:
                samples = mon.stop()
            dt = time.time() - t0
            data = obtener_comparacion(cid, token="dev_token") or {}
            presiones = [s["presion"] for s in samples]
            thermal_lines.append(
                f"[THERMAL {tecnica}] muestras={len(samples)} warning_count={presiones.count('warning')} nominal_count={presiones.count('nominal')}\n"
                + (samples[-1]["raw"] if samples else "sin muestras")
                + "\n"
            )
            print(f"[THERMAL] {len(samples)} muestras durante {tecnica} (warning={presiones.count('warning')}, nominal={presiones.count('nominal')})", flush=True)

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

    thermal_lines.append(f"[POWERMETRICS DESPUES]\n{_sample_powermetrics()}\n")
    (OUT / "thermal.log").write_text("\n".join(thermal_lines), encoding="utf-8")
    (OUT / "pares_v2.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] {OUT / 'pares_v2.json'} y {OUT / 'thermal.log'}")


if __name__ == "__main__":
    main()
