#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

blue()  { printf "\033[34m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }

if [ -f data/logs/backend.pid ]; then
  PID=$(cat data/logs/backend.pid)
  kill "$PID" 2>/dev/null || true
  for i in $(seq 1 10); do kill -0 "$PID" 2>/dev/null || break; sleep 0.5; done
  kill -9 "$PID" 2>/dev/null || true
  rm -f data/logs/backend.pid
fi
pkill -f "uvicorn corpocmente.main:app" 2>/dev/null || true
green "  Backend detenido"

if [ -f data/logs/frontend.pid ]; then
  PID=$(cat data/logs/frontend.pid)
  kill "$PID" 2>/dev/null || true
  for i in $(seq 1 10); do kill -0 "$PID" 2>/dev/null || break; sleep 0.5; done
  kill -9 "$PID" 2>/dev/null || true
  rm -f data/logs/frontend.pid
fi
pkill -f "vite --host" 2>/dev/null || true
green "  Frontend detenido"

blue "▸ Deteniendo contenedores..."
docker compose -f infrastructure/docker-compose.yml down
green "  Contenedores detenidos"
echo
green "✅ Sistema detenido."

