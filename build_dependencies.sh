#!/usr/bin/env bash
# ==============================================================================
# Script de Empaquetado de Dependencias Binarias para Huawei Cloud FunctionGraph
# Arquitectura: Linux x86_64 (manylinux2014_x86_64) - Python 3.9 Runtime
# ==============================================================================

set -euo pipefail

PACKAGE_DIR="build_pkg/python"
ZIP_NAME="bjj_biomechanics_deps.zip"

echo "================================================================="
echo "📦 Iniciando empaquetado de dependencias para Huawei FunctionGraph"
echo "================================================================="

# 1. Preparar directorio temporal con estructura estándar para Python en FunctionGraph
rm -rf build_pkg "${ZIP_NAME}"
mkdir -p "${PACKAGE_DIR}"

echo "⬇️  Descargando e instalando dependencias binarias cross-platform..."

# 2. Descargar e instalar dependencias precompiladas para Linux x86_64 y Python 3.9
pip install \
    --platform manylinux2014_x86_64 \
    --target "${PACKAGE_DIR}" \
    --implementation cp \
    --python-version 3.9 \
    --only-binary=:all: \
    mediapipe==0.10.14 \
    opencv-python-headless==4.10.0.84 \
    numpy==1.26.4 \
    scipy==1.13.1 \
    esdk-obs-python==3.24.3

echo "🗜️  Comprimiendo paquete zip de dependencias privadas..."

# 3. Empaquetar el contenido del directorio en el ZIP
cd build_pkg
zip -r -q "../${ZIP_NAME}" .
cd ..

# 4. Limpieza del directorio temporal de construcción
rm -rf build_pkg

echo "================================================================="
echo "✅ Paquete generado con éxito: ${ZIP_NAME}"
echo "ℹ️  Sube este archivo como 'Dependencia Privada' en la consola web de FunctionGraph."
echo "================================================================="
