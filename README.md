# BJJ Biomechanics - Sistema de Evaluación Postural Asistido por IA

## Visión General

Sistema de asistencia técnica para Jiu-Jitsu Brasileño que utiliza visión artificial (**YOLO26x-Pose**) y modelos lingüísticos (**Gemini 2.5 Flash**) para evaluar la ejecución de técnicas mediante comparación biomecánica 3D.

El alumno graba su movimiento, el sistema extrae y compara su esqueleto 3D contra el patrón del instructor, y genera retroalimentación pedagógica personalizada con contexto extraído de literatura técnica mediante **RAG** (Retrieval-Augmented Generation) sobre **pgvector**.

---

## Arquitectura de Software (Larman — Proceso Unificado)

El sistema sigue una arquitectura en capas orientada a objetos para garantizar **Alta Cohesión** y **Bajo Acoplamiento**:

| Capa | Responsabilidad | Componentes Clave |
|------|----------------|-------------------|
| **Presentación** | PWA sin tecnicismos | `frontend/index.html`, `frontend/app.js`, FastAPI REST |
| **Aplicación** | Controladores de Casos de Uso | `EvaluacionController` (CU-02), `RegistrarTecnicaController` (CU-01) |
| **Servicios** | Pure Fabrication transversal | `SintesisPedagogicaService`, `ChunkerSemanticoBJJ` |
| **Dominio** | Lógica de negocio pura | `CalculadoraBiomecanica`, `TecnicaPatron`, `MatrizEsqueletica` |
| **Infraestructura** | Adaptadores y persistencia | YOLO26x (Colab), Gemini AI, PostgreSQL + pgvector |

### Casos de Uso Implementados

- **CU-01 — Registrar Patrón:** El instructor sube un video; el sistema extrae la `MatrizEsqueletica` patrón via YOLO26x y la persiste con su embedding vectorial.
- **CU-02 — Evaluar Ejecución:** El alumno sube su video; el sistema compara esqueletos, calcula `DesviacionArticular` y genera consejo pedagógico con RAG.

---

## Estructura del Proyecto

```text
JiuJitsu/
├── docs/                          # Documentación académica y técnica
│   └── MANUAL_DE_EJECUCION_REAL.md
├── src/
│   ├── domain/                    # Núcleo puro: Modelos, Interfaces, Lógica Biomecánica
│   │   ├── models.py              # Entidades: Profesor, TecnicaPatron, MatrizEsqueletica
│   │   └── interfaces.py          # Contratos ABC: IInferenceEngine, IProfesorRepository...
│   ├── application/               # Casos de Uso y Controladores GRASP
│   │   ├── controllers.py         # EvaluacionController (CU-02)
│   │   ├── pattern_controller.py  # RegistrarTecnicaController (CU-01)
│   │   ├── profesor_controller.py
│   │   ├── tecnica_controller.py
│   │   ├── fuente_controller.py
│   │   └── factory.py             # Fábrica de dependencias (Inyección de Dependencias)
│   ├── services/                  # Servicios de aplicación (Pure Fabrication — Larman)
│   │   ├── chunker_semantico.py       # Fragmentación semántica de manuales PDF (LangChain)
│   │   └── sintesis_pedagogica_service.py  # Orquestación RAG + Gemini
│   ├── infrastructure/            # Adaptadores concretos (Variaciones Protegidas)
│   │   ├── adapters/              # IA y hardware externo
│   │   │   ├── colab_adapter.py           # ColabYOLOAdapter → YOLO26x vía HTTP/Colab GPU
│   │   │   ├── yolo_adapter.py            # AdaptadorYOLO → orquestación + serialización JSONB
│   │   │   ├── gemini_adapter.py          # GeminiServiceAdapter → Gemini 2.5 Flash (raw)
│   │   │   ├── gemini_service_adapter.py  # AdaptadorGemini → orquestación con fallback 768d
│   │   │   └── gemini_embedding_adapter.py # GeminiEmbedding2Adapter → batch + retry 429
│   │   ├── persistence/           # Repositorios SQL y RAG (BCNF — Mannino)
│   │   │   ├── postgres_repository.py     # PostgresProfesor/Tecnica/FuenteRepository
│   │   │   ├── history_repository.py      # PostgresHistorialRepository
│   │   │   └── rag_ingestion.py           # IngestorRAG + PipelineIngestaRAG
│   │   └── mocks.py               # Dobles de prueba para TDD (sin GPU, sin BD)
│   └── presentation/              # API FastAPI y configuración de rutas
│       └── api.py
├── frontend/                      # PWA (Progressive Web App)
│   ├── index.html                 # SPA con vistas por rol (Instructor / Alumno)
│   ├── app.js                     # Lógica de presentación y consumo de API
│   └── style.css
├── tests/                         # Suite TDD completa (126 tests)
│   ├── test_domain.py             # Pruebas unitarias de lógica biomecánica pura
│   ├── test_application.py        # Pruebas de casos de uso
│   ├── test_integration.py        # Pruebas de integración API ↔ Dominio
│   ├── test_e2e_rag.py            # Pruebas E2E del pipeline RAG
│   └── test_abm_*.py              # Pruebas ABM (Profesores, Técnicas, Fuentes)
├── database/                      # Scripts de inicialización SQL (BCNF)
│   ├── 01_init.sql
│   ├── 02_historico.sql
│   ├── 03_instructores_fuentes.sql
│   └── 04_abm_bcnf.sql
├── tools/                         # Scripts utilitarios de desarrollo
│   └── volcar_todo_a_contexto.py  # Dump completo del código para contexto LLM
├── colab_backend.ipynb            # Notebook de inferencia YOLO26x en Google Colab GPU
├── docker-compose.yml             # PostgreSQL + pgvector
├── requirements.txt
└── .env.example                   # Plantilla de variables de entorno
```

