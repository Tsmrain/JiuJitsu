#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -f backend/.env ]; then
  set -a
  source backend/.env
  set +a
fi
DATA_DIR="${CORPOCMENTE_DATA_DIR:-/tmp/corpocmente_data}"
mkdir -p "$DATA_DIR/logs"
touch "$DATA_DIR/logs/backend.log" "$DATA_DIR/logs/frontend.log"
echo "▸ Siguiendo logs (Ctrl+C para salir)"
tail -f "$DATA_DIR/logs/backend.log" "$DATA_DIR/logs/frontend.log"

