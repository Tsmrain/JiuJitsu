# BJJ Biomechanics - Sistema de Evaluación Postural Asistido por IA

## Visión General

Sistema de asistencia técnica para Jiu-Jitsu Brasileño que utiliza visión artificial (**YOLO26x-Pose**) y modelos lingüísticos (**Gemini 2.5 Flash**) para evaluar la ejecución de técnicas mediante comparación biomecánica 3D.

El alumno graba su movimiento, el sistema extrae y compara su esqueleto 3D contra el patrón del instructor, y genera retroalimentación pedagógica personalizada con contexto extraído de literatura técnica mediante **RAG** (Retrieval-Augmented Generation) sobre **Qdrant Vector Database**.

---

## Arquitectura de Software (Larman — Proceso Unificado)

El sistema sigue una arquitectura en capas orientada a objetos para garantizar **Alta Cohesión** y **Bajo Acoplamiento**:

| Capa | Responsabilidad | Componentes Clave |
|------|----------------|-------------------|
| **Presentación** | PWA sin tecnicismos | `frontend/index.html`, `frontend/app.js`, FastAPI REST |
| **Aplicación** | Controladores de Casos de Uso | `EvaluacionController` (CU-02), `RegistrarTecnicaController` (CU-01) |
| **Servicios** | Pure Fabrication transversal | `SintesisPedagogicaService`, `ChunkerSemanticoBJJ` |
| **Dominio** | Lógica de negocio pura | `CalculadoraBiomecanica`, `TecnicaPatron`, `MatrizEsqueletica` |
| **Infraestructura** | Adaptadores y persistencia | YOLO26x (Colab), PostgreSQL (BCNF) + Qdrant (vectores 2048d) + Gemini 2.5 Flash (solo generación) |

### Casos de Uso Implementados

- **CU-01 — Registrar Patrón:** El instructor sube un video; el sistema extrae la `MatrizEsqueletica` patrón via YOLO26x y la persiste con su embedding vectorial.
- **CU-02 — Evaluar Ejecución con Síntesis Pedagógica Estructurada:** El alumno sube su video; el sistema compara esqueletos, calcula `DesviacionArticular`, recupera literatura técnica con RAG y orquesta **Gemini 2.5 Flash** para generar un reporte estructurado en 4 claves (`analisis_postural`, `riesgo_lesion`, `paso_a_paso`, `resumen_ejecutivo`).
  - **PWA Frontend:** Recibe una concatenación legible de `resumen_ejecutivo` y `paso_a_paso`.
  - **Persistencia Histórica:** Se almacena de forma íntegra en la columna `JSONB` (`consejo_pedagogico`) de la tabla `evaluaciones_alumno`.

---

## Síntesis Pedagógica Estructurada (Gemini 2.5 Flash SOLO Generación)

El flujo de evaluación biomecánica implementa una síntesis pedagógica estructurada bajo el principio de **Variaciones Protegidas**:
1. **Detección Biomecánica:** La capa de Dominio calcula el desajuste angular exacto frente al patrón del maestro.
2. **Recuperación Semántica (RAG):** Si la desviación supera el umbral, se busca contexto de manuales (ej. *Jiu Jitsu University*).
3. **Generación con Gemini 2.5 Flash:** El adaptador `GeminiServiceAdapter` se encarga **exclusivamente** de la generación del texto, delegando los embeddings a Qwen. Solicita un schema JSON con 4 claves:
   - `analisis_postural`: Diagnóstico biomecánico detallado del desajuste angular.
   - `riesgo_lesion`: Riesgo anatómico, sobrecarga articular o pérdida de apalancamiento mecánico.
   - `paso_a_paso`: Instrucciones secuenciales de reajuste corporal accionables por el alumno.
   - `resumen_ejecutivo`: Síntesis concisa para comprensión rápida inmediata.
4. **Almacenamiento JSONB (Mannino):** En la tabla `evaluaciones_alumno`, la columna `consejo_pedagogico` almacena el payload como tipo `JSONB` nativo (`psycopg2.extras.Json`).

---

## Estructura del Proyecto

