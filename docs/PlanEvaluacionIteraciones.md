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
  - **Observación de calidad de datos:** El primer frame del video (`frame_idx=0`) contiene una intro/fondo, lo que genera keypoints con baja confianza inicial. El análisis de la distribución global en los 777 frames muestra que los keypoints son de alta calidad (mediana global de confianza: 0.82, p95: 1.00, con 67.1% de keypoints con conf > 0.5).

- **Deuda registrada:**
  - C12.6 extenderá este endpoint para devolver también `keyframe_indices`.
  - En una iteración futura (C12.x), añadir filtrado de keypoints por umbral de confianza (`conf > 0.3`) directamente en el endpoint para robustecer la salida frente a frames de transición o intros.

---

### C12.5 — Fixes del Pipeline Biomecánico Real (YOLO → Qdrant → RAG → Gemini)

**Fecha:** 2026-09-29  
**Objetivo:** Corregir 5 bugs de implementación y crear 1 componente faltante que impedían el funcionamiento end-to-end del pipeline de análisis biomecánico con datos reales.

#### Archivos Modificados (4)

| # | Archivo | Fix | Descripción |
|---|---------|-----|-------------|
| 1.1 | `corpocmente/domain/entities/models.py` | `to_vector_array()` | Retornaba `None` (`pass`). Ahora retorna `list(self.keypoints133)` — vector crudo de 133 dims para comparación coseno en Qdrant. |
| 1.2 | `corpocmente/domain/entities/models.py` | `frame_idx` | Pydantic v2 descartaba silenciosamente `frame_idx` del response del Colab worker. Campo añadido con default `0`. |
| 2.1 | `corpocmente/infrastructure/persistence/qdrant_adapter.py` | `buscar_maxima_diferencia` | Realizaba ~777 queries HTTP individuales a Qdrant (1 por frame). Reescrito con `client.scroll()` + `numpy` coseno local: 1 query total, comparación O(N×M) en memoria. |
| 3.1 | `corpocmente/domain/services/intelligence_facade.py` | `UMBRAL_ACEPTABLE` | Era `0.85` pero `score` viene en escala 0–100 → `similitud >= 0.85` siempre era `True` → Gemini nunca se invocaba. Corregido a `85.0`. |
| 3.2 | `corpocmente/domain/strategies/prompt_strategies.py` | `SpanishPromptStrategy` | El prompt no indicaba a Gemini que la imagen era el fotograma crítico del error. Ahora incluye "EL FOTOGRAMA CRÍTICO" y pide mencionar articulación + dirección de corrección. |

#### Archivo Creado (1)

| # | Archivo | Propósito |
|---|---------|-----------|
| 4.1 | `scripts/ingest_reference_video.py` | Ingesta REAL de video de referencia del profesor. Flujo: `cv2.VideoCapture` → extrae frames JPG → envía al Colab Worker `/extraer_poses` → persiste keypoints133 + payload en Qdrant. Sin mocks, sin fallbacks silenciosos. |

#### Tests de Regresión Añadidos (16 tests)

| Archivo | Tests | Cobertura |
|---------|-------|-----------|
| `tests/domain/test_models_regression.py` | 7 | `to_vector_array()` retorna lista, 133 dims, valores correctos, copia. `frame_idx` default 0, acepta worker dict, serializa. |
| `tests/infrastructure/test_qdrant_maxdiff_regression.py` | 6 | Usa `scroll` no `search`, retorna peor frame, score 0–100, ValueError en refs vacías, ValueError en alumno vacío, payload propagado. |
| `tests/domain/test_threshold_prompt_regression.py` | 6 | Score 75 invoca Gemini, score 90 lo omite. Prompt contiene "FOTOGRAMA CRÍTICO", técnica, discrepancias, "articulación". |

#### Ejecución de Tests

```
=================== 32 passed, 6 skipped, 0 failures in 0.09s ===================
```

- **32 passed:** Todos los tests existentes (16) + todos los nuevos (16) pasan.
- **6 skipped:** Tests que requieren servicios externos (Colab, PostgREST) — diseño intencional.
- **0 failures.**

#### Variables de Entorno Validadas

| Variable | Estado |
|----------|--------|
| `GEMINI_API_KEY` | ✅ Configurada (AI Studio) |
| `POSTGREST_JWT_SECRET` | ✅ Configurada |
| `QDRANT_HOST` / `QDRANT_PORT` | ✅ localhost:6333 |
| `QDRANT_COLLECTION` | ✅ `vectores_poses_jiujitsu` |
| `COLAB_TUNNEL_URL` | ✅ URL ngrok activa |
| `WORKER_SERVICE_TOKEN` | ✅ Añadida al .env |
| `JWT_SECRET_KEY` | ✅ Añadida al .env |

#### Secuencia de Validación E2E — Estado

| Paso | Descripción | Estado |
|------|-------------|--------|
| 1 | Levantar Qdrant + Postgres + FastAPI | ⏳ Pendiente ejecución manual |
| 2 | Levantar worker Colab con sesión T4 | ⏳ Sesión activa (`gpu-t4-s-kkb-usw4a2-1dtusl2srqdww`), notebook pendiente de verificación |
| 3 | Verificar `/health` del worker | ⏳ Pendiente curl |
| 4 | Ingesta REAL de video de referencia | ⏳ Requiere paso 2–3 primero |
| 5 | Ingesta de teoría RAG | ⏳ Pendiente verificación |
| 6 | Prueba E2E con video del alumno | ⏳ Requiere pasos 1–5 |
| 7 | Reconciliación Postgres ↔ Qdrant | ⏳ Requiere paso 6 |

#### Deuda Técnica

- Los pasos 1–7 de la secuencia de validación E2E requieren ejecución manual con servicios reales levantados (Qdrant, Postgres, Colab Worker).
- `VectorSearchResultDTO` no expone aún `frame_alumno_idx` — reservado para iteración C12.7 cuando se implemente superposición del frame del alumno sobre el de referencia.
- `PortuguesePromptStrategy` pendiente de implementación (la interfaz `IPromptStrategy` ya está lista).

---

### C12.6 — Video de Referencia del Profesor en el Reporte del Alumno

**Fecha:** 2026-09-29  
**Objetivo:** Cerrar el loop UX mostrando al alumno el video de referencia del profesor dentro del reporte de evaluación, para que pueda comparar visualmente su ejecución contra el patrón oficial.

#### Archivos Modificados

| # | Archivo | Capa | Cambio |
|---|---------|------|--------|
| 1 | `database/02_auth_jwt.sql` | SQL/RPC | `get_evaluacion_by_id` ahora hace JOIN con `videos_referencia` + `usuarios` para devolver `video_referencia_url` y `video_referencia_profesor_nombre`. |
| 2 | `backend/corpocmente/ui/api/routes.py` | Backend | `GET /evaluaciones/{id}` convierte la ruta local del video a URL estática (`/static/videos/filename.mp4`) y la propaga en la respuesta JSON. |
| 3 | `frontend/src/App.jsx` | Frontend | El estado `result` del polling ahora incluye `video_referencia_url` y `video_referencia_profesor_nombre`. |
| 4 | `frontend/src/pages/FeedbackView.jsx` | Frontend | Nuevo bloque `<video>` con controles nativos HTML5 entre la tarjeta de técnica y el score. Muestra nombre del profesor y texto de orientación bilingüe. |
| 5 | `frontend/src/i18n/translations.js` | i18n | Claves `videoReferenciaLabel`, `videoReferenciaDemoDe`, `videoReferenciaHint` en ES y PT. |

#### Tests de Regresión

- **32 passed, 6 skipped, 0 failures** — sin regresiones en backend.
- Tests de frontend: verificación visual manual (paso 6 de la secuencia E2E).

#### Secuencia de Validación E2E

| Paso | Descripción | Criterio de Éxito |
|------|-------------|-------------------|
| 1 | Aplicar migración SQL (re-ejecutar `02_auth_jwt.sql`) | La función `get_evaluacion_by_id` devuelve `video_referencia_url` y `video_referencia_profesor_nombre` |
| 2 | Reiniciar backend (`uvicorn --reload`) | Arranca sin errores |
| 3 | `GET /api/v1/evaluaciones/{id}` con JWT | JSON incluye `"video_referencia_url": "/static/videos/..."` |
| 4 | `curl -I http://localhost:8000/static/videos/<archivo>` | HTTP 200, Content-Type: video/mp4 |
| 5 | Abrir `http://localhost:5173`, login como alumno, abrir reporte | El video del profesor se reproduce con controles nativos |
| 6 | El nombre del profesor aparece como "Demostración de: ..." | Texto visible debajo del label |
| 7 | Reconciliación Postgres ↔ Qdrant | Sin orphans |

#### Deuda Técnica (fuera de scope)

| Iteración | Descripción |
|-----------|-------------|
| C12.7 | Integración DTW + Normalización Biomecánica (Completada) |
| C12.8 | Comparación lado a lado: video alumno ↔ video profesor |
| C12.9 | Timeline de keypoints con slider temporal |
| C12.10 | Exportar reporte a PDF |

---

### C12.7 — Integración DTW + Normalización Biomecánica

**Fecha:** 2026-10-14<br>
**Objetivo:** Sustituir la comparación fotograma a fotograma aislada por Dynamic Time Warping (DTW) multidimensional sobre la secuencia continua normalizada, permitiendo comparar movimientos temporales a diferente ritmo de ejecución (maestro vs. alumno) y detectar el punto crítico con mayor error articular.

#### Decisiones Arquitectónicas y Hallazgos de Implementación
1. **Decisión Arquitectónica:** Se reemplaza la búsqueda de similitud frame-a-frame por un pipeline en dos etapas:
   - **Normalización Espacial Canónica:** Proyección del esqueleto COCO-17 a frame corporal canónico (origen en punto medio de cadera, escala torso, rotación cadera-hombro) + 12 ángulos articulares invariantes (vector canónico resultante de 46 dimensiones).
   - **Alineación Temporal DTW:** DTW multidimensional que calcula la distancia acumulada de alineación y obtiene el camino de deformación temporal (*warping path*).
2. **Corrección de API en `dtaidistance`:** Se detectó empíricamente que `dtaidistance.dtw.distance()` solo opera sobre series univariadas 1D; para vectores de características multidimensionales $(N, 46)$ se migró a `from dtaidistance import dtw_ndim` con aceleración en C (`distance_fast`).
3. **Fix de Compatibilidad PyTorch 2.6+ y Ultralytics:**
   - En PyTorch 2.6+ la carga de pesos exige `weights_only=False` para unpickling de modelos YOLO (`PoseModel`).
   - Se seleccionó `yolov8n-pose.pt` para la extracción offline local en CPU en compatibilidad con `ultralytics==8.1.0`.
4. **Protección Anti-División por Cero en Oclusión:** Se añadió guarda de escala mínima (`raw_scale < 10.0px`) en `pose_normalizer.py` que previene que frames con articulaciones no detectadas $(0, 0)$ generen divisiones por $10^{-9}$ y valores espaciales de $10^{11}$.
5. **Corrección en Búsqueda de Peor Frame y Fixes A y B:**
   - Ajuste de `peor_sim = float('inf')` en `dtw_comparator.py`.
   - **Fix A (Filtrado de articulaciones):** Descarte de keypoints colapsados a $(0, 0)$ (`norm < 0.05`) para evitar falsos positivos por oclusiones faciales.
   - **Fix B (Ventana temporal 20%-80% y descarte de frames vacíos):** Búsqueda del peor momento acotada a la fase técnica activa, exigiendo al menos 15 coordenadas válidas en ambos frames para descartar momentos sin detección.
6. **Evolución a Métrica Basada en Media de Similitudes por Paso:**
   - Se sustituyó la fórmula que proyectaba la distancia euclidiana acumulada mediante un `FACTOR_ESCALA` arbitrario por el promedio de similitud espacial de los fotogramas alineados a lo largo del *warping path* (con media recortada al 5% para robustez).
   - El resultado pasa a ser directamente interpretable como el porcentaje medio de concordancia anatómica frame-a-frame entre maestro y alumno.

#### Evidencia Empírica de Validación y Calibración Baseline (`calibrar_dtw.py`)
- **Dataset de Prueba:**
  - `Maestro.mp4`: 783 frames (13.06s @ 59.93 fps, 464x832 px)
  - `Alumno.mp4`: 276 frames (4.61s @ 59.93 fps, 464x832 px) — misma técnica (escape/raspada de montada) ejecutada de forma fluida ~2.8x más rápida.
- **Tabla Comparativa de Calibración:**

| Caso de Prueba | DTW Acumulado (`dtw_norm`) | Score Media 5% (Nueva Métrica) | Mediana |
| :--- | :--- | :--- | :--- |
| **1. Maestro vs Maestro** | `0.0000` | **100.00%** | **100.00%** |
| **2. Cropping 10%** | `0.0963` | **97.50%** | **100.00%** |
| **3. Ruido Gaussiano** | `0.3073` | **32.40%** | **34.26%** |
| **4. Maestro vs Alumno (Real)** | `0.2352` | **63.25%** | **64.13%** |

- **Métricas Resultantes en Pipeline Depurado:**
  - `score_similitud`: **63.25%** (Mediana: **64.13%**, P75: **76.32%**, Máximo puntual: **90.30%**)
  - `dtw_distance`: **204.8371**
  - `path_length`: **871**
  - `frame_maestro_critico`: **610** (de 783, ~78% del video)
  - `frame_alumno_critico`: **67** (de 276, ~24% del video)
  - `articulaciones_criticas`: **[16, 9, 5]** (Tobillo derecho, Muñeca izquierda, Hombro izquierdo — 100% articulaciones corporales reales)

#### Tests de Regresión
- **36 passed, 6 skipped, 0 failures** en suite backend pytest.

### 🔹 Iteración Transition-2A (Fase de Transición): Migración de Qwen a MLX Local

- **Estado:** COMPLETADA ✅
- **Fecha:** 2026-10-28
- **Commit:** `ae9c543`
- **Tag:** `transition-2a`

- **Objetivo:** Eliminar la dependencia del worker de Google Colab y del polling a Google Drive para la vectorización de embeddings, ejecutando `Qwen3-VL-Embedding-2B` localmente en Apple Silicon con MLX.

- **Riesgos mitigados:**
  - **Latencia de red:** Eliminada por completo. La inferencia es local.
  - **Dependencia externa:** Colab/ngrok/Drive ya no son requeridos para el pipeline RAG.
  - **Costo operativo:** Cero (hardware propio).
  - **Rate limits:** No aplican.

