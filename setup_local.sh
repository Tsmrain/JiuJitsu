#!/bin/bash
echo "====================================="
echo "  JiuJitsu Tesis - Setup Local"
echo "====================================="

# Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "🐍 Creando entorno virtual .venv..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Instalar dependencias
echo "📦 Instalando dependencias desde requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Crear directorios necesarios
mkdir -p videos Videos resultados/fotogramas resultados/csv resultados/graficas modelos

echo "✅ Setup local completado!"
echo "📁 Para activar: source .venv/bin/activate"
