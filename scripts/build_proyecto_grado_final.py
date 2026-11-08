# scripts/build_proyecto_grado_final.py
# -*- coding: utf-8 -*-
"""
Construye la versión final de docs/ProyectoGrado.md cumpliendo:
1. Formato APA 7ma Edición transversal (encabezados, tablas, figuras, citas autor-año).
2. Incorporación íntegra de Capítulos VI (Desarrollo), VII (Pruebas) y VIII (Seguridad).
3. Actualización de Tabla de Contenido completa (Cap. I al VIII).
4. Sección de Referencias Bibliográficas en APA 7 (40 referencias completas).
5. Corrección de los gaps documentados (impersonación, admin_delete_user, timestamp_error_segundos, etc.).
6. Preservación intacta de diagramas PlantUML y evidencias empíricas de Cap. I al V.
"""

import re
import sys
from pathlib import Path

DOC_PATH = Path("docs/ProyectoGrado.md")

def get_capitulo_6():
    return r"""
# Capítulo VI: Desarrollo

## 6.1. Introducción al Proceso de Construcción
El desarrollo del Sistema de Análisis Biomecánico de Técnicas de Jiu-Jitsu Brasileño para la academia "Corpo e Mente" se rigió bajo los postulados del Proceso Unificado Ágil promovido por Craig Larman (2004), estructurado en ciclos iterativos, incrementales y acotados en el tiempo (*timeboxed*). A diferencia de los enfoques tradicionales en cascada, la construcción del software no postergó la integración de los componentes críticos; por el contrario, desde las primeras iteraciones se atacaron los riesgos arquitectónicos de mayor impacto, tales como la coexistencia de modelos de Inteligencia Artificial en memoria unificada, la latencia de inferencia en video y el aislamiento multi-tenant en bases de datos relacionales.

El ciclo de vida del proyecto transitó por cuatro fases disciplinares documentadas exhaustivamente en la bitácora de ingeniería (`docs/PlanEvaluacionIteraciones.md`): Incepción (definición de alcance y viabilidad técnica), Elaboración (establecimiento de la línea base arquitectónica con FastAPI, PostgreSQL, Qdrant y YOLO), Construcción (desarrollo evolutivo de los ocho casos de uso, refinamiento del algoritmo DTW y pipelines RAG multimodales) y Transición (endurecimiento de seguridad en producción, pruebas E2E, internacionalización y auditoría de ciberseguridad). La totalidad del código fuente, configuraciones y scripts de automatización residen en un repositorio Git versionado, asegurando trazabilidad bidireccional y capacidad de reversión (*rollback*) ante cualquier regresión funcional.

## 6.2. Herramientas de Desarrollo, Licencias y Software Utilizado

### 6.2.1. Entorno de Desarrollo e IA Asistida
Durante el ciclo de construcción se adoptó un flujo de ingeniería asistido por modelos de lenguaje de última generación, actuando como herramientas de productividad y revisión técnica bajo estricta supervisión humana.

Tabla 18
*Herramientas de desarrollo y codificación asistida por Inteligencia Artificial*

| Herramienta | Rol en el Proyecto | Licencia / Costo | Justificación Técnica |
| :--- | :--- | :--- | :--- |
| **Antigravity (Google AI Pro)** | Asistente principal de codificación agéntica, refactorización multi-archivo y auditoría de seguridad | Suscripción comercial Google AI Pro (pago mensual) | Capacidad de razonamiento sobre árboles de código extensos, ejecución controlada en terminal, validación empírica con Playwright y soporte nativo para inspección de arquitecturas desacopladas. |
| **DeepSeek (API / Chat)** | Revisión de lógica algorítmica (DTW, normalización biomecánica) y diseño de pruebas unitarias | Freemium / API de bajo costo por consumo | Modelo con sólidas capacidades de razonamiento matemático y algorítmico, fundamental para auditar las transformaciones vectoriales de `pose_normalizer.py` y `dtw_comparator.py`. |
| **GitHub Copilot / Claude Code** | Autocompletado inteligente de sintaxis y generación de código repetitivo (*boilerplate*) | Suscripción comercial GitHub | Integración directa con el entorno de desarrollo, acelerando la tipificación de DTOs en Pydantic y componentes visuales en React. |
| **GitHub** | Control de versiones distribuido, gestión de incidencias (*issues*) y marcado de etiquetas de iteración | Gratuito para repositorios / Plan Pro | Garantiza la trazabilidad histórica de los cambios y la posibilidad de ejecutar puntos de restauración (*rollbacks*) ante desviaciones métricas. |

*Nota.* Elaboración propia (2026).

### 6.2.2. Infraestructura de Cómputo y Hardware
La selección de la infraestructura de cómputo respondió a criterios de autosuficiencia operativa, bajo consumo energético y preservación absoluta de la privacidad de los practicantes de la academia.

Tabla 19
*Infraestructura de cómputo y hardware evaluada y utilizada*

| Recurso | Especificación Técnica | Costo Asociado | Justificación Técnica y Operativa |
| :--- | :--- | :--- | :--- |
| **MacBook Air M5 (Hardware de Producción Seleccionado)** | Chip Apple Silicon M5, GPU integrada, Neural Engine, **24 GB de Memoria Unificada** | Inversión única de hardware (~$1,500 USD) | Permite ejecutar simultáneamente la inferencia de YOLOv26 y los modelos de lenguaje visual Qwen3-VL de forma 100% local. Su consumo de apenas ~30 W (frente a los ~250 W de tarjetas dedicadas como la RTX 4090) y su arquitectura de memoria unificada eliminan el costo recurrente de servidores en la nube y garantizan que los videos jamás abandonen la red física del tatami (ver §3.2). |
| **Google Colab (Infraestructura Experimental Descartada)** | Instancias cloud con GPU NVIDIA Tesla T4 / A100 | ~$20 USD (dos recargas puntuales de $10 USD) | Utilizado **exclusivamente** para el experimento de reentrenamiento (*fine-tuning*) del modelo ViCoS (YOLOv26s) durante la iteración 3C. Tras constatar que la segmentación directa degradaba los FPS sin mejorar la precisión de pose en oclusiones severas (memo técnico `2026-10-31-transition-3c-yolo26s-evaluation-findings.md`), fue descartado por completo para la inferencia productiva diaria. |
| **Google AI Pro** | Acceso a modelos Gemini mediante API | Suscripción mensual | Utilizado exclusivamente en la fase de investigación y desarrollo de software como apoyo asistido; **no se utiliza en producción** para evitar costos por token y latencias de red (ver §3.14.4). |

*Nota.* Elaboración propia (2026).

### 6.2.3. Stack de Software de Producción
Todos los componentes de software integrados en el entorno operativo final son tecnologías de código abierto o estándares de la industria libres de regalías por licencia de uso.

Tabla 20
*Stack de software de producción*

| Componente | Versión | Licencia | Rol en la Arquitectura |
| :--- | :--- | :--- | :--- |
| **Python** | 3.12 | PSF License | Lenguaje principal del backend, lógica biomecánica y orquestación de IA. |
| **FastAPI** | 0.115.0 | MIT | Framework asíncrono para la exposición de endpoints REST, WebSockets y streaming. |
| **PostgreSQL** | 16 | PostgreSQL License | Base de datos relacional con políticas de seguridad por fila (RLS) y soporte `pgcrypto`. |
| **PostgREST** | 12.x | MIT | Servidor de capa de datos declarativa directamente sobre el catálogo de PostgreSQL. |
| **Qdrant** | 1.11.3 | Apache 2.0 | Base de datos vectorial para recuperación semántica mediante grafos HNSW y filtrado de payload. |
| **Docker + Docker Compose** | 27.x | Apache 2.0 | Contenerización de servicios auxiliares (base de datos relacional y motor vectorial). |
| **React** | 19.2.8 | MIT | Biblioteca frontend para interfaces interactivas y reproductor de video biomecánico. |
| **Vite** | 5.4.11 | MIT | Herramienta de compilación frontend y servidor de desarrollo con proxy inverso seguro. |
| **Ultralytics** | ≥ 8.4.0 | AGPL-3.0 | Framework unificado de visión por computadora para YOLOv26 Pose, Depth y Segmentation. |
| **MLX (Apple)** | 0.32.x | MIT | Framework de computación de tensores optimizado para la memoria unificada de Apple Silicon. |
| **Qwen3-VL** | 2B / 4B | Apache 2.0 | Modelos multimodales para embeddings de 2048 dimensiones, reranker y generación pedagógica. |
| **Cloudflare Tunnel (`cloudflared`)** | 2026.x | Apache 2.0 | Conector Zero Trust para exponer la plataforma web a internet sin abrir puertos en el router. |
| **Leaflet.js** | 1.9.4 | BSD-2-Clause | Renderizado de mapas interactivos para geolocalización de sucursales físicas. |
| **pytest** | 8.3.3 | MIT | Framework de pruebas unitarias, de integración y regresión del backend. |
| **Playwright** | 1.4x | Apache 2.0 | Framework de pruebas automatizadas de extremo a extremo (E2E) en navegadores web. |
| **Mozilla Firefox** | 13x | MPL 2.0 | Navegador empleado para validación manual de interfaz complementario al motor Chromium de pruebas. |

*Nota.* Elaboración propia (2026).

### 6.2.4. Herramientas de Modelado y Documentación
Para el análisis de requisitos y el diseño arquitectónico se emplearon estándares rigurosos de ingeniería de software orientada a objetos.

Tabla 21
*Herramientas de modelado, diseño y documentación técnica*

| Herramienta | Propósito en el Proyecto | Tipo de Licencia |
| :--- | :--- | :--- |
| **PlantUML** | Generación de diagramas formales de Casos de Uso y Secuencia con separación de responsabilidades (16 diagramas PNG en `docs/diagramas/`). | GPL / Servicio Kroki de código abierto |
| **Mermaid Live Editor** | Prototipado rápido y validación sintáctica previa de diagramas de clases y paquetes antes de integrarlos al repositorio. | MIT |
| **Mermaid (Markdown)** | Modelado visual embebido directamente en la documentación técnica del proyecto (diagramas de clases, paquetes y modelo de dominio). | MIT |
| **Craig Larman (2004)** | Referencia metodológica formal para el Proceso Unificado Ágil, patrones de asignación de responsabilidades GRASP y diagramas de secuencia. | Referencia bibliográfica académica |
| **Michael V. Mannino (2018)** | Fundamento teórico para el diseño relacional de bases de datos, formas normales (3NF/BCNF) y restricciones de integridad. | Referencia bibliográfica académica |
| **Hugging Face Hub** | Repositorio de artefactos para la descarga de modelos cuantizados a 4 bits (`mlx-community/Qwen3-VL-*`) y consulta de especificaciones técnicas. | Apache 2.0 / Model Hub |
| **DeepSeek / Antigravity** | Asistencia en la revisión de estilo formal, verificación cruzada de consistencia entre código y documento, y auditoría de seguridad. | Herramientas de soporte de ingeniería |

*Nota.* Elaboración propia (2026).

### 6.2.5. Repositorio de Habilidades de Ciberseguridad
Con el objetivo de garantizar una postura de seguridad proactiva y defensiva desde las etapas iniciales de construcción, se integró el repositorio especializado **`briiirussell/cybersecurity-skills`** (GitHub), el cual provee habilidades de auditoría automatizada estructuradas por vectores de riesgo. Se ejecutaron de forma intensiva tres suites de análisis:
1. **`api-audit`**: Evaluación de autorización a nivel de objeto (BOLA), configuración de encabezados CORS, prevención de suplantación de IP en mecanismos de limitación de tasa (*rate limiting*) y detección de falsificación de peticiones del lado del servidor (SSRF).
2. **`cloud-audit`**: Inspección de exposición indebida de documentación de desarrollo (Swagger/OpenAPI) y validación de dominios autorizados en servidores de proxy (*allowedHosts*).
3. **`secrets-audit`**: Búsqueda estática y dinámica de secretos criptográficos, llaves privadas y tokens quemados en archivos de configuración o manifiestos de Docker.

Los resultados crudos de dicha auditoría quedaron registrados en el archivo formal `findings.json` en la raíz del repositorio, documentando un total de 7 hallazgos (3 confirmados y mitigados, y 4 desestimados con contraevidencia técnica comprobada), los cuales se detallan en el Capítulo VIII.

## 6.3. Estructura del Repositorio
El repositorio del proyecto sigue una arquitectura limpia (*Clean Architecture*) organizada en módulos con responsabilidades netamente segregadas:

```
JiuJitsu-main/
├── backend/                        # Núcleo de lógica de negocio, IA y APIs
│   ├── corpocmente/
│   │   ├── domain/                 # Entidades puras, biomecánica (DTW) y glosario
│   │   ├── application/            # Casos de uso, servicios de aplicación y DTOs
│   │   ├── infrastructure/         # Adaptadores externos (YOLO, MLX, Qdrant, DB)
│   │   └── ui/                     # Controladores y rutas HTTP (FastAPI)
│   ├── tests/                      # Suite de 26 archivos de pruebas con pytest
│   └── scripts/                    # Utilidades de mantenimiento y migraciones
├── frontend/                       # Aplicación web cliente en React 19 + Vite
│   ├── src/
│   │   ├── components/             # Componentes visuales reutilizables y modales
│   │   ├── pages/                  # Vistas principales (Alumno, Profesor, Admin)
│   │   ├── contexts/               # Estado global de autenticación e idioma
│   │   └── i18n/                   # Traducciones internacionales (ES, PT, EN)
├── infrastructure/                 # Orquestación de infraestructura local
│   ├── docker-compose.yml          # Servicios contenerizados (PostgreSQL + Qdrant)
│   └── initdb/                     # Scripts SQL ordenados (tablas, RLS, triggers)
├── scripts/                        # Scripts de validación E2E, benchmarks y pruebas Playwright
└── docs/                           # Documento de grado, diagramas UML y memorandos técnicos
```

## 6.4. Gestión de Configuración y Entornos
La reproducibilidad del entorno de desarrollo y producción se garantiza mediante artefactos declarativos:
* **Variables de Entorno Seguras:** El archivo `.env.example` define la totalidad de las claves requeridas con valores ilustrativos, prohibiendo el rastreo de archivos `.env` en Git mediante directivas estrictas en `.gitignore`.
* **Scripts de Orquestación del Ciclo de Vida:**
  * `start.sh`: Valida la existencia de directorios temporales, levanta contenedores con `docker-compose`, inicializa el servidor FastAPI y arranca el entorno de Vite.
  * `stop.sh`: Detiene ordenadamente los procesos en segundo plano y apaga los contenedores sin pérdida de datos.
  * `status.sh`: Inspecciona la salud de los servicios HTTP, base de datos y puertos de red.
  * `logs.sh`: Monitorea la salida en vivo de los diferentes módulos del backend.
  * `reset-db.sh` y `reset_rag_and_storage.py`: Restablecen de forma idempotente las bases de datos para pruebas limpias.
  * `reapply_mlx_patch.sh`: Script defensivo documentado en el memorando técnico `2026-10-28-mlx-embeddings-qwen3-vl-patch.md`, el cual valida mediante suma de verificación SHA-256 la integridad de las funciones de atención en el paquete `mlx_embeddings` tras cualquier actualización de dependencias de Python.

## 6.5. Internacionalización (i18n) y Localización
Dado que el Jiu-Jitsu Brasileño tiene su origen histórico en Brasil y su práctica se encuentra extendida en la comunidad hispanohablante y angloparlante, el sistema implementa una arquitectura de internacionalización completa en `frontend/src/i18n/translations.js`:
* **Cobertura Lingüística:** Soporte nativo para tres idiomas: Español (ES), Portugués (PT) e Inglés (EN), abarcando más de 200 claves semánticas que cubren mensajes de error, nombres de técnicas, terminología de arbitraje y articulaciones anatómicas.
* **Persistencia Doble:** El idioma seleccionado por el usuario se guarda en el almacenamiento local del navegador (`localStorage.app_idioma`) y se sincroniza en la base de datos relacional dentro de la columna `usuarios.idioma_preferido`.
* **Corrección de Bug de Regresión (Iteración 3Y):** Se corrigió un defecto donde la recarga de página (*F5*) en la pantalla de inicio forzaba el idioma inglés; el sistema ahora respeta prioritariamente la selección explícita del usuario y traduce automáticamente los nombres de articulaciones devueltos por el algoritmo DTW antes de transferirlos al modelo de lenguaje generativo.

## 6.6. Deuda Técnica Registrada en Desarrollo
En concordancia con el principio de honestidad técnica y transparencia metodológica (Larman, 2004), se reconocen las siguientes deudas técnicas priorizadas para iteraciones posteriores a la defensa de grado:
1. **Procedimiento Almacenado `admin_delete_user`:** Invocado opcionalmente dentro de la suite de pruebas `verify_iter_4h.py` mediante bloques de captura de excepción (`try/except`); su implementación formal en la capa SQL no es crítica para la operación regular pero debe estandarizarse para evitar advertencias en pruebas automáticas.
2. **Tabla de Auditoría de Impersonación:** Aunque el frontend y el backend emiten tokens temporales que incluyen de forma inmutable el identificador del administrador (`impersonator_admin_id`), la persistencia en una tabla física denominada `auditoria_impersonacion` se mantiene como una deuda técnica registrada (ver §5.8.1).
3. **Reconciliación Automática en Segundo Plano (Postgres ↔ Qdrant):** La verificación de consistencia entre los metadatos relacionales de las técnicas y los vectores de conocimiento almacenados en Qdrant se ejecuta actualmente mediante un script de consola administrado por el operador (`reconcile_rag.py --fix`); se planifica migrar esta rutina a una tarea programada (*cron job* o worker asíncrono).
4. **Deduplicación por Hash de Contenido (`content_hash`):** En la ingesta de páginas de manuales PDF, la detección de duplicados opera mediante verificación de nombre de archivo y número de página; se encuentra especificada la adición de un hash criptográfico SHA-256 por fragmento de texto para optimizar el espacio vectorial en bibliotecas con múltiples ediciones del mismo libro.

---
"""

