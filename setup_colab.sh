#!/bin/bash
set -e

echo "🚀 Iniciando configuración Plug & Play para Google Colab..."

# 1. Actualizar herramientas base
echo "📦 Actualizando herramientas base..."
pip install --upgrade pip setuptools wheel

# 2. Instalar mmcv-lite (Versión ligera sin compilación CUDA personalizada)
# ESTO ES CRÍTICO: mmcv-full no tiene wheels para Py3.13. mmcv-lite sí.
echo "📦 Instalando mmcv-lite (evitando compilación desde fuente)..."
pip install mmcv-lite

# 3. Instalar mmdet y mmpose desde índices oficiales
echo "📦 Instalando mmdet y mmpose..."
pip install mmdet -f https://download.openmmlab.com/mmdetection/v3.0/index.html
pip install mmpose -f https://download.openmmlab.com/mmpose/v1/index.html

# 4. Instalar rtmpose3d SIN dependencias (--no-deps)
# Esto evita que pip intente reinstalar mmcv-full o torch, rompiendo el entorno.
echo "📦 Instalando rtmpose3d (sin dependencias para evitar conflictos)..."
pip install git+https://github.com/b-arac/rtmpose3d.git --no-deps

# 5. Instalar dependencias restantes del proyecto manualmente
echo "📦 Instalando dependencias del proyecto..."
pip install numpy opencv-python-headless scipy matplotlib streamlit sqlalchemy pytest

# 6. Verificación de videos Ground Truth
echo "📦 Verificando activos de video reales en Videos/..."
if [ -f "Videos/Maestro.mp4" ] && [ -f "Videos/Alumno.mp4" ]; then
    echo "✔ Videos reales detectados: Videos/Maestro.mp4 y Videos/Alumno.mp4"
else
    echo "⚠ ADVERTENCIA: Asegúrese de tener 'Videos/Maestro.mp4' y 'Videos/Alumno.mp4' en la carpeta Videos/."
fi

echo "✅ ¡Instalación completada exitosamente SIN compilación desde fuente!"
