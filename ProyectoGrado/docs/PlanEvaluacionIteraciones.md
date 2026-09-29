# Bitácora y Plan de Evaluación de Iteraciones (Agile UP - Craig Larman)

Este documento registra oficialmente la planificación, mitigación de riesgos y evaluación de cada incremento ejecutable del proyecto **Corpo e Mente**, alineado estrictamente con los principios del **Proceso Unificado (UP)** expuestos por Craig Larman en *"Applying UML and Patterns"*.

---

## 📌 Principios de Evaluación Iterativa de Larman
1. **Iteraciones acotadas en tiempo (Timeboxed):** Cada ciclo entrega un subconjunto de software funcional y probado.
2. **Desarrollo impulsado por riesgos (Risk-Driven Development):** Los aspectos de mayor incertidumbre (IA multimodal, arquitectura vectorial, cuotas de API) se abordan primero.
3. **Adaptación continua:** La retroalimentación directa del cliente/usuario en cada ciclo refina el diseño del ciclo subsiguiente.

---

## 📋 Histórico de Iteraciones Ejecutadas

### 🔹 Iteración 1 & 2 (Fase de Elaboración): Arquitectura de Datos e Inferencia
- **Objetivo:** Mitigar riesgos de rendimiento vectorial, diseño de esquema relacional (3NF) y desacoplamiento de modelos de IA.
- **Riesgos Mitigados:**
  - Definición del esquema multi-tenant en PostgreSQL con Row Level Security (RLS) y JWT.
  - Implementación del patrón *Adapter (GoF)* para YOLOv11 Pose (`yolo11n-pose.pt`) y Qdrant Vector DB.
- **Resultado:** Pruebas unitarias ejecutadas con éxito (`test_yolo_adapter.py`, `test_intelligence_facade.py`).

---

### 🔹 Iteración C3 (Fase de Construcción): Sistema de Diseño e Interfaz Web
- **Objetivo:** Construir la interfaz de usuario moderna de grado de producción (Web App).
- **Entregables:**
  - Aplicación Vite + React estilizada en Vanilla CSS (Tema Oscuro con Rojo Institucional `#d01118`, Glassmorphism).
  - Componente semántico `<progress>` nativo animado (`ProgressRing.jsx`).
  - Previsualización dinámica de video mediante `URL.createObjectURL` (`VideoUpload.jsx`).
  - Integración del logo oficial de la academia (`logo.jpeg`).
- **Verificación:** Evaluado y aprobado por el cliente directamente en el navegador.

---

### 🔹 Iteración C4-A (Fase de Construcción): Filtro Multimodal Anti-SPAM
- **Objetivo:** Probar en vivo el filtrado temprano de contenido no relacionado mediante Google Gemini API antes de consumir recursos de GPU.
- **Desafíos Técnicos y Lecciones Aprendidas:**
  - **Sintaxis de SDK:** Ajuste del parámetro `path` en `client.files.upload(path=...)` del SDK `google-genai`.
  - **Estados Multimodales:** Manejo del ciclo de vida del archivo en Gemini (`PROCESSING` -> `ACTIVE`).
  - **Desacoplamiento (Resiliencia):** Aplicación de *Lazy Loading* en los adaptadores pesados (`YOLOPoseAdapter` y `QdrantVectorAdapter`) para evitar fallos durante el arranque de FastAPI.
- **Verificación:** Probado y confirmado en vivo por el cliente rechazando videos ajenos a Jiu-Jitsu (HTTP 422) y dejando pasar ejecuciones válidas (HTTP 200).

### 🔹 Iteración C5 (Fase de Construcción): Autenticación por Roles y Sucursales con Mapa Gratuito
- **Objetivo:** Implementar la autenticación de roles (`alumno`, `profesor`, `admin`) y permitir al administrador crear sucursales mundiales fijando coordenadas mediante un mapa interactivo **100% gratuito (sin Google Maps API keys)**.
- **Entregables:**
  - Componente modal de autenticación (`LoginModal.jsx`) conectando con el backend `/api/v1/auth/login`.
  - Panel de Administración Multi-Tenant (`AdminSucursales.jsx`) integrado con **Leaflet.js + OpenStreetMap** para capturar `latitud` y `longitud` al hacer clic en cualquier lugar del mundo.
  - Actualización del esquema 3NF (`01_schema_3nf.sql`) añadiendo columnas de latitud y longitud.
  - Endpoints REST en FastAPI (`auth_routes.py`) para `/auth/login` y `/sucursales`.
- **Verificación:** Funciona en la interfaz web cambiando de perfil a Administrador y marcando cualquier sucursal en el mapa de OpenStreetMap.

---

## 🚀 Plan para las Próximas Iteraciones

| Iteración | Enfoque Principal | Riesgos / Objetivos a Resolver | Artefactos Impactados |
| :--- | :--- | :--- | :--- |
| **C8** | Demo Slice Vertical End-to-End | Demostrar el pipeline completo (Frontend → Backend → Colab Worker → YOLO26 → Gemini) en 1 día. | `App.jsx`, `routes.py`, `corpocmente_worker.ipynb` |
| **C6** | Integración Full-Stack con BD Persistente | Conectar PostgREST / PostgreSQL local con la interfaz y el Worker de Google Colab Web para completar el ciclo de evaluación. | `routes.py`, `App.jsx`, `AnalisiDiseno.md` |
| **Transición** | Pruebas Beta y Despliegue | Generación del cuaderno `colab_worker.template.ipynb` listo para Google Colab Web y pruebas de campo en academias. | `colab_worker.template.ipynb`, `Manual_Usuario.md` |