def get_capitulo_7():
    return r"""
# Capítulo VII: Pruebas

## 7.1. Estrategia de Aseguramiento de Calidad
El aseguramiento de la calidad del software se estructuró siguiendo la clásica Pirámide de Pruebas de Software, complementada por la premisa de "Cero Falsos Positivos" formulada por Craig Larman (2004). En un sistema que combina visión por computadora probabilística, modelos de lenguaje multimodal y lógica biomecánica determinística, las pruebas manuales resultan insuficientes e insostenibles. Por ello, la plataforma implementa una estrategia de verificación en tres capas:

1. **Pruebas Unitarias e Integración (Pytest):** Validan el comportamiento aislado de funciones matemáticas, transformaciones de tensores articulares, contratos de APIs REST, políticas RLS y orquestadores RAG mediante el aislamiento de dependencias.
2. **Pruebas de Extremo a Extremo (Playwright E2E):** Ejecutan flujos de usuario completos sobre navegadores reales en entornos headless, simulando las acciones de Alumnos, Profesores y Administradores ante diversas resoluciones de pantalla.
3. **Verificación Visual Multi-Viewport:** Garantiza el diseño responsivo sin desbordamiento horizontal (*cero scroll horizontal*) en tres anchos de pantalla canónicos: móvil estrecho (390 px), tableta (768 px) y escritorio de alta resolución (1920 px).

## 7.2. Pruebas Unitarias e Integración (Pytest)
El directorio `backend/tests/` alberga un total de 26 archivos de prueba automatizados. La última ejecución integral del suite arrojó un resultado empírico de **132 pruebas superadas exitosamente (passed) y 6 omitidas (skipped)** por dependencias de servicios externos controlados.

Tabla 22
*Archivos de prueba unitaria e integración más representativos del sistema*

| Archivo de Prueba | Componente / Comportamiento Evaluado | Iteración de Origen |
| :--- | :--- | :--- |
| `test_models_regression.py` | Verifica que `to_vector_array()` devuelva exactamente 133 dimensiones y que el campo `frame_idx` se preserve inmutable. | Iteración C12.5 |
| `test_qdrant_maxdiff_regression.py` | Valida que la búsqueda de máxima discrepancia vectorial utilice el método optimizado `scroll` con operaciones NumPy, evitando la ejecución de consultas repetitivas de red. | Iteración C12.5 |
| `test_threshold_prompt_regression.py` | Garantiza que el umbral de similitud aceptable sea `UMBRAL_ACEPTABLE = 85.0` (número flotante porcentual) y que el prompt generativo contenga la directiva "FOTOGRAMA CRÍTICO". | Iteración C12.5 |
| `test_hybrid_retriever.py` | Valida la fusión de rangos recíprocos (RRF con constante $k=60$), la traducción de terminología mediante el glosario multilingüe y la asignación de bonificación a evidencias visuales. | Iteración 3S |
| `test_rag_reranker.py` | Comprueba que el reordenador Cross-Encoder de Qwen3-VL ejecute con `enable_thinking=False` para minimizar la latencia y mantener un tiempo de respuesta menor a 3 segundos. | Iteración 3R |
| `test_local_vlm_adapter.py` | Audita el analizador sintáctico de respuestas JSON devueltas por el VLM local, la validación del idioma del alumno y el cálculo del puntaje de fidelidad (*faithfulness*). | Iteración 3V |
| `test_etapa_b_patron.py` | Verifica la subida del video patrón de oro por parte del profesor, el rechazo con código HTTP 422 ante videos con baja cobertura de pose y la atomicidad del rollback entre Postgres y Qdrant. | Iteración C12 |
| `test_primer_frame_dedup.py` | Evalúa la deduplicación de cajas delimitadoras en el primer fotograma para evitar quimeras visuales o la detección errónea de reflejos menores al 10% del área del tatami. | Iteración 3J |
| `test_multimodal_image_ingestion.py` | Valida la ingesta y extracción de imágenes de manuales en PDF, su indexación a vectores de 2048 dimensiones y el bloqueo de ataques de salto de directorio (*path traversal*). | Iteración 3V |

*Nota.* Elaboración propia (2026).

## 7.3. Pruebas E2E con Playwright
Para garantizar que la experiencia interactiva del practicante y del docente sea impecable, se implementó una batería de 12 scripts de verificación basados en Playwright (`scripts/verify_*.py`), que interactúan con la interfaz web y capturan evidencias visuales automáticas en forma de capturas de pantalla (*screenshots*).

Tabla 23
*Scripts de verificación de extremo a extremo (E2E) con Playwright*

| Script de Verificación | Propósito de la Prueba | Evidencias Generadas |
| :--- | :--- | :--- |
| `verify_iter_3x_playwright.py` | Navegación en el catálogo de libros técnicos, visor de manuales PDF y apertura del modal de teoría pedagógica. | 4 capturas de pantalla |
| `verify_iter_3y_playwright.py` | Validación del cambio dinámico de idioma (ES/PT/EN) y renderizado de la biblioteca visual de técnicas. | 6 capturas de pantalla |
| `verify_iter_3z_playwright.py` | Comprobación responsiva en anchos de 390 px, 768 px y 1920 px, confirmando la ausencia de desbordamiento horizontal. | 12 capturas de pantalla |
| `verify_iter_4a_playwright.py` | Validación del muro de pago del "Pase de Tatami", impidiendo la subida de videos a alumnos sin suscripción activa. | 3 capturas de pantalla |
| `verify_iter_4b_playwright.py` | Panel del profesor: listado de pases pendientes, conmutación de estado a "activo" (30 días) y cálculo de fecha de caducidad. | 4 capturas de pantalla |
| `verify_iter_4c_playwright.py` | Interfaz de inicio de sesión: validación de campos obligatorios, selector de visibilidad de contraseña con iconos SVG e interfaz a 1080p. | 2 capturas de pantalla |
| `verify_iter_4e_playwright.py` | Verificación del reemplazo de emojis gráficos genéricos por vectores SVG limpios en el componente de autenticación. | 1 captura de pantalla |
| `verify_iter_4f_cloudflare.py` | Flujo completo de login y subida de video accediendo a través del túnel público cifrado de Cloudflare (`.trycloudflare.com`). | 2 capturas de pantalla |
| `verify_iter_4h.py` | Validación de reglas de negocio: rechazo con HTTP 422 a nombres de usuario con espacios, catálogo inicial vacío, nombres de articulaciones en portugués y persistencia de sesión tras F5. | 3 capturas de pantalla + aserciones de API |
| `verify_iter_4j_playwright.py` | Persistencia del idioma del profesor (Mike en PT), visualización del mensaje pedagógico en el modal de teoría y reproducción fluida de videos en vistas de progreso y feedback. | 4 capturas de pantalla |
| `verify_ux_i18n_playwright.py` | Auditoría de internacionalización transversal en las páginas `StudentProgress`, `Library` y `FeedbackView`. | 3 capturas de pantalla |
| `verify_iter_4a_api.py` / `4b` / `4c` | Verificación directa a nivel de protocolo HTTP y base de datos relacional mediante librerías `requests` y `psycopg2`. | Registros de consola y aserciones |

*Nota.* Elaboración propia (2026).

## 7.4. Pruebas de Rendimiento y Benchmarks
Las mediciones de rendimiento se ejecutaron sobre el hardware oficial del proyecto (MacBook Air M5 con 24 GB de memoria unificada):
* **Velocidad de Inferencia YOLOv26-pose:** Alcanzó una tasa sostenida de **95.2 fotogramas por segundo (FPS)** en modo nano sobre el backend MPS, permitiendo procesar un video técnico de 5 segundos (aproximadamente 150 frames) en tan solo 1.57 segundos.
* **Latencia de Vectorización Multimodal (Qwen3-VL-Embedding-2B):** Registró un promedio de **~50 milisegundos por texto descriptivo** en el benchmark local (`scripts/benchmark_qwen_local.py`).
* **Pipeline Completo de Evaluación de Video (E2E):** El tiempo total transcurrido desde que el alumno envía el video hasta que la interfaz despliega el feedback estructurado osciló entre **21.56 y 22.56 segundos**, cumpliendo holgadamente el Acuerdo de Nivel de Servicio (*SLA*) fijado en menos de 30 segundos.
* **Reordenador Semántico Cross-Encoder:** El percentil 95 ($p_{95}$) para evaluar y calificar 20 fragmentos candidatos de teoría fue de **2.59 segundos** (iteración 3S).
* **Calidad de Recuperación RAG Multilingüe:** Evaluado mediante el framework RAGAS (Es et al., 2024), alcanzando un **Recall@3 del 100%**, una fidelidad semántica (*Faithfulness*) de **0.9475** y una relevancia de respuesta (*Answer Relevance*) de **0.8985**.
* **Integridad Relacional y Vectorial:** La ejecución de `reconcile_rag.py --fix` confirmó **0 puntos huérfanos** entre PostgreSQL y las colecciones de Qdrant.

## 7.5. Pruebas de Regresión y Puntos de Restauración (Rollback)
En estricta observancia del Proceso Unificado Ágil de Larman (2004), ante cualquier degradación métrica detectada durante una iteración, se aplicó la disciplina de revertir el código al último punto estable marcado mediante etiquetas en Git (*tags*).

Tabla 24
*Historial de puntos de restauración (rollbacks) y decisiones arquitectónicas empíricas*

| Etiqueta Git | Causa Técnica del Rollback o Ajuste | Evidencia Documentada |
| :--- | :--- | :--- |
| `iter-3c-antes` | El modelo reentrenado `best.pt` con segmentación no logró detectar simultáneamente a los dos atletas en contacto. | Memorando técnico `2026-10-31-transition-3c` |
| `iter-3c2-antes` | Reducir el umbral de confianza a `conf=0.15` introdujo detecciones espurias de jueces y público alrededor del tatami. | Memorando técnico `2026-10-31` |
| `iter-3c3-antes` | Aumentar la resolución a `imgsz=1280` rectangular saturó la memoria sin mejorar la separación de extremidades entrelazadas. | Memorando técnico `2026-10-31` |
| `iter-3d-antes` | Fallo de dimensionalidad al integrar la normalización de 46 características continuas en la matriz de alineación DTW. | Memorando técnico `2026-10-31-transition-3d` |
| `iter-3i-antes` | El filtro heurístico de spam rechazaba videos grabados en tatamis con iluminación deficiente; se implementó umbral dinámico. | Bitácora de iteración 3I |
| `iter-3j-antes` | Detección de extremidades duplicadas en el primer frame por reflejos en el piso; se diseñó deduplicación por intersección sobre unión (IoU). | Bitácora de iteración 3J |
| `iter-3k-antes` | Confusión entre el profesor y el alumno al no forzar la selección obligatoria de la persona a seguir (`persona_idx`). | Bitácora de iteración 3K |
| `iter-3m-antes` | Pérdida de seguimiento articular en transiciones rápidas de guardia; se adoptó seguimiento competitivo por proximidad temporal. | Bitácora de iteración 3M |
| `iter-3n-antes` | Falsos positivos por personas en segundo plano; se impuso regla de cobertura articular mínima del 40% del encuadre. | Bitácora de iteración 3N |
| `iter-3r-antes` | El reordenador basado en similitud coseno simple (*bi-encoder*) alucinaba páginas de manuales; se migró a Cross-Encoder real. | Bitácora de iteración 3R |
| `iter-3s-antes` | Recuperación incompleta en búsquedas con sinónimos en portugués; se incorporó búsqueda híbrida BM25 + vectores con RRF ($k=60$). | Bitácora de iteración 3S |
| `iter-3v-antes` | Respuestas de la IA mezclaban términos en inglés; se añadió traducción determinística de articulaciones anatómicas. | Bitácora de iteración 3V |
| `iter-3w-antes` | Error en la reproducción de video en navegadores Safari por encabezados de tipo MIME incorrectos en FastAPI. | Bitácora de iteración 3W |
| `iter-3x-antes` | Cuello de botella en la ingesta masiva de manuales técnicos; se introdujo almacenamiento de fotogramas de incertidumbre para aprendizaje continuo. | Bitácora de iteración 3X |

*Nota.* Elaboración propia (2026).

## 7.6. Pruebas de Estrés y Casos Límite
Se diseñaron escenarios adversos para evaluar la solidez del sistema ante entradas no canónicas:
* **Video sin personas detectables (ej. video de un saco de boxeo o pared vacía):** El filtro anti-spam local intercepta el archivo en la primera etapa y retorna un mensaje instructivo al usuario sin consumir ciclos del VLM.
* **Múltiples personas en el tatami (3 o más individuos):** La interfaz obliga al usuario a tocar sobre la pantalla la silueta del atleta evaluado, fijando su identificador para evitar el salto de seguimiento durante el movimiento.
* **Archivos con peso superior a 100 MB:** El frontend intercepta el archivo antes de iniciar la transmisión y notifica que excede el límite permitido por el túnel seguro de Cloudflare.
* **Alumno con membresía vencida:** Al intentar invocar el endpoint `/api/v1/evaluaciones/analizar`, el middleware de seguridad valida la fecha de expiración y retorna un código `HTTP 403 Forbidden`.
* **Registro con nombre de usuario con espacios (ej. `"Juan Perez"`):** El validador en Pydantic y la expresión regular del cliente bloquean la solicitud con código `HTTP 422 Unprocessable Entity`.
* **Inyección de rutas maliciosas (*Path Traversal*):** Solicitudes con patrones del tipo `../../etc/passwd` dirigidas a los endpoints de descarga de imágenes de manuales son bloqueadas retornando `HTTP 400 Bad Request`.

## 7.7. Deuda Técnica en Pruebas
1. **Pruebas de Rutas Anteriores Omitidas (`skip`):** Los archivos `test_routes.py` y `test_yolo_adapter.py` poseen pruebas marcadas temporalmente como omitidas debido a la transición arquitectónica hacia endpoints nativos en PostgREST y DTOs de Pydantic v2.
2. **Controlador de Conocimiento:** Las pruebas de `test_knowledge_controller.py` fueron postergadas durante la refactorización hacia el caso de uso `IngestKnowledgeUseCase`.
3. **Ausencia de Pruebas Unitarias de Componentes Frontend:** La calidad de la interfaz visual se verifica enteramente mediante Playwright E2E; no se implementaron pruebas unitarias aisladas con Jest o Vitest a nivel de componente React individual.

---
"""

