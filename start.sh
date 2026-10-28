#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/Applications/Docker.app/Contents/Resources/bin:/Users/santiago/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH"

echo "=== Iniciando servicios Docker (PostgreSQL, PostgREST, Qdrant) ==="
cd "$DIR/ProyectoGrado"
docker compose up -d

echo "=== Iniciando Backend FastAPI (http://localhost:8000) ==="
cd "$DIR/ProyectoGrado/codigo_fuente/backend"
nohup ./venv/bin/uvicorn corpocmente.main:app --port 8000 --host 0.0.0.0 > /tmp/corpocmente_backend.log 2>&1 &
echo "PID Backend: $!"

echo "=== Iniciando Frontend React (http://localhost:5173) ==="
cd "$DIR/ProyectoGrado/codigo_fuente/frontend"
nohup ./node_modules/.bin/vite --host 0.0.0.0 --port 5173 > /tmp/corpocmente_frontend.log 2>&1 &
echo "PID Frontend: $!"

echo ""
echo " Sistema iniciado con éxito:"
echo " - Frontend:   http://localhost:5173"
echo " - Backend:    http://localhost:8000 (Docs: http://localhost:8000/docs)"
echo " - PostgREST:  http://localhost:3000"
echo " - Qdrant:     http://localhost:6333/dashboard"