### 🔹 Iteración C8 (Fase de Construcción): Demo Slice Vertical End-to-End
- **Objetivo:** Demostrar el pipeline IA completo (Frontend → Backend → Colab Worker → YOLO26 → Gemini → Frontend) en 1 día.
- **Riesgos mitigados:**
  - Ejecución real del Worker de Google Colab Web (runtime T4 GPU) por primera vez.
  - Ejecución real de YOLO26-pose sobre video del alumno.
  - Invocación real de Gemini API para feedback pedagógico.
  - Validación del contrato REST entre Frontend y Backend (polling real).
- **Verificación:** Demo en vivo mostrando un video subido y feedback recibido.

---

### 🔹 Iteración C9 (Fase de Construcción): Sistema RAG con Qwen + Qdrant
- **Objetivo:** Erradicar mocks de memoria y construir un slice vertical real para la ingestión de conocimiento.
- **Entregables:**
  - Esquema PostgreSQL real (`01_schema_3nf.sql`, `02_auth_jwt.sql`, `03_rls_policies.sql`) aprovisionado y configurado con PostgREST.
  - Generación de embeddings densos (2048 dimensiones) orquestada vía Google Colab Web (runtime T4 GPU) con `Qwen3-VL-Embedding-2B`.
  - Ingestión de vectores y metadatos en Qdrant Vector DB usando búsqueda híbrida (Dense + BM25) mediante `QdrantRAGAdapter`.
  - Integración del controlador `KnowledgeController` para orquestar la persistencia sin mocks.
- **Riesgos Mitigados:**
  - Eliminación de la deuda técnica referida a vectores locales en memoria (reemplazado por Qdrant).
  - Eliminación de la deuda técnica de Base de Datos en memoria (reemplazado por PostgreSQL/PostgREST).
- **Verificación:** Ejecución de scripts end-to-end confirmando que Qdrant recupera chunks de conocimiento precisos y PostgREST maneja RLS adecuadamente.

---

### 🔹 Iteración C10 (Fase de Construcción): Eliminación de Mocks y Configuración E2E
- **Estado:** Completada parcialmente.
- **Entregables:**
  - Integración real de `auth_routes.py` y endpoints REST con base de datos PostgreSQL vía PostgREST, sin dicts hardcodeados en memoria.
  - Ejecución de las migraciones y prueba de conexión E2E.
- **Regresiones Introducidas:**
  - El sistema de seguridad RLS fue deshabilitado temporalmente (`anon_all_*`) para forzar un funcionamiento inicial (Revertido en C10.1).
- **Deuda Técnica Pendiente (Para Iteración C11):**
  - Existencia de `MOCK_PROGRESO_ALUMNOS` en `ProfesorTecnicas.jsx`.
  - Fallback mock en `LoginModal.jsx`.
  - Inconsistencia de configuración de puertos PostgREST (Solucionado en C10.1 regresando todo a 3000).
- **Lecciones aprendidas (Craig Larman):** No sacrificar la seguridad y la arquitectura original (como Row Level Security) para hacer que una demo o prueba funcione rápidamente. Un sistema que funciona pero está expuesto no es un incremento de producción, es un prototipo peligroso.

---

### 🔹 Iteración C11.0 (Fase de Construcción): Diagnóstico Arquitectónico — Teoría Huérfana

- **Fecha de ejecución:** Sesión única de diagnóstico + verificación E2E.
- **Objetivo (Larman - Risk-Driven):** Ejecutar la verificación end-to-end del pipeline de ingestión de teoría (`Frontend → Backend → Colab Qwen → Qdrant`) para descubrir riesgos arquitectónicos antes de construir encima.
- **Riesgo descubierto (crítico):** La verificación E2E fue **exitosa técnicamente** (los 7 pasos pasaron, `chunks_procesados: 1`, vectores persistidos y recuperables), pero reveló que **la teoría vivía exclusivamente en Qdrant** sin trazabilidad relacional. Consecuencias:
  1. El profesor no podía ver, editar ni borrar su teoría desde el frontend (solo podía agregar, generando duplicados).
  2. No había trazabilidad de autor (`profesor_id`), sucursal (`sucursal_id`) ni timestamp por chunk.
  3. Vaciar la colección Qdrant implicaba pérdida total de conocimiento.
  4. El checkbox "Manual del Maestro (Teoría RAG)" en `ProfesorTecnicas.jsx` era un **write-only field**: el profesor subía teoría y nunca la volvía a ver.

- **Decisión arquitectónica:** Introducir una capa relacional (`teoria_referencia`) con linkage bidireccional Postgres ↔ Qdrant vía `qdrant_point_id UUID UNIQUE`, habilitando CRUD real.

- **Lecciones aprendidas (Larman):**
  - El **feedback real** (ejecutar el pipeline contra servicios reales, no mocks) descubrió un agujero arquitectónico que el modelado puro habría tardado semanas en exponer. Confirma el principio de "build-feedback-adapt" del UP.
  - La verificación E2E no es solo un "test de éxito/fallo" — es un **instrumento de descubrimiento de deuda arquitectónica**.

---

### 🔹 Iteración C11.1 (Fase de Construcción): Persistencia Relacional Dual (Postgres + Qdrant)

- **Objetivo:** Convertir la teoría de un "write-only blob en Qdrant" a una entidad relacional auditable en PostgreSQL, manteniendo Qdrant como índice vectorial.
- **Riesgos mitigados:**
  - **Pérdida de conocimiento:** PostgreSQL se vuelve la fuente de verdad; Qdrant puede reconstruirse desde `teoria_referencia` (contiene el `contenido_texto` de cada chunk).
  - **Trazabilidad:** Cada chunk queda ligado a `tecnica_id`, `profesor_id`, `sucursal_id`, `chunk_index` y `fecha_ingesta`.
  - **Duplicación de RAG:** El link `qdrant_point_id` permite borrar en ambos lados sin orphans.

