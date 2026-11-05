#!/usr/bin/env python3
"""
Contexto.py — Genera un archivo Markdown con el contexto completo de tu proyecto.

Escanea el directorio del proyecto, filtra directorios irrelevantes
(venv, .venv, node_modules, __pycache__, .git, dist-info, etc.) y archivos
binarios, y produce un .md con:
  1. Estructura jerárquica de los archivos incluidos.
  2. Contenido completo de cada archivo en bloques de código.

El .md resultante se puede pasar directamente como prompt/contexto a un
agente de IA (Claude, GPT, Cursor, Cline, etc.).

Uso:
    python Contexto.py
    python Contexto.py --root ./mi_proyecto --output contexto.md
    python Contexto.py --max-size 1000          # límite por archivo en KB
"""

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Filtros de directorios
# ─────────────────────────────────────────────────────────────────────────────

EXCLUDED_DIRS = {
    "__pycache__", ".git", ".hg", ".svn", ".idea", ".vscode",
    "venv", ".venv", "env", ".env", "virtualenv", "ENV",
    "node_modules", "dist", "build", ".eggs", ".tox",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache",
    "site-packages", ".next", ".nuxt", ".svelte-kit",
    "coverage", "htmlcov", ".nyc_output",
    "target", "obj", ".gradle", ".mvn",
    "bin", "out", "__MACOSX",
    ".terraform", ".serverless",
    # Carpetas de datos, modelos, temporales y assets pesados
    "data", "storage", "runs", "venv_mlx", "documentos_word",
}

EXCLUDED_DIR_SUFFIXES = (".dist-info", ".egg-info", ".egg", ".framework")

# Archivos concretos a excluir (lockfiles grandes, sistema)
EXCLUDED_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock", "Cargo.lock", "composer.lock",
    "Gemfile.lock", "go.sum", "packages.lock.json",
    ".DS_Store", "Thumbs.db",
}

# ─────────────────────────────────────────────────────────────────────────────
# Extensiones incluidas / excluidas
# ─────────────────────────────────────────────────────────────────────────────

INCLUDED_EXTENSIONS = {
    # Python
    ".py", ".pyi", ".pyx",
    # JS / TS
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts",
    # Web
    ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".vue", ".svelte",
    # Datos / config
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".xml", ".env",
    # Docs
    ".md", ".rst", ".txt",
    # Shell
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
    # DB
    ".sql", ".graphql", ".gql",
    # Otros lenguajes
    ".java", ".kt", ".kts", ".go", ".rs", ".rb", ".php",
    ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx",
    ".cs", ".swift", ".m", ".mm",
    ".r", ".jl", ".lua", ".pl", ".ex", ".exs",
    ".dart", ".scala", ".clj", ".cljs", ".hs", ".elm",
    # Infra
    ".tf", ".tfvars", ".dockerfile",
    # Notebooks
    ".ipynb",
}

INCLUDED_FILENAMES = {
    "Dockerfile", "Makefile", "Procfile", "README", "LICENSE",
    "requirements.txt", "requirements-dev.txt",
    "Pipfile", "pyproject.toml", "setup.py", "setup.cfg",
    ".gitignore", ".dockerignore", ".gitattributes",
    ".env", ".env.example", ".env.local", ".env.template",
    "package.json", "tsconfig.json",
    ".babelrc", ".eslintrc", ".prettierrc", ".editorconfig",
    "docker-compose.yml", "docker-compose.yaml",
}

EXCLUDED_EXTENSIONS = {
    # Modelos y pesos de IA
    ".pt", ".pth", ".onnx", ".engine", ".tflite", ".bin", ".safetensors", ".gguf",
    # Binarios compilados
    ".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".exe",
    ".a", ".o", ".obj", ".lib",
    # Imágenes
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".webp",
    ".svg", ".tiff", ".tif",
    # Documentos
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    # Comprimidos
    ".zip", ".tar", ".gz", ".bz2", ".rar", ".7z", ".xz", ".zst",
    # Media
    ".mp3", ".mp4", ".avi", ".mov", ".wav", ".flac", ".ogg", ".webm",
    # Fuentes
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    # Bases de datos
    ".sqlite", ".db", ".sqlite3",
    # Compilados tzdata / lock
    ".lock", ".tab", ".zi",
}

# ─────────────────────────────────────────────────────────────────────────────
# Detección de venvs
# ─────────────────────────────────────────────────────────────────────────────

def is_venv(path: Path) -> bool:
    """Detecta si un directorio es un entorno virtual Python."""
    try:
        if (path / "pyvenv.cfg").exists():
            return True
        if (path / "Scripts" / "activate.bat").exists():
            return True
        if (path / "bin" / "activate").exists() and (path / "lib").exists():
            return True
    except (OSError, PermissionError):
        pass
    return False


def should_skip_dir(path: Path, name: str) -> bool:
    if name in EXCLUDED_DIRS:
        return True
    if name.startswith("."):
        return True
    if any(name.endswith(s) for s in EXCLUDED_DIR_SUFFIXES):
        return True
    if is_venv(path):
        return True
    return False


def should_include_file(path: Path, excluded_paths: frozenset = frozenset()) -> bool:
    if str(path.resolve()) in excluded_paths:
        return False
    name = path.name
    ext = path.suffix.lower()
    if name in EXCLUDED_FILES:
        return False
    if ext in EXCLUDED_EXTENSIONS:
        return False
    if name in INCLUDED_FILENAMES:
        return True
    if ext in INCLUDED_EXTENSIONS:
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Lectura y recolección
# ─────────────────────────────────────────────────────────────────────────────

def read_file_safe(path: Path, max_size: int) -> str:
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > max_size:
        return f"<!-- Archivo omitido: {size:,} bytes > límite de {max_size:,} bytes -->"
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return None
    except (OSError, PermissionError):
        return None


