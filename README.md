# Corpo e Mente — Sistema Biomecánico

Sistema de análisis biomecánico con IA para la academia Corpo e Mente (Jiu-Jitsu).

## Quickstart

**Requisitos:** Docker Desktop, Python 3.11+, Node 18+.

```bash
# 1. Configurar backend
cp backend/.env.example backend/.env
# Editar backend/.env: GEMINI_API_KEY, POSTGREST_JWT_SECRET, JWT_SECRET_KEY

# 2. Instalar dependencias (solo la primera vez)
cd backend && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..

# 3. Arrancar
./scripts/start.sh
```

Abrí http://localhost:5173

## Comandos

| Comando | Qué hace |
|---|---|
| `./scripts/start.sh` | Arranca todo (idempotente, espera healthchecks) |
| `./scripts/stop.sh`  | Detiene backend, frontend y contenedores |
| `./scripts/status.sh`| Reporte de estado |
| `./scripts/logs.sh`  | Sigue logs de backend y frontend |
| `./scripts/reset-db.sh` | ⚠️ Destructivo: borra DB y vectores locales |

## Estructura

- `backend/` — FastAPI (domain/application/infrastructure/ui)
- `frontend/` — React + Vite
- `infrastructure/` — docker-compose + scripts SQL de initdb
- `scripts/` — orquestación local
- `docs/` — diseño, arquitectura
- `data/` — datos locales (gitignored)

