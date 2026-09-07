#!/bin/bash
set -e

echo "=== Configurando entorno local liviano para desarrollo (Linux/macOS) ==="

if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual .venv..."
    python3 -m venv .venv
fi

echo "Activando entorno virtual..."
source .venv/bin/activate

echo "Instalando dependencias base..."
python3 -m pip install --upgrade pip
pip install -r requirements-core.txt

echo "=== Entorno local listo para TDD ==="
echo "Para ejecutar la suite de pruebas ligeras:"
echo "  source .venv/bin/activate"
echo "  pytest -v"