```text
JiuJitsu/
├── docs/                          # Documentación académica y técnica
│   └── MANUAL_DE_EJECUCION_REAL.md
├── src/
│   ├── domain/                    # Núcleo puro: Modelos, Interfaces, Lógica Biomecánica
│   │   ├── models.py              # Entidades: Profesor, TecnicaPatron, MatrizEsqueletica
│   │   └── interfaces.py          # Contratos ABC: IInferenceEngine, IGenerationService...
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
│   │   │   ├── gemini_adapter.py          # GeminiServiceAdapter → Gemini 2.5 Flash estructurado JSON
│   │   │   ├── gemini_service_adapter.py  # AdaptadorGemini → orquestación
│   │   │   ├── qwen_embedding_adapter.py  # QwenEmbeddingAdapter → 2048d (GPU T4 Colab / Local)
│   │   │   └── qdrant_adapter.py          # QdrantAdapter → persistencia y búsqueda vectorial Local
│   │   ├── persistence/           # Repositorios SQL y RAG (BCNF — Mannino)
│   │   │   ├── postgres_repository.py     # PostgresProfesor/Tecnica/FuenteRepository
│   │   │   ├── history_repository.py      # PostgresHistorialRepository (JSONB)
│   │   │   └── rag_ingestion.py           # PipelineIngestaRAG (Qwen 2048d + Qdrant)
│   │   └── mocks.py               # Dobles de prueba para TDD (sin GPU, sin BD)
│   └── presentation/              # API FastAPI y configuración de rutas
│       └── api.py
├── frontend/                      # PWA (Progressive Web App)
│   ├── index.html                 # SPA con vistas por rol (Instructor / Alumno)
│   ├── app.js                     # Lógica de presentación y consumo de API
│   └── style.css
├── tests/                         # Suite TDD completa
│   ├── test_domain.py             # Pruebas unitarias de lógica biomecánica pura
│   ├── test_application.py        # Pruebas de casos de uso y DTO estructurado
│   ├── test_integration.py        # Pruebas de integración API ↔ Dominio ↔ JSONB
│   ├── test_e2e_rag.py            # Pruebas E2E del pipeline RAG
│   └── test_abm_*.py              # Pruebas ABM (Profesores, Técnicas, Fuentes)
├── database/                      # Scripts de inicialización SQL (BCNF)
│   ├── 01_init.sql
│   ├── 02_historico.sql           # Schema evaluaciones_alumno con JSONB
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
- **Docker y Docker Compose** (para PostgreSQL y Qdrant)
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

# 3. Levantar base de datos PostgreSQL y Qdrant
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

# Pruebas de aplicación e integración de evaluación
pytest tests/test_application.py tests/test_integration.py tests/test_iteracion4.py -v
```

**Cobertura actual:** 126 tests, 0 fallos.

---

## Base de Datos

El esquema sigue diseño **normalizado hasta BCNF** (Mannino, 7th Ed., Cap. 6-8):

| Tabla | Tipo Columna Clave | Descripción |
|-------|--------------------|-------------|
| `profesores` | - | Instructores registrados |
| `tecnicas_patron` | `matriz_esqueletica JSONB` | Técnicas con su `MatrizEsqueletica` en JSONB |
| `fuentes_conocimiento` | - | Manuales técnicos indexados para RAG (Persistencia vectorial delegada a Qdrant) |
| `evaluaciones_alumno` | `consejo_pedagogico JSONB` | Registro histórico con reporte pedagógico estructurado (4 claves) |

Inicialización automática con: `docker compose up -d`

---

## Metodología

| Aspecto | Metodología |
|---------|------------|
| **Desarrollo** | Proceso Unificado (Larman) con iteraciones cortas por Caso de Uso |
| **Patrones** | GRASP: Experto en Información, Controlador, Creador, Variaciones Protegidas, Pure Fabrication |
| **Calidad** | Test-Driven Development (TDD) |
| **Base de datos** | Diseño normalizado BCNF (Mannino) con Qdrant y JSONB |
| **IA Generativa** | RAG sobre embeddings + `gemini-2.5-flash` para síntesis pedagógica estructurada |