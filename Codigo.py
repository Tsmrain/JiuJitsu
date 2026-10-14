#!/usr/bin/env python3
"""
generate_project_context.py

Genera un archivo Markdown con todo el contenido de texto del proyecto.
Excluye directorios y archivos comunes que no aportan contexto (dependencias,
binarios, artefactos de build, almacenamiento de datos, etc.).

Uso:
    python generate_project_context.py -r . -o project_context.md
"""

import os
import sys
import argparse
from pathlib import Path

# ----------------------------------------------------------------------
# Configuración de exclusiones
# ----------------------------------------------------------------------
EXCLUDED_DIRS = {
    '.git', '.github', 'node_modules', '__pycache__', 'dist', 'build',
    'qdrant_storage', 'venv', 'env', '.venv', '.env', 'lib64', 'share',
    'site-packages', '.idea', '.vscode', 'coverage', '.next', 'out',
    'target', 'bin', 'obj', 'pkg', 'vendor', 'tmp', 'temp', 'logs',
    '.mypy_cache', '.pytest_cache', '.ruff_cache', 'htmlcov'
}

EXCLUDED_EXTENSIONS = {
    # Binarios y compilados
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib', '.exe', '.bin',
    '.o', '.a', '.lib', '.obj',
    # Imágenes (excepto svg que es texto)
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp', '.tiff',
    # Audio/Video
    '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac', '.mkv', '.webm',
    # Archivos comprimidos
    '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz',
    # Documentos
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # Fuentes
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    # Mapas y logs
    '.map', '.log',
    # Bases de datos
    '.sqlite', '.db', '.mdb', '.accdb',
    # Otros
    '.lock', '.DS_Store'
}

EXCLUDED_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'poetry.lock', 'Pipfile.lock', 'composer.lock',
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    'project_context.md'  # Evitar incluir el propio archivo de salida
}

# Tamaño máximo por archivo (1 MB). Ajusta según necesidades.
MAX_FILE_SIZE = 1024 * 1024

# Mapeo de extensiones a lenguajes para bloques de código
EXTENSION_LANG_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'jsx',
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.less': 'less',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.xml': 'xml',
    '.md': 'markdown',
    '.sql': 'sql',
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'zsh',
    '.bat': 'batch',
    '.ps1': 'powershell',
    '.dockerfile': 'dockerfile',
    '.go': 'go',
    '.rs': 'rust',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.r': 'r',
    '.m': 'matlab',
    '.pl': 'perl',
    '.lua': 'lua',
    '.toml': 'toml',
    '.ini': 'ini',
    '.cfg': 'ini',
    '.conf': 'nginx',
    '.env': 'bash',
    '.txt': 'text',
    '.csv': 'csv',
    '.tsv': 'tsv',
    '.svg': 'xml',
}

# ----------------------------------------------------------------------
# Funciones auxiliares
# ----------------------------------------------------------------------
def is_text_file(filepath):
    """Intenta determinar si un archivo es de texto leyendo una pequeña muestra."""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return False
            chunk.decode('utf-8')
            return True
    except (UnicodeDecodeError, OSError):
        return False

def get_language(filepath):
    ext = Path(filepath).suffix.lower()
    return EXTENSION_LANG_MAP.get(ext, '')

def should_skip_dir(dirname):
    return dirname in EXCLUDED_DIRS

def should_skip_file(filepath):
    filename = os.path.basename(filepath)
    if filename in EXCLUDED_FILES:
        return True
    ext = Path(filepath).suffix.lower()
    if ext in EXCLUDED_EXTENSIONS:
        return True
    try:
        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            return True
    except OSError:
        return True
    return False

# ----------------------------------------------------------------------
# Generación del Markdown
# ----------------------------------------------------------------------
def generate_markdown(root_dir, output_file):
    root_path = Path(root_dir).resolve()
    output_path = Path(output_file).resolve()
    total_files = 0
    included_files = 0

    with open(output_path, 'w', encoding='utf-8') as out:
        out.write(f"# Contexto del Proyecto: {root_path.name}\n\n")
        out.write(f"Generado desde: `{root_path}`\n\n")
        out.write("---\n\n")

        for dirpath, dirnames, filenames in os.walk(root_path):
            # Filtrar directorios excluidos
            dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
            dirnames.sort()
            filenames.sort()

            for filename in filenames:
                filepath = Path(dirpath) / filename
                total_files += 1

                if should_skip_file(filepath):
                    continue

                rel_path = filepath.relative_to(root_path)

                if not is_text_file(filepath):
                    out.write(f"## {rel_path}\n\n")
                    out.write("*[Archivo binario – contenido no incluido]*\n\n")
                    included_files += 1
                    continue

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    out.write(f"## {rel_path}\n\n")
                    out.write(f"*[Error al leer el archivo: {e}]*\n\n")
                    included_files += 1
                    continue

                out.write(f"## {rel_path}\n\n")
                lang = get_language(filepath)
                out.write(f"```{lang}\n")
                out.write(content)
                if not content.endswith('\n'):
                    out.write('\n')
                out.write("```\n\n")
                included_files += 1

    print(f"✅ Archivo Markdown generado: {output_path}")
    print(f"   Archivos totales encontrados: {total_files}")
    print(f"   Archivos incluidos (texto o binarios marcados): {included_files}")

# ----------------------------------------------------------------------
# Punto de entrada
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description='Genera un archivo Markdown con todo el contenido de texto del proyecto.'
    )
    parser.add_argument(
        '--root', '-r', default='.',
        help='Directorio raíz del proyecto (por defecto: directorio actual)'
    )
    parser.add_argument(
        '--output', '-o', default='project_context.md',
        help='Nombre del archivo Markdown de salida (por defecto: project_context.md)'
    )
    args = parser.parse_args()

    generate_markdown(args.root, args.output)

if __name__ == '__main__':
    main()