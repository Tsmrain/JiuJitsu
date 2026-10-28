#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

check() {
  local n=$1 u=$2
  if curl -sf -o /dev/null --max-time 3 "$u"; then printf "  ✅ %-10s %s\n" "$n" "$u"
  else                                         printf "  ❌ %-10s %s\n" "$n" "$u"; fi
}
echo "── Docker ──"
docker ps --filter "name=corpocmente_" --format "  {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  (docker no disponible)"
echo; echo "── HTTP ──"
check Qdrant    http://localhost:6333/collections
check PostgREST http://localhost:3000/
check Backend   http://localhost:8000/health
check Frontend  http://localhost:5173/
echo; echo "── Qdrant colecciones ──"
curl -sf http://localhost:6333/collections 2>/dev/null \
  | python3 -c "import sys,json; [print('  -',c['name']) for c in json.load(sys.stdin)['result']['collections']]" 2>/dev/null \
  || echo "  (no responde o sin colecciones)"
echo; echo "── Postgres ──"
docker exec corpocmente_postgres psql -U postgres -d corpocmente -tAc "
  SELECT '  usuarios=' || count(*) FROM usuarios
  UNION ALL SELECT '  tecnicas=' || count(*) FROM tecnicas
  UNION ALL SELECT '  evaluaciones=' || count(*) FROM evaluaciones_alumnos
  UNION ALL SELECT '  teoria_chunks=' || count(*) FROM teoria_referencia;
" 2>/dev/null || echo "  (no responde)"
