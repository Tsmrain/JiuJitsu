#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
read -r -p "⚠️  Borra data/postgres/ y data/qdrant/. ¿Continuar? [y/N] " a
[ "$a" = "y" ] || { echo "Cancelado."; exit 0; }
./scripts/stop.sh
rm -rf data/postgres/* data/qdrant/*
echo "✓ Borrado. Ejecutá ./scripts/start.sh; initdb/ recreará el schema."
