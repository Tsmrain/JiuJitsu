# BJJ Biomechanics — Sistema de Análisis Biomecánico de Jiu-Jitsu Brasileño

Tesis de Proyecto de Grado — UPSA — Ingeniería de Sistemas — 2026
Autor: Santiago Borda Zambrana

## Descripción

Sistema de análisis biomecánico de técnicas de BJJ mediante visión por
computadora (YOLO26x-Pose + YOLO26x-Depth), RAG (Qdrant + Qwen3-VL-Embedding-2B)
y síntesis pedagógica (Gemini 2.5 Flash), orquestado bajo el Proceso Unificado
de Craig Larman y una arquitectura en 5 capas.

## Estructura

| Directorio | Capa UP | Responsabilidad |
|------------|---------|-----------------|
| `src/presentation/` | Presentación | API REST FastAPI + PWA |
| `src/application/` | Aplicación | Controladores (Session Facades) |
| `src/services/` | Servicios | Pure Fabrications (RAG, Chunking) |
| `src/domain/` | Dominio | Entidades, Value Objects, Interfaces |
| `src/infrastructure/` | Infraestructura | Adaptadores, Repositorios |
| `frontend/` | Presentación | PWA (HTML/JS/CSS) |
| `tests/` | Testing | Pruebas unitarias e integración |
| `database/` | Persistencia | Esquemas SQL BCNF |
| `docs/` | Documentación | Tesis + diagramas UML |

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d
```

## Ejecución

```bash
uvicorn src.presentation.api:app --reload --port 8000
```

## Pruebas

```bash
pytest -q
```

## Documentación

- Tesis completa: `docs/Documento.pdf`
- Diagramas UML: `docs/Diagramas/`
- Especificación de arquitectura: `docs/GithubDoc.md`
