#!/bin/bash
echo "====================================="
echo "  JiuJitsu Tesis - Setup Colab"
echo "====================================="

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Crear directorios necesarios
mkdir -p videos Videos resultados/fotogramas resultados/csv resultados/graficas modelos

echo "✅ Setup completado!"
echo "📁 Estructura creada:"
ls -la
