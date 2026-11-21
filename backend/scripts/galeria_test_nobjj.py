#!/usr/bin/env python3
"""Verifica que los 3 videos de Nobjj sean rechazados por el clasificador visual de Jiu-Jitsu."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpocmente.application.services.jiujitsu_classifier import clasificar_video_jiujitsu
from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter

GALERIA = Path.home() / "Desktop" / "Galeria"
OUT = Path("/tmp/galeria_report")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    vlm_adapter = LocalVLMAdapter()
    results = []
    for v in sorted((GALERIA / "Nobjj").glob("*")):
        if v.suffix.lower() not in (".mov", ".mp4"):
            continue
        clf = clasificar_video_jiujitsu(v, vlm_adapter=vlm_adapter, n_frames=6)
        results.append({"video": v.name, **clf})
        print(f"\n=== {v.name} ===", flush=True)
        print(json.dumps(clf, indent=2, ensure_ascii=False), flush=True)
    (OUT / "nobjj.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

    rechazados = sum(1 for r in results if not r["es_jiujitsu"])
    print(f"\n[VEREDICTO] Rechazados correctamente: {rechazados}/{len(results)}")


if __name__ == "__main__":
    main()
