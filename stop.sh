#!/usr/bin/env bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

echo "=== Deteniendo Backend y Frontend ==="
pkill -f "uvicorn corpocmente.main:app" || true
pkill -f "vite --host" || true

echo "=== Deteniendo Contenedores Docker ==="
cd "$DIR/ProyectoGrado"
docker compose down

echo "Sistema detenido."