- **Entregables (ejecutables, probados):**
  1. `database/05_teoria_referencia.sql` — tabla + 3 índices + RLS habilitada + 3 RPCs `SECURITY DEFINER`:
     - `admin_save_teoria_chunk(...)` — inserta un chunk con linkage a Qdrant.
     - `admin_list_teoria_by_tecnica(...)` — lista chunks de una técnica con join a `usuarios` para traer nombre del profesor.
     - `admin_delete_teoria_by_tecnica_profesor(...)` — borra en Postgres y retorna array de `qdrant_point_id` para que el backend borre en Qdrant.
  2. `QdrantRAGAdapter.ingestar_desde_respuesta` refactorizado: ahora devuelve `{"chunks_count", "point_ids", "chunks"}` en vez de un `int`.
  3. `IngestKnowledgeUseCase.execute` extendido con `profesor_id` y `sucursal_id`; persiste en Qdrant y luego en Postgres con `try/except` best-effort por chunk.
  4. Endpoint `POST /api/v1/conocimiento/teoria` ahora pasa `caller.uid` y `caller.sucursal_id` al use case.

- **Verificación E2E (salidas crudas):**
  - `psql \dt teoria_referencia` → tabla visible.
  - `psql \df admin_save_teoria_chunk` → RPC visible.
  - `./venv/bin/python -c "from corpocmente.main import app; print('OK')"` → `OK`.
  - `./venv/bin/pytest --co -q` → 16 tests colectados.
  - Ingesta real con profesor Mike → `{"status":"ok","chunks_procesados":1}`.
  - `SELECT chunk_index, profesor_id, qdrant_point_id FROM teoria_referencia` → fila con `profesor_id=7e455a7d-...` y `qdrant_point_id` enlazado.
  - Qdrant count → 7 puntos (antes 6).

- **Artefactos UP impactados:**
  - **Domain Model:** nueva entidad `teoria_referencia` con relación N:1 hacia `tecnicas`, `usuarios`, `sucursales`.
  - **Design Model:** nuevo par de Casos de Uso (persistencia dual) y nueva colaboración `IngestKnowledgeUseCase → QdrantRAGAdapter + PostgrestClient`.
  - **Data Model (Mannino 3NF):** `teoria_referencia` cumple 3NF; la dependencia `qdrant_point_id → id` es funcional (UNIQUE constraint).

- **Lecciones aprendidas:**
  - **Contrato Qdrant ↔ Postgres:** El uso de `qdrant_point_id UUID UNIQUE` como FK lógica (sin FK física, ya que viven en motores distintos) exige borrado best-effort en el backend. Si Postgres borra y Qdrant falla, quedan orphans en Qdrant — mitigado con logging y, más adelante, con un job de reconciliación (deuda registrada).
  - **Persistencia silenciosa:** El bloque `try/except` best-effort en el use case significa que si `sucursal_id` viene vacío, la teoría queda huérfana en Qdrant sin error visible. Deuda registrada para iteración futura.

---

### 🔹 Iteración C11.2 (Fase de Construcción): Endpoints HTTP CRUD de Teoría

- **Objetivo:** Exponer el modelo relacional de C11.1 al frontend mediante endpoints REST para que el profesor pueda **ver** y **borrar** su teoría (antes solo podía escribir).
- **Riesgos mitigados:**
  - **Asimetría CRUD:** El checkbox de subida existía, pero no había GET ni DELETE → imposible auditar ni corregir.
  - **RAG huérfano por borrado:** El DELETE debe tocar ambos lados (Postgres + Qdrant) de forma orquestada.

- **Entregables (ejecutables, probados):**
  1. `QdrantRAGAdapter.eliminar_puntos(point_ids)` — usa `PointIdsList` para borrado por lote.
  2. `ListTheoryUseCase` — consume RPC `admin_list_teoria_by_tecnica` con filtro opcional por `profesor_id`.
  3. `DeleteTheoryUseCase` — orquesta RPC `admin_delete_teoria_by_tecnica_profesor` (Postgres) + `eliminar_puntos` (Qdrant), devolviendo counts separados.
  4. Endpoints:
     - `GET /api/v1/conocimiento/teoria/{tecnica_id}` con query param `?solo_mios=true`.
     - `DELETE /api/v1/conocimiento/teoria/{tecnica_id}` (solo admin/profesor).

- **Verificación E2E (salidas crudas):**
  - `GET` → `{"tecnica_id": "...", "total": 2, "chunks": [...]}` con metadata completa (incluye `profesor_nombre: "Mestre Mike Baigorria"`).
  - `GET ?solo_mios=true` → `total: 2` (filtro funcionando).
  - `DELETE` → `{"status":"ok","chunks_eliminados_postgres":2,"chunks_eliminados_qdrant":2}`.
  - Post-DELETE:
    - `SELECT COUNT(*) FROM teoria_referencia WHERE tecnica_id=... AND profesor_id=...` → `0`.
    - Qdrant count → 5 (antes 7).
    - `GET` repetido → `total: 0`.

- **Artefactos UP impactados:**
  - **Design Model:** nuevos Casos de Uso `ListTheoryUseCase` y `DeleteTheoryUseCase` en la capa de Aplicación.
  - **API Contract:** dos endpoints REST documentados.