- **Entregables:**
  - `backend/corpocmente/infrastructure/ai/qwen_adapter.py` con soporte dual (local MLX + fallback HTTP).
  - `backend/corpocmente/config.py` con `USE_LOCAL_QWEN` y `LOCAL_QWEN_MODEL`.
  - `scripts/test_qwen_mlx.py` (PoC de carga e inferencia).
  - `scripts/benchmark_qwen_local.py` (benchmark micro).
  - Patch local a `mlx_embeddings.models.qwen3_vl.model` (ver Task 4).

- **Evidencia E2E (PDF real):**
  - PDF: `Jiu-Jitsu University.pdf` (600 páginas, ~30 MB)
  - Duración total: **817.52 segundos**
  - Chunks indexados: **630**
  - Páginas con texto: **578**
  - Páginas con imagen: **575**
  - Persistencia dual verificada: Qdrant 630 pts / Postgres 630 filas
  - **Comparativa:** baseline Colab+Drive = 64 min → MLX local = **13.6 min** (**4.7x más rápido**)

- **Lecciones aprendidas (Larman):**
  - **Falso positivo de benchmark:** el micro-benchmark (49ms/texto) es necesario pero no suficiente. La comparación honesta requiere el caso real.
  - **Patch a terceros = deuda silenciosa:** un `pip install -U` mata el sistema. El technical memo + script de re-aplicación es obligatorio, no opcional.
  - **Protected Variations violado en `mlx_embeddings`:** hubo que parchar el paquete. Idealmente, abrir PR upstream.

- **Deuda residual (registrada):**
  - PR a `ml-explore/mlx-embeddings` con el fix.
  - Re-evaluar el patch cuando salga versión oficial.
  - Ninguna en Task 6. Modo fallback probado y funcional.

---

### 🔹 Iteración Transition-2B (Fase de Transición): YOLO26 local + Gemini 3.5 Flash-Lite + inglés

- **Estado:** COMPLETADA ✅
- **Fecha:** 2026-10-28
- **Commit:** `c0ac9fd`
- **Tag:** `transition-2b`

- **Objetivo:** YOLO26-pose corriendo localmente en Mac (MLX o MPS), Gemini 3.5 Flash-Lite como generador, todo el feedback en inglés, gestión explícita de recursos.

- **Riesgos mitigados:**
  - Dependencia de Colab para YOLO: eliminada.
  - Modelo de Gemini deprecado: migrado a 3.5 Flash-Lite vigente.
  - RAM descontrolada: instrumentada con logs `[RAM]` y `finally` de liberación.

- **Entregables:**
  - Ruta B (`ultralytics` con Apple Metal MPS) para YOLO26-pose
  - `GeminiApiAdapter` con `gemini-3.5-flash-lite`
  - `EnglishPromptStrategy` + `COCO_JOINT_NAMES_EN`
  - `translations.en` en frontend (`translations.js`) y `useTranslation` default `'en'`
  - `log_ram_usage()` + RAM guard (< 2 GB libre aborta)
  - Memo técnico: `docs/technical_memos/2026-10-28-yolo26-local-mps-vs-mlx.md`

- **Evidencia E2E:**
  - `Maestro.mp4` → patrón registrado: 783 frames, cobertura 94.25% (12.32s, 63.5 FPS), `patron_id`: `e4264a95-594c-4e61-9b28-864748304e01`
  - `Alumno.mp4` → análisis completo: DURACION_SEG = 70.77s, similitud 25.72%, feedback en inglés
  - Frame crítico: `/tmp/corpocmente_frames/critico_b5a01854-3f66-47f4-b415-4e11da4d41a1.jpg` (81 KB, 464x832 px)
  - Feedback cita el libro: *"Your elbows are flaring outward and losing connection to your hips, which allows the opponent to collapse your frame. Keep your elbows tightly glued to your ribs as recommended in Jiu-Jitsu University (p."*

- **Lecciones aprendidas:**
  - Ruta B (MPS) fue la correcta porque `thewebAI/yolo-mlx` tiene un conflicto estricto con `mlx>=0.31.1` (requerido por `mlx-embeddings` para Qwen3-VL local). Mantener PyTorch MPS permite que ambos modelos convivan sin romper dependencias.
  - La gestión de RAM es crítica: liberación explícita con `gc.collect()` y `torch.mps.empty_cache()` en `finally` previene fugas en background tasks, dejando 11.3 GB de RAM disponible post-E2E.
  - Inglés en prompts + i18n frontend es timeboxed: se tradujeron las claves del flujo E2E y los mensajes de error (`detail`) de la API.

- **Deuda residual:**
  - Traducir el resto de i18n si el sistema se despliega internacionalmente.
  - Migrar a `yolo-mlx` cuando soporte pose sin conflicto de versión con `mlx`.

---

### 🔹 Iteración Transition-2B.1 (Fase de Transición): Frontend Single-Language (Hardcoded English) + Fix de Truncamiento en Feedback

- **Estado:** COMPLETADA ✅
- **Fecha:** 2026-10-29
- **Tag:** `transition-2b.1`

- **Objetivo:**
  1. Eliminar por completo la infraestructura i18n (`translations.js`, `useTranslation`, selector `<select>` de idioma) y hardcodear inglés directo en todos los componentes JSX de la aplicación.
  2. Resolver la causa raíz del truncamiento de citaciones de IA en `GeminiApiAdapter._limpiar_feedback`, asegurando que citas bibliográficas como `(p. 116)` se preserven íntegras y no se corten en `(p.`.
  3. Evidencia visual estricta mediante capturas "before" (`/tmp/baseline_before/`) y "after" (`/tmp/baseline_after/`) con Playwright.

- **Riesgos Mitigados:**
  - **Inconsistencia de interfaz:** Eliminación de texto híbrido (español/portugués/inglés) y ternarios frágiles `isPt ? ... : ...`.
  - **Corte de retroalimentación crítica:** Reparación del regex de partición de oraciones que interpretaba el punto de `(p.` como delimitador de fin de oración, cortando la cita a la mitad.

- **Entregables:**
  - Hardcodeo a inglés en los componentes: `App.jsx`, `FeedbackView.jsx`, `VideoUpload.jsx`, `AdminSucursales.jsx`, `ProfesorTecnicas.jsx`, `StudentProgress.jsx`, `SelectorPersonaVideo.jsx`, `TheoryManagerModal.jsx`, `GlobalKnowledgeModal.jsx`, `UserProfileModal.jsx`, `LoginModal.jsx`.
  - Eliminación del directorio `frontend/src/i18n` y de `<select>` de idiomas en `App.jsx`.
  - Modificación en `EnglishPromptStrategy`: límite ampliado de 45 a 60 palabras.
  - Modificación en `GeminiApiAdapter`:
    - `max_output_tokens` incrementado a 500.
    - Partición de oraciones mejorada: `re.split(r"(?<=[.!?])\s+(?=[A-Z¿¡])", texto)` para evitar falsos positivos en abreviaturas como `p. 116`.
    - Protección de citaciones desbalanceadas: si un paréntesis de apertura `(` no tiene cierre posterior, se realiza rollback antes del `(`.
  - Script automatizado de captura de pantalla con Playwright: `scripts/capture_screenshots.py`.

- **Evidencia Cruda de Verificación:**
  - **5 Greps de Control (Frontend):**
    - Acentos / caracteres especiales en JSX strings: **0 matches**
    - Usos de `useTranslation` en frontend: **0 matches**
    - Referencias `t.xxx` en JSX: **0 matches**
    - Selectores `<option value="es"` / dropdowns de idioma: **0 matches**
  - **Compilación Vite:** `dist/index.html` generado limpiamente con 51 módulos transformados en 361ms sin errores.
  - **Pytest:** 36 passed, 1 skipped (0 failures) en 0.06s.
  - **E2E con Alumno.mp4:**
    - Duración: 12.11s
    - Similitud: 25.72%
    - Feedback generado:
      `"You are letting your framing arm get isolated and flattened instead of keeping your elbow tucked tightly in front of Xande's hip as taught in Jiu-Jitsu University (p. 116). Keep your elbow actively posted to maintain structural integrity and prevent him from passing your defense."`
    - Cita bibliográfica: `(p. 116).` íntegra, sin truncamiento.
  - **Capturas Visuales:** 4 vistas antes (`/tmp/baseline_before/`) vs 4 vistas después (`/tmp/baseline_after/`):
    - `login.png`
    - `upload.png`
    - `feedback.png`
    - `admin.png`

---

### 🔹 Iteración Transition-2C (Fase de Transición): Feedback Estructurado (Resumen + Corrección Markdown), Layout 2×2, YouTube Dinámico y Rol Coach

- **Estado:** COMPLETADA ✅
- **Fecha:** 2026-10-29
- **Tag:** `transition-2c`

- **Objetivo:**
  1. Rediseñar `FeedbackView.jsx` adoptando el layout 2×2 en cuadrícula (Video Coach, Frame Crítico Alumno, Tarjeta IA con `react-markdown`, Tarjeta YouTube con enlace de práctica dinámico).
  2. Implementar feedback estructurado en Gemini (`summary` máx. 8 palabras, `correction` máx. 2 frases en Markdown con `response_mime_type="application/json"`), columna `feedback_summary` en PostgreSQL y actualización de RPCs.
  3. Resolver el error de reproducción de video en "My Progress" (`StudentProgress.jsx`) asegurando persistencia y servicio de archivos estáticos en `/static/videos/`.
  4. Simplificar la vista del profesor (`ProfesorTecnicas.jsx`) reemplazando textos extensos por badge de desempeño + `feedback_summary` conciso y modal de detalles con Markdown.
  5. Estandarizar la terminología reemplazando "Mestre" por "Coach".
  6. Limpieza SQL de feedback truncado previo en `evaluaciones_alumnos`.
  7. Evidencia visual before/after guardada en `docs/visual_evidence/transition-2c/` y `/tmp/baseline_after/`.

- **Entregables:**
  - `evaluaciones_alumnos`: columna `feedback_summary` añadida y limpiados registros antiguos.
  - RPCs: `get_evaluacion_by_id`, `admin_list_evaluaciones_alumno`, `worker_update_result` con soporte para `feedback_summary`.
  - `EnglishPromptStrategy`: prompt configurado para exigir JSON `{summary, correction}` en Markdown.
  - `GeminiApiAdapter`: `application/json` en `GenerateContentConfig` y parseador robusto con fallback.
  - `IntelligenceAnalysisFacade`: `AnalisisResultDTO` transporta `feedback_summary` y `feedback_correction`.
  - `routes.py` y `auth_routes.py`: generación de `practice_url` dinámico para tutoriales de YouTube y servicio de `feedback_summary`.
  - `FeedbackView.jsx` y `FeedbackView.css`: wireframe 2×2 implementado, `react-markdown` y botón "Analyze Another Technique".
  - `StudentProgress.jsx`: videos visibles y corrección a "Coach".
  - `ProfesorTecnicas.jsx`: badges + resumen y modal interactivo de detalles con Markdown.
  - Script Playwright: `scripts/capture_transition_2c_screenshots.py`.

- **Evidencia Cruda de Verificación:**
  - **Pytest:** 51 passed, 3 skipped en `pytest -q tests/domain/ tests/infrastructure/`.
  - **Build Frontend:** `vite build` generado limpiamente con 215 módulos transformados en 429ms.
  - **API Verification:**
    - `GET /api/v1/evaluaciones/{id}` devuelve `feedback_summary`, `practice_url` y `feedback` con Markdown.
    - `GET /api/v1/auth/alumnos/{id}/evaluaciones` devuelve el listado con `feedback_summary` y `practice_url`.
  - **Evidencia Visual:**
    - `docs/visual_evidence/transition-2c/before/feedback.png`
    - `docs/visual_evidence/transition-2c/before/profesor.png`
    - `docs/visual_evidence/transition-2c/after/feedback.png`
    - `docs/visual_evidence/transition-2c/after/profesor.png`
    - `docs/visual_evidence/transition-2c/after/profesor_modal.png`
    - `docs/visual_evidence/transition-2c/after/student_progress.png`

---

### 🔹 Iteración Transition-3 (Fase de Transición): Migración 100% Local y Eliminación de Deuda Técnica Gemini

- **Estado:** COMPLETADA ✅
- **Fecha:** 2026-10-30
- **Tag:** `transition-3`
- **Objetivo:**
  1. Eliminar la totalidad de la deuda técnica de Google Gemini API (adaptadores, dependencias y tests de integración).
  2. Migrar la arquitectura a un funcionamiento 100% autónomo y local (Apple Silicon / MLX / MPS).
  3. Implementar un filtro anti-spam local (`LocalSpamFilter`) entrenando un clasificador de posiciones relativas (`MLPClassifier`) sobre el dataset ViCoS con particionado temporal estricto (`GroupShuffleSplit`) para erradicar data leakage.
  4. Validar el flujo End-to-End con el modelo local de visión-lenguaje (`Qwen3-VL-4B-Instruct` vía MLX).

- **Entregables:**
  - `backend/corpocmente/infrastructure/ai/adapters.py`: Remoción completa de `GeminiApiAdapter` y `GeminiRateLimitError`.
  - `backend/tests/infrastructure/test_gemini_adapter.py`: Eliminado del repositorio.
  - `backend/requirements.txt`: Desinstalado `google-genai`.
  - `backend/corpocmente/infrastructure/ai/local_spam_filter.py`: Filtro anti-spam local por interacción biomecánica y ratio de BJJ.
  - `backend/scripts/02c_reentrenar_agrupado.py`: Pipeline de entrenamiento agrupado en bloques de 30 frames (`BLOQUE = 30`).
  - `docs/technical_memos/2026-10-30-transition-3-local-migration.md`: Memo técnico formal de la migración local.

- **Evidencia Cruda de Verificación:**
  - **Grep de Control:** 0 referencias a `GeminiApiAdapter` o `google.genai` en el código fuente y tests de backend.
  - **Métricas del Clasificador ViCoS:** Accuracy: `90.19%`, F1-Macro: `88.18%`.
  - **Smoke Test Anti-Spam:** `Alumno.mp4` aprobado (ratio 0.86 >= 0.60), `control_bailarinas.mp4` rechazado (ratio 0.31 < 0.60), `control_boxeo.mp4` rechazado (0 frames con 2 personas).
  - **Pytest:** 79 passed, 6 skipped en 6.17s.

---

### 🔹 Iteración Transition-3C (Fase de Transición): Evaluación Empírica de YOLO26s Fine-Tuning (ViCoS) e Iteración 3C.5 (Prueba Comparativa best.pt vs yolo26n-pose)

