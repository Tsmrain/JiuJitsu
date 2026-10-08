"""
exportar_contexto.py
Exporta TODO el contenido de texto del proyecto JiuJitsu en un solo archivo
para dárselo como contexto a cualquier LLM (Gemini, Claude, ChatGPT).
"""
import os
from pathlib import Path
from datetime import datetime

# ============ CONFIGURACIÓN ============
ROOT = Path(r"C:\Users\InvitadoPSL\Desktop\JiuJitsu")
OUT  = ROOT / "CONTEXTO_PROYECTO.txt"

# Carpetas a EXCLUIR (en cualquier nivel)
EXCLUIR_DIRS = {
    "venv", ".venv", "env",
    "node_modules", "__pycache__", ".git",
    ".vite", "dist", "build", ".next",
    "qdrant_storage", "artifacts",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".idea", ".vscode", "coverage", "htmlcov",
}

# Archivos a EXCLUIR por nombre
EXCLUIR_FILES = {
    "CONTEXTO_PROYECTO.txt",
    "CONTEXTO_ESENCIAL.txt",
    "lista_archivos.txt",
    "package-lock.json",   # ocupa mucho y no aporta contexto
    ".package-lock.json",
}

# Extensiones de TEXTO que queremos incluir
EXT_VALIDAS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".json", ".jsonl", ".md", ".txt", ".rst",
    ".sql", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
    ".html", ".css", ".scss", ".puml", ".mmd",
    ".sh", ".ps1", ".bat", ".cmd",
    ".xml", ".csv", ".ipynb",
    ".env", ".example", ".gitignore", ".dockerignore",
}

# Nombres exactos sin extensión que también queremos
NOMBRES_VALIDOS = {
    ".env", ".env.example", ".gitignore", ".dockerignore",
    "Dockerfile", "Makefile", "Procfile",
}

# Archivos sensibles que NO queremos exportar tal cual (opcional)
# Déjalo vacío si quieres incluirlos, o ponlos aquí si NO quieres secretos
ARCHIVOS_SENSIBLES_A_OCULTAR = {
    ".env",
}

# Tamaño máximo por archivo (bytes). Salta archivos gigantes.
MAX_BYTES = 500_000  # 500 KB

# ============ LÓGICA ============
def debe_excluir_dir(nombre: str) -> bool:
    return nombre in EXCLUIR_DIRS

def es_archivo_valido(path: Path) -> bool:
    if path.name in EXCLUIR_FILES:
        return False
    if path.name in ARCHIVOS_SENSIBLES_A_OCULTAR:
        return False
    if path.name in NOMBRES_VALIDOS:
        return True
    if path.suffix.lower() in EXT_VALIDAS:
        return True
    return False

def recorrer_proyecto(root: Path):
    """Genera rutas de archivos válidos, saltando carpetas excluidas."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Modificar in-place para que os.walk no entre a estas carpetas
        dirnames[:] = [d for d in dirnames if not debe_excluir_dir(d)]
        for fname in filenames:
            p = Path(dirpath) / fname
            if es_archivo_valido(p):
                yield p

def leer_texto(path: Path) -> str | None:
    """Intenta leer como UTF-8; si falla, prueba latin-1; si no, None."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, PermissionError):
            continue
    return None

def construir_arbol(root: Path) -> str:
    """Genera un árbol tipo 'tree' pero sin carpetas excluidas."""
    lineas = []
    def _walk(d: Path, prefijo: str = ""):
        try:
            items = sorted(
                [x for x in d.iterdir() if not (x.is_dir() and debe_excluir_dir(x.name))],
                key=lambda x: (x.is_file(), x.name.lower())
            )
        except PermissionError:
            return
        for i, item in enumerate(items):
            ultimo = (i == len(items) - 1)
            conector = "└── " if ultimo else "├── "
            lineas.append(f"{prefijo}{conector}{item.name}")
            if item.is_dir():
                extension = "    " if ultimo else "│   "
                _walk(item, prefijo + extension)
    lineas.append(root.name + "/")
    _walk(root)
    return "\n".join(lineas)

def main():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(f"📂 Ruta raíz: {ROOT}")
    print(f"📄 Archivo de salida: {OUT}\n")

    archivos = sorted(recorrer_proyecto(ROOT), key=lambda p: str(p).lower())
    print(f"🔎 Encontrados {len(archivos)} archivos de texto válidos.\n")

    total_bytes = 0
    omitidos = []

    with OUT.open("w", encoding="utf-8") as f:
        # ---------- Encabezado ----------
        f.write("=" * 100 + "\n")
        f.write("# CONTEXTO COMPLETO DEL PROYECTO JIUJITSU\n")
        f.write(f"# Generado: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"# Ruta base: {ROOT}\n")
        f.write(f"# Total archivos: {len(archivos)}\n")
        f.write("=" * 100 + "\n\n")

        # ---------- Árbol de carpetas ----------
        f.write("## ESTRUCTURA DE CARPETAS\n")
        f.write("-" * 100 + "\n")
        f.write(construir_arbol(ROOT))
        f.write("\n\n")

        # ---------- Contenido de cada archivo ----------
        f.write("## CONTENIDO DE ARCHIVOS\n")
        f.write("-" * 100 + "\n")

        for p in archivos:
            rel = p.relative_to(ROOT).as_posix()
            size = p.stat().st_size

            if size > MAX_BYTES:
                omitidos.append((rel, size, "demasiado grande"))
                print(f"  ⏭️  Omitido (>{MAX_BYTES//1000} KB): {rel}")
                continue

            contenido = leer_texto(p)
            if contenido is None:
                omitidos.append((rel, size, "no es texto"))
                print(f"  ⏭️  Omitido (binario): {rel}")
                continue

            print(f"  ✅ {rel} ({size} bytes)")
            total_bytes += size

            f.write("\n" + "=" * 100 + "\n")
            f.write(f"FILE: {rel}\n")
            f.write(f"SIZE: {size} bytes\n")
            f.write("=" * 100 + "\n")
            f.write(contenido)
            if not contenido.endswith("\n"):
                f.write("\n")

        # ---------- Resumen final ----------
        f.write("\n" + "=" * 100 + "\n")
        f.write("## RESUMEN\n")
        f.write("-" * 100 + "\n")
        f.write(f"Archivos incluidos : {len(archivos) - len(omitidos)}\n")
        f.write(f"Archivos omitidos  : {len(omitidos)}\n")
        f.write(f"Bytes totales      : {total_bytes:,}\n")
        if omitidos:
            f.write("\n### Omitidos:\n")
            for rel, sz, motivo in omitidos:
                f.write(f"  - {rel} ({sz:,} bytes) — {motivo}\n")

    print(f"\n✅ Listo. Generado: {OUT}")
    print(f"   Tamaño total del archivo: {OUT.stat().st_size:,} bytes")

if __name__ == "__main__":
    main()