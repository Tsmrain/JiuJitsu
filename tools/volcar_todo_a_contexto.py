#!/usr/bin/env python3
"""
Vuelca TODO el contenido de los archivos de texto/código del proyecto
dentro de docs/CONTEXTO_ARQUITECTURA_QWEN.md, respetando la estructura
de carpetas. Además lista los binarios referenciados (vídeos, iconos,
comprimidos) sin volcar sus bytes.

Uso:
    python3 scripts/volcar_todo_a_contexto.py
    python3 scripts/volcar_todo_a_contexto.py --root . --out docs/CONTEXTO_ARQUITECTURA_QWEN.md
"""

import argparse
import os
from collections import Counter
from pathlib import Path

# --- Configuración ---------------------------------------------------------

# Carpetas que NO queremos recorrer (ruido, binarios, artefactos)
EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
}

# Extensiones consideradas texto/código legible
TEXT_EXTS = {
    # Python
    ".py", ".pyi", ".pyx",
    # JS / TS
    ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
    # Web
    ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".svg", ".xml",
    # Datos / config
    ".json", ".jsonc", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".csv", ".tsv",
    # Docs
    ".md", ".rst", ".txt", ".log",
    # SQL / shell
    ".sql", ".sh", ".bash", ".zsh", ".fish",
    # Notebooks
    ".ipynb",
    # Otros lenguajes
    ".java", ".kt", ".go", ".rs", ".rb", ".php",
    ".c", ".h", ".cpp", ".hpp",
    ".swift", ".m", ".mm",
    ".r", ".R", ".jl",
    # Docker / env
    ".dockerfile", ".env",
}

# Nombres exactos que queremos incluir aunque no tengan extensión
INCLUDE_NAMES = {
    "Dockerfile", "dockerfile",
    "Makefile", "makefile",
    "README", "LICENSE", "NOTICE",
    ".gitignore", ".dockerignore", ".env", ".env.example",
    "requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "setup.cfg",
    "package.json", "package-lock.json", "yarn.lock",
    "pytest.ini", "tox.ini", "mypy.ini",
}

# Archivos concretos que NO queremos volcar
EXCLUDE_FILES = {
    "CONTEXTO_ARQUITECTURA_QWEN.md",  # el propio output
    "tree.txt",                        # el árbol
}

# Extensiones binarias que solo referenciamos (no volcamos)
BIN_EXTS = {
    ".mp4", ".mov", ".avi", ".webm", ".mkv",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
    ".gz", ".zip", ".tar", ".tgz", ".bz2", ".xz", ".7z",
    ".pdf", ".woff", ".woff2", ".ttf", ".eot",
    ".pyc", ".pyo", ".so", ".dll", ".dylib", ".exe",
    ".db", ".sqlite", ".sqlite3",
}

# Tamaño máximo por archivo (bytes) para evitar volcar cosas enormes
MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MB

# --- Utilidades ------------------------------------------------------------

def debe_excluir_dir(name: str) -> bool:
    return name in EXCLUDE_DIRS or name.startswith(".")

def es_texto(path: Path) -> bool:
    if path.name in INCLUDE_NAMES:
        return True
    if path.suffix.lower() in TEXT_EXTS:
        return True
    return False

def es_binario(path: Path) -> bool:
    return path.suffix.lower() in BIN_EXTS

def debe_excluir_archivo(path: Path) -> bool:
    if path.name in EXCLUDE_FILES:
        return True
    try:
        if path.stat().st_size > MAX_FILE_BYTES and not es_binario(path):
            return True
    except OSError:
        return True
    return False