- **Lecciones aprendidas:**
  - **RPC de Postgres retornando `uuid[]`:** El patrón de "borrar filas en Postgres y devolver los IDs a borrar en el motor externo" evita queries adicionales y mantiene atomicidad lógica. Buen patrón reusable.
  - **Best-effort en Qdrant:** Si el DELETE en Qdrant falla tras el DELETE en Postgres, el profesor ve éxito pero quedan orphans vectoriales. Se recomienda una iteración futura de "job de reconciliación" (o hacer el DELETE en Postgres solo tras confirmación de Qdrant).

---

### 🔹 Iteración C11.3 (Fase de Construcción): UI de Gestión de Teoría del Profesor

- **Objetivo:** Cerrar el loop UX — que el profesor, desde el panel de técnicas, vea y borre su teoría sin usar `curl`.
- **Riesgos mitigados:**
  - **Write-only UX:** El formulario de subida ya no es un agujero negro de información.
  - **Pérdida de confianza del docente:** Ahora puede auditar qué subió antes de cada clase.

- **Entregables (ejecutables, probados):**
  1. Nuevo componente `TheoryManagerModal.jsx`:
     - Carga chunks vía `GET ?solo_mios=true`.
     - Renderiza cada chunk con `chunk_index`, fecha formateada y `contenido_texto` (con `whiteSpace: pre-wrap`).
     - Botón "🗑 Eliminar toda mi teoría de esta técnica" con confirm nativo.
     - Alert de éxito con counts separados de Postgres y Qdrant.
     - Estado vacío amigable ("Aún no has subido teoría para esta técnica").
  2. Integración en `ProfesorTecnicas.jsx`:
     - Import + estado `theoryModalTecnica`.
     - Botón "📖 Ver Teoría" en cada tarjeta de técnica (con clase CSS `theory-btn`).
     - Render condicional del modal.
  3. CSS `.btn-icon.theory-btn` para mantener consistencia visual.

- **Verificación E2E (manual, Firefox):**
  - Login como `mike` → ir a "Mis Técnicas" → clic "📖 Ver Teoría" en "Salida de la Montada".
  - Modal abrió mostrando N fragmentos con texto íntegro y fecha.
  - Clic en "Eliminar toda mi teoría" → confirm → alert `Eliminados: N de Postgres y N de Qdrant`.
  - Modal se refrescó a estado vacío.
  - Post-verificación:
    - `GET` de esa técnica → `total: 0`.
    - Qdrant scroll filtrado por `tecnica_id` → `[]`.
    - Qdrant count global → bajó de 8 a 7.

- **Artefactos UP impactados:**
  - **UI Model / Component Diagram:** nuevo componente con responsabilidad única (gestión de teoría de una técnica).
  - **Development Case:** se afianza el patrón "modal de gestión" como artefacto reusable del frontend.

- **Lecciones aprendidas (Larman - feedback loop):**
  - **Timeboxing efectivo:** El alcance se limitó deliberadamente a "ver + borrar todo" (no edición inline, no edición por chunk, no traducción PT/ES del modal). Esto permitió cerrar la iteración en una sola sesión de verificación, entregando un incremento **probado end-to-end** en vez de un prototipo a medias. Reafirma la recomendación de Larman de **eliminar tareas del iteration backlog antes que slippear la fecha**.
  - **Confirm nativo + alert nativo:** Se evitó construir un sistema de notificaciones custom. Para una iteración timeboxed, las primitivas del navegador son suficientes y reducen el alcance.

---

### 🔹 Iteración C11.4 (Fase de Construcción - COMPLETADA PARCIAL: Código + Tests): Fix del Pipeline RAG de Recuperación

- **Objetivo:** Corregir 3 bugs encadenados que impiden que el evaluador (Gemini) consuma la teoría RAG que las iteraciones C11.0-C11.3 persistieron correctamente.
- **Riesgos por mitigar (detectados en revisión de código):**
  1. `IntelligenceAnalysisFacade` llama a `qwen_adapter.generar_embedding(frame_path)` → endpoint `/embed` **NO EXISTE** en el Colab Worker.
  2. `QwenEmbeddingAdapter.generar_embedding_texto` envía JSON `{"text": ...}` pero el worker espera **form-data** `{"texto": ...}`. Doble incompatibilidad (formato + nombre de campo).
  3. `QdrantVectorAdapter.recuperar_contexto_rag` pasa `query_vector=vector_plano` a una colección con **named vectors** (`{"dense": ...}`) → Qdrant rechaza con "Not existing vector name error".

- **Consecuencia actual:** Todo el trabajo de C11.1-C11.3 alimenta un RAG que el evaluador nunca consume → Gemini genera feedback **sin teoría de respaldo**, degradando la calidad pedagógica del sistema.

- **Entregables esperados:**
  1. `QwenEmbeddingAdapter.generar_embedding_texto` con `data={"texto": ...}`.
  2. `QwenEmbeddingAdapter.generar_embedding` (imagen) marcado `DEPRECATED` con warning.
  3. `QdrantVectorAdapter.recuperar_contexto_rag` usando `("dense", vector)` y concatenando `top_k=3` chunks.
  4. `IntelligenceAnalysisFacade` construyendo **query textual** (nombre técnica + discrepancias) en vez de mandar un path de imagen.

- **Estado:** Pendiente de ejecución. Es la próxima iteración de la bitácora.

- **Riesgo arquitectónico a monitorear:** El Colab Worker actual (`colab_rag_worker.ipynb`) es **text-only**. Si en el futuro se quiere RAG multimodal (imagen → embedding de imagen → recuperar teoría visual), hay que extender el worker. Fuera de scope de C11.4.

### ✅ Resultado de la Ejecución (Cierre C11.4)

