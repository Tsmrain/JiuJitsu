# scripts/render_sistema_completo.py
# -*- coding: utf-8 -*-
"""
Renderiza los 3 diagramas consolidados del sistema completo a PNG desde
docs/diagramas/codigo/ hacia docs/diagramas/.
"""

import sys
from pathlib import Path

from generate_plantuml_diagrams import OUTPUT_DIR, SOURCE_DIR, render_plantuml

CONSOLIDATED_STEMS = [
    "sistema_completo_actividad",
    "sistema_completo_casos_uso",
    "sistema_completo_clases",
]


def main():
    exitos = 0
    for stem in CONSOLIDATED_STEMS:
        src = SOURCE_DIR / f"{stem}.puml"
        if not src.exists():
            print(f"Falta archivo fuente: {src}")
            sys.exit(1)
        code = src.read_text(encoding="utf-8")
        out_path = OUTPUT_DIR / f"{stem}.png"
        if render_plantuml(stem, code, out_path):
            exitos += 1

    print(f"\nTotal renderizados: {exitos} de {len(CONSOLIDATED_STEMS)}")
    if exitos != len(CONSOLIDATED_STEMS):
        sys.exit(1)


if __name__ == "__main__":
    main()