def collect_files(root: Path, excluded_paths: frozenset = frozenset()) -> list:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = sorted(d for d in dirnames if not should_skip_dir(current / d, d))
        for filename in sorted(filenames):
            full = current / filename
            if should_include_file(full, excluded_paths):
                files.append(full)
    return files


# ─────────────────────────────────────────────────────────────────────────────
# Árbol jerárquico
# ─────────────────────────────────────────────────────────────────────────────

def build_tree(root: Path, files: list) -> str:
    """Construye un árbol con únicamente los archivos que se incluirán."""
    tree = defaultdict(lambda: {"dirs": set(), "files": []})

    for f in files:
        rel = f.relative_to(root)
        parent_parts = rel.parent.parts if str(rel.parent) != "." else ()
        tree[parent_parts]["files"].append(rel.name)
        for i in range(len(parent_parts)):
            tree[parent_parts[:i]]["dirs"].add(parent_parts[i])

    lines = [(root.name or str(root)) + "/"]

    def render(parts, prefix=""):
        node = tree[parts]
        entries = ([(d, True) for d in sorted(node["dirs"])]
                   + [(f, False) for f in sorted(node["files"])])
        for i, (name, is_dir) in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + name + ("/" if is_dir else ""))
            if is_dir:
                render(parts + (name,), prefix + ("    " if is_last else "│   "))

    render(())
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Syntax highlighting para los bloques de código
# ─────────────────────────────────────────────────────────────────────────────

LANG_MAP = {
    "py": "python", "pyi": "python", "pyx": "cython",
    "js": "javascript", "jsx": "jsx", "mjs": "javascript", "cjs": "javascript",
    "ts": "typescript", "tsx": "tsx", "mts": "typescript", "cts": "typescript",
    "html": "html", "htm": "html", "css": "css", "scss": "scss",
    "sass": "sass", "less": "less",
    "json": "json", "yaml": "yaml", "yml": "yaml", "toml": "toml",
    "ini": "ini", "cfg": "ini", "conf": "conf",
    "md": "markdown", "rst": "rst", "txt": "text",
    "sh": "bash", "bash": "bash", "zsh": "bash",
    "ps1": "powershell", "bat": "batch", "cmd": "batch",
    "sql": "sql", "graphql": "graphql", "gql": "graphql",
    "java": "java", "kt": "kotlin", "kts": "kotlin",
    "go": "go", "rs": "rust", "rb": "ruby", "php": "php",
    "c": "c", "cpp": "cpp", "cc": "cpp", "cxx": "cpp",
    "h": "c", "hpp": "cpp", "hxx": "cpp",
    "cs": "csharp", "swift": "swift",
    "xml": "xml", "vue": "vue", "svelte": "svelte",
    "dockerfile": "dockerfile", "tf": "hcl", "tfvars": "hcl",
    "ipynb": "json", "env": "bash",
}


# ─────────────────────────────────────────────────────────────────────────────
# Generación del Markdown final
# ─────────────────────────────────────────────────────────────────────────────

def generate_markdown(root: Path, files: list, max_size: int) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(files)

    out = [
        f"# Contexto del Proyecto: `{root.name}`",
        "",
        f"- **Generado:** {timestamp}",
        f"- **Raíz:** `{root.resolve()}`",
        f"- **Archivos incluidos:** {total}",
        "",
        "> Este documento contiene el contexto completo del proyecto para ser "
        "utilizado por un agente de IA.",
        "",
        "---",
        "",
        "## 📁 Estructura del proyecto",
        "",
        "```",
        build_tree(root, files),
        "```",
        "",
        "---",
        "",
        "## 📄 Contenido de los archivos",
        "",
    ]

    included = 0
    for filepath in files:
        content = read_file_safe(filepath, max_size)
        if content is None:
            continue
        included += 1
        rel = filepath.relative_to(root)
        ext = filepath.suffix.lstrip(".").lower()
        lang = LANG_MAP.get(ext, ext or "text")

        out.append(f"### `{rel}`")
        out.append("")
        out.append(f"```{lang}")
        out.append(content.rstrip("\n"))
        out.append("```")
        out.append("")

    out.append("---")
    out.append("")
    out.append(f"*Fin del contexto. {included} archivos incluidos.*")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Genera un .md con el contexto completo del proyecto para un agente de IA."
    )
    parser.add_argument("--root", "-r", default=".",
                        help="Directorio raíz del proyecto (default: actual).")
    parser.add_argument("--output", "-o", default=None,
                        help="Archivo .md de salida (default: <root>/contexto_proyecto.md).")
    parser.add_argument("--max-size", "-m", type=int, default=500,
                        help="Tamaño máximo por archivo en KB (default: 500).")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"Error: '{root}' no existe o no es un directorio.", file=sys.stderr)
        sys.exit(1)

    output = Path(args.output).resolve() if args.output else root / "contexto_proyecto.md"
    max_size = args.max_size * 1024

    print(f"🔍 Escaneando: {root}")
    files = collect_files(root, excluded_paths=frozenset({str(output)}))
    print(f"📄 Archivos detectados: {len(files)}")

    if not files:
        print("⚠️  No se encontraron archivos válidos para incluir.", file=sys.stderr)
        sys.exit(1)

    print("📝 Generando Markdown...")
    md = generate_markdown(root, files, max_size)

    output.write_text(md, encoding="utf-8")
    size_kb = output.stat().st_size / 1024

    print()
    print(f"✅ Archivo generado: {output}")
    print(f"   Tamaño:            {size_kb:.1f} KB")
    print(f"   Archivos:          {len(files)}")


if __name__ == "__main__":
    main()