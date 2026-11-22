#!/usr/bin/env python3
"""
Contexto.py — Genera un archivo Markdown con el contexto completo de tu proyecto.

Escanea el directorio del proyecto, filtra directorios irrelevantes
(venv, .venv, node_modules, __pycache__, .git, dist-info, etc.) y credenciales
sensibles (.env, client_secret_*), y produce un .md con:
  1. Historial reciente de commits y estado local de Git.
  2. Mapa completo del proyecto usando el comando `tree` (con pesos y activos
     no textuales como modelos .pt, diagramas .png y documentos .docx).
  3. Métricas cuantitativas por módulo y lenguaje/extensión.
  4. Árbol de archivos incluidos con líneas y tamaño por archivo.
  5. Contenido completo de cada archivo en bloques de código seguros.

El .md resultante se puede pasar directamente como prompt/contexto a un
agente de IA (Claude, GPT, Cursor, Cline, etc.).

Uso:
    python Contexto.py
    python Contexto.py --root ./mi_proyecto --output contexto.md
    python Contexto.py --max-size 1000          # límite por archivo en KB
"""

import argparse
import os
import re
import shutil
import subprocess
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
    # Carpetas de modelos/temporales pesados (se mantienen visibles en `tree`)
    "storage", "runs", "venv_mlx", "documentos_word", "datasets", "dataset",
}

EXCLUDED_DIR_SUFFIXES = (".dist-info", ".egg-info", ".egg", ".framework")

# Archivos concretos a excluir (lockfiles grandes, sistema, credenciales reales)
EXCLUDED_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock", "Cargo.lock", "composer.lock",
    "Gemfile.lock", "go.sum", "packages.lock.json",
    ".DS_Store", "Thumbs.db", ".env",
}

EXCLUDED_FILE_PREFIXES = ("client_secret_", "~$")

# Patrón base para `tree -I`: oculta entornos/cachés pesados y credenciales,
# pero preserva activos visibles importantes (storage, modelos .pt, .png, .docx).
TREE_IGNORE_PATTERNS = (
    ".git", ".hg", ".svn", ".idea", ".vscode",
    "node_modules", "venv", ".venv", "venv_mlx", "virtualenv", "ENV",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache",
    "dist", "build", "coverage", "htmlcov", "__MACOSX",
    "*.dist-info", "*.egg-info",
    ".DS_Store", "Thumbs.db", ".env", "client_secret_*", "~$*",
)

# ─────────────────────────────────────────────────────────────────────────────
# Extensiones incluidas / excluidas
# ─────────────────────────────────────────────────────────────────────────────