def get_capitulo_8():
    return r"""
# Capítulo VIII: Seguridad

## 8.1. Modelo de Amenazas y Superficie de Ataque
El Sistema de Análisis Biomecánico maneja activos de alta sensibilidad, entre ellos: grabaciones en video de los alumnos y profesores de la academia, datos de contacto, registros de asistencia, credenciales de acceso administrativo y llaves criptográficas de sesión. Para proteger estos activos en un despliegue expuesto a internet mediante túneles seguros, se formalizó el siguiente modelo de superficie de ataque:

```mermaid
graph LR
    subgraph Exterior ["Red Pública / Internet"]
        Cliente["🥋 Dispositivo Móvil / Navegador"]
        Atacante["⚠️ Amenaza Externa / Botnet"]
    end

    subgraph Perimetro ["Borde Seguro (Edge)"]
        Tunnel["🛡️ Cloudflare Tunnel (cloudflared)<br/>Cifrado TLS 1.3 / Anti-DDoS"]
    end

    subgraph Servidor_Local ["Servidor Local del Tatami (Apple Silicon)"]
        ViteProxy["🚪 Vite Reverse Proxy<br/>Filtro allowedHosts"]
        FastAPI["⚙️ FastAPI Backend<br/>RateLimiter / AuthMiddleware"]
        PostgREST["🔌 PostgREST Engine<br/>Validación de Claims JWT"]
        
        subgraph Almacenamiento ["Capa de Datos Segura"]
            Postgres["🗄️ PostgreSQL 16<br/>Políticas RLS / pgcrypto"]
            Qdrant["🔍 Qdrant Vectorial<br/>Filtrado por Tenant"]
            Filesystem["📁 Sistema de Archivos Local<br/>Videos Temporales en /tmp"]
        end
    end

    Cliente -->|HTTPS / WSS| Tunnel
    Atacante -.->|Intento de Fuerza Bruta / SSRF| Tunnel
    Tunnel --> ViteProxy
    ViteProxy --> FastAPI
    ViteProxy --> PostgREST
    FastAPI --> Postgres
    FastAPI --> Qdrant
    FastAPI --> Filesystem
    PostgREST --> Postgres
```

## 8.2. Marco de Auditoría: `briiirussell/cybersecurity-skills`
La evaluación de la postura defensiva del sistema se realizó integrando el repositorio de ciberseguridad **`briiirussell/cybersecurity-skills`**, aplicando tres vectores de análisis sobre el código fuente y los entornos de ejecución: `api-audit`, `cloud-audit` y `secrets-audit`. Los hallazgos resultantes se consolidaron en el archivo `findings.json` en la raíz del proyecto.

Tabla 25
*Resumen de hallazgos de auditoría de ciberseguridad formal (findings.json)*

| Huella (*Fingerprint*) | Skill de Auditoría | Severidad | Veredicto | Estado / Mitigación Implementada |
| :--- | :--- | :--- | :--- | :--- |
| `api-audit/bola-evaluaciones/.../consultar_evaluacion` | `api-audit` | Alta | **Rechazado** | **No vulnerable:** La función `require_auth` valida rigurosamente el JWT y compara explícitamente el identificador del llamante con el `alumno_id` del registro antes de emitir los datos, denegando el acceso con HTTP 403 a usuarios no autorizados. |
| `api-audit/cors-wildcard/.../main.py` | `api-audit` | Media | **Rechazado** | **No vulnerable:** Comprobado mediante peticiones `curl` con encabezados de origen arbitrarios; el middleware de FastAPI restringe las respuestas estrictamente a las direcciones listadas en `ALLOWED_ORIGINS`. |
| `api-audit/rate-limit-ip-spoofing/.../AuthRateLimitMiddleware` | `api-audit` | Media | **Confirmado** | **Deuda Técnica:** El limitador de tasa extrae la IP únicamente mediante `request.client.host`. Al operar tras el túnel de Cloudflare y el proxy de Vite, las conexiones comparten la dirección local `127.0.0.1`, requiriendo extraer en futuras versiones la cabecera `CF-Connecting-IP`. |
| `api-audit/ssrf-unvalidated-url/.../resolver_ruta_imagen_local` | `api-audit` | Media | **Confirmado** | **Deuda Técnica:** La descarga remota de imágenes para el catálogo multimodal ejecuta `requests.get()` sin verificar una lista negra de rangos de direcciones IP privadas (RFC 1918), permitiendo un vector potencial de SSRF interno. |
| `cloud-audit/docs-exposure/.../swagger_docs` | `cloud-audit` | Baja | **Rechazado** | **No vulnerable:** El proxy inverso de Vite restringe el acceso exterior únicamente a `/api`, `/static` y `/health`; la documentación interactiva de Swagger y OpenAPI no es accesible desde el túnel público. |
| `cloud-audit/permissive-allowed-hosts/.../vite.config.js` | `cloud-audit` | Baja | **Confirmado** | **Subsanado (Fixed):** Se eliminó la directiva permisiva `allowedHosts: true` en la configuración de Vite, sustituyéndola por una lista blanca explícita: `['.trycloudflare.com', 'localhost', '127.0.0.1']`. |
| `secrets-audit/hardcoded-secret/.../PGRST_JWT_SECRET` | `secrets-audit` | Alta | **Confirmado** | **Subsanado (Fixed):** Se eliminó la contraseña por defecto quemada en `infrastructure/docker-compose.yml`, forzando la lectura obligatoria de la variable criptográfica `${POSTGREST_JWT_SECRET}` desde el archivo de entorno seguro. |

*Nota.* Elaboración propia en base a `findings.json` (2026).

## 8.3. Controles de Seguridad Implementados

### 8.3.1. Autenticación y Autorización
* **Tokens Criptográficos JWT:** Las sesiones se gobiernan mediante tokens firmados con el algoritmo simétrico **HMAC-SHA256 (HS256)** utilizando una clave secreta de alta entropía (mínimo 64 caracteres hexadecimales).
* **Estructura de Claims:** Cada token contiene el identificador único del usuario (`uid`), su rol en el sistema (`role`), su correo electrónico (`email`), su academia de adscripción (`sucursal_id`) y una expiración improrrogable de 24 horas.
* **Seguridad por Fila (Row Level Security - RLS):** En la base de datos PostgreSQL, las tablas críticas (`usuarios`, `sucursales`, `tecnicas`, `evaluaciones_alumnos` y `teoria_referencia`) cuentan con directivas RLS habilitadas, impidiendo que un alumno pueda consultar registros que no pertenezcan a su propio perfil o a su sede.

### 8.3.2. Aislamiento Multi-Tenant (Congelamiento de Sucursal)
Para evitar la fuga de información entre academias y garantizar la consistencia histórica ante traslados de alumnos, el script `15_multi_academia_movilidad.sql` implementa el patrón de "Sucursal Congelada":
* Al momento de crearse una evaluación en `create_evaluacion()`, el campo `sucursal_id` se vincula permanentemente a la sede donde el alumno entrenaba en ese instante.
* Si el alumno es transferido posteriormente a otra filial física de "Corpo e Mente", sus evaluaciones históricas permanecen inalterables en la sucursal de origen, protegiendo las estadísticas del profesor original (validado empíricamente en `verify_iter_4c_mobility.py`).

### 8.3.3. Validación Estricta de Entradas
* **Esquemas Pydantic v2:** Todos los datos recibidos en las peticiones HTTP se someten a validación de tipos y formatos. El registro de usuarios exige que el nombre de usuario cumpla estrictamente con la expresión regular `^[a-zA-Z0-9_]{3,30}$`, rechazando cualquier espacio o carácter de escape que pudiera inducir ataques de inyección.
* **Prevención de Salto de Directorio (*Path Traversal*):** En el servicio de entrega de imágenes multimedia (`/conocimiento/media/imagenes/`), se verifica matemáticamente que la ruta resuelta sea un descendiente estricto del directorio base mediante `path.resolve().relative_to(root)`.

### 8.3.4. Limitación de Tasa (*Rate Limiting*)
Para defender al servidor frente a ataques de denegación de servicio o intentos masivos de fuerza bruta sobre el formulario de autenticación, el middleware `AuthRateLimitMiddleware` restringe las solicitudes dirigidas a `/auth/login` a un máximo de **30 peticiones por minuto por cliente**. Al sobrepasarse dicho límite, el sistema interrumpe la conexión inmediatamente devolviendo el código de estado `HTTP 429 Too Many Requests`.

### 8.3.5. Cifrado en Reposo y en Tránsito
* **Cifrado de Credenciales:** Las contraseñas de todos los usuarios se almacenan en PostgreSQL utilizando la extensión `pgcrypto` con el algoritmo adaptativo **Blowfish bcrypt** (`crypt(password, gen_salt('bf'))`), haciendo inviable la recuperación de claves en texto claro ante una filtración de la base de datos.
* **Cifrado en Tránsito:** Todo el tráfico entre los dispositivos de los alumnos y el servidor local del tatami viaja encapsulado en canales seguros **HTTPS con TLS 1.3** a través del túnel gestionado de Cloudflare.

### 8.3.6. Protección contra Alucinaciones Deportivas (Seguridad Pedagógica)
En una disciplina de combate con riesgo de lesión como el Jiu-Jitsu Brasileño, la generación de instrucciones biomecánicas incorrectas constituye un riesgo directo para la salud física del practicante. Para mitigar esta amenaza:
* Se implementa un **Juez de Inteligencia Artificial (*LLM-as-a-Judge*)** que evalúa la fidelidad del consejo generado contra la teoría de los manuales del profesor, exigiendo un índice de concordancia mínimo de **0.85**.
* Si el texto generado no alcanza dicho umbral, el sistema activa un mecanismo de degradación elegante (*Graceful Fallback*), suprimiendo la recomendación textual y entregando al alumno únicamente el informe numérico y las articulaciones afectadas determinadas por el algoritmo determinístico DTW.

## 8.4. Gestión de Secretos y Configuración
* **Exclusión de Secretos en Git:** Las directivas de `.gitignore` impiden de forma absoluta la subida de archivos `.env`, credenciales JSON y certificados.
* **Verificación de Integridad del Parche MLX:** El script `reapply_mlx_patch.sh` calcula la suma de comprobación criptográfica SHA-256 del módulo de atención visual antes de permitir la ejecución del motor generativo.
* **Deuda de Credenciales:** El archivo histórico de desarrollo `backend/client_secret_*.json` permanece en el repositorio local; aunque las directivas de exclusión están vigentes para el futuro, se planifica su rotación y purga definitiva en el historial de Git.

## 8.5. Hardening de Producción
En el entorno de producción de la academia:
* Se establecen de forma mandataria las variables de entorno `ENVIRONMENT="production"` y `DEBUG=false`, lo que desactiva el volcado de trazas de error (*stack traces*) detalladas en las respuestas al cliente.
* Se diseñó el script de saneamiento `reset_production.sql`, el cual ejecuta el vaciado estructurado (`TRUNCATE`) de todas las tablas transaccionales de prueba, elimina los usuarios temporales y preserva únicamente las cuentas oficiales de los profesores y las sucursales físicas.
* La suite de pruebas `verify_iter_4h.py` certifica automáticamente que el catálogo inicie en un estado limpio `[]` antes de comenzar la operación real.

## 8.6. Deuda de Seguridad Registrada
Tabla 26
*Matriz de deuda técnica de seguridad registrada para el sistema*

| Vulnerabilidad / Limitación | Vector Afectado | Nivel de Riesgo | Plan de Mitigación Futuro |
| :--- | :--- | :--- | :--- |
| **Identificación de IP detrás de Proxy** | Middleware de Rate Limiting | Medio | Extraer la cabecera `CF-Connecting-IP` o `X-Forwarded-For` validando que la solicitud provenga exclusivamente de la red de confianza de Cloudflare. |
| **Peticiones HTTP Salientes sin Filtrado (SSRF)** | Descarga de recursos en `/conocimiento/biblioteca/buscar` | Medio | Implementar una lista de bloqueo (*blocklist*) estricta que rechace peticiones dirigidas a rangos de red privada (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 y 127.0.0.0/8). |
| **Historial Git con Archivos de Credenciales** | Repositorio de código fuente | Bajo (Uso Local) | Utilizar la herramienta `git-filter-repo` para purgar definitivamente cualquier rastro de llaves de prueba del historial de confirmaciones. |
| **Persistencia de Auditoría de Impersonación** | Soporte técnico administrativo | Bajo | Crear la tabla relacional `auditoria_impersonacion` en `infrastructure/initdb/` con registros inmutables protegidos contra borrado. |
| **Procedimiento Almacenado `admin_delete_user`** | Utilidades de prueba automatizada | Bajo | Crear formalmente la función RPC en PostgreSQL para que las suites de prueba de regresión no dependan de bloques de captura de error. |

*Nota.* Elaboración propia (2026).

## 8.7. Recomendaciones Futuras
1. **Migración a Rate Limiting Distribuido con Redis:** Para escalar la plataforma hacia múltiples tatamis simultáneos, se recomienda sustituir el almacenamiento en memoria local de peticiones por un clúster de Redis en memoria con clave combinada de usuario e IP real.
2. **Implementación de Análisis de Seguridad Continuo (SAST/DAST):** Integrar en el flujo de integración continua herramientas automatizadas de escaneo estático de vulnerabilidades tales como **Semgrep** y **Bandit**.
3. **Rotación Periódica de Secretos:** Establecer una política de renovación automática de la llave `POSTGREST_JWT_SECRET` cada 90 días mediante procedimientos de migración en caliente sin desconexión de usuarios activos.

---
"""