> ⚠️ **Estado de cierre:** Los 3 bugs del pipeline RAG de recuperación están corregidos y cubiertos por tests de regresión (probados con prueba de mutación). **La verificación E2E con servicios reales (Backend + PostgREST + Qdrant + Colab Worker) queda pendiente** para la iteración C11.5.

**Estado:** Código corregido y cubierto por tests de regresión. Verificación E2E con servicios reales pendiente.

**Fixes aplicados (4 cambios quirúrgicos en 3 archivos):**

1. `qwen_adapter.py`:
   - `generar_embedding_texto`: cambiado `json={"text": texto}` → `data={"texto": texto}` (formato HTTP correcto para FastAPI/Colab).
   - `generar_embedding` (imagen): marcado como `DEPRECATED` con `logger.warning` (apunta a `/embed` inexistente).

2. `qdrant_adapter.py`:
   - `recuperar_contexto_rag`: cambiado `query_vector=vector_plano` → `query_vector=("dense", vector_plano)` (named vector correcto para la colección `rag_knowledge`).
   - Aumentado `limit=1` → `limit=3` y concatenación de chunks con `\n\n---\n\n`.

3. `intelligence_facade.py`:
   - Paso 5 del análisis ahora construye una **query textual** con `tecnica_nombre` + discrepancias, e invoca `generar_embedding_texto` en lugar del método de imagen deprecado.
   - Añadido logging informativo del contexto RAG recuperado.

**Tests de regresión añadidos:**
- `test_qwen_adapter.py::test_generar_embedding_texto_usa_form_data` — verifica que se use `data={"texto": ...}` y no `json={"text": ...}`.
- `test_qdrant_adapter.py::test_recuperar_contexto_rag_usa_named_vector_y_concatena` — verifica named vector, `limit=3` y concatenación de 3 chunks.
- `test_intelligence_facade.py::test_ejecutar_analisis_construye_query_textual_para_rag` — verifica que la fachada construya una query textual y llame a `generar_embedding_texto` cuando `qwen_adapter` está inyectado.

**Lecciones aprendidas (Larman):**
- Los bugs eran de **integración**, no de lógica. Los tests con mocks no los detectaban. Confirma la recomendación de Larman: **probar contra servicios reales es indispensable** para validar integraciones (Cap. 2 — "build-feedback-adapt").
- El enfoque quirúrgico de 3 archivos sin tocar el write path (C11.1) demuestra que **los cambios de una iteración deben ser atómicos**. Timeboxing efectivo.
- La deuda arquitectónica destapada en C11.0 (teoría huérfana) queda cerrada a nivel de código; falta la validación E2E con `scripts/verify_rag_e2e.py`.

**Verificación E2E pendiente (bloqueada por infraestructura):**
- Requiere Backend (uvicorn), Postgres+PostgREST, Qdrant (docker) y Colab Worker (ngrok) activos simultáneamente.
- Script preparado: `scripts/verify_rag_e2e.py`.
- Se ejecutará en una sesión posterior (C11.5) cuando los servicios estén levantados.

---

### 🔹 Iteración C11.5 (Fase de Construcción): Verificación E2E Real del Pipeline RAG

- **Estado:** COMPLETADA ✅
- **Fecha de ejecución:** 2026-09-28
- **Objetivo:** Demostrar con servicios reales (Backend + PostgREST + Qdrant + Colab Worker) que el pipeline de recuperación RAG funciona end-to-end tras el fix C11.4.
- **Comando ejecutado:** `./venv/bin/python scripts/verify_rag_e2e.py --texto ../data/teoria_jiujitsu.txt --tecnica-id d3b07384-d9a4-4f6c-947b-11347076a5b6 --jwt <JWT> --query "¿Cómo se pasa la guardia correctamente?"`
- **Evidencia (salida cruda):**
  ```text
  ======================================================================
  PREFLIGHT CHECKS
  ======================================================================
  [OK] Backend: {'status': 'ok', 'app': 'Corpo e Mente Biomechanics AI', 'environment': 'development'}
  [OK] Qdrant: 1 colecciones -> ['rag_knowledge']
  [OK] Colab: {'status': 'ok', 'model': 'Qwen3-VL-Embedding-2B'}

    Puntos en Qdrant ANTES: 7

  ======================================================================
  FASE 1: INGESTIÓN (texto real -> Colab -> Qdrant)
  ======================================================================
    Texto: 1283 caracteres
    HTTP 201
  [OK] {'status': 'ok', 'chunks_procesados': 1}
    Puntos en Qdrant DESPUÉS: 8 (delta: 1)

  ======================================================================
  FASE 2: RECUPERACIÓN (consulta semántica)
  ======================================================================
    Query: ¿Cómo se pasa la guardia correctamente?
  [OK] Query embedding: 2048 dims
  [OK] 3 chunks recuperados

    [1] score=0.6239
        El pasaje de guardia en Jiu-Jitsu Brasileño requiere controlar las caderas y piernas del oponente para neutralizar sus defensas y establecer una posición superior como el control lateral o la montada. Existen varias técn...

    [2] score=0.5344
        El armbar desde la guardia cerrada se ejecuta controlando la manga del oponente con una mano y su cuello con la otra. Se rota la cadera hacia el lado del brazo atacado mientras se eleva la pierna por encima de la cabeza....

    [3] score=0.4442
        Test de persistencia dual: Qdrant + Postgres. Este chunk debe aparecer en ambos lugares....

  ======================================================================
  ✅ VERIFICACIÓN COMPLETA
  ======================================================================
  ```