def leer_texto(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return None
    except Exception:
        return None

def fence_para(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    mapping = {
        "py": "python", "pyi": "python",
        "js": "javascript", "mjs": "javascript", "cjs": "javascript",
        "ts": "typescript", "tsx": "tsx", "jsx": "jsx",
        "html": "html", "htm": "html",
        "css": "css", "scss": "scss", "sass": "sass", "less": "less",
        "json": "json", "jsonc": "jsonc",
        "yaml": "yaml", "yml": "yaml",
        "toml": "toml", "ini": "ini", "cfg": "ini", "conf": "conf",
        "md": "markdown", "rst": "rst", "txt": "text",
        "sql": "sql",
        "sh": "bash", "bash": "bash", "zsh": "bash", "fish": "fish",
        "ipynb": "json",
        "xml": "xml", "svg": "xml",
        "csv": "csv", "tsv": "tsv",
        "java": "java", "kt": "kotlin",
        "go": "go", "rs": "rust", "rb": "ruby", "php": "php",
        "c": "c", "h": "c", "cpp": "cpp", "hpp": "cpp",
        "swift": "swift", "m": "objectivec", "mm": "objectivec",
        "r": "r", "jl": "julia",
    }
    if path.name in ("Dockerfile", "dockerfile"):
        return "dockerfile"
    return mapping.get(ext, "")

def humano(bytes_: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}" if unit != "B" else f"{bytes_} B"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"

# --- Recorrido -------------------------------------------------------------

def recorrer(root: Path):
    """Devuelve (archivos_texto, archivos_binarios) ordenados."""
    textos, binarios = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not debe_excluir_dir(d))
        for fname in sorted(filenames):
            p = Path(dirpath) / fname
            if debe_excluir_archivo(p):
                continue
            if es_texto(p):
                textos.append(p)
            elif es_binario(p):
                binarios.append(p)
    return textos, binarios

# --- Volcado ---------------------------------------------------------------

def escribir_contexto(root: Path, out: Path):
    textos, binarios = recorrer(root)
    total = len(textos)

    with out.open("w", encoding="utf-8") as f:
        f.write("# CONTEXTO ARQUITECTURA QWEN\n\n")
        f.write(f"> Proyecto: `{root.resolve()}`\n")
        f.write(f"> Archivos de texto/código volcados: **{total}**\n")
        f.write(f"> Binarios referenciados (no volcados): **{len(binarios)}**\n")
        f.write(f"> Generado automáticamente por `scripts/volcar_todo_a_contexto.py`\n\n")

        # Contadores por extensión
        exts = Counter((p.suffix.lower() or "<sin_ext>") for p in textos)
        f.write("## Resumen por extensión\n\n")
        for e, n in sorted(exts.items(), key=lambda kv: (-kv[1], kv[0])):
            f.write(f"- `{e:14}` {n}\n")
        f.write("\n---\n\n")

        # Índice
        f.write("## Índice de archivos de texto/código\n\n")
        for p in textos:
            rel = p.relative_to(root).as_posix()
            f.write(f"- `{rel}`\n")
        f.write("\n---\n\n")

        # Contenido
        for i, p in enumerate(textos, 1):
            rel = p.relative_to(root).as_posix()
            f.write(f"\n## [{i}/{total}] `{rel}`\n\n")

            contenido = leer_texto(p)
            if contenido is None:
                f.write("_No se pudo leer como texto (posible binario o encoding desconocido)._\n")
                continue

            lang = fence_para(p)
            fence = "```"
            while fence in contenido:
                fence += "`"

            f.write(f"{fence}{lang}\n")
            f.write(contenido)
            if not contenido.endswith("\n"):
                f.write("\n")
            f.write(f"{fence}\n\n")

        # Binarios referenciados
        f.write("\n---\n\n")
        f.write("## Binarios referenciados (no volcados)\n\n")
        f.write("Estos archivos existen en el proyecto pero no se volcaron por ser binarios.\n")
        f.write("Se listan aquí para que Qwen sepa que existen.\n\n")
        for p in binarios:
            rel = p.relative_to(root).as_posix()
            try:
                size = p.stat().st_size
                f.write(f"- `{rel}` — {humano(size)}\n")
            except OSError:
                f.write(f"- `{rel}` — (no accesible)\n")

    print(f"[OK] Volcados {total} archivos de texto en {out}")
    print(f"[OK] Referenciados {len(binarios)} binarios")

# --- CLI -------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="Raíz del proyecto (default: .)")
    ap.add_argument(
        "--out",
        default="docs/CONTEXTO_ARQUITECTURA_QWEN.md",
        help="Archivo de salida (default: docs/CONTEXTO_ARQUITECTURA_QWEN.md)",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out = (root / args.out).resolve()

    if not root.is_dir():
        raise SystemExit(f"No existe la carpeta: {root}")

    out.parent.mkdir(parents=True, exist_ok=True)
    escribir_contexto(root, out)

if __name__ == "__main__":
    main()