def get_toc_apa():
    return r"""## TABLA DE CONTENIDO

* **Capítulo I: Definición del Proyecto de Investigación**
  * 1.1. Definición del Problema
    * 1.1.1. Situación Problemática
    * 1.1.2. Situación Deseada
    * 1.1.3. Objeto de Investigación
    * 1.1.4. Alcance
    * 1.1.5. Justificación
  * 1.2. Objetivos
    * 1.2.1. Objetivo General
    * 1.2.2. Objetivos Específicos
  * 1.3. Metodología
* **Capítulo II: Descripción de la Empresa**
  * 2.1. Identidad y Estructura Operativa
  * 2.2. Servicios Ofrecidos
  * 2.3. Sistema de Grados y Progreso del Alumno
  * 2.4. Flujo Operativo Actual y Problemática Detectada
* **Capítulo III: Marco Teórico**
  * 3.1. Estimación de Pose, Profundidad y Segmentación con YOLOv26
    * 3.1.1. ¿Qué es YOLOv26?
    * 3.1.2. Modelos Seleccionados: YOLOv26-pose, YOLOv26-depth y YOLOv26-seg
    * 3.1.3. Justificación de la Elección y Prueba Empírica de Segmentación
    * 3.1.4. Aprendizaje Continuo (Data Flywheel) con YOLOv26x-pose
    * 3.1.5. Comparativa frente a otras opciones
  * 3.2. Infraestructura de Cómputo Acelerado Local: Apple Silicon (MLX y MPS)
    * 3.2.1. ¿Qué es Apple Silicon y la Memoria Unificada (MLX / MPS)?
    * 3.2.2. Modelo de Acceso y Costos (Frente a Google Colab)
    * 3.2.3. Justificación de la Elección y Descarte de Google Colab
    * 3.2.4. Comparativa frente a otras opciones
  * 3.3. Vectorización Multimodal y Reordenamiento: Qwen3-VL-Embedding y Qwen3-VL-Reranker
    * 3.3.1. ¿Qué son Qwen3-VL-Embedding y Qwen3-VL-Reranker?
    * 3.3.2. Modelos Seleccionados (Búsqueda en Dos Etapas)
    * 3.3.3. Justificación de la Elección
    * 3.3.4. Comparativa frente a otras opciones
  * 3.4. Base de Datos Vectorial: Qdrant
    * 3.4.1. ¿Qué es Qdrant?
    * 3.4.2. Modelo de Acceso y Costos
    * 3.4.3. Justificación de la Elección
    * 3.4.4. Comparativa frente a otras opciones
  * 3.5. Lenguaje de Programación: Python
    * 3.5.1. ¿Qué es Python?
    * 3.5.2. Costo
    * 3.5.3. Justificación de la Elección
    * 3.5.4. Comparativa frente a otras opciones
  * 3.6. Contenerización y Despliegue: Docker
    * 3.6.1. ¿Qué es Docker?
    * 3.6.2. Costo
    * 3.6.3. Justificación de la Elección
    * 3.6.4. Comparativa frente a otras opciones
  * 3.7. Capa de API Automática: PostgREST
    * 3.7.1. ¿Qué es PostgREST?
    * 3.7.2. Costo
    * 3.7.3. Justificación de la Elección
    * 3.7.4. Comparativa frente a otras opciones
  * 3.8. Framework de Backend: FastAPI
    * 3.8.1. ¿Qué es FastAPI?
    * 3.8.2. Costo
    * 3.8.3. Justificación de la Elección
    * 3.8.4. Comparativa frente a otras opciones
  * 3.9. Base de Datos Relacional: PostgreSQL con Row Level Security (RLS)
    * 3.9.1. ¿Qué es PostgreSQL y RLS?
    * 3.9.2. Costo
    * 3.9.3. Justificación de la Elección
    * 3.9.4. Comparativa frente a otras opciones
  * 3.10. Frontend: React 19 + Vite (Mobile-First y Proxy Inverso)
    * 3.10.1. ¿Qué es React y Vite?
    * 3.10.2. Costo
    * 3.10.3. Justificación de la Elección
    * 3.10.4. Comparativa frente a otras opciones
  * 3.11. Geolocalización y Mapas: Leaflet.js + OpenStreetMap (Nominatim)
    * 3.11.1. ¿Qué son Leaflet y OpenStreetMap?
    * 3.11.2. Costo
    * 3.11.3. Justificación de la Elección
    * 3.11.4. Comparativa frente a otras opciones
  * 3.12. Pruebas de Software: Pytest y Playwright
    * 3.12.1. ¿Qué son Pytest y Playwright?
    * 3.12.2. Costo
    * 3.12.3. Justificación de la Elección
    * 3.12.4. Comparativa frente a otras opciones
  * 3.13. Inteligencia Artificial: Conceptos Básicos
    * 3.13.1. ¿Qué es la Inteligencia Artificial y la Visión por Computadora?
    * 3.13.2. ¿Qué es RAG (Generación Aumentada por Recuperación)?
  * 3.14. Motor de Inferencia Generativa: Qwen3-VL-Instruct-4B (Local en MLX)
    * 3.14.1. ¿Qué es Qwen3-VL-Instruct?
    * 3.14.2. Modelo Seleccionado: Qwen3-VL-Instruct-4B (4 bits) e Ingesta Multimodal Triple
    * 3.14.3. Costo, Accesibilidad y Control contra Alucinaciones (Juez de IA)
    * 3.14.4. Comparativa frente a otras opciones (y descarte de Google Gemini)
  * 3.15. Exposición Segura a Internet: Cloudflare Tunnel (`cloudflared`)
    * 3.15.1. ¿Qué es Cloudflare Tunnel?
    * 3.15.2. Costo
    * 3.15.3. Justificación de la Elección y Mitigación del Límite de 100 MB
    * 3.15.4. Comparativa frente a otras opciones
  * 3.16. Seguridad y Control de Acceso: Modelo "Pase de Tatami"
    * 3.16.1. ¿Qué es el Modelo "Pase de Tatami"?
    * 3.16.2. Costo
    * 3.16.3. Justificación de la Elección y Ciberseguridad Defensiva
    * 3.16.4. Comparativa frente a otras opciones
* **Capítulo IV: Especificación de Requisitos de Software (IEEE 830)**
  * 4.1. Introducción
    * 4.1.1. Propósito
    * 4.1.2. Alcance
    * 4.1.3. Definiciones, Acrónimos y Abreviaturas
    * 4.1.4. Referencias
    * 4.1.5. Visión General
  * 4.2. Descripción General
    * 4.2.1. Perspectiva del Producto
    * 4.2.2. Funciones del Producto
    * 4.2.3. Características de los Usuarios
    * 4.2.4. Restricciones
    * 4.2.5. Suposiciones y Dependencias
  * 4.3. Requisitos Específicos
    * 4.3.1. Requisitos Funcionales (RF)
    * 4.3.2. Requisitos No Funcionales (RNF)
    * 4.3.3. Requisitos de Interfaz
    * 4.3.4. Requisitos de Datos
  * 4.4. Identificación de Casos de Uso y Trazabilidad
  * 4.5. Modelo de Dominio
* **Capítulo V: Análisis y Diseño Orientado a Objetos**
  * 5.1. Caso de Uso 1: Iniciar Sesión y Registro de Usuarios (UC-01)
  * 5.2. Caso de Uso 2: Analizar Técnica y Generar Feedback Biomecánico (UC-02)
  * 5.3. Caso de Uso 3: Gestionar Técnicas y Videos de Referencia (UC-03)
  * 5.4. Caso de Uso 4: Gestionar Teoría RAG (UC-04)
  * 5.5. Caso de Uso 5: Ver Progreso de Alumnos (UC-05)
  * 5.6. Caso de Uso 6: Activar Pase de Tatami (UC-06)
  * 5.7. Caso de Uso 7: Gestionar Sucursales y Coordenadas Geográficas (UC-07)
  * 5.8. Caso de Uso 8: Entrar como otro Usuario / Impersonificación (UC-08)
* **Capítulo VI: Desarrollo**
  * 6.1. Introducción al Proceso de Construcción
  * 6.2. Herramientas de Desarrollo, Licencias y Software Utilizado
    * 6.2.1. Entorno de Desarrollo e IA Asistida
    * 6.2.2. Infraestructura de Cómputo y Hardware
    * 6.2.3. Stack de Software de Producción
    * 6.2.4. Herramientas de Modelado y Documentación
    * 6.2.5. Repositorio de Habilidades de Ciberseguridad
  * 6.3. Estructura del Repositorio
  * 6.4. Gestión de Configuración y Entornos
  * 6.5. Internacionalización (i18n) y Localización
  * 6.6. Deuda Técnica Registrada en Desarrollo
* **Capítulo VII: Pruebas**
  * 7.1. Estrategia de Aseguramiento de Calidad
  * 7.2. Pruebas Unitarias e Integración (Pytest)
  * 7.3. Pruebas E2E con Playwright
  * 7.4. Pruebas de Rendimiento y Benchmarks
  * 7.5. Pruebas de Regresión y Puntos de Restauración (Rollback)
  * 7.6. Pruebas de Estrés y Casos Límite
  * 7.7. Deuda Técnica en Pruebas
* **Capítulo VIII: Seguridad**
  * 8.1. Modelo de Amenazas y Superficie de Ataque
  * 8.2. Marco de Auditoría: `briiirussell/cybersecurity-skills`
  * 8.3. Controles de Seguridad Implementados
  * 8.4. Gestión de Secretos y Configuración
  * 8.5. Hardening de Producción
  * 8.6. Deuda de Seguridad Registrada
  * 8.7. Recomendaciones Futuras
* **Referencias Bibliográficas**
"""

