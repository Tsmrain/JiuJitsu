#!/usr/bin/env python3
"""
Genera un único archivo con TODA la estructura y contenido del proyecto
para dárselo como contexto a un agente de IA.
"""
import os
import sys
from pathlib import Path

# ---------------- Configuración ----------------
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
OUTPUT = ROOT / "proyecto_contexto.md"

# Carpetas a excluir (por nombre)
EXCLUDE_DIRS = {
    ".git", ".hg", ".svn",
    "venv", ".venv", "env", ".env",
    "node_modules",
    "__pycache__",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".idea", ".vscode",
    "dist", "build", ".eggs",
    "site-packages",
    ".tox", ".cache",
    "lib64",  # el enlace simbólico de tu venv
}

# Archivos a excluir (por nombre exacto)
EXCLUDE_FILES = {
    "pyvenv.cfg",
    ".DS_Store",
    "proyecto_contexto.md",
    ".env",
}

# Extensiones binarias / pesadas a excluir
EXCLUDE_EXT = {
    ".pyc", ".pyo", ".pyd",
    ".so", ".dll", ".dylib",
    ".exe", ".bin", ".o", ".a",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".whl", ".egg",
    ".mp3", ".mp4", ".mov", ".avi",
    ".ttf", ".woff", ".woff2", ".eot",
    ".db", ".sqlite", ".sqlite3",
    ".lock",
}

# Límite por archivo (evita volcar archivos gigantes)
MAX_FILE_SIZE = 300_000  # 300 KB

# ---------------- Utilidades ----------------
def is_excluded_dir(name: str) -> bool:
    return name in EXCLUDE_DIRS

def is_excluded_file(name: str) -> bool:
    if name in EXCLUDE_FILES:
        return True
    return Path(name).suffix.lower() in EXCLUDE_EXT

def tree_lines(root: Path):
    """Genera un árbol tipo `tree` saltando exclusiones."""
    lines = []
    def walk(path: Path, prefix: str = ""):
        try:
            entries = sorted(
                [e for e in path.iterdir() if not (e.is_dir() and is_excluded_dir(e.name))
                 and not (e.is_file() and is_excluded_file(e.name))],
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except PermissionError:
            return
        for i, entry in enumerate(entries):
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = "    " if i == len(entries) - 1 else "│   "
                walk(entry, prefix + extension)
    lines.append(root.name + "/")
    walk(root)
    return lines

def lang_hint(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return {
        "py": "python", "pyi": "python",
        "js": "javascript", "ts": "typescript", "tsx": "tsx", "jsx": "jsx",
        "json": "json", "yaml": "yaml", "yml": "yaml", "toml": "toml",
        "md": "markdown", "txt": "text", "sh": "bash",
        "html": "html", "css": "css", "scss": "scss",
        "sql": "sql", "xml": "xml", "ini": "ini", "cfg": "ini",
        "rs": "rust", "go": "go", "java": "java", "c": "c", "cpp": "cpp",
        "h": "c", "hpp": "cpp", "rb": "ruby", "php": "php",
    }.get(ext, "")

def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # Modifica in-place para que os.walk no baje a excluidas
        dirnames[:] = [d for d in dirnames if not is_excluded_dir(d)]
        for fname in sorted(filenames):
            if is_excluded_file(fname):
                continue
            fpath = Path(dirpath) / fname
            try:
                if fpath.stat().st_size > MAX_FILE_SIZE:
                    yield fpath, None
                    continue
                # ¿Es texto?
                with open(fpath, "rb") as f:
                    raw = f.read()
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    yield fpath, None
                    continue
                yield fpath, text
            except (PermissionError, OSError):
                continue

# ---------------- Main ----------------
def main():
    print(f"📂 Proyecto: {ROOT}")
    with open(OUTPUT, "w", encoding="utf-8") as out:
        out.write(f"# Contexto del proyecto: {ROOT.name}\n\n")

        # 1) Estructura
        out.write("## Estructura de directorios\n\n```\n")
        out.write("\n".join(tree_lines(ROOT)))
        out.write("\n```\n\n")

        # 2) Contenido
        out.write("## Contenido de archivos\n\n")
        count = 0
        skipped = 0
        for fpath, text in iter_files(ROOT):
            rel = fpath.relative_to(ROOT)
            if text is None:
                out.write(f"### `{rel}`\n\n_(binario o demasiado grande, omitido)_\n\n")
                skipped += 1
                continue
            lang = lang_hint(fpath)
            out.write(f"### `{rel}`\n\n")
            out.write(f"```{lang}\n")
            out.write(text)
            if not text.endswith("\n"):
                out.write("\n")
            out.write("```\n\n")
            count += 1

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"✅ Generado: {OUTPUT}")
    print(f"   Archivos incluidos: {count}")
    print(f"   Omitidos (binarios/grandes): {skipped}")
    print(f"   Tamaño: {size_kb:.1f} KB")

if __name__ == "__main__":
    main()