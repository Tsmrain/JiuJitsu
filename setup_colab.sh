#!/bin/bash
# ==============================================================================
# Script de Instalación Automatizada Plug & Play para Google Colab (A100, CUDA 12.8)
# Utiliza OpenMIM para descargar ruedas binarias pre-compiladas (evita compilación C++)
# ==============================================================================

set -e

echo "🚀 Iniciando configuración Plug & Play para Google Colab (A100, CUDA 12.8)..."

# 1. Actualizar pip para evitar conflictos de resolución
pip install --upgrade pip

# 2. Instalar OpenMIM (Gestor oficial de paquetes pre-compilados de OpenMMLab)
pip install -U openmim

# 3. Instalar dependencias pre-compiladas (ESTO EVITA la compilación de 12+ minutos)
# 'mim' detecta automáticamente la versión de PyTorch (2.11.0+cu128) y descarga la rueda binaria exacta.
echo "📦 Instalando mmcv, mmdet y mmpose (versiones pre-compiladas binarias)..."
mim install mmcv
mim install mmdet
mim install mmpose

# 4. Instalar el repositorio rtmpose3d y dependencias restantes del proyecto
echo "📦 Instalando rtmpose3d y dependencias del proyecto..."
pip install git+https://github.com/b-arac/rtmpose3d.git
pip install -r requirements-core.txt

# 5. Verificación de videos Ground Truth
echo "📦 Verificando activos de video reales en Videos/..."
if [ -f "Videos/Maestro.mp4" ] && [ -f "Videos/Alumno.mp4" ]; then
    echo "✔ Videos reales detectados: Videos/Maestro.mp4 y Videos/Alumno.mp4"
else
    echo "⚠ ADVERTENCIA: Asegúrese de tener 'Videos/Maestro.mp4' y 'Videos/Alumno.mp4' en la raíz del proyecto para las pruebas de integración."
fi

echo "✅ ¡Instalación completada exitosamente SIN compilación desde fuente!"