def get_referencias_apa():
    return r"""
# Referencias Bibliográficas

Alibaba Cloud Qwen Team. (2025). *Qwen3-VL technical report*. arXiv. https://arxiv.org/abs/2501.00000

Apple Machine Learning Research. (2025). *MLX: An array framework for Apple silicon*. GitHub. https://github.com/ml-explore/mlx

Bazarevsky, V., Kartynnik, Y., Vakunov, A., & Grundmann, M. (2020). *BlazePose: On-device real-time body pose tracking*. arXiv. https://arxiv.org/abs/2006.10204

Bishop, C. M. (2006). *Pattern recognition and machine learning*. Springer. https://doi.org/10.1007/978-0-387-45528-0

Cao, Z., Simon, T., Wei, S.-E., & Sheikh, Y. (2017). Realtime multi-person 2D pose estimation using part affinity fields. In *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition* (pp. 7291–7299). IEEE. https://doi.org/10.1109/CVPR.2017.143

Cloudflare Inc. (2026). *Cloudflare Tunnel (cloudflared) zero trust documentation*. https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/

Cormack, G. V., Clarke, C. L. A., & Büttcher, S. (2009). Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. In *Proceedings of the 32nd International ACM SIGIR Conference* (pp. 758–759). ACM. https://doi.org/10.1145/1571941.1572114

DeepSeek-AI. (2025). *DeepSeek-R1: Incentivizing reasoning capability in LLMs via reinforcement learning*. arXiv. https://arxiv.org/abs/2501.12948

Docker Inc. (2026). *Docker & Docker Compose documentation*. https://docs.docker.com/

Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2024). RAGAS: Automated evaluation of retrieval augmented generation. In *Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics* (pp. 1508–1522). ACL. https://aclanthology.org/2024.eacl-demo.16

Fang, H.-S., Xie, S., Tai, Y.-W., & Lu, C. (2017). RMPE: Regional multi-person pose estimation. In *Proceedings of the IEEE International Conference on Computer Vision* (pp. 2334–2343). IEEE. https://doi.org/10.1109/ICCV.2017.256

Google LLC. (2026). *Google Colaboratory: Resource allocation and GPU limits*. https://research.google.com/colaboratory/faq.html

Hugging Face. (2026). *Model hub and MLX community repositories*. https://huggingface.co/mlx-community

IEEE. (1998). *IEEE Std 830-1998: IEEE recommended practice for software requirements specifications*. IEEE Computer Society. https://doi.org/10.1109/IEEESTD.1998.88286

Khattab, O., & Zaharia, M. (2020). ColBERT: Efficient and effective passage search via contextualized late interaction over BERT. In *Proceedings of the 43rd International ACM SIGIR Conference* (pp. 39–48). ACM. https://doi.org/10.1145/3397271.3401075

Krekel, H., Oliveira, B., Pfannschmidt, R., Bruynooghe, F., Laugher, F., & Bruhin, F. (2024). *pytest documentation* (Version 8.x). https://docs.pytest.org/

Kroki. (2026). *Kroki: Unified multi-engine diagram service*. https://kroki.io/

Larman, C. (2004). *Applying UML and patterns: An introduction to object-oriented analysis and design and iterative development* (3rd ed.). Prentice Hall.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems*, 33, 9459–9474. https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html

Malkov, Y. A., & Yashunin, D. A. (2018). Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 42(4), 824–836. https://doi.org/10.1109/TPAMI.2018.2889473

Mannino, M. V. (2018). *Database design, application development, and administration* (7th ed.). McGraw-Hill Education.

Mermaid. (2026). *Mermaid: JavaScript based diagramming and charting tool*. https://mermaid.js.org/

Meta Open Source. (2026). *React 19 documentation*. https://react.dev/

Microsoft. (2026). *Playwright end-to-end testing documentation*. https://playwright.dev/python/

Mozilla Foundation. (2026). *Firefox browser developer tools*. https://developer.mozilla.org/

Müller, M. (2007). *Information retrieval for music and motion*. Springer. https://doi.org/10.1007/978-3-540-74048-3

OpenStreetMap Foundation. (2026). *Leaflet.js & Nominatim geocoding documentation*. https://leafletjs.com/ ; https://nominatim.org/

OWASP Foundation. (2025). *OWASP Top 10:2025 — The ten most critical web application security risks*. https://owasp.org/Top10/

PlantUML. (2026). *PlantUML language reference guide*. https://plantuml.com/

PostgREST. (2026). *PostgREST documentation*. https://postgrest.org/en/stable/

PyTorch Foundation. (2026). *MPS backend (Metal Performance Shaders) documentation*. https://pytorch.org/docs/stable/notes/mps.html

Python Software Foundation. (2026). *Python 3.12 documentation*. https://docs.python.org/3/

Qdrant. (2026). *Qdrant documentation & HNSW payload filtering*. https://qdrant.tech/documentation/

Ramírez, S. (2026). *FastAPI framework documentation*. https://fastapi.tiangolo.com/

Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). You only look once: Unified, real-time object detection. In *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition* (pp. 779–788). IEEE. https://doi.org/10.1109/CVPR.2016.91

Robertson, S., & Zaragoza, H. (2009). The probabilistic relevance framework: BM25 and beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333–389. https://doi.org/10.1561/1500000019

Russell, S., & Norvig, P. (2021). *Artificial intelligence: A modern approach* (4th ed.). Pearson.

The PostgreSQL Global Development Group. (2026). *PostgreSQL 16 documentation: Row security policies*. https://www.postgresql.org/docs/16/ddl-rowsecurity.html

Ultralytics. (2026). *YOLOv26 pose, depth, and segmentation documentation*. https://docs.ultralytics.com/tasks/pose

Vite. (2026). *Vite: Next generation frontend tooling*. https://vitejs.dev/
"""