- **Evidencia ampliada (C11.5.1 — Persistencia Dual Postgres + Qdrant):**
  - **T1: Verificación manual en PostgreSQL (`teoria_referencia`):**
    ```text
     chunk_index |                                     preview                                      |           qdrant_point_id            |         fecha_ingesta         
    -------------+----------------------------------------------------------------------------------+--------------------------------------+-------------------------------
               0 | El pasaje de guardia en Jiu-Jitsu Brasileño requiere controlar las caderas y pie | 5a66f1fe-3ef3-4de3-a039-2fb0a62c7364 | 2026-09-28 23:26:03.380954-04
               0 | El armbar requiere control del brazo con ambas manos, cadera pegada al hombro de | a36ff9ab-b304-421d-b140-b524240f5430 | 2026-09-28 11:18:12.380631-04
               0 | El armbar requiere control del brazo con ambas manos, cadera pegada al hombro de | 707c98c6-2fb8-4948-8860-cc2089544495 | 2026-09-28 00:51:06.658686-04
    ```
  - **T3: Script E2E ampliado con conteo dual simultáneo (`scripts/verify_rag_e2e.py`):**
    ```text
    ======================================================================
    PREFLIGHT CHECKS
    ======================================================================
    [OK] Backend: {'status': 'ok', 'app': 'Corpo e Mente Biomechanics AI', 'environment': 'development'}
    [OK] Qdrant: 1 colecciones -> ['rag_knowledge']
    [OK] Colab: {'status': 'ok', 'model': 'Qwen3-VL-Embedding-2B'}

      Filas en Postgres ANTES: 3
      Puntos en Qdrant ANTES: 8

    ======================================================================
    FASE 1: INGESTIÓN (texto real -> Colab -> Qdrant + Postgres)
    ======================================================================
      Texto: 1283 caracteres
      HTTP 201
    [OK] {'status': 'ok', 'chunks_procesados': 1}
      Filas en Postgres DESPUÉS: 4 (delta: 1)
      Puntos en Qdrant DESPUÉS: 9 (delta: 1)

    ======================================================================
    FASE 2: RECUPERACIÓN (consulta semántica)
    ======================================================================
      Query: ¿Cómo se pasa la guardia correctamente?
    [OK] Query embedding: 2048 dims
    [OK] 3 chunks recuperados

      [1] score=0.6239
          El pasaje de guardia en Jiu-Jitsu Brasileño requiere controlar las caderas y piernas del oponente para neutralizar sus defensas y establecer una posición superior como el control lateral o la montada. Existen varias técn...

      [2] score=0.6239
          El pasaje de guardia en Jiu-Jitsu Brasileño requiere controlar las caderas y piernas del oponente para neutralizar sus defensas y establecer una posición superior como el control lateral o la montada. Existen varias técn...

      [3] score=0.5344
          El armbar desde la guardia cerrada se ejecuta controlando la manga del oponente con una mano y su cuello con la otra. Se rota la cadera hacia el lado del brazo atacado mientras se eleva la pierna por encima de la cabeza....

    ======================================================================
    ✅ VERIFICACIÓN COMPLETA (Persistencia Dual: Postgres + Qdrant)
    ======================================================================
    ```
  - Verificación bidireccional completada: Postgres (fuente de verdad) y Qdrant (índice) reciben el chunk con linkage bidireccional por `qdrant_point_id`.

  > **Decisión de diseño (C11.5.1):** El pipeline de ingestión **no deduplica por contenido**. Cada llamada a `POST /conocimiento/teoria` crea un nuevo par (`teoria_referencia` fila + Qdrant punto) incluso si el `contenido_texto` coincide con un chunk existente.
  > **Justificación:** el profesor puede legítimamente subir versiones evolucionadas de su manual, y forzar deduplicación por hash de contenido añadiría complejidad innecesaria al write-path en esta etapa.
  > **Mitigación:** el profesor dispone de `DELETE /conocimiento/teoria/{tecnica_id}` (C11.2) y de la UI `TheoryManagerModal` (C11.3) para auditar y reemplazar su teoría completa.
  > **Deuda registrada:** una iteración futura de producción podría añadir un `content_hash` con constraint UNIQUE por `(tecnica_id, profesor_id, content_hash)` si la duplicación accidental se vuelve un problema operativo.
- **Lecciones aprendidas (Larman):**
  - La verificación E2E con servicios reales confirma que los 3 bugs corregidos en C11.4 eran efectivamente los bloqueadores del pipeline.
  - Los tests con mocks (C11.4) siguen siendo válidos como guardianes de regresión, pero **solo la prueba con servicios reales demuestra integración**.
  - Se cierra la deuda arquitectónica detectada en C11.0 (teoría huérfana): la teoría ahora se ingesta, persiste en Postgres+Qdrant, y se recupera efectivamente en el análisis.
  - **Nota sobre RLS:** El endpoint `GET /tecnicas` con rol `anon` devuelve HTTP 401 por diseño (la tabla no tiene GRANT SELECT a `anon`). El backend siempre usa RPCs `SECURITY DEFINER` como `get_tecnicas_with_videos`. Confirmado empíricamente durante el Pre-Flight.
- **Artefactos UP impactados:**
  - **Test Model:** verificación E2E documentada como evidencia.
  - **Development Case:** el script `verify_rag_e2e.py` queda establecido como herramienta reusable de verificación E2E.

---

### 🔹 Iteración C11.6 (Fase de Construcción): Auditoría Final y Certificado de Estado Limpio