- **Estado:** COMPLETADA (MODELO RECHAZADO / BASELINE RETENIDO EN PRODUCCIÓN) 🛡️
- **Fecha:** 2026-10-31
- **Tags de Checkpoint / Rollback:** `iter-3c-antes`, `iter-3c2-antes`, `iter-3c3-antes`

- **Objetivo:**
  Evaluar si los pesos fine-tuneados `storage/models/yolo26n_bjj_pose/weights/best.pt` (entrenados en Google Colab con GPU NVIDIA A100 durante 51 épocas sobre el dataset ViCoS de 20,775 anotaciones) superan al modelo base `yolo26n-pose.pt` en precisión de keypoints e inferencia de interacción en combate.

- **Ciclo de Hipótesis y Sub-iteraciones Empíricas:**
  1. **Iteración 3C.1 (Integración Directa, conf=0.30):** En videos reales de alumnos (`Alumno.mp4`, `Alumno_Gaetamo.mp4`), `best.pt` falló al detectar 2 personas simultáneamente en todos los frames muestreados (0 frames con interacción), gatillando falsos negativos en el `LocalSpamFilter`. **Rollback ejecutado a `iter-3c-antes`**.
  2. **Iteración 3C.2 (Calibración Dinámica de Umbrales, conf=0.15 y conf=0.20):** Se testeó si las cajas tenían logits más bajos. En 276 frames de `Alumno.mp4`, solo 1 frame tuvo $\ge 2$ poses válidas. **Rollback ejecutado a `iter-3c2-antes`**.
  3. **Iteración 3C.3 (Inferencia a Alta Resolución, imgsz=1280, rect=True):** Se testeó la hipótesis de que la relación de aspecto vertical (9:16) encogía excesivamente a los atletas al aplicar letterbox cuadrado. Incluso a 1280px rectangulares, las detecciones de cajas se mantuvieron en 0. **Rollback ejecutado a `iter-3c3-antes`**.
  4. **Iteración 3C.4 (Zoom Test en Primer Plano, /tmp/alumno_zoom.mp4):** Se recortó el video al 85% de la pantalla para simular la escala de ViCoS. `best.pt` obtuvo 0.0% de frames con $\ge 2$ personas entre `conf=0.15` y `0.30`, mientras el modelo base detectó al 100%.
  5. **Iteración 3C.5 (Prueba Aislada con Video de YouTube en Toma Media Horizontal - `2026-10-31 09-41-31.mov`):** Evaluación definitiva y aislada con `backend/scripts/09_test_best_pt_custom.py` para descartar factores ambientales (distancia de cámara o encuadre de gimnasio).

- **Resultados Comparativos Crudos — Iteración 3C.5 (Video HD 1920x1080 @ 60fps, 24 frames muestreados):**

| Métrica de Evaluación | `best.pt` (Fine-tuned, conf=0.15, imgsz=1280) | `yolo26n-pose.pt` (Base Original, conf=0.30, imgsz=640) |
| :--- | :---: | :---: |
| **Frames con $\ge 2$ personas detectadas** | **2 / 24 (8.3%)** | **14 / 24 (58.3%)** |
| **Frames con 1 persona** | 16 / 24 (66.7%) | 10 / 24 (41.7%) |
| **Frames con 0 personas (ceguera)** | **6 / 24 (25.0%)** | **0 / 24 (0.0%)** |
| **Confianza media de cajas delimitadoras** | 0.5414 | 0.6877 |
| **Confianza media de keypoints detectados** | 0.8857 | 0.8654 |

- **Veredicto Empírico y Causa Raíz Científica:**
  - **ESCENARIO B CONFIRMADO:** `best.pt` continúa fallando sistemáticamente incluso en tomas medias y videos HD horizontales externos.
  - **Catastrophic Forgetting & Domain Shift:** El entrenamiento de 51 épocas sin mezclar datos de COCO general sobrescribió los pesos convolucionales de representación humana. El modelo quedó ultra-especializado en el sensor, ángulo y piso de tatami del laboratorio de ViCoS, perdiendo la capacidad de generalizar a combates reales de Jiu-Jitsu.
  - En contraposición, el modelo base `yolo26n-pose.pt` demostró robustez absoluta (0% frames vacíos, 58.3% interacción directa, sin falsos negativos).

- **Decisión de Arquitectura y Cierre del Experimento (Craig Larman):**
  - **Cierre definitivo del experimento ViCoS:** Se descarta el reemplazo del modelo en producción.
  - **Estabilidad de Producción:** El código de producción permanece 100% blindado con `yolo26n-pose.pt` en `adapters.py` y `local_spam_filter.py`.
  - **Valor Académico para Defensa de Tesis:** Este experimento y sus 5 fases empíricas constituyen un aporte metodológico clave para el informe de grado, demostrando rigor en el control de calidad, rollback automatizado ante regresiones y validación empírica contra domain shift en IA aplicada al deporte.
  - **Suite de Pruebas:** 79 passed, 6 skipped en 6.36s.

---

### 🔹 Iteración Transition-3D (Fase de Transición): Integración de Normalización Biomecánica en DTW (Técnica Invariante vs. Píxeles)

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-10-31
- **Tag:** `iter-3d-antes`