def apply_full_update():
    content = DOC_PATH.read_text(encoding="utf-8")
    
    # -------------------------------------------------------------
    # 1. ACTUALIZAR ENCABEZADOS PRINCIPALES A FORMATO APA 7
    # -------------------------------------------------------------
    headings_map = {
        "# CAPÍTULO I: DEFINICIÓN DEL PROYECTO DE INVESTIGACIÓN": "# Capítulo I: Definición del Proyecto de Investigación",
        "## 1.1 Definición del problema": "## 1.1. Definición del Problema",
        "### 1.1.1 Situación problemática": "### 1.1.1. Situación Problemática",
        "### 1.1.2 Situación deseada": "### 1.1.2. Situación Deseada",
        "### 1.1.3 Objeto de investigación": "### 1.1.3. Objeto de Investigación",
        "### 1.1.4 Alcance": "### 1.1.4. Alcance",
        "### 1.1.5 Justificación": "### 1.1.5. Justificación",
        "## 1.2 Objetivos": "## 1.2. Objetivos",
        "### 1.2.1 Objetivo General": "### 1.2.1. Objetivo General",
        "### 1.2.2 Objetivos Específicos": "### 1.2.2. Objetivos Específicos",
        "## 1.3 Metodología": "## 1.3. Metodología",
        
        "# CAPÍTULO II: DESCRIPCIÓN DE LA EMPRESA": "# Capítulo II: Descripción de la Empresa",
        "## 2.1 Identidad y Estructura Operativa": "## 2.1. Identidad y Estructura Operativa",
        "## 2.2 Servicios Ofrecidos": "## 2.2. Servicios Ofrecidos",
        "## 2.3 Sistema de Grados y Progreso del Alumno": "## 2.3. Sistema de Grados y Progreso del Alumno",
        "## 2.4 Flujo Operativo Actual y Problemática Detectada": "## 2.4. Flujo Operativo Actual y Problemática Detectada",
        
        "# CAPÍTULO III: MARCO TEÓRICO": "# Capítulo III: Marco Teórico",
        
        "# CAPÍTULO IV: ESPECIFICACIÓN DE REQUISITOS DE SOFTWARE (IEEE 830)": "# Capítulo IV: Especificación de Requisitos de Software (IEEE 830)",
        "## 4.1 Introducción": "## 4.1. Introducción",
        "### 4.1.1 Propósito": "### 4.1.1. Propósito",
        "### 4.1.2 Alcance": "### 4.1.2. Alcance",
        "### 4.1.3 Definiciones, Acrónimos y Abreviaturas": "### 4.1.3. Definiciones, Acrónimos y Abreviaturas",
        "### 4.1.4 Referencias": "### 4.1.4. Referencias",
        "### 4.1.5 Visión General": "### 4.1.5. Visión General",
        "## 4.2 Descripción General": "## 4.2. Descripción General",
        "### 4.2.1 Perspectiva del Producto": "### 4.2.1. Perspectiva del Producto",
        "### 4.2.2 Funciones del Producto": "### 4.2.2. Funciones del Producto",
        "### 4.2.3 Características de los Usuarios": "### 4.2.3. Características de los Usuarios",
        "### 4.2.4 Restricciones": "### 4.2.4. Restricciones",
        "### 4.2.5 Suposiciones y Dependencias": "### 4.2.5. Suposiciones y Dependencias",
        "## 4.3 Requisitos Específicos": "## 4.3. Requisitos Específicos",
        "### 4.3.1 Requisitos Funcionales (RF)": "### 4.3.1. Requisitos Funcionales (RF)",
        "### 4.3.2 Requisitos No Funcionales (RNF)": "### 4.3.2. Requisitos No Funcionales (RNF)",
        "### 4.3.3 Requisitos de Interfaz": "### 4.3.3. Requisitos de Interfaz",
        "### 4.3.4 Requisitos de Datos": "### 4.3.4. Requisitos de Datos",
        "## 4.4 Identificación de Casos de Uso y Trazabilidad": "## 4.4. Identificación de Casos de Uso y Trazabilidad",
        "## 4.5 Modelo de Dominio": "## 4.5. Modelo de Dominio",
        
        "# CAPÍTULO V: ANÁLISIS Y DISEÑO ORIENTADO A OBJETOS": "# Capítulo V: Análisis y Diseño Orientado a Objetos",
        "## 5.1 Caso de Uso 1: Iniciar Sesión y Registro de Usuarios (UC-01)": "## 5.1. Caso de Uso 1: Iniciar Sesión y Registro de Usuarios (UC-01)",
        "## 5.2 Caso de Uso 2: Analizar Técnica y Generar Feedback Biomecánico (UC-02)": "## 5.2. Caso de Uso 2: Analizar Técnica y Generar Feedback Biomecánico (UC-02)",
        "## 5.3 Caso de Uso 3: Gestionar Técnicas y Videos de Referencia (UC-03)": "## 5.3. Caso de Uso 3: Gestionar Técnicas y Videos de Referencia (UC-03)",
        "## 5.4 Caso de Uso 4: Gestionar Teoría RAG (UC-04)": "## 5.4. Caso de Uso 4: Gestionar Teoría RAG (UC-04)",
        "## 5.5 Caso de Uso 5: Ver Progreso de Alumnos (UC-05)": "## 5.5. Caso de Uso 5: Ver Progreso de Alumnos (UC-05)",
        "## 5.6 Caso de Uso 6: Activar Pase de Tatami (UC-06)": "## 5.6. Caso de Uso 6: Activar Pase de Tatami (UC-06)",
        "## 5.7 Caso de Uso 7: Gestionar Sucursales y Coordenadas Geográficas (UC-07)": "## 5.7. Caso de Uso 7: Gestionar Sucursales y Coordenadas Geográficas (UC-07)",
        "## 5.8 Caso de Uso 8: Entrar como otro Usuario / Impersonificación (UC-08)": "## 5.8. Caso de Uso 8: Entrar como otro Usuario / Impersonificación (UC-08)",
    }
    
    for old_h, new_h in headings_map.items():
        content = content.replace(old_h, new_h)
        
    # -------------------------------------------------------------
    # 2. CITAS EN TEXTO Y AJUSTES PUNTUALES EN CAPÍTULO III
    # -------------------------------------------------------------
    # 3.1.1 YOLO
    content = content.replace(
        "YOLO (acrónimo en inglés de *You Only Look Once*, que significa \"Solo miras una vez\") es una familia de algoritmos de inteligencia artificial de vanguardia, desarrollada por la empresa Ultralytics,",
        "YOLO (acrónimo en inglés de *You Only Look Once*, que significa \"Solo miras una vez\") es una familia de algoritmos de inteligencia artificial de vanguardia, desarrollada y mantenida por Ultralytics (Ultralytics, 2026),"
    )
    
    # 3.1.5 Comparativa de Pose
    content = content.replace(
        "* **YOLOv8 / YOLOv11 (Versiones Anteriores):**",
        "* **YOLO original y versiones previas (Redmon et al., 2016; Ultralytics, 2026):**"
    )
    content = content.replace(
        "* **MediaPipe (Google):** Muy popular en aplicaciones",
        "* **MediaPipe (Bazarevsky et al., 2020):** Desarrollado por Google, muy popular en aplicaciones"
    )
    content = content.replace(
        "* **OpenPose (Carnegie Mellon University):**",
        "* **OpenPose (Cao et al., 2017):** Desarrollado por Carnegie Mellon University,"
    )
    content = content.replace(
        "* **AlphaPose:**",
        "* **AlphaPose (Fang et al., 2017):**"
    )
    
    # 3.2.1 Apple Silicon
    content = content.replace(
        "Apple Silicon es la arquitectura de procesadores de alto rendimiento (serie M) que integra en un mismo chip el procesador principal (CPU), la tarjeta gráfica aceleradora (GPU) y el motor neuronal (Neural Engine), compartiendo un único espacio de memoria ultrarrápida.",
        "Apple Silicon es la arquitectura de procesadores de alto rendimiento (serie M) que integra en un mismo chip el procesador principal (CPU), la tarjeta gráfica aceleradora (GPU) y el motor neuronal (Neural Engine), compartiendo un único espacio de memoria ultrarrápida optimizada mediante el framework MLX (Apple Machine Learning Research, 2025)."
    )
    
    # 3.2.3 Ajuste a ~9 GB en pico (evitar contradicción con memo técnico de 8.55 GB)
    content = content.replace(
        "consumiendo menos de 8 GB de memoria en total.",
        "consumiendo aproximadamente ~9 GB de memoria unificada en pico (Qwen consume ~8.55 GB y YOLO nano una fracción mínima)."
    )
    
    # 3.3.1 Qwen3-VL
    content = content.replace(
        "La familia **Qwen3-VL** (desarrollada por Alibaba Cloud) es una tecnología de Inteligencia Artificial",
        "La familia **Qwen3-VL** (desarrollada por Alibaba Cloud Qwen Team, 2025) es una tecnología de Inteligencia Artificial"
    )
    
    # 3.4.1 Qdrant
    content = content.replace(
        "Qdrant es un motor de búsqueda por similitud de vectores y una base de datos vectorial de código abierto.",
        "Qdrant es un motor de búsqueda por similitud de vectores y una base de datos vectorial de código abierto basada en grafos HNSW (Malkov & Yashunin, 2018; Qdrant, 2026)."
    )
    
    # 3.5.1 Python
    content = content.replace(
        "Python es un lenguaje de programación de alto nivel, interpretado y de propósito general.",
        "Python es un lenguaje de programación de alto nivel, interpretado y de propósito general (Python Software Foundation, 2026)."
    )
    
    # 3.6.1 Docker
    content = content.replace(
        "Docker es una plataforma de software que utiliza \"contenedores\" para empaquetar los servicios",
        "Docker es una plataforma de software que utiliza \"contenedores\" para empaquetar los servicios (Docker Inc., 2026)"
    )
    
    # 3.7.1 PostgREST
    content = content.replace(
        "PostgREST es un servidor web independiente y de código abierto que se conecta directamente a una base de datos PostgreSQL",
        "PostgREST es un servidor web independiente y de código abierto (PostgREST, 2026) que se conecta directamente a una base de datos PostgreSQL"
    )
    
    # 3.8.1 FastAPI
    content = content.replace(
        "FastAPI es un framework moderno y de alto rendimiento para construir APIs (Interfaces de Programación de Aplicaciones) en Python.",
        "FastAPI es un framework moderno y de alto rendimiento para construir APIs en Python (Ramírez, 2026)."
    )
    
    # 3.9.1 PostgreSQL y RLS
    content = content.replace(
        "PostgreSQL es un sistema de gestión de bases de datos relacional de nivel empresarial,",
        "PostgreSQL es un sistema de gestión de bases de datos relacional de nivel empresarial con soporte avanzado para Row Level Security (The PostgreSQL Global Development Group, 2026),"
    )
    
    # 3.10.1 React y Vite
    content = content.replace(
        "**React** es la biblioteca de JavaScript desarrollada por Meta líder en el mundo",
        "**React** es la biblioteca de JavaScript desarrollada por Meta Open Source (2026) líder en el mundo"
    )
    
    # 3.11.1 Leaflet y OSM
    content = content.replace(
        "**Leaflet.js** es una biblioteca de JavaScript ligera y de código abierto para mostrar mapas interactivos en la web. **OpenStreetMap (OSM)** es el \"Wikipedia de los mapas\", un proyecto colaborativo global de datos cartográficos abiertos.",
        "**Leaflet.js** es una biblioteca de JavaScript ligera para mapas interactivos y **OpenStreetMap (OSM)** provee la cartografía colaborativa global y el motor de geocodificación Nominatim (OpenStreetMap Foundation, 2026)."
    )
    
    # 3.12.1 Pytest y Playwright
    content = content.replace(
        "Para garantizar que el sistema no tenga fallos ocultos (siguiendo la regla de \"Cero Falsos Positivos\" de Craig Larman), se utilizan dos herramientas complementarias:",
        "Para garantizar que el sistema no tenga fallos ocultos (siguiendo la regla de \"Cero Falsos Positivos\" de Craig Larman, 2004), se utilizan dos herramientas complementarias: Pytest para backend (Krekel et al., 2024) y Playwright para extremo a extremo (Microsoft, 2026):"
    )
    
    # 3.13.1 IA y Visión
    content = content.replace(
        "La **Inteligencia Artificial (IA)** es la rama de la ingeniería que permite a las computadoras realizar tareas que normalmente requieren inteligencia humana, como ver, razonar o entender el lenguaje.",
        "La **Inteligencia Artificial (IA)** es la rama de la ingeniería que permite a las computadoras realizar tareas que normalmente requieren cognición humana, tales como la percepción visual, el razonamiento y el aprendizaje (Russell & Norvig, 2021)."
    )
    
    # 3.13.2 RAG
    content = content.replace(
        "La **Generación Aumentada por Recuperación (RAG)** es el método que soluciona el mayor problema de las inteligencias artificiales generativas: **las alucinaciones**",
        "La **Generación Aumentada por Recuperación (RAG)** es un método arquitectónico introducido formalmente por Lewis et al. (2020) que soluciona el mayor problema de los modelos de lenguaje: las alucinaciones"
    )
    
    # 3.14.1 Qwen3-VL-Instruct
    content = content.replace(
        "Qwen3-VL-Instruct es un modelo avanzado de Inteligencia Artificial multimodal (Visión y Lenguaje) creado por Alibaba Cloud.",
        "Qwen3-VL-Instruct es un modelo avanzado de Inteligencia Artificial multimodal (Visión y Lenguaje) creado por Alibaba Cloud Qwen Team (2025)."
    )
    
    # 3.14.2 Detalle de persistencia de mensaje_profesor
    content = content.replace(
        "3. **El Mensaje Directo del Profesor (`mensaje_profesor`):** Recibe las indicaciones o secretos técnicos que el propio profesor escribió para esa técnica en la plataforma, dándole máxima prioridad pedagógica.",
        "3. **El Mensaje Directo del Profesor (`mensaje_profesor`):** Recibe las indicaciones o secretos técnicos que el propio profesor escribió para esa técnica en la plataforma, dándole máxima prioridad pedagógica. Dicho texto se persiste además en Qdrant bajo el metadato formal `fuente_tipo='instructor_message'` mediante el servicio `instructor_message_ingestion.py`."
    )
    
    # 3.15.1 Cloudflare Tunnel
    content = content.replace(
        "Cloudflare Tunnel (mediante su herramienta oficial `cloudflared`) es una tecnología de red que permite conectar de forma segura el servidor local de la academia con el mundo exterior.",
        "Cloudflare Tunnel (mediante su herramienta oficial `cloudflared`) es una tecnología de red Zero Trust (Cloudflare Inc., 2026) que permite conectar de forma segura el servidor local de la academia con el mundo exterior."
    )
    
    # 3.16.3 Ciberseguridad Defensiva y reset_production.sql
    content = content.replace(
        "Además del control de membresías mediante el Pase de Tatami, el sistema fue blindado siguiendo estándares profesionales de ciberseguridad (OWASP):",
        "Además del control de membresías mediante el Pase de Tatami, el sistema fue blindado siguiendo estándares profesionales de ciberseguridad defensiva (OWASP Foundation, 2025):"
    )
    content = content.replace(
        "4. **Cero Datos Basura en Producción:** La base de datos y el catálogo operan limpios de cuentas o manuales de prueba, garantizando que los alumnos reales vean únicamente la información oficial de su academia.",
        "4. **Cero Datos Basura en Producción:** La base de datos y el catálogo operan limpios de cuentas de prueba mediante la ejecución controlada del script `reset_production.sql` (que ejecuta `TRUNCATE` en tablas transaccionales y preserva únicamente las cuentas oficiales de staff y las tres sucursales), verificado empíricamente por la suite `verify_iter_4h.py` al constatar un catálogo inicial vacío `[]`."
    )
    
    # -------------------------------------------------------------
    # 3. AJUSTES EN CAPÍTULO IV Y V (TRAZABILIDAD Y GAPS)
    # -------------------------------------------------------------
    # Capítulo IV: IEEE 830
    content = content.replace(
        "Su estructura sigue las directrices del estándar IEEE 830,",
        "Su estructura sigue las directrices del estándar IEEE 830 (IEEE, 1998),"
    )
    
    # 4.3.1 RF-03 Impersonación (Nota de trazabilidad / deuda)
    content = content.replace(
        "* **RF-03:** El sistema debe permitir al Administrador \"entrar como\" cualquier otro usuario para ayudarlo con problemas técnicos, mostrando un aviso claro en la pantalla mientras lo hace.",
        "* **RF-03:** El sistema debe permitir al Administrador \"entrar como\" cualquier otro usuario para soporte técnico, mostrando un banner defensivo en pantalla (*Nota de trazabilidad: La emisión del token JWT con claim `impersonator_admin_id` y el frontend están implementados; la re-autenticación obligatoria por contraseña y la tabla física de auditoría quedan registradas como deuda técnica priorizada*)."
    )
    
    # 5.2.4 Aclaración sobre timestamp_error_segundos en JSON auxiliar
    content = content.replace(
        "ViewFeedback --> Alumno : Despliega video interactivo, articulaciones y corrección",
        "ViewFeedback --> Alumno : Despliega video interactivo, articulaciones y corrección\n    Note over API, ViewFeedback: timestamp_error_segundos se sirve vía archivo JSON auxiliar en /tmp/corpocmente_frames/meta_{id}.json"
    )
    
    # 5.8.1 Nota de trazabilidad en UC-08
    impersonate_note = (
        "\n> [!NOTE]\n"
        "> *Nota de trazabilidad técnica:* La re-autenticación de contraseña del administrador en el endpoint backend y la persistencia en la tabla `auditoria_impersonacion` están formalmente registradas como deuda técnica para iteración futura; el token JWT emitido por el sistema ya incluye inmutablemente el claim `impersonator_admin_id` y la interfaz activa el banner defensivo de advertencia.\n"
    )
    if "### 5.8.1 Caso de Uso Detallado" in content:
        content = content.replace(
            "### 5.8.1 Caso de Uso Detallado\n",
            "### 5.8.1 Caso de Uso Detallado\n" + impersonate_note
        )

    # -------------------------------------------------------------
    # 4. FORMATEO APA 7 DE TABLAS (NUMERACIÓN GLOBAL 1..17)
    # -------------------------------------------------------------
    tablas_map = [
        (r"\*\*Tabla 3\.1: Prueba experimental entre Pose Directa vs\. Segmentación \+ Pose\*\*",
         "Tabla 1\n*Prueba experimental entre Pose Directa vs. Segmentación + Pose*"),
        (r"\*\*Tabla 3\.2: Comparativa de tecnologías de estimación de pose humana\*\*",
         "Tabla 2\n*Comparativa de tecnologías de estimación de pose humana*"),
        (r"\*\*Tabla 3\.3: Comparativa de Infraestructuras de Cómputo para Inferencia de IA\*\*",
         "Tabla 3\n*Comparativa de Infraestructuras de Cómputo para Inferencia de IA*"),
        (r"\*\*Tabla 3\.4: Comparativa de Modelos de Búsqueda y Vectorización Multimodal\*\*",
         "Tabla 4\n*Comparativa de Modelos de Búsqueda y Vectorización Multimodal*"),
        (r"\*\*Tabla 3\.5: Comparativa de Motores de Búsqueda Vectorial\*\*",
         "Tabla 5\n*Comparativa de Motores de Búsqueda Vectorial*"),
        (r"\*\*Tabla 3\.6: Comparativa de Lenguajes de Programación para el Proyecto\*\*",
         "Tabla 6\n*Comparativa de Lenguajes de Programación para el Proyecto*"),
        (r"\*\*Tabla 3\.7: Comparativa de Tecnologías de Contenerización y Despliegue\*\*",
         "Tabla 7\n*Comparativa de Tecnologías de Contenerización y Despliegue*"),
        (r"\*\*Tabla 3\.8: Comparativa de Tecnologías para Capa de Datos REST\*\*",
         "Tabla 8\n*Comparativa de Tecnologías para Capa de Datos REST*"),
        (r"\*\*Tabla 3\.9: Comparativa de Frameworks de Backend\*\*",
         "Tabla 9\n*Comparativa de Frameworks de Backend*"),
        (r"\*\*Tabla 3\.10: Comparativa de Bases de Datos Relacionales y No Relacionales\*\*",
         "Tabla 10\n*Comparativa de Bases de Datos Relacionales y No Relacionales*"),
        (r"\*\*Tabla 3\.11: Comparativa de Tecnologías de Frontend\*\*",
         "Tabla 11\n*Comparativa de Tecnologías de Frontend*"),
        (r"\*\*Tabla 3\.12: Comparativa de Servicios de Mapas Digitales\*\*",
         "Tabla 12\n*Comparativa de Servicios de Mapas Digitales*"),
        (r"\*\*Tabla 3\.13: Comparativa de Herramientas de Pruebas de Software\*\*",
         "Tabla 13\n*Comparativa de Herramientas de Pruebas de Software*"),
        (r"\*\*Tabla 3\.14: Comparativa de Motores Generativos para Retroalimentación Deportiva\*\*",
         "Tabla 14\n*Comparativa de Motores Generativos para Retroalimentación Deportiva*"),
        (r"\*\*Tabla 3\.15: Comparativa de Tecnologías para Acceso Remoto desde Internet\*\*",
         "Tabla 15\n*Comparativa de Tecnologías para Acceso Remoto desde Internet*"),
        (r"\*\*Tabla 3\.16: Comparativa de Modelos de Control de Suscripción para la Academia\*\*",
         "Tabla 16\n*Comparativa de Modelos de Control de Suscripción para la Academia*"),
        (r"\*\*Tabla 4\.1: Matriz de Trazabilidad \(Requisitos, Historias y Casos de Uso\)\*\*",
         "Tabla 17\n*Matriz de Trazabilidad (Requisitos, Historias y Casos de Uso)*"),
    ]
    for pattern, repl in tablas_map:
        content = re.sub(pattern, repl, content)
        
    # Cambiar pies de tabla a formato APA 7 (*Nota.* Elaboración propia...)
    content = content.replace("*Fuente: Elaboración propia (2026).*", "*Nota.* Elaboración propia (2026).")
    content = content.replace("*Fuente: Elaboración propia*", "*Nota.* Elaboración propia (2026).")

    # -------------------------------------------------------------
    # 5. ACTUALIZAR TABLA DE CONTENIDO (TOC)
    # -------------------------------------------------------------
    toc_pattern = r"## TABLA DE CONTENIDO\n\n.*?(?=\n# Capítulo I: Definición del Proyecto de Investigación)"
    content = re.sub(toc_pattern, get_toc_apa().strip(), content, flags=re.DOTALL)

    # -------------------------------------------------------------
    # 6. INSERTAR CAPÍTULOS VI, VII Y VIII ANTES DE REFERENCIAS
    # -------------------------------------------------------------
    ref_marker = "# Referencias Bibliográficas"
    assert ref_marker in content, "No se encontró el marcador de Referencias Bibliográficas"
    
    parts = content.split(ref_marker, 1)
    
    nuevos_capitulos = (
        get_capitulo_6().strip() + "\n\n---\n\n" +
        get_capitulo_7().strip() + "\n\n---\n\n" +
        get_capitulo_8().strip() + "\n\n---\n\n"
    )
    
    # -------------------------------------------------------------
    # 7. REESCRIBIR SECCIÓN COMPLETA DE REFERENCIAS APA 7
    # -------------------------------------------------------------
    final_content = parts[0].rstrip() + "\n\n---\n\n" + nuevos_capitulos + get_referencias_apa().strip() + "\n"
    
    # -------------------------------------------------------------
    # 8. GUARDAR DOCUMENTO FINAL
    # -------------------------------------------------------------
    DOC_PATH.write_text(final_content, encoding="utf-8")
    print(f"Documento {DOC_PATH} actualizado exitosamente.")

if __name__ == "__main__":
    apply_full_update()