INCLUDED_EXTENSIONS = {
    # Python
    ".py", ".pyi", ".pyx", ".patched",
    # JS / TS
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts",
    # Web
    ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".vue", ".svelte",
    # Datos / config
    ".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".xml",
    # Docs y diagramas
    ".md", ".rst", ".txt", ".puml", ".mmd",
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
    ".env.example", ".env.template",
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
    if name in EXCLUDED_FILES or name.startswith(EXCLUDED_FILE_PREFIXES):
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
# Árbol jerárquico, comando `tree` y métricas
# ─────────────────────────────────────────────────────────────────────────────

def _format_size_kb(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    return f"{size_bytes / 1024:.1f} KB"


def get_system_tree_block(root: Path, excluded_output_name: str = "") -> list:
    """Ejecuta el comando `tree` del sistema (o un fallback) para mapear todo el disco."""
    ignore_items = list(TREE_IGNORE_PATTERNS)
    if excluded_output_name:
        ignore_items.append(excluded_output_name)
    ignore_expr = "|".join(ignore_items)

    tree_output = ""
    tree_cmd = shutil.which("tree")
    if tree_cmd:
        try:
            res = subprocess.run(
                [
                    tree_cmd, "-a", "--dirsfirst", "-h", "--du", "-F",
                    "-I", ignore_expr, str(root),
                ],
                capture_output=True, text=True, check=False, timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                tree_output = res.stdout.replace(str(root), root.name or str(root)).strip()
        except Exception:
            tree_output = ""

    if not tree_output:
        # Fallback puro en Python si `tree` no está instalado en el sistema
        all_paths = []
        skip_names = EXCLUDED_DIRS - {"storage"}
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            dirnames[:] = sorted(
                d for d in dirnames
                if d not in skip_names and not d.startswith(".")
                and not any(d.endswith(s) for s in EXCLUDED_DIR_SUFFIXES)
            )
            for fname in sorted(filenames):
                if (fname in EXCLUDED_FILES
                        or fname.startswith(EXCLUDED_FILE_PREFIXES)
                        or fname == excluded_output_name):
                    continue
                all_paths.append(current / fname)
        records = [{"rel": p.relative_to(root), "size": p.stat().st_size, "lines": None} for p in all_paths]
        tree_output = build_tree(root, records, show_metrics=False)

    return [
        "## 🌳 Mapa Completo en Disco (`tree` sin dependencias pesadas)",
        "",
        "> Incluye activos no textuales (pesos `.pt`/`.pkl`, imágenes `.png`/`.jpg`, `.docx`, `storage/`, etc.) omitidos en los bloques de código.",
        "",
        "```text",
        tree_output,
        "```",
        "",
        "---",
        "",
    ]


def build_tree(root: Path, records: list, show_metrics: bool = True) -> str:
    """Construye un árbol jerárquico con métricas por archivo (líneas y tamaño)."""
    tree = defaultdict(lambda: {"dirs": set(), "files": []})

    for rec in records:
        rel = rec["rel"]
        parent_parts = rel.parent.parts if str(rel.parent) != "." else ()
        tree[parent_parts]["files"].append(rec)
        for i in range(len(parent_parts)):
            tree[parent_parts[:i]]["dirs"].add(parent_parts[i])

    lines = [(root.name or str(root)) + "/"]

    def render(parts, prefix=""):
        node = tree[parts]
        sorted_dirs = [(d, True, None) for d in sorted(node["dirs"])]
        sorted_files = [(r["rel"].name, False, r) for r in sorted(node["files"], key=lambda x: x["rel"].name)]
        entries = sorted_dirs + sorted_files
        for i, (name, is_dir, rec) in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            if is_dir:
                lines.append(f"{prefix}{connector}{name}/")
                render(parts + (name,), prefix + ("    " if is_last else "│   "))
            else:
                if show_metrics and rec and rec["lines"] is not None:
                    meta = f" ({rec['lines']:,} líneas, {_format_size_kb(rec['size'])})"
                elif show_metrics and rec:
                    meta = f" ({_format_size_kb(rec['size'])})"
                else:
                    meta = ""
                lines.append(f"{prefix}{connector}{name}{meta}")

    render(())
    return "\n".join(lines)


def build_metrics_summary(records: list) -> list:
    """Genera tablas de resumen por módulo raíz y por extensión."""
    by_module = defaultdict(lambda: {"files": 0, "lines": 0, "bytes": 0})
    by_ext = defaultdict(lambda: {"files": 0, "lines": 0, "bytes": 0})
    total_lines = 0
    total_bytes = 0

    for rec in records:
        rel = rec["rel"]
        module = rel.parts[0] if len(rel.parts) > 1 else "(raíz)"
        ext = rel.suffix.lower() or rel.name
        lines_cnt = rec["lines"] or 0
        size_b = rec["size"]

        by_module[module]["files"] += 1
        by_module[module]["lines"] += lines_cnt
        by_module[module]["bytes"] += size_b

        by_ext[ext]["files"] += 1
        by_ext[ext]["lines"] += lines_cnt
        by_ext[ext]["bytes"] += size_b

        total_lines += lines_cnt
        total_bytes += size_b

    out = [
        "## 📊 Resumen Cuantitativo del Código y Documentación",
        "",
        f"- **Total archivos leídos:** {len(records):,}",
        f"- **Total líneas:** {total_lines:,}",
        f"- **Peso total de texto incluido:** {_format_size_kb(total_bytes)}",
        "",
        "### Por Módulo Principal",
        "",
        "| Módulo | Archivos | Líneas | Tamaño |",
        "|---|---:|---:|---:|",
    ]
    for mod, st in sorted(by_module.items(), key=lambda x: (-x[1]["bytes"], x[0])):
        out.append(f"| `{mod}` | {st['files']:,} | {st['lines']:,} | {_format_size_kb(st['bytes'])} |")

    out.extend([
        "",
        "### Por Extensión / Tipo (Top 12)",
        "",
        "| Tipo | Archivos | Líneas | Tamaño |",
        "|---|---:|---:|---:|",
    ])
    for ext, st in sorted(by_ext.items(), key=lambda x: (-x[1]["files"], -x[1]["bytes"]))[:12]:
        out.append(f"| `{ext}` | {st['files']:,} | {st['lines']:,} | {_format_size_kb(st['bytes'])} |")

    out.extend(["", "---", ""])
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Syntax highlighting para los bloques de código
# ─────────────────────────────────────────────────────────────────────────────

LANG_MAP = {
    "py": "python", "pyi": "python", "pyx": "cython", "patched": "python",
    "js": "javascript", "jsx": "jsx", "mjs": "javascript", "cjs": "javascript",
    "ts": "typescript", "tsx": "tsx", "mts": "typescript", "cts": "typescript",
    "html": "html", "htm": "html", "css": "css", "scss": "scss",
    "sass": "sass", "less": "less",
    "json": "json", "jsonl": "json", "yaml": "yaml", "yml": "yaml", "toml": "toml",
    "ini": "ini", "cfg": "ini", "conf": "conf",
    "md": "markdown", "rst": "rst", "txt": "text",
    "puml": "plantuml", "mmd": "mermaid",
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

def safe_code_fence(content: str) -> str:
    """Devuelve un delimitador de backticks que no colisiona con bloques internos."""
    runs = [len(m.group(0)) for m in re.finditer(r"`+", content)]
    return "`" * max(3, (max(runs) + 1) if runs else 3)


def get_git_history_block(root: Path) -> list:
    """Captura historial reciente de commits y estado de cambios locales si existe Git."""
    if not (root / ".git").exists():
        return []
    blocks = []
    try:
        log_res = subprocess.run(
            ["git", "-C", str(root), "log", "-n", "40", "--date=short", "--pretty=format:%h %ad %s"],
            capture_output=True, text=True, check=False, timeout=5,
        )
        st_res = subprocess.run(
            ["git", "-C", str(root), "status", "--short"],
            capture_output=True, text=True, check=False, timeout=5,
        )
        if log_res.returncode == 0 and log_res.stdout.strip():
            blocks.extend([
                "## 🕰️ Historial Reciente de Commits (`git log`)",
                "",
                "```text",
                log_res.stdout.strip(),
                "```",
                "",
            ])
        if st_res.returncode == 0 and st_res.stdout.strip():
            blocks.extend([
                "## 🛠️ Cambios Locales en Curso (`git status --short`)",
                "",
                "```text",
                st_res.stdout.strip(),
                "```",
                "",
            ])
        if blocks:
            blocks.append("---")
            blocks.append("")
    except Exception:
        pass
    return blocks


def generate_markdown(root: Path, files: list, max_size: int, output_name: str = "") -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = []
    for filepath in files:
        content = read_file_safe(filepath, max_size)
        if content is None:
            continue
        rel = filepath.relative_to(root)
        try:
            size_b = filepath.stat().st_size
        except OSError:
            size_b = len(content.encode("utf-8"))
        line_cnt = len(content.splitlines())
        records.append({
            "path": filepath,
            "rel": rel,
            "content": content,
            "size": size_b,
            "lines": line_cnt,
        })

    included = len(records)
    out = [
        f"# Contexto del Proyecto: `{root.name}`",
        "",
        f"- **Generado:** {timestamp}",
        f"- **Raíz:** `{root.resolve()}`",
        f"- **Archivos de código/texto incluidos:** {included}",
        "",
        "> Este documento contiene el contexto completo del proyecto (mapa en disco con `tree`, métricas, historial Git y código fuente) para ser utilizado por un agente de IA.",
        "",
        "---",
        "",
    ]
    out.extend(get_git_history_block(root))
    out.extend(get_system_tree_block(root, output_name))
    out.extend(build_metrics_summary(records))
    out.extend([
        "## 📁 Estructura de Archivos Incluidos (con líneas y tamaño)",
        "",
        "```text",
        build_tree(root, records, show_metrics=True),
        "```",
        "",
        "---",
        "",
        "## 📄 Contenido de los archivos",
        "",
    ])

    for rec in records:
        rel = rec["rel"]
        content = rec["content"]
        ext = rel.suffix.lstrip(".").lower()
        lang = LANG_MAP.get(ext, ext or "text")
        fence = safe_code_fence(content)

        out.append(f"### `{rel}` ({rec['lines']:,} líneas, {_format_size_kb(rec['size'])})")
        out.append("")
        out.append(f"{fence}{lang}")
        out.append(content.rstrip("\n"))
        out.append(fence)
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
    md = generate_markdown(root, files, max_size, output_name=output.name)

    output.write_text(md, encoding="utf-8")
    size_kb = output.stat().st_size / 1024

    print()
    print(f"✅ Archivo generado: {output}")
    print(f"   Tamaño:            {size_kb:.1f} KB")
    print(f"   Archivos:          {len(files)}")


if __name__ == "__main__":
    main()