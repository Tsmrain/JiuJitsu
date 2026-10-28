#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="/Applications/Docker.app/Contents/Resources/bin:/Users/santiago/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH"

red()   { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
blue()  { printf "\033[34m%s\033[0m\n" "$*"; }
die()   { red "✗ $*"; exit 1; }

blue "▸ Verificando precondiciones..."
command -v docker >/dev/null || die "Docker no está en PATH"
command -v curl   >/dev/null || die "curl no está disponible"
[ -f backend/.env ]                     || die "Falta backend/.env"
[ -d backend/venv ]                     || die "Falta backend/venv"
[ -d frontend/node_modules ]            || die "Falta frontend/node_modules"
[ -f infrastructure/docker-compose.yml ]|| die "Falta infrastructure/docker-compose.yml"
mkdir -p data/logs data/uploads data/frames
green "  Precondiciones OK"

blue "▸ Levantando Docker..."
docker compose -f infrastructure/docker-compose.yml up -d

blue "▸ Esperando Postgres healthy..."
status="starting"
for i in $(seq 1 60); do
  status=$(docker inspect --format='{{.State.Health.Status}}' corpocmente_postgres 2>/dev/null || echo starting)
  [ "$status" = "healthy" ] && break
  sleep 1
done
[ "$status" = "healthy" ] || die "Postgres no healthy en 60s"

blue "▸ Esperando PostgREST..."
for i in $(seq 1 30); do curl -sf -o /dev/null http://localhost:3000/ && break; sleep 1; done
curl -sf -o /dev/null http://localhost:3000/ || die "PostgREST no responde"

blue "▸ Esperando Qdrant..."
for i in $(seq 1 30); do curl -sf -o /dev/null http://localhost:6333/collections && break; sleep 1; done
curl -sf -o /dev/null http://localhost:6333/collections || die "Qdrant no responde"

blue "▸ Backend :8000..."
if lsof -iTCP:8000 -sTCP:LISTEN -P -n >/dev/null 2>&1; then
  blue "  Ya corriendo, no relanzo"
else
  cd "$ROOT/backend"
  python3 -c "import subprocess, os; p = subprocess.Popen(['./venv/bin/uvicorn', 'corpocmente.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'], stdin=subprocess.DEVNULL, stdout=open('$ROOT/data/logs/backend.log', 'w'), stderr=subprocess.STDOUT, preexec_fn=os.setsid); open('$ROOT/data/logs/backend.pid', 'w').write(str(p.pid))"
  cd "$ROOT"
fi
for i in $(seq 1 30); do curl -sf -o /dev/null http://localhost:8000/health && break; sleep 1; done
curl -sf -o /dev/null http://localhost:8000/health || die "Backend no responde (ver data/logs/backend.log)"

blue "▸ Frontend :5173..."
if lsof -iTCP:5173 -sTCP:LISTEN -P -n >/dev/null 2>&1; then
  blue "  Ya corriendo, no relanzo"
else
  cd "$ROOT/frontend"
  python3 -c "import subprocess, os; p = subprocess.Popen(['./node_modules/.bin/vite', '--host', '0.0.0.0', '--port', '5173'], stdin=subprocess.DEVNULL, stdout=open('$ROOT/data/logs/frontend.log', 'w'), stderr=subprocess.STDOUT, preexec_fn=os.setsid); open('$ROOT/data/logs/frontend.pid', 'w').write(str(p.pid))"
  cd "$ROOT"
fi
for i in $(seq 1 30); do curl -sf -o /dev/null http://localhost:5173/ && break; sleep 1; done
curl -sf -o /dev/null http://localhost:5173/ || die "Frontend no responde (ver data/logs/frontend.log)"

echo
green "✅ Sistema listo:"
echo "   Frontend:   http://localhost:5173"
echo "   Backend:    http://localhost:8000       (docs: http://localhost:8000/docs)"
echo "   PostgREST:  http://localhost:3000"
echo "   Qdrant:     http://localhost:6333/dashboard"
echo
echo "   Estado:  ./scripts/status.sh"
echo "   Logs:    ./scripts/logs.sh"
echo "   Parar:   ./scripts/stop.sh"
