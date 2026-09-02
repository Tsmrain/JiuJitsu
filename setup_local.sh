#!/bin/bash
# ==============================================================================
# Script de Configuración Ultraligera para Desarrollo Local (Dell / Debian 13)
# Instala solo las dependencias esenciales de prueba, dominio y UI ligera
# ==============================================================================

set -e

echo "🚀 Iniciando configuración ligera para desarrollo local (Debian)..."

if [ ! -d ".venv" ]; then
    echo "📦 Creando entorno virtual .venv..."
    python3 -m venv .venv
fi

echo "📦 Activando entorno virtual..."
source .venv/bin/activate

echo "📦 Actualizando pip e instalando dependencias ligeras de requirements-core.txt..."
pip install --upgrade pip
pip install -r requirements-core.txt

echo "✅ Entorno local listo para TDD rápido. (El adaptador de inferencia se omitirá gracefully si no hay torch)."
