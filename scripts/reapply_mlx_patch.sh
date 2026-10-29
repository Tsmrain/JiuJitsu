#!/usr/bin/env bash
# reapply_mlx_patch.sh — re-aplica el patch de mlx-embeddings tras reinstalación.
# Verifica SHA256 contra el archivo vendor de referencia.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATCHED="$ROOT/backend/vendor/mlx_embeddings_qwen3_vl_model.py.patched"
TARGET=$(find "$ROOT/backend/venv" -path "*mlx_embeddings/models/qwen3_vl/model.py" 2>/dev/null | head -1)

[ -f "$PATCHED" ] || { echo "✗ Falta archivo de referencia: $PATCHED"; exit 1; }
[ -n "$TARGET" ] || { echo "✗ No se encontró mlx_embeddings/model.py en backend/venv"; exit 1; }

EXPECTED=$(sha256sum "$PATCHED" | awk '{print $1}')
ACTUAL=$(sha256sum "$TARGET" | awk '{print $1}')

if [ "$EXPECTED" = "$ACTUAL" ]; then
  echo "✅ Patch ya aplicado (SHA256 coincide)."
  exit 0
fi

echo "⚠️  SHA256 no coincide. Re-aplicando desde $PATCHED"
cp "$PATCHED" "$TARGET"
NEW=$(sha256sum "$TARGET" | awk '{print $1}')
if [ "$EXPECTED" = "$NEW" ]; then
  echo "✅ Patch re-aplicado."
else
  echo "✗ Re-aplicación fallida."
  exit 1
fi