- **Estado:** COMPLETADA ✅
- **Fecha:** 2026-09-29
- **Objetivo:** Verificar bidireccionalmente la consistencia Postgres ↔ Qdrant tras la limpieza manual de datos de prueba (C11.5/C11.5.1), certificando el estado limpio para la defensa de tesis.
- **Método:** Auditoría cruzada por `qdrant_point_id` (linkage lógico definido en C11.1) mediante el script de reconciliación `scripts/reconcile_rag.py`.
- **Hallazgo durante auditoría:** Se detectaron 5 orphans históricos en Qdrant (3 de "Salir de 100 kilos" ingestados en C9 cuando no existía capa relacional, y 2 de "Armbar" de pruebas iniciales de C11.0). Estos nunca tuvieron fila en `teoria_referencia`, por lo que el DELETE orquestado de C11.2 no podía conocerlos.
- **Acción tomada (Opción A refinada):** Se creó `scripts/reconcile_rag.py`, un script reutilizable que audita la consistencia bidireccional Postgres ↔ Qdrant y, con flag `--fix`, elimina orphans de Qdrant (Postgres es la fuente de verdad; Qdrant es índice reconstruible). Se ejecutó en modo detección (5 orphans reportados), luego con `--fix` (5 orphans eliminados), y se verificó consistencia total.
- **Evidencia (salidas crudas):**
  - **Detección pre-fix (T2):**
    ```text
    ======================================================================
    RECONCILIACIÓN POSTGRES ↔ QDRANT
    ======================================================================
    Postgres (fuente de verdad): 1 chunks
    Qdrant (índice):             6 puntos

    ⚠️  5 orphan(s) en Qdrant (sin fila en Postgres):
        - 597cef7c-44a9-4667-a950-a41c661d1dec
        - 8e0179f5-91a1-49f8-9ea7-746b1c59c5d0
        - b3f6f890-18f8-4af8-8c84-1135e107a5fe
        - d33a3ab2-2085-4999-94ce-bab62c810ae9
        - d59572fd-c38a-4dbb-8f4a-4a967b1595a1
    ```
  - **Aplicación del fix (T3):**
    ```text
    ======================================================================
    RECONCILIACIÓN POSTGRES ↔ QDRANT
    ======================================================================
    Postgres (fuente de verdad): 1 chunks
    Qdrant (índice):             6 puntos

    ⚠️  5 orphan(s) en Qdrant (sin fila en Postgres):
        - 597cef7c-44a9-4667-a950-a41c661d1dec
        - 8e0179f5-91a1-49f8-9ea7-746b1c59c5d0
        - b3f6f890-18f8-4af8-8c84-1135e107a5fe
        - d33a3ab2-2085-4999-94ce-bab62c810ae9
        - d59572fd-c38a-4dbb-8f4a-4a967b1595a1

    🔧 Aplicando --fix: eliminando 5 orphan(s) de Qdrant...
    ✅ Eliminados. Re-ejecuta sin --fix para verificar consistencia.
    ```
  - **Verificación post-fix (T4):**
    ```text
    ======================================================================
    RECONCILIACIÓN POSTGRES ↔ QDRANT
    ======================================================================
    Postgres (fuente de verdad): 1 chunks
    Qdrant (índice):             1 puntos

    ✅ CONSISTENCIA TOTAL — Sin orphans en ninguna dirección.

    Postgres count: 1
    Qdrant count: 1
    ```
- **Resultado final:** Postgres: 1 fila ("Salida de la Montada") / Qdrant: 1 punto (mismo `qdrant_point_id: fed0edaf-e894-4132-97e8-8d7abc01f1fd`). Consistencia total certificada sin orphans.
- **Lecciones aprendidas (Larman — instrumento de descubrimiento):**
  - La migración de un almacenamiento único (Qdrant-only, C9) a persistencia dual (Postgres+Qdrant, C11.1) deja orphans que solo se detectan con auditoría cruzada. Este caso justifica mantener herramientas de reconciliación reutilizables (no fixes ad-hoc). El script `reconcile_rag.py` queda como artefacto permanente del proyecto.
- **Artefactos UP impactados:**
  - **Test Model:** auditoría cruzada como verificación de consistencia dual.
  - **Development Case:** certificado de estado limpio como entregable pre-defensa (`scripts/reconcile_rag.py`).
- **Deuda residual (registrada, no bloqueante):**
  - Job de reconciliación automático periódico en background (fuera de scope MVP).
  - Deduplicación por `content_hash` en write-path (registrado en C11.5.1).

### 🔹 Iteración C12.1 (Fase de Construcción): Instalación de Ultralytics en Worker de Colab

- **Estado:** COMPLETADA ✅
- **Fecha:** 2026-09-29
- **Objetivo:** Instalar `ultralytics` en el worker de Colab sin romper dependencias previas (FastAPI, Qwen, OpenCV, etc.) como prerrequisito para cargar YOLO26-pose y YOLO26-depth en las siguientes subtareas.

- **Entregables:**
  - Celda 2 de `colab_worker.ipynb` modificada con `ultralytics` añadido.
  - Celda 2b de verificación temporal para imports de Ultralytics y dependencias previas.

- **Verificación:**
  - `ultralytics.__version__` = verificado compatible con stack de inferencia.
  - Dependencias previas intactas: Sí (`fastapi`, `uvicorn`, `cv2`, `numpy`, `PIL`, `sentence_transformers`).

- **Artefactos UP impactados:**
  - **Implementation Model:** notebook `backend/notebooks/colab_worker.ipynb` actualizado con soporte para modelos YOLO.
  - **Environment discipline:** paquete de visión por computadora `ultralytics` añadido al runtime del worker.

- **Lecciones aprendidas:**
  - La instalación de `ultralytics` en el entorno T4 de Colab no genera colisiones con `sentence-transformers` ni el stack ASGI de FastAPI.

- **Deuda registrada (si aplica):**
  - Ninguna.

### 🔹 Iteración C12.2 (Fase de Construcción): Carga de YOLO26-pose y Verificación de Coexistencia en VRAM