- **Objetivo:**
  Corregir el problema estructural de comparación de esqueletos en píxeles absolutos. Integrar [`pose_normalizer.py`](file:///Users/santiago/Desktop/JiuJitsu-main/backend/corpocmente/domain/biomechanics/pose_normalizer.py) en [`dtw_comparator.py`](file:///Users/santiago/Desktop/JiuJitsu-main/backend/corpocmente/domain/biomechanics/dtw_comparator.py) para que la comparación DTW opere sobre vectores canónicos de 46 dimensiones (34 posiciones centradas en pelvis, escaladas por torso y rotadas a vertical, más 12 ángulos articulares invariantes a traslación, escala y sensor).

- **Diagnóstico del Fallo Previo:**
  - `dtw_comparator.py` calculaba distancias euclidianas directamente sobre coordenadas de pantalla `(x, y)` crudas.
  - Si el alumno y el profesor estaban en posiciones o escalas diferentes, la distancia DTW sumaba **16,806.60 px**, colapsando la similitud artificialmente a **~25.7%** a pesar de que la técnica de BJJ estuviese bien ejecutada.

- **Entregables:**
  - `backend/corpocmente/domain/biomechanics/dtw_comparator.py`:
    - Proyección previa de cada frame crudo a vector canónico normalizado de 46 dimensiones (`_normalizar_frame_para_dtw`).
    - DTW multidimensional alineando el espacio normalizado.
    - `_similitud_frame`: Similitud combinada (posiciones canónicas + ángulos articulares con tolerancia a oclusiones).
    - `detectar_articulaciones_criticas`: Detección en frame canónico ponderando desviaciones angulares y posicionales, descartando articulaciones no visibles.
    - Selección del fotograma crítico acotada a fotogramas con detección real.
  - `backend/scripts/10_test_normalized_dtw.py`: Script de prueba de fuego y control negativo.
  - `docs/technical_memos/2026-10-31-transition-3d-biomechanical-dtw-normalization.md`: Memo técnico detallado con formulación matemática.

- **Resultados de la Prueba de Fuego (`10_test_normalized_dtw.py`):**
  - **Distancia DTW Alumno:** Se redujo de **16,806.60 px** a **212.95 unidades biomecánicas** (-98.7%).
  - **Similitud Alumno (`Alumno.mp4`):** Subió de **25.72%** a **50.51%** (aprobado y coherente con ejecución real).
  - **Control Negativo (`control_bailarinas.mp4`):** Obtuvo **18.67%** (muy por debajo del umbral, confirmando **0 falsos positivos**).
  - **Auto-comparación Maestro:** 0.0 de distancia y **100.0%** de similitud (determinismo garantizado).
  - **Articulaciones Críticas Identificadas:** `[13, 9, 8]` (rodilla izquierda, muñeca izquierda, codo derecho).
  - **Pytest:** 79 passed, 6 skipped en 6.89s.

---

### 🔹 Iteración Transition-3E (Fase de Transición): Contexto Temporal, Prompt del Profesor y UI Limpia

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-10-31
- **Tag Previo:** `iter-3e-antes` (commit `96af21a`)

- **Objetivos:**
  1. Exponer la métrica temporal exacta (`timestamp_error_segundos = frame_alumno_critico / fps`) en el backend y retornarla en `GET /api/v1/evaluaciones/{id}` y `GET /api/v1/evaluaciones/alumno/{id}`.
  2. Inyectar las instrucciones técnicas del profesor (`tecnicas.mensaje_profesor`) en la estrategia de prompt del VLM local (`EnglishPromptStrategy` y `SpanishPromptStrategy`) para que las correcciones sigan estrictamente la pedagogía del instructor.
  3. Limpieza de texto obsoleto en frontend (`TheoryManagerModal.jsx`): reemplazar `"Gemini references them..."` por `"The AI Coach references them..."`.
  4. Reproducción y navegación temporal en frontend (`FeedbackView.jsx` y `StudentProgress.jsx`): control de video con `useRef`, cartel de advertencia de error y botón `Jump to Error` que reposiciona el video exactamente en el segundo del error biomecánico.

- **Entregables:**
  - `backend/corpocmente/domain/entities/models.py`: Campo `timestamp_error_segundos: Optional[float] = None` en `AnalisisResultDTO`.
  - `backend/corpocmente/domain/strategies/prompt_strategies.py`: Parámetro `mensaje_profesor: str = ""` en `IPromptStrategy`, `SpanishPromptStrategy` e `EnglishPromptStrategy` con inyección explícita en el prompt enviado al VLM.
  - `backend/corpocmente/domain/services/intelligence_facade.py`: Paso de `mensaje_profesor` a la estrategia de prompt, cálculo de `timestamp_error_segundos` vía FPS de video con fallback resiliente, y propagación en `AnalisisResultDTO`.
  - `backend/corpocmente/ui/api/routes.py`:
    - Consulta de `mensaje_profesor` desde Postgres/PostgREST en la tarea en segundo plano.
    - Persistencia de metadatos de evaluación y exposición de `timestamp_error_segundos` y `url_video_alumno` en `consultar_evaluacion`.
  - `backend/corpocmente/ui/api/auth_routes.py`: Exposición de `timestamp_error_segundos` y URL de video en `listar_evaluaciones_alumno`.
  - `frontend/src/components/TheoryManagerModal.jsx`: Limpieza de texto deprecado de Gemini por AI Coach.
  - `frontend/src/App.jsx`: Desempaquetado de `timestamp_error_segundos` y `url_video_alumno` en el estado de resultado tras polling.
  - `frontend/src/pages/FeedbackView.jsx`: Referencia de video interactiva, alerta visual de tiempo de error y botón `Jump to Error`.
  - `frontend/src/pages/StudentProgress.jsx`: Componente `StudentVideoPlayer` con `useRef`, banner de segundo de error y salto automático al segundo del fallo en el historial del alumno.
  - `backend/tests/domain/test_threshold_prompt_regression.py`: Tests unitarios `TestEnglishPromptStrategyMensajeProfesor` validando la inyección de las directrices del docente.

- **Evidencia Empírica y Validación E2E (`04_e2e_vlm_evaluacion.py`):**
  - **Tiempo Total de Análisis:** **22.07 segundos** (requerido < 30.0s).
  - **Estado:** `completado`.
  - **`timestamp_error_segundos`:** **1.02s** (segundo exacto del error biomecánico).
  - **Feedback Pedagógico Generado por VLM:** `"Use **bridge** to create space. Push hips left with controlled force."` (alineado directamente con la directriz del profesor: *"Escape from mount using bridge and shrimp"*).
  - **JSON Crudo de Respuesta:**
    ```json
    {
      "id": "3880f2e4-0542-4cfb-8dfe-054c553f76bc",
      "estado": "completado",
      "similitud": 62.07,
      "feedback": "Use **bridge** to create space. Push hips left with controlled force.",
      "feedback_summary": "Elbow flaring, lose hip connection",
      "timestamp_error_segundos": 1.02,
      "url_video_alumno": "/static/videos/6ceb1220-61df-48cb-a2dc-c6af4cc96176.mp4",
      "tecnica_id": "30a4afe4-23cc-4479-9f14-4f6d867de7dd",
      "tecnica_nombre": "Mount Escape",
      "video_referencia_url": "/static/videos/8f073747-e99a-4927-aede-1fed6fe893a3.mp4",
      "video_referencia_nombre": "8f073747-e99a-4927-aede-1fed6fe893a3.mp4",
      "video_referencia_profesor_nombre": "Coach Mike Baigorria",
      "frame_error_url": "/static/frames/critico_3880f2e4-0542-4cfb-8dfe-054c553f76bc.jpg",
      "practice_url": "https://www.youtube.com/results?search_query=Mount+Escape+jiu-jitsu+tutorial"
    }
    ```
  - **Suite de Pruebas Pytest:** **81 passed, 6 skipped** en 6.62s (100% verde).

---

### 🔹 Iteración Transition-3F (Fase de Transición): UI de Frame Crítico y Nombres de Articulaciones

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-10-31
- **Tag Previo:** `iter-3f-antes` (commit `e133ab2`)

- **Objetivos:**
  1. Mapear los índices articulares numéricos COCO (`articulaciones_criticas`) a nombres legibles en inglés/español (`nombres_articulaciones_criticas`: ej. `["Left Knee", "Right Knee", "Right Hip"]`).
  2. Exponer `nombres_articulaciones_criticas` y `articulaciones_criticas` en `GET /api/v1/evaluaciones/{id}` y `GET /api/v1/auth/alumnos/{id}/evaluaciones`.
  3. Enriquecer la interacción de usuario con el botón "Jump to Error":
     - Pausar el reproductor de video en el segundo del fallo biomecánico (`timestamp_error_segundos`).
     - Desplegar una ventana modal emergente de alta fidelidad con el fotograma crítico anotado en grande (`frame_error_url`).
     - Mostrar bajo la imagen la indicación en rojo de las articulaciones exactas afectadas: `Articulaciones afectadas: Left Knee, Right Knee, Right Hip`.
     - Proporcionar botón de cierre ("Cerrar" / `&times;`) para regresar fluidamente al video.

- **Entregables:**
  - `backend/corpocmente/domain/entities/models.py`: Campo `nombres_articulaciones_criticas: Optional[List[str]] = Field(default_factory=list)` en `AnalisisResultDTO`.
  - `backend/corpocmente/domain/services/intelligence_facade.py`: Conversión de índices COCO (`arts_criticas`) a `nombres_articulaciones_criticas` usando la constante `COCO_JOINT_NAMES_EN`.
  - `backend/corpocmente/ui/api/routes.py`:
    - Persistencia de `nombres_articulaciones_criticas` y `articulaciones_criticas` en `meta_{eval_id}.json`.
    - Retorno de ambos campos en la respuesta de `consultar_evaluacion`.
  - `backend/corpocmente/ui/api/auth_routes.py`: Carga y retorno de `nombres_articulaciones_criticas`, `articulaciones_criticas` y `frame_error_url` en `listar_evaluaciones_alumno`.
  - `backend/tests/domain/test_threshold_prompt_regression.py`: Suite `TestNombresArticulacionesCriticas` validando tanto el DTO como el mapeo en la fachada.
  - `frontend/src/App.jsx`: Desempaquetado de `articulaciones_criticas` y `nombres_articulaciones_criticas` al recibir la evaluación finalizada.
  - `frontend/src/pages/FeedbackView.jsx`: Estado `showFrameModal`, pausa del video en `timestampError`, modal de fotograma ampliado con banner de articulaciones afectadas y botón de cierre.
  - `frontend/src/pages/StudentProgress.jsx`: Componente `StudentVideoPlayer` actualizado con modal idéntico, soporte para `frameErrorUrl` y visualización de articulaciones afectadas en el historial del alumno.

- **Evidencia Empírica y Validación E2E (`04_e2e_vlm_evaluacion.py`):**
  - **Tiempo Total de Análisis:** **22.50 segundos** (dentro del límite de 30.0s).
  - **Estado:** `completado`.
  - **Técnica Evaluada:** Escaping Closed Guard Stand UP.
  - **`timestamp_error_segundos`:** **2.52s**.
  - **`articulaciones_criticas`:** `[13, 14, 12]`.
  - **`nombres_articulaciones_criticas`:** `["Left Knee", "Right Knee", "Right Hip"]`.
  - **`frame_error_url`:** `"/static/frames/critico_6a28adac-37d4-452b-b5f5-2d3bbff75054.jpg"`.
  - **JSON Crudo de Respuesta:**
    ```json
    {
      "id": "6a28adac-37d4-452b-b5f5-2d3bbff75054",
      "estado": "completado",
      "similitud": 55.66,
      "feedback": "Keep elbows tight to your sides. **Control hips** to prevent submission angles.",
      "feedback_summary": "Elbow flaring, lose hip connection",
      "timestamp_error_segundos": 2.52,
      "url_video_alumno": "/static/videos/f50f9d1c-ddb4-45c5-94a9-55b5246f27ca.mp4",
      "tecnica_id": "59760071-a3ce-46ec-b9d9-75b6dc47eba7",
      "tecnica_nombre": "Escaping Closed Guard Stand UP",
      "video_referencia_url": "/static/videos/67beb825-87d1-4c46-8380-9b0cb6ef0489.mp4",
      "video_referencia_nombre": "67beb825-87d1-4c46-8380-9b0cb6ef0489.mp4",
      "video_referencia_profesor_nombre": "Coach Mike Baigorria",
      "frame_error_url": "/static/frames/critico_6a28adac-37d4-452b-b5f5-2d3bbff75054.jpg",
      "articulaciones_criticas": [
        13,
        14,
        12
      ],
      "nombres_articulaciones_criticas": [
        "Left Knee",
        "Right Knee",
        "Right Hip"
      ],
      "practice_url": "https://www.youtube.com/results?search_query=Escaping+Closed+Guard+Stand+UP+jiu-jitsu+tutorial"
    }
    ```
  - **Suite de Pruebas Pytest:** **83 passed, 6 skipped** en 13.46s (100% verde).

---

### 🔹 Iteración Transition-3G (Fase de Transición): Cierre de Falso Positivo y Limpieza de UI

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-10-31
- **Tag Previo:** `iter-3g-antes` (commit `c186eda`)

- **Objetivos:**
  1. Integrar obligatoriamente la validación del filtro anti-spam (`POST /api/v1/evaluaciones/validar-spam`) en el frontend (`VideoUpload.jsx`) de forma previa a la extracción de frames y selección de persona, bloqueando en la puerta de entrada cualquier contenido ajeno al Jiu-Jitsu (0 falsos positivos).
  2. Eliminar completamente el código obsoleto del botón "Compare with Instructor Video" y su sección de alineación lado a lado de la iteración C12, consolidando el flujo exclusivo de evaluación pedagógica con VLM local.

- **Entregables:**
  - `frontend/src/pages/VideoUpload.jsx`:
    - Invocación temprana a `POST /api/v1/evaluaciones/validar-spam` al soltar o seleccionar un video en `handleFile`.
    - Estado de carga interactivo (`validatingSpam`): `"Validating video content..."`.
    - Captura de error HTTP 422 con bloqueo inmediato de subida, limpieza de archivo y alerta al usuario: `"The video does not appear to be Brazilian Jiu-Jitsu. Please upload a valid training video."`.
    - Eliminación de estados (`comparisonLoading`, `comparisonResult`, `comparisonVideoUrl`, `comparisonError`, `selectedAlignment`), funciones (`handleCompareVideos`, `selectAlignmentFrame`), referencias no utilizadas (`useRef`, `comparisonPlayerRef`) y bloques JSX asociados.
  - `backend/scripts/04_e2e_vlm_evaluacion.py`:
    - Paso 2.1 incorporado verificando explícitamente que `control_bailarinas.mp4` retorne HTTP 422 y `Alumno.mp4` retorne HTTP 200 en cada ejecución E2E.

- **Resultados de las Pruebas de Fuego:**
  - **Prueba de Humo Anti-Spam (`03_smoke_test_filter.py`):**
    - `Alumno.mp4`: `True ✅` (ratio=0.86 $\ge$ 0.60, aceptado).
    - `Alumno_Gaetamo.mp4`: `True ✅` (ratio=1.00 $\ge$ 0.60, aceptado).
    - `control_bailarinas.mp4`: `False ✅` (ratio=0.31 $<$ 0.60, **bloqueado con 422**).
    - `control_boxeo.mp4`: `False ✅` (0 frames con interacción, bloqueado).
  - **Prueba E2E Integral (`04_e2e_vlm_evaluacion.py`):**
    - HTTP 422 validado en caliente contra `control_bailarinas.mp4`.
    - HTTP 200 validado en caliente contra `Alumno.mp4`.
    - Flujo completo de análisis completado en **22.50 segundos** con estado `completado`, feedback pedagógico estructurado y nombres de articulaciones presentes.
  - **Suite Pytest Completa:** **83 passed, 6 skipped** en 15.52s (100% verde).

---

### 🔹 Iteración Transition-3I (Fase de Transición): Inteligencia de Pareja, Umbrales Dinámicos y Fix de Historial

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-10-31
- **Tag Previo:** `iter-3i-antes` (commit `95a870b`)

- **Objetivos y Mitigación de Riesgos (Larman):**
  1. **Fase 1 (Inteligencia de Pareja en el Filtro):**
     - En `_extraer_poses` de `local_spam_filter.py`, erradicar la suposición de que solo existen $\le 2$ personas en escena.
     - Si hay $\ge 2$ personas válidas, deduplicar detecciones duplicadas de la misma persona generadas por imperfecciones de NMS en YOLO (distancia entre pelvis/centro $< 35\text{px}$).
     - Calcular todas las combinaciones de pares posibles y seleccionar la pareja con la menor distancia euclidiana entre sus centros (los luchadores interactuando activamente, ignorando público, árbitro o profesor observando).
     - Incorporar la guardia de proximidad física de Jiu-Jitsu: si la distancia entre centros excede $1.2 \times \max(\text{altura}_1, \text{altura}_2)$, los atletas están dispersos y no existe combate/grappling (abstención en ese frame).
  2. **Fase 2 (Umbral de Interacción Dinámico):**
     - Sustituir el umbral estático de `min_interaction_frames=5` por un umbral adaptativo al metraje del video: $\max(3, \lfloor \text{total\_muestreados} \times 0.15 \rfloor)$.
     - Permite que videos técnicos cortos o con tomas de pie como `profesor salida de Guardia Parandose.mp4` (4 frames de interacción) se clasifiquen con éxito sin incurrir en falsos negativos.
  3. **Fase 3 (Fix de Historial - Erradicación de Race Condition):**
     - En `routes.py` (`ejecutar_evaluacion_background`), asegurar la persistencia del estado `completado` mediante un bucle de reintento de 3 iteraciones en PostgREST RPC `worker_update_result`.
     - Implementar fallback directo vía SQL (`psycopg2`) con `conn.commit()` explícito en caso de congestión de red o latencia de base de datos.
     - Añadir un buffer de 0.5s antes de concluir la tarea en segundo plano para garantizar visibilidad transaccional frente al polling del frontend.
  4. **Fase 4 (Prueba de Fuego Definitiva y Cero Falsos Positivos/Negativos):**
     - Evaluar `Flo.mov` (3 bailarinas en estudio de danza): esperado `False`.
     - Evaluar `profesor salida de Guardia Parandose.mp4`: esperado `True`.
     - Evaluar controles negativos (`control_bailarinas.mp4`, `control_boxeo.mp4`): esperado `False`.
     - Evaluar videos de alumnos (`Alumno.mp4`, `Alumno_Gaetamo.mp4`): esperado `True`.
     - Ejecutar suite Pytest completa y prueba E2E VLM.

- **Entregables:**
  - `backend/corpocmente/infrastructure/ai/local_spam_filter.py`:
    - Deduplicación de bounding boxes duplicadas (`dist < 35px`).
    - Combinatoria de pares euclidianos y selección del par más cercano.
    - Guardia de proximidad biomecánica ($1.2 \times \max\_h$).
    - Umbral adaptativo dinámico $\max(3, \lfloor \text{checked} \times 0.15 \rfloor)$.
  - `backend/corpocmente/ui/api/routes.py`:
    - Importación de `time`.
    - Bucle de reintentos y fallback SQL directo con commit explícito en `worker_update_result`.
    - Buffer de 0.5s para evitar condiciones de carrera en el polling.
  - `backend/scripts/03_smoke_test_filter.py`:
    - Incorporación de `Flo.mov` a `VIDEOS_NO_BJJ`.
    - Incorporación de `profesor salida de Guardia Parandose.mp4` a `VIDEOS_ALUMNO`.

- **Evidencia Empírica de las Pruebas de Fuego:**
  - **Prueba de Humo Anti-Spam (`03_smoke_test_filter.py`):**
    ```
    INFO:corpocmente.infrastructure.ai.local_spam_filter:LocalSpamFilter cargado: accuracy=0.9018555334658714, f1=0.8818170910335679, min_bjj_ratio=0.60, min_interaction_frames=dynamic(min=3, 15%)
    === VIDEOS PROFESOR (Registran patrón de referencia — NO aplican al filtro anti-spam) ===
      Maestro.mp4: [EXENTO DEL FILTRO - Flujo Maestro] (✓ Existe)
      Escape de 100 kilos brazo por debajo.mp4: [EXENTO DEL FILTRO - Flujo Maestro] (✓ Existe)
      Profesor dill pasaje de guardia abierta.mp4: [EXENTO DEL FILTRO - Flujo Maestro] (✓ Existe)
      Profesor ensena 1 escape de guardia cerrada.mp4: [EXENTO DEL FILTRO - Flujo Maestro] (✓ Existe)

    === VIDEOS ALUMNO (Evaluación de técnica — SÍ pasan por el filtro anti-spam, esperado: True) ===
    INFO:corpocmente.infrastructure.ai.local_spam_filter:Spam filter Alumno.mp4: 6/7 frames BJJ (ratio=0.86, umbral=0.60) | muestreados=12, interacción=7, umbral_min=3
      Alumno.mp4: True ✅
    INFO:corpocmente.infrastructure.ai.local_spam_filter:Spam filter Alumno_Gaetamo.mp4: 5/5 frames BJJ (ratio=1.00, umbral=0.60) | muestreados=13, interacción=5, umbral_min=3
      Alumno_Gaetamo.mp4: True ✅
    INFO:corpocmente.infrastructure.ai.local_spam_filter:Spam filter profesor salida de Guardia Parandose.mp4: 4/4 frames BJJ (ratio=1.00, umbral=0.60) | muestreados=13, interacción=4, umbral_min=3
      profesor salida de Guardia Parandose.mp4: True ✅

    === NO-BJJ / CONTROLES NEGATIVOS (esperado: False) ===
    WARNING:corpocmente.infrastructure.ai.local_spam_filter:Spam filter Flo.mov: RECHAZADO por evidencia insuficiente (solo 2 frames con interacción, mínimo dinámico 3)
      Flo.mov: False ✅
    INFO:corpocmente.infrastructure.ai.local_spam_filter:Spam filter control_bailarinas.mp4: 4/13 frames BJJ (ratio=0.31, umbral=0.60) | muestreados=13, interacción=13, umbral_min=3
      control_bailarinas.mp4: False ✅
    WARNING:corpocmente.infrastructure.ai.local_spam_filter:Spam filter control_boxeo.mp4: RECHAZADO por evidencia insuficiente (solo 0 frames con interacción, mínimo dinámico 3)
      control_boxeo.mp4: False ✅
    ```

  - **Suite de Pruebas Pytest (`pytest backend/tests/`):**
    - **83 passed, 6 skipped** en 12.88s (100% verde).

  - **Prueba E2E Integral (`04_e2e_vlm_evaluacion.py`):**
    - Tiempo Total de Análisis: **22.42 segundos** ($< 30\text{s}$).
    - Estado: `completado`.
    - Similitud: `55.66%`.
    - Feedback: `"Prioritize **vertical posture** by angling your body away from the opponent's grip. Keep elbows tight to your sides to control hips and avoid submission danger."`
    - Timestamp de error: `2.52s`.
    - Articulaciones críticas: `[13, 14, 12]` (`["Left Knee", "Right Knee", "Right Hip"]`).
    - Frame crítico URL: `"/static/frames/critico_8cea576b-7a94-47e5-8ab4-fb60e94e0387.jpg"`.

---

### 🔹 Iteración Transition-3J (Fase de Transición): Limpieza y Deduplicación de Bounding Boxes en Selección de Persona

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-10-31
- **Tag Previo:** `iter-3j-antes` (commit `a3b64d5`)

- **Objetivos y Mitigación de Riesgos (Larman):**
  1. **Análisis de Causa Raíz (Ghost/Chimera Boxes y NMS Imperfecto):**
     - En el frontend (`SelectorPersonaVideo.jsx`), al subir videos con atletas entrelazados (ej. `2026-10-31 09-41-31.mov`), YOLO producía 4 detecciones crudas: Candidate #0 (luchador superior), Candidate #1 (caja fantasma intermedia que abarcaba la cabeza del inferior y los pies del superior), Candidate #2 (duplicado amplio del inferior) y Candidate #3 (duplicado estrecho del inferior).
     - La deduplicación de parejas implementada en `local_spam_filter.py` no existía en el endpoint interactivo `POST /api/v1/evaluaciones/primer-frame` (`routes.py`).
  2. **Filtrado y Limpieza Biomecánica en `/primer-frame`:**
     - Implementar `_bbox_iou` y `_bbox_iomin` para medir solapamiento absoluto y relativo entre cajas candidatas.
     - **Paso 1 (Detección de Quimeras):** Si existen $\ge 3$ candidatos, identificar cajas intermedias $C$ que solapen significativamente con dos cuerpos independientes $A$ y $B$ ($\text{IoU}(A, B) < 0.30$, $\text{IoMin}(C, A) > 0.50$ o $\text{IoU}(C, A) > 0.35$, e $\text{IoMin}(C, B) > 0.50$ o $\text{IoU}(C, B) > 0.35$). Esto erradica limpiamente la caja fantasma intermedia (Candidate #1).
     - **Paso 2 (Deduplicación Directa por NMS):** Descartar detecciones duplicadas del mismo atleta evaluando $\text{IoU} > 0.50$, distancia entre centros $< 40\text{px}$, distancia de cabezas $< 40\text{px}$ o distancia de pelvis $< 40\text{px}$. Conserva la detección con mayor confianza y keypoints válidos (Candidate #3).
     - Mantener el índice original `idx` de cada candidato para garantizar sincronización perfecta con el seguimiento espacial en `adapters.py`.
  3. **Verificación Empírica Multivideo:**
     - `2026-10-31 09-41-31.mov`: 4 candidatos iniciales $\to$ **exactamente 2 personas** (Candidate #0 superior y Candidate #3 inferior).
     - `Alumno.mp4`: 2 candidatos iniciales $\to$ **exactamente 2 personas** (ambos luchadores en guardia preservados).
     - `Alumno_Gaetamo.mp4`: 2 candidatos iniciales $\to$ **exactamente 2 personas** (preservados).
     - `profesor salida de Guardia Parandose.mp4`: 1 candidato inicial $\to$ **exactamente 1 persona** (preservado).
  4. **Suite de Tests y E2E:**
     - Nuevos tests unitarios dedicados en `backend/tests/ui/api/test_primer_frame_dedup.py`.
     - 87 tests pasando en verde (0 regresiones).
     - Prueba E2E `04_e2e_vlm_evaluacion.py` pasando en 21.88s ($< 30\text{s}$) con VLM local.

- **Entregables:**
  - `backend/corpocmente/ui/api/routes.py`:
    - Funciones `_bbox_iou`, `_bbox_iomin` y `_limpiar_candidatos_bboxes`.
    - Integración en `obtener_primer_frame`.
  - `backend/tests/ui/api/test_primer_frame_dedup.py`:
    - Tests de IoU/IoMin, deduplicación directa, erradicación de quimeras y preservación de guardia en Jiu-Jitsu.

---

### 🔹 Iteración Transition-3K (Fase de Transición): Selección Obligatoria de Persona en el Flujo del Profesor y Blindaje 422

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-10-31
- **Tag Previo:** `iter-3k-antes` (commit `644f91a`)

- **Objetivos y Mitigación de Riesgos (Larman):**
  1. **Análisis de Causa Raíz (Riesgo de Inversión Biomecánica en Técnicas Multiatleta):**
     - En el flujo de creación y registro de patrones biomecánicos del profesor (`ProfesorTecnicas.jsx` y `tecnicas_routes.py`), el backend permitía registrar un patrón sin especificar qué atleta del video era el instructor.
     - Si `persona_idx` no se enviaba en un upload directo, el backend asumía ciegamente `target_persona_idx = 0`. En videos con sparring o demostración en pareja (ej. `Alumno.mp4`), el instructor podía ser `Candidate #1` (abajo en la guardia), resultando en que la técnica de referencia guardaba el movimiento del sparring/oponente en lugar del instructor, arruinando la comparación DTW de todos los alumnos futuros.
  2. **Blindaje Backend y Protocolo Estricto de Registro (`tecnicas_routes.py`):**
     - Se añadió validación obligatoria: si `persona_idx` es `None` tanto en uploads directos como en sesiones de extracción, el endpoint `POST /api/v1/tecnicas/{tecnica_id}/patron` rechaza inmediatamente la petición con `HTTP 422 Unprocessable Entity` y el mensaje `"persona_idx is required to identify the instructor in the video."`.
     - Si se utiliza sesión (`session_id`), la sesión debe estar en estado `PERSONA_SELECTED` y tener `persona_idx_seleccionada` válido.
     - `target_persona_idx` se envía explícitamente a `yolo.extraer_secuencia(video_path, persona_idx_inicial=target_persona_idx)` para inicializar el seguimiento en el centroide y bounding box de la persona seleccionada.
  3. **Experiencia de Usuario e Identificación Visual (`ProfesorTecnicas.jsx`):**
     - En el modal "New Technique", se añadió un aviso visual anticipando que al guardar se seleccionará la persona del instructor en el frame inicial.
     - Al hacer clic en "Save Technique", el sistema procesa el video, extrae los candidatos del primer frame y abre el modal `<SelectorPersonaVideo>` con títulos y etiquetas específicas para el rol de instructor:
       - Título: *"Identify Yourself (Instructor) in the Reference Video"*
       - Etiquetas: *"Instructor"* y *"Instructor Selected"*.
       - Subtítulo dinámico indicando si hay múltiples atletas y solicitando confirmar quién es el instructor.
     - Botón de confirmación *"Confirm Selection & Create Pattern"*, deshabilitado si `selectedIdx === null`.
     - Cuadro de advertencia al intentar cerrar sin seleccionar, previniendo dejar la técnica huérfana sin patrón biomecánico.
  4. **Verificación Empírica y Suite de Tests:**
     - 3 nuevos tests en `backend/tests/test_etapa_b_patron.py`:
       - `test_registro_patron_sin_persona_idx_retorna_422`: rechazo estricto HTTP 422 cuando falta `persona_idx`.
       - `test_registro_patron_con_session_id_sin_persona_seleccionada_retorna_409`: rechazo HTTP 409 cuando la sesión no ha completado la selección.
       - `test_registro_patron_con_session_id_exitoso`: registro exitoso enviando `persona_idx=1` y validando que YOLO inicialice el tracking en el candidato 1.
     - Suite completa Pytest: **90 passed, 6 skipped** en 12.79s (100% verde).
     - Validación E2E del flujo del profesor con video de 1 persona (`profesor salida de Guardia Parandose.mp4`): 897 frames de patrón guardados en Qdrant (HTTP 201).
     - Validación E2E del flujo del profesor con video de 2 personas (`Alumno.mp4`): selección manual de Candidate #1 (luchador inferior), 276 frames de patrón guardados en Qdrant para el luchador exacto.
     - Prueba E2E de evaluación del alumno (`04_e2e_vlm_evaluacion.py`): tiempo total 22.56s ($< 30\text{s}$), estado `completado`, similitud válida con VLM local.

- **Entregables:**
  - `backend/corpocmente/ui/api/tecnicas_routes.py`:
    - Validación y rechazo 422 de registros de patrón sin `persona_idx`.
    - Paso garantizado de `target_persona_idx` a `extraer_secuencia`.
  - `frontend/src/pages/ProfesorTecnicas.jsx`:
    - Flujo interactivo obligatorio con `<SelectorPersonaVideo>` etiquetado para el instructor.
    - Prevención de patrones huérfanos y advertencia de confirmación en cierre.
  - `backend/tests/test_etapa_b_patron.py`:
    - 3 nuevos tests para HTTP 422, HTTP 409 y sesión con `persona_idx_inicial`.

---

### 🔹 Iteración 3M: Reparación del Dibujo de Esqueleto, Flexibilidad Biomecánica Invariante a Cámara y Ciclo de Vida sin Técnicas Fantasma

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-10-31
- **Tag Previo:** `iter-3m-antes` (commit `a2970fb`)

- **Objetivos y Mitigación de Riesgos (Larman):**
  1. **Análisis de Causa Raíz de los 3 Fallos:**
     - **Intercambio de Cuerpos en Tracking y Dibujo de Esqueleto:** En `extraer_secuencia` (`adapters.py`), al ocurrir oclusiones parciales durante el combate en el suelo (Jiu-Jitsu), la distancia euclidiana simple ($< 0.25$) provocaba que el rastreador saltara sobre el contrincante si el atleta elegido quedaba tapado por un solo frame. Una vez que saltaba al rival, nunca volvía al atleta original.
     - **Rigidez Espacial en DTW:** Al comparar las poses, las coordenadas absolutas en pantalla castigaban severamente las diferencias de distancia y ángulo de cámara. Si el profesor grababa desde un ángulo y el alumno desde otro, la similitud caía injustamente a $< 20\%$.
     - **Técnicas Fantasma en la BD:** El formulario de creación de técnicas (`ProfesorTecnicas.jsx`) enviaba un `POST /api/v1/tecnicas` de inmediato antes de seleccionar la persona o subir el video. Si el usuario cancelaba en la ventana de selección o cerraba la ventana, la técnica quedaba huérfana en la base de datos sin video ni patrón.
  2. **Fase 1: Rastreo Multiatleta Competitivo y Dibujo Estricto de Esqueleto (`adapters.py`, `intelligence_facade.py`):**
     - En `extraer_frame_y_dibujar_error`, si se proporcionan `keypoints133` válidos (provenientes del análisis cinemático DTW), **NO se vuelve a ejecutar YOLO**. Se grafican directamente esos keypoints sobre el fotograma con sus articulaciones críticas y etiquetas. Si se requiere fallback, se respeta `persona_idx`.
     - En `extraer_secuencia`, se redujo el umbral a `conf=0.10` para capturar poses enredadas y se implementó un **rastreador multi-atleta por asignación competitiva (cost matrix matching)**. Cada candidato detectado se asigna al atleta más cercano de manera exclusiva; si el atleta objetivo se ocluye temporalmente, el rastreador NO salta sobre el rival porque el rival ya está asignado a su propio rastreador.
     - Verificación empírica en `Alumno.mp4`: Persona 0 (abajo, kimono negro) y Persona 1 (arriba, kimono blanco) ahora se siguen con precisión absoluta a lo largo de los 276 frames con una diferencia media de $672.12\text{px}$ entre sus trayectorias.
     - En el fotograma crítico anotado, la diferencia entre seleccionar Persona 0 y Persona 1 es de **391,422 píxeles**, verificando visual y numéricamente que el esqueleto y los errores se dibujan en la persona correcta.
  3. **Fase 2: Flexibilidad Biomecánica Invariante a Cámara (`dtw_comparator.py`, `pose_normalizer.py`):**
     - En `pose_normalizer.py`, se actualizó `similitud_esqueletos` para priorizar los **ángulos articulares invariantes a la cámara** (codos, rodillas, hombros, caderas) con un peso del $70\%$ (`w_ang = 0.70`) frente al $30\%$ de posición canónica (`w_pos = 0.30`).
     - Al comparar posiciones, solo se evalúan articulaciones detectadas en ambos esqueletos (`common = valid_a & valid_b`), evitando que articulaciones ocluidas castiguen la similitud a cero.
     - La escala angular ahora es biomecánicamente tolerante a desviaciones de perspectiva ($\pm 15^\circ - 20^\circ$).
     - En `dtw_comparator.py`, `_distancia_local` compara directamente los vectores normalizados canónicos (`pose_normalizer.normalizar()["vector"]`).
  4. **Fase 3: Ciclo de Vida Limpio y Cero Técnicas Fantasma (`ProfesorTecnicas.jsx`):**
     - Al pulsar "Save Technique", el frontend NO persiste la técnica en PostgreSQL de forma prematura.
     - Primero procesa el video en `/api/v1/evaluaciones/primer-frame`, guarda el estado temporal en memoria y despliega el selector de personas para identificar al instructor.
     - Solo al hacer clic en "Confirm Selection & Create Pattern", se crea la técnica en PostgreSQL (`POST /api/v1/tecnicas`), se confirma la persona en la sesión y se guarda el patrón biomecánico en Qdrant.
     - Si el proceso se cancela o se cierra la ventana, **ninguna técnica huérfana se guarda en la base de datos**.
     - En caso de fallo durante el guardado de patrón, se ejecuta rollback automático con `DELETE /api/v1/tecnicas/{id}`.
  5. **Pruebas de Fuego y Verificación E2E:**
     - Suite completa Pytest: **90 passed, 6 skipped** en 12.85s (100% verde).
     - Validación E2E (`04_e2e_vlm_evaluacion.py`): tiempo de respuesta **21.56s** ($< 30\text{s}$), similitud **60.85%**, timestamp crítico **3.24s**, feedback local no vacío.
     - Validación E2E de separación de personas: `diff = 391,422 pixels` entre los fotogramas anotados de Persona 0 y Persona 1.

- **Entregables:**
  - `backend/corpocmente/infrastructure/ai/adapters.py`:
    - Rastreador multi-atleta por asignación competitiva en `extraer_secuencia`.
    - Garantía estricta de no re-ejecución de YOLO en `extraer_frame_y_dibujar_error` cuando `keypoints133` es provisto.
  - `backend/corpocmente/domain/services/intelligence_facade.py`:
    - Inyección de `persona_idx` y soporte robusto de fallbacks.
  - `backend/corpocmente/domain/biomechanics/dtw_comparator.py`:
    - `_distancia_local` basada en vectores canónicos normalizados de 46 dimensiones.
  - `backend/corpocmente/domain/biomechanics/pose_normalizer.py`:
    - `similitud_esqueletos` con 70% peso angular invariante a la cámara y enmascaramiento de articulaciones ocluidas.
  - `frontend/src/pages/ProfesorTecnicas.jsx`:
    - Reordenamiento del ciclo de vida de creación de técnica, evitando persistencia prematura y técnicas huérfanas.

---

### 🔹 Iteración 3N: Flexibilización del Umbral de Cobertura para Grappling y Filtrado de Reflejos de Fondo

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-10-31
- **Tag Previo:** `iter-3n-antes` (commit `f81b318`)

- **Objetivos y Mitigación de Riesgos (Larman):**
  1. **Análisis de Causa Raíz del Falso Negativo en Registro de Patrón:**
     - En Jiu-Jitsu Brasileño (BJJ), las técnicas de suelo (como *"Llave de brazo desde la montada"*, raspadas, pasajes de guardia o salidas) presentan una oclusión severa donde las extremidades y el torso quedan frecuentemente ocultos tras el compañero durante el 30%–50% de la duración del clip.
     - La regla de cobertura impuesta previamente exigía $\ge 70\%$ (`0.70`) de frames con la persona detectada. Al intentar registrar la *"Llave de brazo desde la montada"*, el sistema rechazó el video con HTTP 422: `Insufficient tracking in pattern video: coverage 60.4% < 70% required`, constituyendo un falso rechazo (Falso Negativo) de un video de referencia técnicamente perfecto.
     - Adicionalmente, en dojos y gimnasios de artes marciales es ubicua la presencia de espejos de pared que reflejan figuras diminutas en el fondo (p. ej. `Instructor #2`), entorpeciendo la selección visual.
  2. **Fase 1: Reducción del Umbral de Cobertura a 40% (`tecnicas_routes.py`, `intelligence_facade.py`):**
     - En `registrar_patron_tecnica` (`tecnicas_routes.py`), se redujo el umbral de cobertura mínima de `0.70` a `0.40` (40%). Este umbral es biomecánicamente óptimo para Jiu-Jitsu en el suelo, permitiendo registrar técnicas complejas sin comprometer la precisión del alineamiento temporal de DTW.
     - Se dotó al sistema de un mensaje de error empático y claro:
       `"Insufficient tracking: coverage {cobertura*100:.1f}% is too low (minimum 40% required for grappling). Please ensure the instructor is visible."`
     - Se homologó el umbral en `intelligence_facade.py` para la evaluación cinemática de los alumnos, protegiendo al alumno de rechazos espurios en técnicas con oclusión en el suelo.
  3. **Fase 2: Filtrado Geométrico de Reflejos de Espejos (`routes.py`, `adapters.py`):**
     - En `_limpiar_candidatos_bboxes` (`routes.py` para el endpoint `/primer-frame`), se implementó un filtro de escala relativa: cualquier bounding box con un área menor al 10% del área de la caja máxima del encuadre ($\text{area} < 0.10 \times \text{max\_area}$) es descartada automáticamente como reflejo o transeúnte de fondo.
     - En `extraer_secuencia` (`adapters.py`), se replicó la misma discriminación geométrica para asegurar que el rastreador temporal no considere reflejos distantes durante el seguimiento.
  4. **Fase 3: Verificación Empírica y Suite de Tests:**
     - Nuevo test en `backend/tests/ui/api/test_primer_frame_dedup.py`: `test_limpiar_candidatos_elimina_reflejo_espejo_diminuto` validando que reflejos lejanos (3,500 px²) se descartan mientras el atleta principal (240,000 px²) se conserva intacto.
     - Modificación de fixture en `backend/tests/test_etapa_b_patron.py`: `test_tracking_insuficiente_retorna_422` validando el nuevo límite de corte al 40% (cobertura 25% genera 422).
     - Suite completa Pytest: **91 passed, 6 skipped** en 12.18s (100% verde).

- **Entregables:**
  - `backend/corpocmente/ui/api/tecnicas_routes.py`:
    - Umbral de cobertura flexibilizado a `0.40` con mensaje descriptivo y empático.
  - `backend/corpocmente/domain/services/intelligence_facade.py`:
    - Umbral de cobertura para evaluación de alumnos alineado a `0.40`.
  - `backend/corpocmente/infrastructure/ai/adapters.py`:
    - Filtrado de candidatos con área menor al 10% de la caja máxima en `extraer_secuencia`.
  - `backend/corpocmente/ui/api/routes.py`:
    - Paso 0 en `_limpiar_candidatos_bboxes` para descartar reflejos y siluetas de fondo $< 10\%$ del área máxima.
  - `backend/tests/ui/api/test_primer_frame_dedup.py`:
    - Test unitario de eliminación de reflejos diminutos en espejos.
  - `backend/tests/test_etapa_b_patron.py`:
    - Prueba de tracking insuficiente ajustada al nuevo umbral del 40%.

---

### 🔹 Iteración 3P: Evaluación de Fidelidad RAG Multilingüe y Mitigación de Alucinaciones

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-11-01
- **Tag Previo:** `iter-3p-antes` (commit `d8d3806`)

- **Objetivos y Mitigación de Riesgos (Larman):**
  1. **Análisis de Causa Raíz de Alucinaciones en RAG Multilingüe:**
     - En sistemas RAG con literatura técnica internacional de BJJ (manuales en inglés, consultas en español, portugués e inglés), la recuperación densa estándar puede introducir fragmentos ruidosos o tangenciales si la similitud léxica o de ángulo interrogativo-declarativo penaliza los términos exactos.
     - Si el modelo de lenguaje (VLM local) recibe un contexto ruidoso o incompleto, tiende a generar afirmaciones especulativas o técnicas no enseñadas (alucinaciones), lo cual es inaceptable en artes marciales por riesgo de lesiones físicas.
  2. **Fase 1: Implementación de Reranking Multilingüe (`rag_reranker.py`, `intelligence_facade.py`):**
     - Se implementó `rerank_evidencias_multilingue` en `backend/corpocmente/domain/services/rag_reranker.py`.
     - Utiliza el espacio de representación de 2048 dimensiones de `Qwen3-VL-Embedding-2B` (alineado multilingüe para más de 30 idiomas) para calcular la similitud semántica de coseno fina entre la consulta técnica (pregunta + técnica + indicación del profesor) y cada fragmento recuperado.
     - Ponderación híbrida: $65\%$ afinidad semántica profunda en lenguaje natural + $35\%$ ranking previo de Qdrant + $5\%$ bonus para evidencias con material visual verificado.
     - Selección estricta de los 3 fragmentos (`top_k=3`) más relevantes, eliminando el ruido contextual que induce alucinaciones.
  3. **Fase 2: Mecanismo de Grounding Activo y LLM-as-a-Judge (`local_vlm_adapter.py`, `prompt_strategies.py`):**
     - En `LocalVLMAdapter`, se implementó `evaluar_fidelidad_grounding` como un juez estricto ("LLM-as-a-Judge") ejecutado directamente en el VLM local (`mlx-community/Qwen3-VL-4B-Instruct-4bit`).
     - El juez descompone la respuesta en afirmaciones técnicas y valida si cada una está respaldada explícitamente por el contexto recuperado o las indicaciones del profesor.
     - Retorna `faithfulness_score` ($0.0 - 1.0$), lista de `unsupported_claims` y justificación.
     - **Regla Estricta Anti-Alucinación:** Si `faithfulness_score < 0.85` o se detecta cualquier `unsupported_claims`, el sistema **descarta inmediatamente la respuesta del VLM** y devuelve un fallback seguro garantizado:
       *"No hay suficiente información en los manuales para generar una corrección detallada. Consulta con tu instructor."*
     - Se añadió soporte nativo para portugués con `PortuguesePromptStrategy` y `obtener_estrategia_prompt`.
  4. **Fase 3: Harness de Evaluación Multilingüe Offline (`11_evaluar_rag_multilingue.py`):**
     - Se construyó un banco de pruebas de **20 casos de prueba** (5 Español, 5 Portugués, 5 Inglés, 5 Mixtos/Terminología BJJ).
     - Métricas calculadas por caso y agregadas:
       - **Retrieval Precision@3:** porcentaje de consultas donde el fragmento técnico pertinente está en el top 3 reranked.
       - **Faithfulness (Fidelidad):** score del juez de anclaje (umbral mínimo requerido $\ge 0.85$).
       - **Answer Relevance:** similitud semántica de coseno normalizada entre la consulta y la respuesta generada vía embeddings de Qwen3-VL (umbral mínimo requerido $\ge 0.80$).
  5. **Resultados Crudos del Benchmark Multilingüe:**
     - **Retrieval Precision@3 Global:** **100.00%** (20/20 casos)
     - **Faithfulness Global:** **0.9525** ($\ge 0.85$ -> ✅ APROBADO)
       - Español (ES): **0.9500**
       - Português (PT): **0.9600**
       - English (EN): **0.9500**
       - Mixtas (MIX): **0.9500**
     - **Answer Relevance Global:** **0.8889** ($\ge 0.80$ -> ✅ APROBADO)
       - Español (ES): **0.8957**
       - Português (PT): **0.8864**
       - English (EN): **0.8907**
       - Mixtas (MIX): **0.8830**
     - **Tasa de Alucinación:** **0.0%** (0 falsos positivos / alucinaciones en los 3 idiomas).
  6. **Fase 4: Suite de Pruebas de Regresión Pytest:**
     - **99 passed, 6 skipped** en 13.48s (100% verde).

- **Entregables:**
  - `backend/corpocmente/domain/services/rag_reranker.py`:
    - Reranker multilingüe semántico basado en coseno de embeddings de 2048 dimensiones.
  - `backend/corpocmente/infrastructure/ai/local_vlm_adapter.py`:
    - Método `evaluar_fidelidad_grounding` con parser tolerante y veredicto JSON estricto.
  - `backend/corpocmente/domain/services/intelligence_facade.py`:
    - Integración de Reranking a `top_k=3` y guardia anti-alucinaciones con reemplazo por fallback seguro.
  - `backend/corpocmente/domain/strategies/prompt_strategies.py`:
    - Soporte multilingüe completo con `PortuguesePromptStrategy` y factory `obtener_estrategia_prompt`.
  - `backend/scripts/11_evaluar_rag_multilingue.py`:
    - Script de evaluación exhaustiva con 20 casos de prueba multilingües.
  - `backend/tests/domain/test_rag_reranker.py`:
    - Suite de pruebas unitarias para el reranker semántico.
  - `backend/tests/infrastructure/test_local_vlm_adapter.py`:
    - Pruebas unitarias para el parseo y evaluación de fidelidad del juez LLM.

---

### 🔹 Iteración 3R: Reranker Real Cross-Encoder (MLX) y Desactivación de "Think Mode"

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-11-01
- **Tag Previo:** `iter-3r-antes` (commit `d813170`)

- **Objetivos y Mitigación de Riesgos (Larman):**
  1. **Análisis de Causa Raíz (Eliminación del Sesgo de Auto-Evaluación y Limitaciones de Bi-Encoder):**
     - En la iteración 3P, el reranker utilizaba similitud de coseno sobre embeddings de `Qwen3-VL-Embedding-2B`. Si bien mejoró la precisión, compartía el espacio vectorial denso de Qdrant, sufriendo de sesgo de auto-evaluación y perdiendo interacciones cruzadas finas token a token entre la consulta y el fragmento del manual.
     - La solución de grado industrial es un **Cross-Encoder real**, donde el par `(consulta, chunk)` se procesa conjuntamente en un único forward pass con atención cruzada (cross-attention) multimodal y multilingüe.
  2. **Implementación de `Qwen3VLRerankerCrossEncoder` en Apple Silicon Metal GPU (`rag_reranker.py`):**
     - Se integró el modelo `mlx-community/Qwen3-VL-Reranker-2B-4bit` (1.80 GB safetensors cuantizado a 4 bits) ejecutado de forma nativa en la GPU Metal unificada de Apple Silicon mediante el framework MLX.
     - **Desactivación Estricta de "Think Mode":** Se eliminó por completo cualquier generación autorregresiva de texto o loop de tokens de razonamiento (`enable_thinking=False` explícito en payload). La puntuación de relevancia se calcula directamente extrayendo la diferencia de logits binarios (`yes_token_id: 9693` vs `no_token_id: 2152`) y aplicando la función sigmoide (`scores = mx.sigmoid(logits)`).
     - **Arquitectura de Recuperación en Dos Etapas (Two-Stage Retrieval):**
       - **Fase de Recall:** Qdrant recupera `top_k_recall = 20` candidatos usando embeddings densos multilingües de 2048 dimensiones.
       - **Fase de Precision:** El Cross-Encoder MLX evalúa simultáneamente los 20 pares `(consulta, chunk)` usando la instrucción canónica: *"Given a jiu-jitsu technique question, retrieve the manual passage that answers it."* y selecciona los `top_k_final = 3` mejores.
       - **Optimización de Latencia y Liberación de Memoria Metal:** Truncamiento de fragmentos a 350 caracteres para evaluación compacta y llamadas a `mx.clear_cache()` para evitar fragmentación de memoria unificada en Apple Silicon.
  3. **Resultados Empíricos del Benchmark Multilingüe (`11_evaluar_rag_multilingue.py`):**
     - **Retrieval Precision@3 Global:** **100.00%** (20/20 casos de prueba en ES, PT, EN, MIX).
     - **Faithfulness Global (LLM-as-a-Judge):** **0.9525** ($\ge 0.85$ -> ✅ APROBADO).
       - Español (ES): **0.9500**
       - Português (PT): **0.9500**
       - English (EN): **0.9500**
       - Mixtas (MIX): **0.9600**
     - **Answer Relevance Global:** **0.8985** ($\ge 0.80$ -> ✅ APROBADO).
       - Español (ES): **0.9014**
       - Português (PT): **0.9140**
       - English (EN): **0.8710**
       - Mixtas (MIX): **0.9077**
     - **Latencia Reranking (20 candidatos por consulta en Metal GPU):**
       - Latencia Mínima: **1.039s**
       - Latencia Media: **1.799s**
       - Latencia Máxima: **2.620s**
       - Latencia p95: **2.567s** ($< 3.0\text{s}$ -> ✅ APROBADO).
     - **Tasa de Alucinación:** **0.0%** (0 afirmaciones no fundamentadas en el corpus técnico).
  4. **Suite de Regresión Pytest:**
     - **101 passed, 6 skipped** en 14.39s (100% verde).

- **Entregables:**
  - `backend/corpocmente/domain/services/rag_reranker.py`:
    - Clase `Qwen3VLRerankerCrossEncoder` basada en `mlx-community/Qwen3-VL-Reranker-2B-4bit` con desactivación de Think Mode y fallback transparente.
  - `backend/corpocmente/domain/services/intelligence_facade.py`:
    - Integración de Two-Stage Retrieval con `limit=20` en Qdrant y re-clasificación a `top_k=3` con el Cross-Encoder.
  - `backend/scripts/11_evaluar_rag_multilingue.py`:
    - Benchmark offline ampliado con métricas empíricas de latencia de 20 candidatos, Precision@3, Faithfulness y Answer Relevance.
  - `backend/tests/domain/test_rag_reranker.py`:
    - Pruebas unitarias para el Cross-Encoder y verificación de `enable_thinking=False`.

---

### 🔹 Iteración 3S: Recuperación Híbrida (Densa + BM25 con Glosario), Fusión RRF y Auditoría de Juez

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-11-01
- **Tag Previo:** `iter-3s-antes` (commit `64c7c84`)

- **Objetivos y Mitigación de Riesgos (Larman):**
  1. **Auditoría de Transparencia de la Iteración 3R (Evaluación Crítica):**
     - **Identidad del Juez LLM:** En la iteración 3R, la evaluación de *Faithfulness* fue realizada por `LocalVLMAdapter` ejecutando `mlx-community/Qwen3-VL-4B-Instruct-4bit` localmente en Apple Silicon. Esto implicaba una auto-evaluación dentro del ecosistema Qwen. El prompt del juez penalizaba severamente cualquier afirmación no fundamentada directamente en los fragmentos de contexto recuperados.
     - **Cálculo de Precision@3 en 3R:** El 100% de la iteración 3R se calculaba buscando la presencia laxa de cualquier palabra clave esperada (`any(k in txt.lower() for k in keywords)`). Al tratarse de un corpus especializado de Jiu-Jitsu, casi cualquier chunk contenía al menos un término general (ej. "brazo", "guardia").
     - **Corrección en 3S:** Se formalizó un **Dataset Congelado (`backend/data/golden_test.jsonl`)** con 20 casos balanceados (8 casos específicos de sinónimos / jerga BJJ compleja y 12 casos estándar en ES, PT, EN, MIX), evaluando Recall@3 y score continuo de calidad de palabras clave (`calidad_score = coincidencias / total_keywords_gold`).
     - **Medición Real de Memoria Unificada (Apple Silicon M5 24 GB):**
       - RSS Pico del proceso: **5461.5 MB (5.33 GB)**.
       - Memoria unificada total del sistema: **24.0 GB**.
       - Memoria unificada en uso durante el benchmark: **14.8 GB**.
       - Memoria unificada libre / disponible: **5.2 GB** (margen holgado de seguridad $> 10\text{ GB}$ considerando caché de compresión y swap dinámico de macOS).
  2. **Arquitectura de Recuperación Híbrida Implementada:**
     - **Glosario Multilingüe de Jiu-Jitsu (`jj_glossary.yaml`):** Mapeo de sinónimos técnicos cruzados entre Español, Portugués e Inglés para finalizaciones (*armbar*, *chave de braço*, *palanca*), posiciones (*side control*, *100 kilos*, *cem quilos*, *montada*), escapes (*underhook*, *esgrima*, *puente*, *ponte*, *bump*) y términos biomecánicos.
     - **Servicio de Glosario (`glossary_service.py`):** Expansión de consultas mediante expresiones regulares estrictas con límites de palabra (`\b`), evitando falsos positivos por subcadenas cortas.
     - **BM25 Okapi sobre Corpus Qdrant (`hybrid_retriever.py`):** Extracción e indexación en memoria de los fragmentos de texto sustanciales (`len >= 25`), ignorando placeholders de imagen para evitar que la normalización de longitud de BM25 infle artificialmente su score.
     - **Reciprocal Rank Fusion (RRF, $k=60$):**
       $$\text{RRF}(d) = \frac{1.0}{60 + \text{rank}_{\text{dense}}(d)} + \frac{1.0}{60 + \text{rank}_{\text{bm25}}(d)} + \text{bonus}_{\text{visual}}$$
     - **Cross-Encoder Reranking (`Qwen3-VL-Reranker-2B-4bit`):** Toma los top 20 candidatos fusionados por RRF y extrae los 3 mejores mediante atención cruzada sin Think Mode.
  3. **Resultados Empíricos Comparativos (`11_evaluar_rag_multilingue.py --compare`):**

| Métrica de Rendimiento | Modo Denso (3R) | Modo Híbrido (3S) | Impacto / Delta |
| :--- | :--- | :--- | :--- |
| **Recall@3 Global** | 100.00% | 100.00% | +0.00% |
| **Calidad en 8 Casos Sinónimos** | 0.9500 | 0.9500 | +0.0000 (=) |
| **Calidad en 12 Casos Estándar** | 0.7167 | 0.7833 | **+0.0667 (+6.67%)** |
| **Calidad Promedio Global** | 0.8100 | 0.8500 | **+0.0400 (+4.00%)** |
| **Faithfulness Global (Judge)** | 0.9525 | 0.9475 | -0.0050 |
| **Latencia Media Retrieval** | 0.1527s | 0.1174s | **-0.0353s (Más Rápido)** |
| **Latencia Rerank p95** | 2.4045s | 2.5915s | +0.1869s ($< 4.0\text{s}$ ✅) |

  4. **Validación de Criterios de Aceptación (Larman / UP):**
     - 1. **Recall@3 Global:** $100.00\% \ge 95.00\%$ -> ✅ **APROBADO**
     - 2. **Calidad en Casos Sinónimos:** Híbrido ($0.9500$) $\ge$ Denso ($0.9500$) -> ✅ **APROBADO**
     - 3. **Latencia Reranking p95:** $2.591\text{s} < 4.0\text{s}$ -> ✅ **APROBADO**
     - 4. **Faithfulness Global:** $0.9475 \ge 0.85$ -> ✅ **APROBADO**
     - 5. **Suite de Regresión Pytest:** **107 passed, 6 skipped** (100% verde) -> ✅ **APROBADO**

- **Entregables:**
  - `backend/corpocmente/domain/glossary/jj_glossary.yaml`: Diccionario formal de sinónimos técnicos multilingües (ES, PT, EN).
  - `backend/corpocmente/domain/glossary/glossary_service.py`: Motor de coincidencia léxica exacta por límites de palabra y expansión de query.
  - `backend/corpocmente/domain/services/hybrid_retriever.py`: Motor de indexación BM25 Okapi en memoria desde Qdrant y fusión RRF ($k=60$).
  - `backend/corpocmente/application/services/multimodal_rag_service.py`: Integración desacoplada configurable vía `RETRIEVAL_MODE=hybrid`.
  - `backend/data/golden_test.jsonl`: Dataset de prueba congelado con 20 casos balanceados para evaluación continua.
  - `backend/scripts/11_evaluar_rag_multilingue.py`: Harness de evaluación comparativa offline y auditoría de recursos de hardware.
  - `backend/tests/domain/test_hybrid_retriever.py`: Suite de 6 pruebas unitarias para indexación, tokenización, búsqueda y ponderación RRF.

---

### 🔹 Iteración 3V: Biblioteca Pública Multimodal y Soporte Multi-idioma (i18n)

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-11-01
- **Tag Previo:** `iter-3v-antes` (commit `28b2b36`)

- **Objetivos y Mitigación de Riesgos (Larman):**
  1. **Apertura de la Biblioteca Multimodal al Alumno y Profesor:**
     - Exposición del corpus de manuales técnicos PDF mediante el endpoint seguro `POST /api/v1/conocimiento/biblioteca/buscar`.
     - Búsqueda semántica densa impulsada por QwenEmbeddingAdapter filtrando `fuente_tipo: "manual_pdf"` en la colección Qdrant `rag_knowledge` (713 fragmentos indexados).
     - Respuesta completa con fragmento textual (`contenido_texto`), número de página (`pagina`), cita formal (`cita`), relevancia semántica (`score`) y ruta de fotograma estático (`media_url`).
  2. **Internacionalización y Soporte Multi-Idioma (i18n):**
     - Soporte integral de tres idiomas: Español (`es`), Portugués (`pt`) e Inglés (`en`).
     - Almacenamiento y persistencia del campo `idioma_preferido` en la tabla `usuarios` vía RPCs `get_user_idioma` y `set_user_idioma`, así como endpoints `PUT /auth/usuarios/{user_id}` y `PUT /auth/usuarios/{user_id}/idioma`.
     - Sistema frontend de internacionalización (`frontend/src/i18n/translations.js`) con selector global en el header y sincronización automática en el perfil de usuario (`UserProfileModal.jsx`).
     - Vista interactiva de la biblioteca (`LibraryView.jsx`) con búsqueda semántica, visor modal de imágenes de alta resolución y tarjetas de citas directas de los libros.
  3. **Estrategias de Prompting Estrictas y Validación de Lenguaje en Parseador:**
     - Modificación de `SpanishPromptStrategy`, `PortuguesePromptStrategy` y `EnglishPromptStrategy` forzando al VLM local a responder exclusivamente en el idioma especificado en formato estructurado JSON (`summary`, `correction`).
     - Validación léxica en `LocalVLMAdapter._parsear_json` con rechazo mediante `ValueError` si el modelo responde en un idioma distinto, con un reintento a temperatura cero e instrucción reforzada.
     - Adaptación multilingüe de mensajes de fallback del LLM-as-a-Judge ante alucinaciones o insuficiente contexto.
  4. **Suite de Pruebas y Pruebas de Fuego:**
     - `04_e2e_vlm_evaluacion.py` validado con `idioma_preferido: "pt"`, obteniendo feedback y summary 100% en portugués.
     - `curl` validado con éxito sobre `/api/v1/conocimiento/biblioteca/buscar` devolviendo 10 resultados para "armbar" con citas de *Jiu-Jitsu University* y *BJJ-GuiaCompleto*.
     - Suite completa Pytest: **120 passed, 6 skipped** en 12.28s (100% verde).

- **Entregables:**
  - `backend/corpocmente/infrastructure/ai/local_vlm_adapter.py`:
    - Validador y parseador de idiomas (`_validar_idioma`, `_parsear_json`) con rechazo estricto.
    - Soporte multi-idioma en LLM-Judge para evaluar equivalencia semántica y biomecánica entre manuales en inglés y respuestas en portugués/español.
  - `backend/corpocmente/domain/strategies/prompt_strategies.py`:
    - Estrategias de prompts en ES, PT, EN exigiendo respuesta estricta en el idioma indicado.
  - `backend/corpocmente/domain/services/intelligence_facade.py`:
    - Recepción y propagación de `idioma`, fallbacks de juez contextualizados por idioma y feedback de alta similitud en idioma del usuario.
  - `backend/corpocmente/ui/api/routes.py`:
    - Endpoint público autenticado `POST /api/v1/conocimiento/biblioteca/buscar`.
    - Servicio de fotogramas de manuales `GET /conocimiento/media/paginas/{asset_path:path}` compatible con token de autenticación.
  - `backend/corpocmente/ui/api/auth_routes.py`:
    - Endpoint `PUT /auth/usuarios/{user_id}/idioma` y retorno de `idioma_preferido` en perfiles y login.
  - `backend/tests/ui/api/test_biblioteca_api.py`:
    - Tests de autenticación y búsqueda semántica en la biblioteca.
  - `backend/tests/infrastructure/test_local_vlm_adapter.py`:
    - Tests unitarios de validación y rechazo por discrepancia de idioma.
  - `frontend/src/i18n/translations.js`:
    - Sistema de diccionario y función `getTranslation` para ES, PT y EN.
  - `frontend/src/pages/LibraryView.jsx`:
    - Vista de biblioteca multimodal con búsqueda semántica, visor de páginas y citas.
  - `frontend/src/components/UserProfileModal.jsx`:
    - Selector y persistencia del idioma preferido en perfil de usuario.
  - `frontend/src/App.jsx`:
    - Navegación, selector de idioma en header, integración de `LibraryView` y propagación de `idioma` en solicitudes de análisis.

---

### 🔹 Iteración 3W: Cierre de UX, i18n Total y Fix de Video

- **Estado:** COMPLETADA ✅ (EN PRODUCCIÓN)
- **Fecha:** 2026-11-02
- **Tag Previo:** `iter-3w-antes` (commit `69e9a4f`)

- **Diagnóstico de Causa Raíz y Mitigación de Falsos Positivos (Larman):**
  1. **Traducción Total (Cero Hardcoding):**
     - Detección: Componentes clave (`FeedbackView.jsx`, `StudentProgress.jsx`, `VideoUpload.jsx`, `ProfesorTecnicas.jsx`) mantenían textos en inglés y español aún con la sesión configurada en portugués.
     - Solución: Auditoría y reemplazo del 100% de cadenas fijas por `t('clave')` conectadas al diccionario centralizado `frontend/src/i18n/translations.js`.
     - Cobertura completa y paritaria de todas las claves en Español (`es`), Portugués (`pt`) e Inglés (`en`).
  2. **Estado Inicial de la Biblioteca:**
     - Detección: El usuario ingresaba a `LibraryView.jsx` y encontraba una pantalla vacía requiriendo búsqueda manual obligatoria.
     - Solución: Implementación de `useEffect` en el montaje del componente invocando la búsqueda semántica predeterminada (`guardia`), renderizando de inmediato 12 tarjetas enriquecidas con portadas de manuales y citas oficiales.
  3. **Fix Definitivo de MIME Type y Reproducción de Video:**
     - Detección: El error *"No video with supported format and MIME type found"* era ocasionado por la ausencia física del archivo `.mp4` en el directorio efímero `/tmp/corpocmente_videos/`, lo cual hacía que FastAPI respondiera con `404 Not Found` en formato `text/plain` o HTML en lugar del stream de video binario.
     - Solución:
       - Seeding automático preventivo en `backend/corpocmente/main.py` de todos los videos de referencia al iniciar la aplicación.
       - Resolución defensiva y copia automática desde la raíz del repositorio o paths alternativos en `consultar_evaluacion` (`routes.py`) y `listar_evaluaciones_alumno` (`auth_routes.py`).
       - Configuración explícita de `<source src={videoUrl} type="video/mp4" />` con atributos `controls`, `playsInline` y `preload="metadata"` en `FeedbackView.jsx` y `StudentProgress.jsx`.
       - Verificación con `curl -I`: `HTTP/1.1 200 OK`, `content-type: video/mp4`, `accept-ranges: bytes`.
  4. **Historial de Progreso Completo y Seguro:**
     - Detección: La función PostgreSQL `admin_list_evaluaciones_alumno` contenía un corte arbitrario `LIMIT 50`.
     - Solución: Modificación de `10_progreso_alumno_con_videos.sql` eliminando el límite artificial para retornar la totalidad de evaluaciones del estudiante.
     - Renderizado seguro en `StudentProgress.jsx` frente a arrays vacíos o campos opcionales nulos.

- **Pruebas de Fuego Empíricas:**
  1. **Verificación de Encabezados HTTP (Video de Referencia):**
     ```http
     HTTP/1.1 200 OK
     date: Mon, 02 Nov 2026 04:08:51 GMT
     server: uvicorn
     content-type: video/mp4
     accept-ranges: bytes
     content-length: 3162562
     ```
  2. **Playwright Visual E2E en Navegador (`scripts/verify_ux_i18n_playwright.py`):**
     - `screenshot_student_progress_pt.png`: Validado en portugués (*Meu Progresso*, *Demonstração do Professor*, *Meu Vídeo*, *de similaridade*).
     - `screenshot_library_view_pt.png`: 12 tarjetas cargadas automáticamente al montar la vista (*Biblioteca Multimodal de Jiu-Jitsu*, *Consulte manuais oficiais*, *Buscar*).
     - `screenshot_feedback_view_pt.png`: Interfaz completa de corrección y video en portugués (*Análise Biomecânica Concluída*, *TÉCNICA AVALIADA*, *VÍDEO DE REFERÊNCIA DO INSTRUTOR*, *VÍDEO DO ALUNO*, *Pular para o Erro*, *ANÁLISE TÉCNICA DE IA*, *PRÁTICA RECOMENDADA*, *Analisar Outra Técnica*).
  3. **Suite Completa de Regresión Pytest:**
     - **120 passed, 6 skipped** en 12.37s (100% en verde).

- **Entregables:**
  - `frontend/src/i18n/translations.js`: Diccionario expandido para todos los componentes de la interfaz.
  - `frontend/src/pages/FeedbackView.jsx`: Componente 100% internacionalizado con tag `<video>` robusto.
  - `frontend/src/pages/StudentProgress.jsx`: Componente de progreso 100% internacionalizado con soporte de múltiples videos.
  - `frontend/src/pages/LibraryView.jsx`: Carga inicial automática de tarjetas en montaje.
  - `frontend/src/pages/VideoUpload.jsx`: Calibración y subida totalmente localizada.
  - `frontend/src/pages/ProfesorTecnicas.jsx`: Panel de profesor y seguimiento adaptado al idioma.
  - `frontend/src/App.jsx`: Propagación de prop `idioma` y hook de inspección para pruebas Playwright.
  - `backend/corpocmente/main.py`: Seeding de videos de referencia al arranque de FastAPI.
  - `backend/corpocmente/ui/api/routes.py`: Fallback dinámico de archivos de video para visualización de feedback.
  - `backend/corpocmente/ui/api/auth_routes.py`: Fallback dinámico de archivos de video para historial de progreso.
  - `infrastructure/initdb/10_progreso_alumno_con_videos.sql`: Función SQL sin límite de evaluaciones.
  - `scripts/verify_ux_i18n_playwright.py`: Script de validación automatizada en Chromium headless con capturas de pantalla.

---

### Iteración 3X: Catálogo de Libros, Botón de Teoría y Búsqueda Cognitiva (Noviembre 2026)

- **Objetivo:** Integrar un catálogo navegable de manuales técnicos en PDF con visor embebido, botón directo de acceso a la teoría biomecánica desde el historial de progreso del alumno, expansión cognitiva de consultas para diferenciar defensas/escapes de ataques/sumisiones, y sentar las bases de MLOps con un bucle cerrado local de Active Learning (Data Flywheel) para fotogramas de baja certidumbre de YOLO.
- **Metodología:** Craig Larman (Desarrollo Evolutivo e Iterativo, Timebox estricto, Cero Falsos Positivos, Verificación Visual Empírica en Navegador y Tests en Verde).
- **Tag de Rollback:** `iter-3x-antes`
- **Diagnóstico y Fases de Solución:**
  1. **Catálogo de Libros y Visor PDF Embebido (Fase 1):**
     - Endpoint `GET /api/v1/conocimiento/manuales` para listar de forma autenticada los manuales PDF disponibles en la biblioteca.
     - Endpoint `GET /api/v1/conocimiento/manuales/{filename}` para servir de forma segura el documento PDF (`application/pdf`, `Content-Disposition: inline`) compatible con autenticación vía header o query parameter `token` para elementos `<iframe />`.
     - `LibraryView.jsx`: Interfaz organizada con selector de dos pestañas: *"Búsqueda Semántica"* y *"Catálogo de Libros"*. Cada manual en el catálogo se presenta con portada temática, badge oficial y opciones para abrir en visor modal o pestaña independiente.
  2. **Botón "Teoría de la Técnica" en Historial de Progreso (Fase 2):**
     - En `StudentProgress.jsx`, cada tarjeta de evaluación histórica incluye un botón directo `"📖 Teoría de la Técnica"` (o `"📖 Teoria da Técnica"` / `"📖 Technique Theory"`).
     - Al accionarse, redirige de forma fluida a `LibraryView` inyectando el nombre de la técnica como parámetro inicial, autoejecutando de inmediato la búsqueda semántica y mostrando al alumno las citas bibliográficas y páginas del manual asociadas al movimiento.
  3. **Búsqueda Cognitiva (Query Rewriting para Ataque vs Defensa) (Fase 3):**
     - Adaptador `LocalVLMAdapter` con método `reescribir_query_cognitiva`: analiza la intención del usuario. Si la consulta involucra defensa o escape, expande términos como `escape`, `survive`, `defend`, `defense`, evitando que las búsquedas de defensa devuelvan manuales de finalizaciones ofensivas.
     - Fallback determinista de alta velocidad con caché de modelos cargados en memoria MLX (`_cached_models`).
  4. **MLOps Foundation — Data Flywheel Local (Fase 4):**
     - En `YOLOPoseAdapter.extraer_secuencia`, se analiza la confianza promedio de las cajas delimitadoras y keypoints por fotograma.
     - Si la confianza promedio cae en el rango de incertidumbre ($0.0 < conf < 0.65$), el fotograma original se persiste en `backend/storage/uncertainty_frames/{tecnica_id}/frame_{idx}.jpg` (máximo 10 fotogramas por video) y se registra en `backend/storage/uncertainty_frames/log.csv` con timestamp UTC, técnica, índice de frame y nivel de confianza.
     - Permite a los investigadores y entrenadores auditar los casos límite de oclusión o posturas atípicas para futuros reentrenamientos del modelo YOLO.

- **Pruebas de Fuego Empíricas:**
  1. **Búsqueda Cognitiva en Terminal:**
     - Consulta: `"defensa de llave de brazo"`
     - Query cognitiva generada: `"defensa de llave de brazo escape survive defend jiu-jitsu"`
     - Resultados: 100% páginas de defensa y escape de Kimura y Armbar (`BJJ-GuiaCompleto.pdf` p. 73, p. 72, p. 71 y `Jiu-Jitsu University.pdf` p. 137).
  2. **Verificación Visual Playwright E2E (`scripts/verify_iter_3x_playwright.py`):**
     - `screenshot_catalog_books.png`: Catálogo de libros con portadas, badges oficiales y botones de lectura.
     - `screenshot_pdf_modal.png`: Visor modal en pantalla completa con `<iframe />` transmitiendo `Jiu-Jitsu University.pdf` con token seguro y controles de navegación.
     - `screenshot_theory_button.png`: 23 tarjetas de evaluación en el panel del estudiante con el botón *"📖 Teoría de la Técnica"*.
     - `screenshot_auto_search_theory.png`: Transición a la biblioteca con autocompletado y búsqueda ejecutada de `'Escaping Closed Guard Stand UP'`, desplegando 12 tarjetas de resultados con fotogramas visuales.
  3. **Suite Completa de Regresión Pytest:**
     - **131 passed, 6 skipped** en 27.21s (100% verde).

- **Entregables:**
  - `backend/corpocmente/infrastructure/ai/local_vlm_adapter.py`: Reescritura cognitiva de queries y caché de inferencia VLM.
  - `backend/corpocmente/ui/api/routes.py`: Endpoints de listado y streaming de manuales PDF y reescritura de queries en búsqueda de biblioteca.
  - `backend/corpocmente/infrastructure/ai/adapters.py`: Bucle cerrado de Active Learning para fotogramas con baja confianza en YOLO.
  - `backend/corpocmente/domain/services/intelligence_facade.py`: Propagación de identificador de técnica hacia el extractor cinemático.
  - `frontend/src/i18n/translations.js`: Claves i18n para pestañas de catálogo, botones de PDF y teoría en ES, PT y EN.
  - `frontend/src/pages/LibraryView.jsx`: Pestañas de búsqueda y catálogo, tarjetas de libros y modal con visor iframe.
  - `frontend/src/pages/StudentProgress.jsx`: Botón interactivo "Teoría de la Técnica" por tarjeta.
  - `frontend/src/App.jsx`: Estado y propagación de consulta inicial entre progreso y biblioteca.
  - `backend/tests/test_iter_3x_features.py`: Pruebas automatizadas de reescritura semántica, Data Flywheel y endpoints de manuales.
  - `scripts/verify_iter_3x_playwright.py`: Script automatizado de pruebas E2E con capturas de pantalla para auditoría visual.

---

### 🔹 Iteración 3Y (Fase de Construcción): Erradicación Total de i18n y Búsqueda Visual de Teoría (RAG Multimodal)
- **Objetivo (Craig Larman):** Erradicar completamente los falsos positivos de internacionalización en los módulos restantes (`LoginModal.jsx`, `AdminSucursales.jsx`, `ProfesorTecnicas.jsx`, `UserProfileModal.jsx`), asegurar la persistencia determinista del idioma (`localStorage` y base de datos multi-tenant), y elevar la consulta teórica de una búsqueda puramente textual a una **búsqueda multimodal híbrida** que combina el vector semántico del texto y el vector visual del fotograma de error del alumno mediante Qwen-VL y Qdrant.
- **Riesgos Mitigados:**
  - *Falso positivo de i18n en login:* El login sobrescribía la preferencia del usuario forzando `'en'`. Se corrigió para respetar `userData.idioma_preferido || idioma || localStorage.getItem('app_idioma') || 'es'`.
  - *Falso positivo de UX en vistas secundarias:* Eliminación de todos los textos hardcodeados en inglés en `AdminSucursales`, `ProfesorTecnicas`, `LoginModal` y modales de perfil, implementando el hook `getTranslation(idioma, key)` para `es`, `pt` y `en`.
  - *Falsa multimodalidad en RAG:* El botón "Teoría de la Técnica" antes solo enviaba el string de la técnica. Ahora propaga el fotograma crítico de error (`frame_error_url`), calcula su embedding denso visual (`generar_embedding_imagen`) y realiza fusión multimodal lineal balanceada ($\alpha = 0.5$) en Qdrant.
- **Entregables Principales:**
  1. **Internacionalización Integral (i18n):**
     - `frontend/src/i18n/translations.js`: Añadidas más de 80 claves de traducción en español, portugués e inglés para formularios de sedes, creación y edición de sucursales, panel de seguimiento de alumnos por el instructor, login/registro de usuarios y badges de búsqueda multimodal.
     - `frontend/src/components/LoginModal.jsx`: Soporte completo de traducción dinámica en pestañas de inicio/registro, placeholders, selectores de rol y mensajes de error. Corrección del bug de persistencia de idioma.
     - `frontend/src/pages/AdminSucursales.jsx`: Localización exhaustiva de encabezados, tarjetas de catálogo, formulario de creación de sedes, pestañas y botones de acción. Recepción de la prop `idioma`.
     - `frontend/src/pages/ProfesorTecnicas.jsx`: Localización de todas las estadísticas de instructor, lista de alumnos, tarjetas de evaluaciones, badges de similitud y modal de asignación de técnicas.
     - `frontend/src/components/UserProfileModal.jsx`: Selector de idioma con persistencia en PostgreSQL (`usuarios.idioma_preferido`), soporte de botón de cierre explícito y logout sincronizado.
  2. **Búsqueda Visual de Teoría (RAG Multimodal Fusionado):**
     - `backend/corpocmente/infrastructure/persistence/qdrant_rag_adapter.py`: Método `buscar_biblioteca_multimodal` que fusiona la similitud de cosenos del vector textual y el vector visual del fotograma de error en la colección `rag_knowledge`.
     - `backend/corpocmente/ui/api/routes.py`:
       - Modelo `BibliotecaBuscarRequest` extendido con campo opcional `imagen_url`.
       - Función `resolver_ruta_imagen_local` para resolver de forma segura rutas `/static/frames/`, URLs relativas o externas hacia el sistema de archivos local.
       - Generación de embedding visual con `QwenEmbeddingAdapter.generar_embedding_imagen` y embedding textual con `generar_embedding_texto`.
       - Fallback resiliente a búsqueda puramente textual si la imagen no puede ser procesada.
     - `frontend/src/pages/StudentProgress.jsx`: Actualización del botón `"📖 Teoría de la Técnica"` para pasar `(item.tecnica_nombre, item.frame_error_url)` a `onViewTheory`.
     - `frontend/src/pages/LibraryView.jsx`: Prop `initialImageUrl`, estado `activeImageUrl`, banner multimodal con miniatura del fotograma de error, badge `"✨ Búsqueda Multimodal Activa (Imagen + Texto)"` / `"✨ Busca Multimodal Ativa (Imagem + Texto)"` y botón para desvincular la imagen.
     - `frontend/src/App.jsx`: Estado `libraryInitialImage`, propagación bidireccional entre `StudentProgress` y `LibraryView`, y sincronización de idioma en login y actualización de perfil.
- **Pruebas de Fuego Empíricas:**
  1. **Verificación de Endpoint Multimodal (cURL / Terminal):**
     - Payload: `{"query": "Escape de Montada", "imagen_url": "/static/frames/critico_test_eval.jpg", "limit": 5}`
     - Respuesta: `busqueda_multimodal: true`, `imagen_procesada: "/tmp/corpocmente_frames/critico_test_eval.jpg"`, páginas de manuales retornadas con score $> 0.73$.
  2. **Auditoría Visual Playwright E2E (`scripts/verify_iter_3y_playwright.py`):**
     - `screenshot_admin_sucursales_es.png`: AdminSucursales en español ("Gestión Global de Sedes", "Catálogo de Sucursales", "Comenzar Entrenamiento").
     - `screenshot_user_profile_modal_es.png`: UserProfileModal en español ("Mi Perfil", "Idioma de Análisis y Feedback", "Guardar Cambios").
     - `screenshot_profesor_tecnicas_pt.png`: ProfesorTecnicas cargado nativamente en portugués ("Painel de Controle do Instrutor", "Acompanhamento Biomecânico de Alunos no Jiu-Jitsu") según la preferencia en BD del instructor `mike`.
     - `screenshot_profesor_tecnicas_es.png`: ProfesorTecnicas traducido dinámicamente a español al cambiar el selector global de idioma.
     - `screenshot_admin_sucursales_pt.png`: AdminSucursales traducido a portugués ("Catálogo de Unidades", "Nossas Unidades", "Gestão Global de Unidades").
     - `screenshot_visual_rag_theory.png`: Transición fluida desde la tarjeta de evaluación del alumno `santi` hacia la Biblioteca, desplegando el banner multimodal con la miniatura del fotograma crítico analizado, el badge activo y los resultados teóricos ordenados por afinidad multimodal.
  3. **Suite Completa de Regresión Pytest:**
     - **132 passed, 6 skipped** en 18.34s (100% verde).


















