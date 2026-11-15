#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="$HOME/.docker/bin:/Applications/Docker.app/Contents/Resources/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

blue()  { printf "\033[34m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }

if [ -f backend/.env ]; then
  set -a
  source backend/.env
  set +a
fi
DATA_DIR="${CORPOCMENTE_DATA_DIR:-/tmp/corpocmente_data}"

if [ -f "$DATA_DIR/logs/backend.pid" ]; then
  PID=$(cat "$DATA_DIR/logs/backend.pid")
  kill "$PID" 2>/dev/null || true
  for i in $(seq 1 10); do kill -0 "$PID" 2>/dev/null || break; sleep 0.5; done
  kill -9 "$PID" 2>/dev/null || true
  rm -f "$DATA_DIR/logs/backend.pid"
fi
pkill -f "uvicorn corpocmente.main:app" 2>/dev/null || true
green "  Backend detenido"

if [ -f "$DATA_DIR/logs/frontend.pid" ]; then
  PID=$(cat "$DATA_DIR/logs/frontend.pid")
  kill "$PID" 2>/dev/null || true
  for i in $(seq 1 10); do kill -0 "$PID" 2>/dev/null || break; sleep 0.5; done
  kill -9 "$PID" 2>/dev/null || true
  rm -f "$DATA_DIR/logs/frontend.pid"
fi
pkill -f "vite --host" 2>/dev/null || true
green "  Frontend detenido"

blue "▸ Deteniendo contenedores..."
docker compose --env-file backend/.env -f infrastructure/docker-compose.yml down
green "  Contenedores detenidos"
echo
green "✅ Sistema detenido."

