# scripts/generate_plantuml_diagrams.py
# -*- coding: utf-8 -*-
"""
Renderiza todos los diagramas fuente (*.puml y *.mmd) ubicados en
docs/diagramas/codigo/ hacia imágenes PNG en docs/diagramas/
utilizando Kroki (PlantUML y Mermaid) con respaldo oficial.
"""

import base64
import json
import sys
import urllib.request
import zlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT_DIR / "docs" / "diagramas" / "codigo"
OUTPUT_DIR = ROOT_DIR / "docs" / "diagramas"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "Content-Type": "text/plain; charset=utf-8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
}


def _is_valid_png(data: bytes) -> bool:
    return data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) > 500


def render_plantuml(name: str, puml_code: str, out_path: Path) -> bool:
    try:
        req = urllib.request.Request(
            "https://kroki.io/plantuml/png",
            data=puml_code.encode("utf-8"),
            headers=HEADERS,
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            png_bytes = response.read()
            if not _is_valid_png(png_bytes):
                raise ValueError("Respuesta no es un PNG válido")
            out_path.write_bytes(png_bytes)
            print(f"  [OK Kroki PlantUML] {name}.png ({len(png_bytes)} bytes)")
            return True
    except Exception as e:
        print(f"  [Fallback PlantUML para {name}: {e}]")

    try:
        compressed = zlib.compress(puml_code.encode("utf-8"))[2:-4]
        mapping = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
        res = []
        for i in range(0, len(compressed), 3):
            b1 = compressed[i]
            b2 = compressed[i + 1] if i + 1 < len(compressed) else 0
            b3 = compressed[i + 2] if i + 2 < len(compressed) else 0
            res.append(mapping[b1 >> 2])
            res.append(mapping[((b1 & 0x3) << 4) | (b2 >> 4)])
            res.append(mapping[((b2 & 0xF) << 2) | (b3 >> 6)])
            res.append(mapping[b3 & 0x3F])
        encoded = "".join(res)
        url = f"http://www.plantuml.com/plantuml/png/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=30) as response:
            png_bytes = response.read()
            if not _is_valid_png(png_bytes):
                raise ValueError("Fallback no devolvió un PNG válido")
            out_path.write_bytes(png_bytes)
            print(f"  [OK PlantUML Fallback] {name}.png ({len(png_bytes)} bytes)")
            return True
    except Exception as e2:
        print(f"  [ERROR PlantUML {name}]: {e2}")
        return False


def render_mermaid(name: str, mmd_code: str, out_path: Path) -> bool:
    try:
        req = urllib.request.Request(
            "https://kroki.io/mermaid/png",
            data=mmd_code.encode("utf-8"),
            headers=HEADERS,
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            png_bytes = response.read()
            if not _is_valid_png(png_bytes):
                raise ValueError("Respuesta no es un PNG válido")
            out_path.write_bytes(png_bytes)
            print(f"  [OK Kroki Mermaid] {name}.png ({len(png_bytes)} bytes)")
            return True
    except Exception as e:
        print(f"  [Fallback Mermaid para {name}: {e}]")

    try:
        payload = json.dumps({"code": mmd_code, "mermaid": {"theme": "default"}}).encode("utf-8")
        encoded = base64.urlsafe_b64encode(payload).decode("ascii")
        url = f"https://mermaid.ink/img/{encoded}?type=png"
        req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=30) as response:
            png_bytes = response.read()
            if not _is_valid_png(png_bytes):
                raise ValueError("mermaid.ink no devolvió un PNG válido")
            out_path.write_bytes(png_bytes)
            print(f"  [OK mermaid.ink Fallback] {name}.png ({len(png_bytes)} bytes)")
            return True
    except Exception as e2:
        print(f"  [ERROR Mermaid {name}]: {e2}")
        return False


def main():
    if not SOURCE_DIR.exists():
        print(f"No existe el directorio fuente {SOURCE_DIR}")
        sys.exit(1)

    sources = sorted(
        p for p in SOURCE_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".puml", ".mmd"}
    )
    if len(sys.argv) > 1:
        filters = set(sys.argv[1:])
        sources = [p for p in sources if p.stem in filters]
    if not sources:
        print(f"No se encontraron diagramas en {SOURCE_DIR}")
        sys.exit(1)

    print(f"Renderizando {len(sources)} diagramas desde {SOURCE_DIR} -> {OUTPUT_DIR} ...")
    exitos = 0
    for src in sources:
        code = src.read_text(encoding="utf-8")
        out_path = OUTPUT_DIR / f"{src.stem}.png"
        if src.suffix.lower() == ".puml":
            ok = render_plantuml(src.stem, code, out_path)
        else:
            ok = render_mermaid(src.stem, code, out_path)
        if ok:
            exitos += 1

    print(f"\nTotal renderizados: {exitos} de {len(sources)}")
    if exitos != len(sources):
        sys.exit(1)


if __name__ == "__main__":
    main()
