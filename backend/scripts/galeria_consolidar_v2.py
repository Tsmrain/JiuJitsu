#!/usr/bin/env python3
"""Consolida resultados v2 en REPORT_v2.txt sin edición manual."""
import json
from pathlib import Path

OUT = Path("/tmp/galeria_report")
lines = []


def add(title, content):
    lines.append(f"\n===== {title} =====\n")
    lines.append(content if isinstance(content, str) else json.dumps(content, indent=2, ensure_ascii=False))


pares_v1_path = OUT / "pares_v1.json"
if not pares_v1_path.exists():
    pares_v1_path = OUT / "pares.json"

add("INVENTORY", (OUT / "inventory.txt").read_text(encoding="utf-8"))
add("INDIVIDUAL_V1", (OUT / "individual.json").read_text(encoding="utf-8"))
add("PARES_V1", pares_v1_path.read_text(encoding="utf-8"))
add("PARES_V2", (OUT / "pares_v2.json").read_text(encoding="utf-8"))
add("NOBJJ", (OUT / "nobjj.json").read_text(encoding="utf-8"))
add("THERMAL", (OUT / "thermal.log").read_text(encoding="utf-8") if (OUT / "thermal.log").exists() else "NO DISPONIBLE")

(OUT / "REPORT_v2.txt").write_text("".join(lines), encoding="utf-8")
print(f"[OK] {OUT / 'REPORT_v2.txt'}")
