#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p data/logs
touch data/logs/backend.log data/logs/frontend.log
echo "▸ Siguiendo logs (Ctrl+C para salir)"
tail -f data/logs/backend.log data/logs/frontend.log