---

## Requisitos Previos

- **Python 3.13+**
- **Docker y Docker Compose** (para PostgreSQL + pgvector)
- **Cuenta en Google AI Studio** (para API Key de Gemini)
- **Acceso a Google Colab Pro** (para inferencia YOLO26x en GPU)

---

## Instalación y Ejecución Local

```bash
# 1. Clonar repositorio
git clone <url-del-repositorio>
cd JiuJitsu

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales de Gemini y base de datos

# 3. Levantar base de datos PostgreSQL + pgvector
docker compose up -d

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar servidor local
uvicorn src.presentation.api:app --reload
```

La aplicación estará disponible en: `http://localhost:8000`

---

## Pruebas (TDD)

```bash
# Suite completa
pytest tests/ -v

# Solo pruebas de dominio (sin dependencias externas, < 1 segundo)
pytest tests/test_domain.py tests/test_application.py -v
```

**Cobertura actual:** 126 tests, 0 fallos.

---

## Base de Datos

El esquema sigue diseño **normalizado hasta BCNF** (Mannino, 7th Ed., Cap. 6-8):

| Tabla | Descripción |
|-------|-------------|
| `profesores` | Instructores registrados |
| `tecnicas_patron` | Técnicas con su `MatrizEsqueletica` en JSONB |
| `fuentes_conocimiento` | Manuales técnicos indexados con embeddings 768-dim |
| `historial_evaluaciones` | Registro de evaluaciones por alumno |

Inicialización automática con: `docker compose up -d`

---

## Metodología

| Aspecto | Metodología |
|---------|------------|
| **Desarrollo** | Proceso Unificado (Larman) con iteraciones cortas por Caso de Uso |
| **Patrones** | GRASP: Experto en Información, Controlador, Creador, Variaciones Protegidas, Pure Fabrication |
| **Calidad** | Test-Driven Development (TDD) — cobertura >90% en capa de dominio |
| **Base de datos** | Diseño normalizado BCNF (Mannino) con pgvector para búsqueda semántica |
| **IA Generativa** | RAG sobre `gemini-embedding-2` (768d) + `gemini-2.5-flash` para síntesis pedagógica |