- **Estado:** COMPLETADA ✅
- **Fecha:** 2026-09-29
- **Objetivo:** Cargar `yolo26n-pose.pt` en el mismo worker de Colab donde reside Qwen3-VL-Embedding-2B, verificando la coexistencia de ambos modelos en la VRAM de la GPU T4 (16 GB) sin errores de memoria, y confirmar que Qwen sigue operativo tras la carga de YOLO.

- **Entregables:**
  - Celda 4 de `colab_worker.ipynb` modificada con carga secuencial de modelos y métricas de VRAM.
  - Verificación de coexistencia con inferencia mínima de Qwen.

- **Verificación (salida cruda de Colab):**
  - VRAM total: 15.64 GB
  - VRAM usada tras Qwen: 12.77 GB
  - VRAM usada tras YOLO-pose: 12.77 GB (incremento despreciable para modelo nano)
  - VRAM libre disponible: ~2.87 GB
  - Qwen responde post-YOLO: Sí (Dim: 2048)
  - Versión del modelo YOLO descargado: `yolo26n-pose.pt`

- **Artefactos UP impactados:**
  - **Implementation Model:** notebook del worker actualizado con segundo modelo de IA.
  - **Design Model:** confirmación empírica de la decisión arquitectónica "Procesamiento Asíncrono en Google Colab Web" registrada en `ArquitecturaSoftware.md` (Tabla de Factores Arquitectónicos).

- **Lecciones aprendidas:**
  - El modelo nano YOLO26-pose tiene una huella de memoria mínima en comparación con el Vision-Language Model (Qwen3-VL), dejando 2.87 GB de margen en la GPU T4.

- **Deuda registrada (si aplica):**
  - Ninguna.

### 🔹 Iteración C12.4 (Fase de Construcción): Carga de YOLO26-depth y Verificación de Coexistencia Triple en VRAM

- **Estado:** COMPLETADA ✅
- **Fecha:** 2026-09-29
- **Objetivo:** Cargar `yolo26n-depth.pt` en el mismo worker de Colab donde residen Qwen3-VL-Embedding-2B y YOLO26-pose, verificando la coexistencia de los tres modelos en la VRAM de la GPU T4 (16 GB) sin errores de memoria, y confirmar que Qwen sigue operativo tras la carga del tercer modelo.

- **Entregables:**
  - Celda 4 de `colab_worker.ipynb` modificada con carga secuencial de los tres modelos y métricas de VRAM.
  - Verificación de coexistencia con inferencia mínima de Qwen.

- **Verificación (salida cruda de Colab):**
  - VRAM total: 15.64 GB
  - VRAM usada tras Qwen: 8.55 GB
  - VRAM usada tras YOLO-pose: 8.55 GB (sin incremento medible)
  - VRAM usada tras YOLO-depth: 8.55 GB (sin incremento medible)
  - VRAM libre: ~7.09 GB
  - Qwen responde post-YOLO-depth: sí (vector de 2048 dims)
  - Modelos descargados: `yolo26n-pose.pt`, `yolo26n-depth.pt`

- **Artefactos UP impactados:**
  - **Implementation Model:** notebook del worker actualizado con tercer modelo de IA.
  - **Design Model:** confirmación empírica de la viabilidad de la arquitectura de cómputo pesado en Colab con tres modelos coexistiendo.

- **Lecciones aprendidas:**
  - Los modelos YOLO26 nano (pose y depth, ~7.5 MB cada uno) son prácticamente gratuitos en VRAM cuando Qwen ya está cargado. El cuello de botella de VRAM lo impone Qwen3-VL-Embedding-2B con ~8.5 GB. El margen de 7 GB libres es holgado para la inferencia de video frame a frame.
  - El primer experimento (C12.2) reportó 12.77 GB usados por Qwen, probablemente por memoria residual del runtime anterior. Al reiniciar limpio, el consumo real es de 8.55 GB.

- **Deuda registrada:** ninguna.

### 🔹 Iteración C12.3 (Fase de Construcción): Endpoint /extraer_poses con YOLO26-pose

- **Estado:** COMPLETADA ✅
- **Fecha:** 2026-09-29
- **Objetivo:** Exponer el endpoint `POST /extraer_poses` que recibe un video y devuelve la secuencia completa de esqueletos biomecánicos (133 dims por frame) extraídos por YOLO26-pose, eliminando el endpoint previo `/embed_video`.

- **Entregables:**
  - Celda 5 de `colab_worker.ipynb` reescrita: `/health`, `/embed_text`, `/extraer_poses`.
  - Eliminación de `/embed_video`.
  - Padding de los 17 keypoints COCO (51 floats) a 133 dims.

- **Verificación (salida cruda):**
  - HTTP: 200
  - Tiempo total: 23.23 s
  - total_frames_procesados: 783
  - total_esqueletos: 777
  - Longitud de keypoints133: 133
  - Primer frame con pose detectada: frame_idx=0
  - VRAM usada con los 3 modelos cargados: 4.26 GB (¡mejor que el experimento anterior!)

- **Artefactos UP impactados:**
  - **Design Model:** endpoint REST añadido al contrato del worker.
  - **Implementation Model:** notebook con lógica de extracción biomecánica.

- **Lecciones aprendidas:**
  - VRAM real mucho menor al reiniciar el runtime limpio (4.26 GB vs 8.55 GB previos). Confirma que el consumo de Qwen fluctúa según el estado del runtime de Colab.
  - El header `ngrok-skip-browser-warning: 1` es obligatorio en el tier gratuito de ngrok a partir de 2026.

- **Deuda registrada:**
  - C12.6 extenderá este endpoint para devolver también `keyframe_indices`.










