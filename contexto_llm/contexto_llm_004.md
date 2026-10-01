

--- ARCHIVO: ProyectoGrado/docs/AnalisiDiseno.md ---
# Análisis y Diseño Orientado a Objetos (Proceso Unificado)
## Sistema de Análisis Biomecánico de Técnicas de Jiu-Jitsu Brasileño (Corpo e Mente)

Este documento aplica estrictamente la metodología iterativa e incremental de **Craig Larman** descrita en *"Applying UML and Patterns"*, estructurando el ciclo de vida del software mediante las Fases e Iteraciones del **Proceso Unificado (UP)**.

---

## FASE 1: INCEPCIÓN (Visión y Delimitación)

El objetivo de la Incepción es establecer la visión, el caso de negocio y delimitar el alcance del Producto Mínimo Viable (MVP).

* **Visión:** Desarrollar un sistema de análisis biomecánico por inteligencia artificial para la red internacional de academias "Corpo e Mente" (Soporte i18n PT/ES).
* **Restricciones de Negocio y Arquitectura:**
  * **Zero-Shot AI:** Solo se dispone de 2 videos por técnica. No hay datos para entrenar un modelo; se usará inferencia directa con **YOLO v11/26** (Pose Estimation).
  * **Procesamiento de Bajo Costo:** Inferencia pesada aislada en **Google Colab Pro** (Worker asíncrono).
  * **Modelos IA Gratuitos:** **Gemini API Free Tier** para lenguaje natural y retroalimentación, requiriendo un control estricto de cuotas (Rate Limits).
  * **Almacenamiento:** Arquitectura Híbrida (PostgreSQL/PostgREST para operacional + Qdrant para vectores).

---

## FASE 2: ELABORACIÓN - ITERACIÓN 1 (Núcleo Biomecánico)

La primera iteración aborda los riesgos fundamentales del negocio y modela la lógica básica para el análisis de una técnica.

### 2.1 Caso de Uso UC1: Analizar Técnica y Generar Feedback (*Fully Dressed*)

*   **Caso de Uso UC1:** Analizar Técnica y Generar Feedback
*   **Actor Principal:** Alumno
*   **Partes Interesadas e Intereses:**
    *   **Alumno:** Desea subir un video de su ejecución, recibir una evaluación objetiva y precisa en su idioma (PT/ES), y obtener retroalimentación biomecánica clara sin demoras excesivas.
    *   **Profesor / Academia ("Corpo e Mente"):** Desea garantizar que los alumnos ejecuten las técnicas de acuerdo con el patrón de referencia y mantener un estándar de enseñanza uniforme en todas las sucursales.
    *   **Administrador del Sistema:** Requiere un control estricto sobre el consumo de recursos (Google Colab Pro, cuotas de Gemini API Free Tier) y prevención de SPAM en el almacenamiento.
*   **Precondición:** El alumno está autenticado en la plataforma y pertenece a una sucursal válida.
*   **Garantía de Éxito (Postcondiciones):** El video de la técnica es procesado, los vectores biomecánicos son extraídos y comparados contra la referencia, se genera el informe explicativo multimodal en el idioma correspondiente y los resultados son almacenados de forma persistente en PostgreSQL y Qdrant.

**Flujo Principal (Escenario Principal de Éxito):**
1. El Alumno selecciona el idioma de evaluación (PT/ES), elige la Técnica a evaluar y sube el archivo de video de su intento.
2. El Sistema valida mediante la API de Gemini Flash que el video contenga una ejecución válida de Jiu-Jitsu (prevención de contenido no relacionado / SPAM).
3. El Sistema registra la evaluación con estado 'procesando' y encola la tarea de análisis asíncrono para el Worker de Colab Pro.
4. El Worker extrae los vectores del esqueleto biomecánico (keypoints) del video del Alumno utilizando el modelo YOLO (Pose Estimation).
5. El Worker consulta la base de datos vectorial Qdrant y calcula la similitud del coseno entre la pose del Alumno y el esqueleto de referencia del Profesor.
6. El Sistema orquesta el re-ranking visual y genera el feedback biomecánico estructurado utilizando la estrategia de prompt en el idioma seleccionado mediante Gemini.
7. El Sistema actualiza el estado de la evaluación a 'completado' y presenta los resultados visuales (video con esqueleto superpuesto) y textuales al Alumno.

**Extensiones (Flujos Alternativos y de Excepción):**
*   **2a. El contenido del video no es reconocido como Jiu-Jitsu:**
    1. El Sistema rechaza el procesamiento, marca la evaluación como 'inválida' y notifica al Alumno el motivo del rechazo.
*   **3a. El servicio de cola o Worker en Colab Pro no se encuentra disponible:**
    1. El Sistema registra el estado como 'en_espera_worker' y reintenta la conexión de acuerdo con la política de tolerancia a fallos.
    2. Si el tiempo de espera excede el límite (timeout), se envía una notificación al Alumno informando que su video será procesado en diferido.
*   **4a. YOLO no logra detectar la estructura corporal en el video (baja iluminación o encuadre incompleto):**
    1. Worker notifica falla de extracción, el Sistema cambia el estado a 'error_procesamiento' y solicita al Alumno volver a grabar el video siguiendo las recomendaciones de captura.
*   **6a. Se supera el límite de cuota (Rate Limit) en Gemini API (Free Tier):**
    1. El Sistema aplica una pausa o delega la petición a una estrategia de prompts de contingencia, reteniendo la tarea en la cola hasta la renovación del token.

**Requisitos Especiales:**
*   El procesamiento del video en el Worker de Colab Pro no debe exceder los 90 segundos por intento.
*   La interfaz debe soportar internacionalización fluida (i18n) en Portugués y Español.
*   El control de privacidad debe garantizar que el video y las evaluaciones solo sean accesibles por el Alumno y los instructores de su sucursal (mediante políticas RLS en PostgreSQL).

**Lista de Variaciones Tecnológicas y de Datos:**
*   Formatos de video de entrada: MP4, MOV o WebM con resolución mínima de 720p.
*   Dispositivos de captura: Cámaras de dispositivos móviles (iOS/Android) o cámaras web.

**Frecuencia de Ocurrencia:** Alta en horarios de entrenamiento (estimado de 5 a 20 evaluaciones por alumno a la semana).

**Cuestiones Abiertas:**
*   ¿Se debe permitir la comparación del video del alumno contra más de un video de referencia de distintos profesores?


### 2.2 Diagrama de Secuencia del Sistema (SSD)

Modela los eventos en la frontera del sistema para el escenario principal.

```mermaid
sequenceDiagram
    actor Alumno
    participant Sistema as :Sistema
    
    Alumno->>Sistema: solicitarAnalisisTecnica(idTecnica, videoArchivo, idioma)
    Sistema-->>Alumno: acuseReciboProcesamiento(idEvaluacion)
    
    Note over Sistema: [Procesamiento Asíncrono en Background]
    
    Alumno->>Sistema: consultarEstadoEvaluacion(idEvaluacion)
    Sistema-->>Alumno: resultadosAnalisis(feedbackIA, porcentajeSimilitud, videoSuperpuesto)
```

### 2.3 Contratos de Operación
* **Operación:** `solicitarAnalisisTecnica(idTecnica, videoArchivo, idioma)`
* **Pre-condiciones:** Existe una `Tecnica` con el `idTecnica`. El Alumno está autenticado.
* **Post-condiciones:** 
  * Se creó una instancia `ev` de `Evaluacion`.
  * Se asoció `ev` al `Alumno` y a la `Tecnica`.
  * El estado de `ev` pasó a 'procesando'.

### 2.4 Modelo de Dominio Conceptual
Muestra los conceptos del problema del mundo real (sin identificadores de base de datos ni métodos de software).

```mermaid
classDiagram
    class Academia {
        nombre
    }
    class Sucursal {
        pais
        idiomaPrincipal
    }
    class Usuario {
        nombreCompleto
        rol
    }
    class Tecnica {
        nombre
        nivel
    }
    class Video {
        archivoVideo
    }
    class EsqueletoBiomecanico {
        coordenadasArticulaciones
    }
    class Evaluacion {
        porcentajeSimilitud
        feedbackTextual
        estado
    }

    Academia "1" *-- "1..*" Sucursal : tiene
    Sucursal "1" o-- "1..*" Usuario : aloja
    Usuario "1" -- "1..*" Video : graba
    Video "*" -- "1" Tecnica : demuestra
    Video "1" *-- "1" EsqueletoBiomecanico : contiene
    Usuario "1" -- "*" Evaluacion : recibe
    Evaluacion "1" -- "2" Video : compara (Profesor vs Alumno)
```

### 2.5 Diseño Lógico Orientado a Objetos (GRASP)
Asignación de responsabilidades mediante patrones GRASP.
* **Controller:** Un `VideoAnalysisController` recibe el evento `solicitarAnalisisTecnica`. Delega el almacenamiento y encola la petición.
* **Creator & Information Expert:** La entidad `Video` contiene la responsabilidad de extraer el `EsqueletoBiomecanico` (alta cohesión), ya que posee la imagen base.

---

## FASE 2: ELABORACIÓN - ITERACIÓN 2 (Pipeline Biomecánico YOLO -> Gemini)

La iteración 2 aborda la lógica central de la IA: comparación biomecánica matemática y retroalimentación pedagógica condicional.

### 3.1 Lógica del Pipeline y Optimización de Recursos
Para minimizar costos y maximizar la precisión, el flujo se define de la siguiente manera:
1. **YOLO26 (Pose Estimation):** Extrae los vectores (keypoints) del video del alumno frame a frame.
2. **Comparación Matemática (Qdrant/Similitud Coseno):** Se compara cada frame del alumno contra la técnica de referencia. Se busca el fotograma exacto con la mayor diferencia (distancia vectorial).
3. **Resaltado Visual del Error:** El sistema utiliza YOLO26 para **dibujar con precisión** sobre la imagen del fotograma qué articulación o parte del cuerpo específica tiene la mayor diferencia respecto al profesor.
4. **Validación de Umbral (Tolerancia):** 
   - Si la diferencia máxima está dentro de un rango aceptable (ej. > 85% de similitud), la técnica se considera **correcta**. NO se invoca a la IA generativa (Gemini).
   - Si la diferencia supera el umbral, la técnica es **incorrecta**. Se extrae el fotograma crítico (keyframe) ya marcado/dibujado.
5. **Cerebro Pedagógico (Gemini):** Solo si la técnica es incorrecta, se envía a Gemini el **nombre de la técnica** (para dar contexto exacto de lo que se evalúa) y el fotograma con el error resaltado. Gemini genera la corrección pedagógica textual.

*Nota sobre Qwen-VL:* Inicialmente se contempló usar Qwen para un "re-ranking visual" de los fotogramas. Sin embargo, dado que YOLO y el cálculo de distancia matemática ya nos devuelven el fotograma exacto con mayor diferencia de forma precisa y determinista, el paso de Qwen resulta redundante y ha sido eliminado de la arquitectura para optimizar la velocidad y consumo de VRAM.

### 3.2 Diagrama de Interacción de Software (Secuencia UML)

```mermaid
sequenceDiagram
    participant Worker as WorkerColabPro
    participant YOLO as YOLO_Extractor
    participant Math as ComparadorMatematico
    participant Gemini as GeminiApiAdapter
    participant DB as PostgresDB

    Worker->>YOLO: extraerVectoresPose(videoAlumno)
    YOLO-->>Worker: vectoresBiomecanicos (133 keypoints por frame)
    
    Worker->>Math: buscarFotogramaMaxDiferencia(vectoresAlumno, referenciaQdrant)
    Math-->>Worker: frameErrorCritico, porcentajeSimilitud
    
    alt Similitud > Umbral Aceptable (Técnica Correcta)
        Worker->>DB: actualizarEvaluacion("¡Técnica Excelente!", estado='completado')
    else Similitud < Umbral Aceptable (Técnica Incorrecta)
        Worker->>Gemini: generarFeedbackBiomecanico(frameErrorCritico, PromptStrategy)
        Gemini-->>Worker: textoExplicativoCorreccion (ES/PT)
        Worker->>DB: actualizarEvaluacion(textoExplicativoCorreccion, estado='completado')
    end
```

---

## FASE 2: ELABORACIÓN - ITERACIÓN 3 (Persistencia Híbrida y Resiliencia)

La iteración 3 estabiliza la infraestructura de software y maneja problemas de rendimiento, concurrencia de múltiples sucursales y almacenamiento robusto.

### 4.1 Arquitectura de Cola Asíncrona (Resiliencia Rate Limits)
El Nivel Gratuito de la API de Gemini impone límites estrictos (RPM/RPD). Larman aconseja manejar estos riesgos en la capa de **Servicios Técnicos (Infraestructura)**.
* Se implementará una cola de mensajes (Broker, ej. Redis o RabbitMQ, consumida por el script de Colab Pro).
* El controlador web no espera a Gemini; añade la tarea a la cola y retorna inmediatamente (Patrón `Fire-and-Forget`).

### 4.2 Persistencia de Objetos (Híbrida)
* **Datos Operacionales (PostgreSQL + PostgREST):** El modelo de dominio conceptual se traduce a tablas relacionales normalizadas (3NF) gestionando Usuarios, Roles, Sucursales y Evaluaciones. Se implementa seguridad **RLS (Row Level Security)** en PostgreSQL para garantizar que un alumno solo vea sus propias evaluaciones y el administrador de Brasil no vea los datos de Colombia.
* **Datos Vectoriales (Qdrant):** El objeto `EsqueletoBiomecanico` y su estado trigonométrico se guarda como un arreglo de punto flotante indexado por HNSW en Qdrant, vinculado a la BD transaccional por un `UUID`. *(Ver detalles técnicos en el documento de Diseño de Base de Datos).*

---

---

## FASE 3: CONSTRUCCIÓN - ITERACIONES E INCREMENTOS EJECUTABLES

La Fase de Construcción sigue el Proceso Unificado (UP) de Craig Larman, construyendo incrementos probados de grado de producción.

### 5.1 Iteración C1: Infraestructura de API y Mocks
- **Objetivo:** Codificar el núcleo de FastAPI, Controladores (`VideoAnalysisController`) y Fachadas (`IntelligenceAnalysisFacade`).
- **Logros:** Implementación de enrutamiento REST, validación con Pydantic, y pruebas unitarias aisladas (`test_intelligence_facade.py`) usando inyección de dependencias y objetos Mock, cumpliendo el principio de *Test-First Programming* de Larman.

### 5.2 Iteración C2: Seguridad (RLS/JWT), Base de Datos 3NF y Extracción Biomecánica (YOLO)
- **Caso de Uso (UC2 - Autenticación y Privacidad Multi-Tenant):**
  - **Actores:** Alumno / Profesor
  - **Flujo:** El usuario se autentica y el sistema garantiza, mediante **Row Level Security (RLS)** en PostgreSQL (`03_rls_policies.sql`), que un Alumno solo acceda a sus propias evaluaciones y un Profesor a las de su sucursal.
- **Implementación de YOLOPoseAdapter:**
  - Se materializó el *Experto de Información (Information Expert)* para la extracción vectorial de la pose usando `ultralytics` (`yolo11n-pose.pt`).
  - Aplicación efectiva del patrón *Adapter (GoF)* para encapsular el aplanamiento de tensores de 133 dimensiones y su mapeo al modelo conceptual `EsqueletoBiomecanico`.
- **Capa de Datos Transaccional (Mannino):**
  - Esquema en **Tercera Forma Normal (3NF)** y Boyce-Codd (BCNF) en SQL puro (`01_schema_3nf.sql`).
  - Funciones nativas de base de datos (`pgcrypto`) delegando la autenticación a PostgREST (`02_auth_jwt.sql`).

### 5.3 Iteración C3: Sistema de Diseño e Interfaz de Usuario (React + Vite)
- **Caso de Uso (UC3 - Carga e Inspección Visual de la Técnica):**
  - **Actores:** Alumno / Atleta
  - **Interfaz de Usuario:** Construcción de la Web App en React + Vite utilizando un Sistema de Diseño basado en tokens de Vanilla CSS (Tema Oscuro con Rojo Institucional `#d01118` y Glassmorphism).
- **Componentes Creados:**
  - `ProgressRing.jsx`: Anillo de progreso biomecánico mediante `<progress>` nativo animado con `conic-gradient` CSS.
  - `VideoUpload.jsx`: Módulo de carga mediante *Drag & Drop* con previsualización del archivo de video (`URL.createObjectURL`).
  - `FeedbackReport.jsx` (Vista de Resultados): Interfaz estructurada donde:
    - **Sección Superior (Visual):** Muestra el **Video Original del Maestro** (en bucle/reproducción) lado a lado con el **Fotograma del Alumno** (que tiene el área del cuerpo incorrecta dibujada/resaltada por YOLO26).
    - **Sección Inferior (Texto):** Muestra el texto explicativo generado por Gemini detallando el error y cómo corregirlo (solo si hubo error). Si no hubo error, muestra un mensaje de felicitación.

### 5.4 Iteración C4: Filtro Inteligente Anti-SPAM (Gemini Multimodal API)
- **Caso de Uso (UC4 - Prevenir Contenido No Relacionado / SPAM):**
  - **Actores:** Sistema / Gemini API
  - **Flujo:** Antes de enviar un video a la GPU de procesamiento pesado, el sistema realiza una llamada asíncrona a `GeminiApiAdapter.validar_es_jiujitsu()` enviando el video a la *Files API* de Gemini para verificar si contiene ejecuciones de Jiu-Jitsu o Grappling.
- **Resiliencia y Manejo de Estado:**
  - Implementación de espera activa de estado (`PROCESSING` -> `ACTIVE`) en Gemini Files API.
  - Aplicación del patrón *Lazy Loading* en `YOLOPoseAdapter` y `QdrantVectorAdapter` para desacoplar el arranque del servidor HTTP de la disponibilidad de modelos pesados o BDs externas.
  - Endpoint REST expuesto en `/api/v1/evaluaciones/validar-spam` devolviendo HTTP 422 si el contenido es rechazado.

### 5.5 Iteración C5: Autenticación por Roles, Impersonalización y Perfil
- **Caso de Uso (UC5 - Autenticación, Gestión de Perfil y Cambio de Roles):**
  - **Actores:** Alumno / Profesor / Administrador
  - **Flujo:** El modal de inicio de sesión (`LoginModal.jsx`) permite conmutar entre roles. Los usuarios pueden actualizar su perfil (`UserProfileModal.jsx`), incluyendo la carga de una foto de perfil (`avatar_url`) procesada en Base64 para persistencia de sesión.
  - **Patrón Impersonalización (Admin Proxy):** Se implementó un flujo avanzado para control de calidad donde el Administrador General puede "impersonalizar" cualquier cuenta de usuario o profesor (`/api/v1/auth/impersonate/{user_id}`). El sistema utiliza un banner persistente en la aplicación React para advertir el estado de impersonificación y ofrecer una vía de escape al perfil administrador original.
  - **Patrón Singleton y Controlador MOCK (Backend):** Toda la lógica de roles interactúa con un estado persistente simulado (`USUARIOS_DB` y `SUCURSALES_DB` en `auth_routes.py`) siguiendo el patrón **Controller** y preservando las reglas de normalización (Mannino) al hacer referencias mutuas por `sucursal_id` (UUID).
- **Caso de Uso (UC6 - Gestión Multi-Tenant de Sucursales Globales):**
  - **Actores:** Administrador
  - **Flujo:** El panel de administración (`AdminSucursales.jsx`) permite el registro CRUD de sedes físicas con un mapa mundial interactivo **100% Gratuito y Libre (Leaflet.js + OpenStreetMap)**.
  - **Resolución Analítica de Coordenadas (Web Scraping & Plus Codes):** El administrador puede pegar un enlace de Google Maps. El sistema extrae en el backend las coordenadas exactas de la URI (`!3d / !4d`), realiza *Reverse Geocoding* gratuito con Nominatim y, si la ubicación carece de calle registrada, aplica un algoritmo compensatorio usando la librería de Google `openlocationcode` para generar matemáticamente el identificador de área exacto (Plus Code) evitando imprecisiones de barrio.

### 5.6 Iteración C6: Gestión de Técnicas y Referencias (Profesor)
- **Caso de Uso (UC7 - Gestión del Catálogo de Técnicas y Videos de Referencia):**
  - **Actores:** Profesor
  - **Flujo:** Desde su panel exclusivo (`ProfesorTecnicas.jsx`), un profesor puede poblar el catálogo global de técnicas creando, editando y eliminando elementos especificando únicamente el `nombre` propio universal de la técnica y su nivel de cinturón (`nivel_cinturon`), además de adjuntar sus propios videos de demostración (previsualización interactiva con `URL.createObjectURL`).
  - **Refinamiento del Modelo y Nombres Propios:** Siguiendo las directrices del dominio del Jiu-Jitsu, las técnicas (ej. *Armbar*, *Kimura*, *Triângulo*, *De la Riva*) se tratan como **nombres propios universales**, por lo que se consolidaron los campos bilingües en una única propiedad `nombre`. Asimismo, se eliminaron los campos redundantes `categoria` y `descripcion`. Los campos dinámicos traducibles (como el nivel de cinturón) son adaptados automáticamente por la interfaz según el idioma preferido del usuario.
  - **Justificación de Diseño (Mannino 3NF):** Las Técnicas (`tecnicas`) son tratadas como entidades fuertes (catálogo global universal) independientes del profesor que las crea para evitar anomalías de inserción y redundancia. La relación de pertenencia se establece de manera M:N (muchos profesores pueden subir su versión de una misma técnica) mediante la entidad asociativa `videos_referencia`.

### 5.7 Iteración C7: Selección de Profesor de Sucursal y Evaluación de Alumno
- **Caso de Uso (UC8 - Evaluación Biomecánica basada en Selección de Profesor y Técnica):**
  - **Actores:** Alumno / Atleta
  - **Flujo:** Al ingresar a la vista de carga de ejecuciones (`VideoUpload.jsx`), el alumno primero selecciona el **Profesor registrado en su Sucursal** (`GET /api/v1/profesores?sucursal_id=...`). A continuación, el sistema filtra dinámicamente el catálogo mostrando únicamente las **Técnicas que dicho profesor ha demostrado y subido como patrón de referencia** (`GET /api/v1/tecnicas?profesor_id=...`). El alumno carga su video y el sistema realiza la inferencia comparativa biomecánica contra la referencia vectorial en Qdrant registrada por ese profesor específico.
  - **Justificación de Diseño (Mannino 3NF & Relaciones Relacionales):**
    - `sucursales (1) -> (N) usuarios (profesores)`: Garantiza el aislamiento multi-tenant por sede.
    - `profesores (M) <-> (N) tecnicas`: Resuelto mediante la entidad asociativa `videos_referencia`. Esto permite que un alumno evalúe su técnica con el patrón exacto asignado por los instructores de su propia academia, preservando la normalización 3NF en el modelo transaccional.

---
*(La fase de **Transición** contemplará la corrección de errores finales, pruebas beta en las sedes de Corpo e Mente, y el despliegue en producción).*

### 5.8 Iteración C9: Integración Multimodal (YOLO + Qwen + Gemini)
- **Caso de Uso (UC9 - RAG Multimodal con Qwen para Libros y Videos):**
  - **Actores:** Alumno / Atleta, Profesor
  - **Flujo y Responsabilidades (Larman - Asignación de Responsabilidades):**
    - **Gestión de Conocimiento (Profesor):** El profesor puede subir material teórico (libros, manuales) y videos. **QwenEmbeddingAdapter** asume la responsabilidad de procesar estos archivos y generar sus embeddings multimodales (2048 dimensiones).
    - **Base de Datos Vectorial (Qdrant):** Almacena estos embeddings masivos (2048-dim). Se convierte en el núcleo del sistema **RAG (Retrieval-Augmented Generation)**.
    - **YOLOPoseAdapter (Experto en Extracción Cruda):** Sigue siendo responsable de la cinemática. Extrae keypoints para aislar el instante exacto del error (el fotograma crítico).
    - **Evaluación RAG (Alumno):** Una vez que YOLO detecta el fotograma crítico del alumno, Qwen lo vectoriza. Este vector se usa para consultar a Qdrant y recuperar la teoría exacta (del libro del profesor) o referencias visuales similares.
    - **GeminiApiAdapter (Cerebro Pedagógico):** Recibe el análisis crudo de YOLO junto con la **teoría recuperada por el RAG (Qwen+Qdrant)**, y consolida esta información para redactar un feedback profundamente técnico y empático.
  - **Justificación de Diseño (Domain Model & Variaciones Protegidas):**
    - Se consagra el patrón **RAG Multimodal**. Qwen no es solo un extractor de características, sino el motor de recuperación de conocimiento (teoría y práctica).
    - **Qwen3-VL** actúa puramente como Motor de Vectorización Multimodal (RAG).
    - **Gemini** se exime del cálculo matemático y de la búsqueda, actuando como la interfaz generativa (NLP) que explica la teoría recuperada.
    - `IntelligenceAnalysisFacade` orquesta: YOLO (Fallo) -> Qwen (Vectorizar) -> Qdrant (Recuperar Libro/Video) -> Gemini (Explicar).

### 5.9 Iteración C11: Gestión Completa de Conocimiento RAG (Postgres + Qdrant + UI)

- **Caso de Uso (UC10 - Gestión de Teoría del Profesor con CRUD Completo):**
  - **Actores:** Profesor, Alumno (consumidor indirecto vía feedback enriquecido)
  - **Flujo:**
    1. El profesor sube teoría desde `ProfesorTecnicas.jsx` (campo "Manual del Maestro").
    2. El backend (`IngestKnowledgeUseCase`) vectoriza los chunks vía Colab Qwen y los persiste en **Qdrant** (búsqueda vectorial) y en **PostgreSQL** (`teoria_referencia`, trazabilidad).
    3. El profesor puede ver los chunks que subió vía `TheoryManagerModal.jsx` (consume `GET /conocimiento/teoria/{tecnica_id}?solo_mios=true`).
    4. El profesor puede borrar toda su teoría vía `DELETE /conocimiento/teoria/{tecnica_id}` (sincroniza Postgres + Qdrant).
  - **Justificación de Diseño (Mannino 3NF & Trazabilidad):**
    - Nueva entidad `teoria_referencia` con FK a `tecnicas`, `usuarios` (profesor) y `sucursales`. Índices separados por cada FK.
    - **Linkage bidireccional Postgres ↔ Qdrant:** `qdrant_point_id UUID UNIQUE` actúa como FK lógica entre motores. PostgreSQL es la fuente de verdad; Qdrant es índice reconstruible.
    - **RLS habilitada** en `teoria_referencia`; todo acceso se hace vía RPC `SECURITY DEFINER` (`admin_save_teoria_chunk`, `admin_list_teoria_by_tecnica`, `admin_delete_teoria_by_tecnica_profesor`).
  - **Hallazgos arquitectónicos (Larman - Feedback real):**
    - La verificación E2E de C11.0 reveló que la teoría vivía **exclusivamente en Qdrant**, sin trazabilidad ni CRUD. El "checkbox de teoría" en `ProfesorTecnicas.jsx` era un write-only field.
    - Se corrigió introduciendo una **capa relacional de metadata** + endpoints HTTP de gestión + UI de visualización/borrado.
    - **Deuda técnica pendiente (C11.4):** El pipeline de **consumo** de la teoría (recuperación RAG en `IntelligenceAnalysisFacade`) tiene 3 bugs de integración (endpoint `/embed` inexistente, formato JSON vs form-data, vector sin nombre en Qdrant). El trabajo de C11.1-C11.3 es correcto; el evaluador no consume lo persistido aún.
  - **Refinamiento del Modelo Conceptual:**
    - `Tecnica` (1) ──── (N) `TeoriaReferencia` ──── (1) `Usuario` (profesor)
    - Cada `TeoriaReferencia` es un chunk vectorizable con trazabilidad individual.
  - **Justificación de Alcance Timeboxed:**
    - Se dividió en 4 mini-iteraciones (C11.1 a C11.3) + 1 backlog (C11.4). Cada una entrega un incremento probado. Esto respeta el principio de Larman: **"Small steps, rapid feedback, and adaptation"**.




--- ARCHIVO: ProyectoGrado/docs/ArquitecturaSoftware.md ---
# DOCUMENTO DE ARQUITECTURA DE SOFTWARE (SAD)
## SISTEMA DE ANÁLISIS BIOMECÁNICO DE TÉCNICAS DE JIU-JITSU BRASILEÑO (CORPO E MENTE)

---

Este documento formaliza la arquitectura del sistema aplicando las recomendaciones del **Documento de Arquitectura de Software (SAD)** y el **Diseño Lógico Orientado a Objetos** según la metodología de **Craig Larman** en *"Applying UML and Patterns"* (Capítulos 19, 20, 30, 31 y 32).

---

## 1. TABLA DE FACTORES ARQUITECTÓNICOS (Capítulo 32)

Identificación de los requisitos no funcionales (NFRs) críticos y las soluciones arquitectónicas diseñadas para mitigarlos.

| Factor Arquitectónico | Restricción / Desafío | Solución de Diseño / Patrón Adoptado |
| :--- | :--- | :--- |
| **Bajo Presupuesto Hardware** | No se dispone de servidor propio con GPU para inferencia pesada de IA. | **Procesamiento Asíncrono en Google Colab Web:** El backend delega la inferencia de YOLO y Qwen3-VL a un Worker ejecutado como un notebook en Google Colab Web (runtime T4 GPU). |
| **Límite de Cuota (Gemini API)** | Nivel Gratuito de Gemini API impone cuotas estrictas de solicitudes por minuto (RPM). | **Patrón Message Queue (Cola de Tareas):** Encolado de tareas asíncronas con reintentos para no saturar las llamadas a Gemini. |
| **Estimación 3D / Profundidad** | Capturar la profundidad espacial ($Z$) en llaves y agarres complejos. | **Ultralytics Pose & Depth Tasks:** Estimación de profundidad y keypoints tridimensionales ($X, Y, Z$). |
| **Identificación de Error** | Encontrar el momento exacto donde el alumno falla en la técnica. | **YOLO + Distancia Coseno:** Comparación matemática de vectores frame a frame para hallar la diferencia máxima. |
| **Cerebro Pedagógico** | Generación de retroalimentación cualitativa comprensible y estructurada. | **Google Gemini API (Condicional):** Solo se invoca si hay errores, asumiendo el rol del Maestro (ES/PT). |
| **Internacionalización (i18n)** | Soporte fluído para alumnos y profesores en Portugués y Español. | **Patrón Strategy (GoF):** Algoritmos de construcción de prompts encapsulados en estrategias polimórficas por idioma. |
| **Multi-Tenancy / Privacidad** | Múltiples sucursales internacionales de la academia "Corpo e Mente". | **Row Level Security (RLS) en PostgreSQL:** Aislamiento de datos por sucursal a nivel de motor de base de datos. |

---

## 2. ARQUITECTURA LÓGICA EN CAPAS Y DIAGRAMA DE PAQUETES (Capítulos 30 y 31)

Se adopta una **Arquitectura en Capas (Layers)** para garantizar alta cohesión y bajo acoplamiento, asegurando que la capa de Dominio no dependa directamente de la interfaz de usuario ni de detalles técnicos específicos de las bibliotecas de IA.

### 2.1 Diagrama de Paquetes UML (Package Diagram)

```mermaid
graph TD
    subgraph UI_Layer ["Capa de Presentación (UI)"]
        UI_Web["corpocmente.ui.web"]
        UI_Mobile["corpocmente.ui.mobile"]
    end

    subgraph Application_Layer ["Capa de Aplicación y Dominio"]
        Controllers["corpocmente.domain.controllers"]
        Services["corpocmente.domain.services"]
        Entities["corpocmente.domain.entities"]
        Strategies["corpocmente.domain.strategies"]
    end

    subgraph Infrastructure_Layer ["Capa de Servicios Técnicos / Infraestructura"]
        Adapters_AI["corpocmente.infrastructure.ai.adapters"]
        Adapters_DB["corpocmente.infrastructure.persistence"]
        Queue_Broker["corpocmente.infrastructure.queue"]
    end


    UI_Web --> Controllers
    UI_Mobile --> Controllers
    Controllers --> Services
    Services --> Entities
    Services --> Strategies
    Services --> Adapters_AI
    Services --> Adapters_DB
    Services --> Queue_Broker

    style UI_Layer fill:#f9f9f9,stroke:#333,stroke-width:1px
    style Application_Layer fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style Infrastructure_Layer fill:#fff3e0,stroke:#f57c00,stroke-width:2px
```

---

## 3. DIAGRAMA DE CLASES DE DISEÑO (DCD - Design Class Diagram) [Capítulo 19]

El DCD traduce el Modelo de Dominio Conceptual en clases de software con visibilidad (`+` público, `-` privado), tipos de datos concretos, firmas de métodos y estereotipos de diseño GRASP/GoF.

```mermaid
classDiagram
    class VideoAnalysisController {
        <<Controller>>
        -TaskQueueManager queueManager
        +solicitarAnalisisTecnica(tecnicaId: UUID, videoPath: String, idioma: String) UUID
        +consultarEstadoEvaluacion(evaluacionId: UUID) EvaluacionDTO
    }

    class IntelligenceAnalysisFacade {
        <<Facade>>
        -YOLOPoseAdapter yoloAdapter
        -QdrantVectorAdapter qdrantAdapter
        -GeminiApiAdapter geminiAdapter
        +ejecutarAnalisisCompleto(videoPath: String, tecnicaId: UUID, tecnicaNombre: String, idioma: String) AnalisisResultDTO
    }

    class IPromptStrategy {
        <<Interface / Strategy>>
        +construirPromptEvaluacion(discrepancias: List~String~) String
    }

    class PortuguesePromptStrategy {
        <<Strategy>>
        +construirPromptEvaluacion(discrepancias: List~String~) String
    }

    class SpanishPromptStrategy {
        <<Strategy>>
        +construirPromptEvaluacion(discrepancias: List~String~) String
    }

    class YOLOPoseAdapter {
        <<Adapter>>
        +extraerKeypoints(videoPath: String) List~EsqueletoBiomecanico~
    }

    class QdrantVectorAdapter {
        <<Adapter>>
        +buscarSimilitudPose(vectorAlumno: List~Float~, tecnicaId: UUID) VectorSearchResultDTO
        +insertarVector(vectorId: UUID, vector: List~Float~, payload: Map) void
    }

    class GeminiApiAdapter {
        <<Adapter>>
        -String apiKey
        +validarEsJiuJitsu(videoPath: String) Boolean
        +generarTextoFeedback(prompt: String, frameImage: String, tecnicaNombre: String) String
    }

    class EsqueletoBiomecanico {
        -List~Point3D~ keypoints133
        -Map~String, Float~ angulosArticulares
        +calcularAnguloArticular(articulacionA: String, articulacionB: String) Float
        +toVectorArray() List~Float~
    }

    class Evaluacion {
        -UUID id
        -UUID alumnoId
        -UUID tecnicaId
        -Float porcentajeSimilitud
        -String feedbackGeminiES
        -String feedbackGeminiPT
        -String estado
        +actualizarResultado(similitud: Float, feedbackES: String, feedbackPT: String) void
        +marcarEstado(nuevoEstado: String) void
    }

    VideoAnalysisController --> IntelligenceAnalysisFacade : delega a través de Cola
    IntelligenceAnalysisFacade --> YOLOPoseAdapter : usa
    IntelligenceAnalysisFacade --> QdrantVectorAdapter : usa
    IntelligenceAnalysisFacade --> GeminiApiAdapter : usa
    IntelligenceAnalysisFacade --> IPromptStrategy : utiliza
    IPromptStrategy <|.. PortuguesePromptStrategy : implementa
    IPromptStrategy <|.. SpanishPromptStrategy : implementa
    YOLOPoseAdapter ..> EsqueletoBiomecanico : crea
```

---

## 4. VISTA DE DESPLIEGUE (DEPLOYMENT VIEW)

Ilustra la distribución física híbrida: la máquina local mantiene la persistencia de datos (PostgreSQL 3NF) y vectores (Qdrant Local) de forma permanente sin riesgo de desconexión, mientras que Google Colab Pro proporciona la potencia GPU para la inferencia pesada (YOLO Pose/Depth + Qwen3-VL Reranker).

**Nota importante sobre el Worker Remoto:** El Worker de cómputo pesado se ejecuta en Google Colab Web. El usuario sube el notebook `colab_worker.template.ipynb` a colab.research.google.com, selecciona un runtime T4 GPU, y expone los endpoints FastAPI mediante túnel ngrok. La URL pública se configura en la variable de entorno `COLAB_TUNNEL_URL` del backend local.

```mermaid
graph LR
    subgraph Local_Machine ["Máquina Local (Persistencia & Servidores)"]
        UI_App["App Frontend (React + Vite)"]
        FastAPI_Node["FastAPI Backend Server"]
        PostgREST_Node["PostgREST API Engine"]
        PostgreSQL_Node[("PostgreSQL DB (3NF + RLS)")]
        Qdrant_Local[("Qdrant Vector DB (Persistente)")]
    end

    subgraph Colab_Worker ["Google Colab Pro (GPU Worker)"]
        Python_Worker["PyTorch Worker Script"]
        YOLO_Engine["YOLO v11/26 (Pose 3D + Depth)"]
    end

    subgraph External_SaaS ["Servicios Cloud SaaS"]
        Gemini_SaaS["Google Gemini API (Cerebro Pedagógico)"]
    end

    UI_App -->|HTTP REST| FastAPI_Node
    UI_App -->|REST / JWT| PostgREST_Node
    PostgREST_Node -->|SQL / RLS| PostgreSQL_Node

    Python_Worker -->|Lee Tareas / HTTP| FastAPI_Node
    Python_Worker -->|Pose 3D + Depth| YOLO_Engine
    Python_Worker -->|Matemática Vectorial| Qdrant_Local
    Python_Worker -->|GenAI Feedback| Gemini_SaaS
    Python_Worker -->|Actualiza Evaluación| PostgREST_Node
```

---

## 5. MAPEO DE DISEÑO A CÓDIGO (Capítulo 20)

Traducción directa de los diagramas de diseño a código fuente en Python (Backend / Worker).

### 5.1 Definición de la Interfaz y Estrategias (Patrón Strategy en Python)

```python
from abc import ABC, abstractmethod
from typing import List

class IPromptStrategy(ABC):
    @abstractmethod
    def construir_prompt_evaluacion(self, discrepancias: List[str]) -> str:
        pass

class PortuguesePromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(self, discrepancias: List[str]) -> str:
        prompt = "Você é um mestre faixa preta de Jiu-Jitsu Brasileiro. "
        prompt += "Analise os seguintes erros biomecânicos detectados na técnica:\n"
        for d in discrepancias:
            prompt += f"- {d}\n"
        prompt += "Forneça instruções claras e corretivas em português."
        return prompt

class SpanishPromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(self, discrepancias: List[str]) -> str:
        prompt = "Eres un maestro cinturón negro de Jiu-Jitsu Brasileño. "
        prompt += "Analiza los siguientes errores biomecánicos detectados en la técnica:\n"
        for d in discrepancias:
            prompt += f"- {d}\n"
        prompt += "Proporciona instrucciones claras y correctivas en español."
        return prompt
```

### 5.2 Fachada de Análisis de IA (Patrón Facade en Python)

```python
class IntelligenceAnalysisFacade:
    def __init__(self, yolo_adapter, qdrant_adapter, gemini_adapter):
        self.yolo = yolo_adapter
        self.qdrant = qdrant_adapter
        self.gemini = gemini_adapter

    def ejecutar_analisis_completo(self, video_path: str, tecnica_id: str, tecnica_nombre: str, idioma: str) -> dict:
        # 1. Extraer esqueleto con YOLO26
        esqueletos_frames = self.yolo.extraer_keypoints(video_path)
        
        # 2. Búsqueda matemática del fotograma con mayor diferencia
        # (Se compara contra la base de referencia en Qdrant)
        resultado_comparacion = self.qdrant.buscar_maxima_diferencia(esqueletos_frames, tecnica_id)
        
        # 3. Dibujar/Resaltar el error en el fotograma (YOLO26)
        frame_resaltado = self.yolo.dibujar_error_en_frame(resultado_comparacion.frame_path, resultado_comparacion.discrepancias)
        
        similitud = resultado_comparacion.score
        UMBRAL_ACEPTABLE = 0.85 # 85% de similitud mínima

        # 4. Lógica Condicional para Gemini
        if similitud >= UMBRAL_ACEPTABLE:
            feedback_texto = "Técnica executada corretamente. Excelente trabalho!" if idioma == 'pt' else "¡Técnica ejecutada correctamente. Excelente trabajo!"
        else:
            # Seleccionar estrategia de idioma y pasar el nombre de la técnica
            strategy = PortuguesePromptStrategy() if idioma == 'pt' else SpanishPromptStrategy()
            prompt = strategy.construir_prompt_evaluacion(tecnica_nombre, resultado_comparacion.discrepancias)
            
            # Generar feedback pedagógico solo para el frame con error resaltado
            feedback_texto = self.gemini.generar_texto_feedback(prompt, frame_resaltado)

        return {
            "similitud": similitud,
            "feedback": feedback_texto
        }
```

---

## 6. CONCLUSIÓN DE LA FASE DE ELABORACIÓN (UP)

Con la publicación de este documento (**SAD**), la especificación del **DCD**, el **Diagrama de Paquetes** y la **Vista de Despliegue**, se da por concluida satisfactoriamente la **Fase de Elaboración del Proceso Unificado (Craig Larman)**.

Todos los riesgos principales (Rate Limits de Gemini, Inferencia pesada sin GPU local, Búsqueda Vectorial, Soporte Multilingüe e Integridad de BD Híbrida) quedan arquitectónicamente mitigados y listos para la **Fase de Construcción**.

---

## 7. ANEXO: MATERIALIZACIÓN FASE DE CONSTRUCCIÓN (Iteraciones C1 y C2)

Conforme a la metodología iterativa, la arquitectura lógica fue llevada a código físico:
- **Separación de SQL:** El esquema lógico de la base de datos se desacopló físicamente en scripts dedicados (`01_schema_3nf.sql`, `02_auth_jwt.sql` y `03_rls_policies.sql`) dentro del directorio `database/`, garantizando una evolución controlada de la capa operacional y su RLS.
- **Implementación del Adaptador YOLO:** La clase `YOLOPoseAdapter` se instanció exitosamente usando la librería `ultralytics` aislando la complejidad vectorial de PyTorch en la capa de Infraestructura, respetando el DCD propuesto.

---

## 8. ANEXO: MATERIALIZACIÓN FASE DE CONSTRUCCIÓN (Iteraciones C3 y C4)

- **Capa de Presentación Web (Iteración C3):**
  - Implementación de la aplicación en React + Vite en `frontend/` desacoplada del Backend.
  - Sistema de tokens de diseño en Vanilla CSS (Tema Oscuro con Rojo Marca `#d01118`, Glassmorphism con `backdrop-filter`).
  - Animación del anillo de progreso biomecánico nativo (`<progress>`) registrando `@property` y `conic-gradient`.
  - Módulo de carga con previsualización en tiempo real del video mediante `URL.createObjectURL`.

- **Filtro Anti-SPAM y Resiliencia HTTP (Iteración C4):**
  - Exposición del endpoint REST `/api/v1/evaluaciones/validar-spam` en FastAPI.
  - **Manejo del Ciclo de Vida Multimodal:** Integración con Google GenAI SDK (`client.files.upload(path=...)`) añadiendo un bucle de espera de estado (`PROCESSING` -> `ACTIVE`).
  - **Patrón Lazy Loading:** Desacoplamiento de la inicialización de adaptadores pesados (`YOLOPoseAdapter` y `QdrantVectorAdapter`) mediante propiedades computadas, evitando fallos de arranque del servidor web cuando las BDs o pesos locales de IA no se encuentran cargados aún.



--- ARCHIVO: ProyectoGrado/docs/DisenoBaseDatos.md ---
# DISEÑO DE BASE DE DATOS HÍBRIDA (RELACIONAL + VECTORIAL)
## SISTEMA DE ANÁLISIS BIOMECÁNICO DE TÉCNICAS DE JIU-JITSU BRASILEÑO (CORPO E MENTE)

---

### 1. FUNDAMENTACIÓN TEÓRICA Y ARQUITECTURA DE DATOS

Siguiendo las directrices metodológicas de **Michael V. Mannino** en *"Database Design, Application Development, and Administration (7th Edition)"*, el diseño de almacenamiento de datos para un sistema multi-sucursal e internacional exige separar los datos operacionales transaccionales de las estructuras de índice especializado de alta dimensión.

#### 1.1 Justificación de la Arquitectura Híbrida
* **Capa Operacional Relacional (PostgreSQL + PostgREST):** Garantiza las propiedades **ACID** (Atomicidad, Consistencia, Aislamiento, Durabilidad), la integridad referencial mediante claves foráneas y la eliminación de anomalías de modificación mediante la normalización hasta la **Tercera Forma Normal (3NF) / BCNF**. La capa PostgREST expone automáticamente un API REST declarativo y seguro con Row Level Security (RLS).
* **Capa Vectorial Especializada (Qdrant Vector DB):** Proporciona almacenamiento óptimo e indexación mediante grafos **HNSW (Hierarchical Navigable Small World)** para los vectores numéricos biomecánicos (133 keypoints de pose YOLO v11/26 y embeddings del modelo Reranker Qwen3-VL).

```
+-----------------------------------------------------------------------+
|                           CAPA DE APLICACIÓN                          |
|                       (Frontend / API Gateway)                        |
+-----------------------------------+-----------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|  PostgREST API Layer  |                       |   Qdrant REST/gRPC    |
+-----------+-----------+                       +-----------+-----------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|  PostgreSQL Database  |                       |  Qdrant Engine (HNSW) |
|  (Datos Operacionales)|                       | (Vectores Biomecánicos|
|   3NF/BCNF + RLS      |<==== UUID Linkage ===>|  + Payloads Mínimos)  |
+-----------------------+                       +-----------------------+
```

---

### 2. MODELO ENTIDAD-RELACIÓN (DER) - POSTGRESQL

```mermaid
erDiagram
    SUCURSALES ||--o{ USUARIOS : "pertenece_a"
    USUARIOS ||--o{ VIDEOS_REFERENCIA : "registra_profesor"
    USUARIOS ||--o{ EVALUACIONES_ALUMNOS : "realiza_alumno"
    TECNICAS ||--o{ VIDEOS_REFERENCIA : "clasifica"
    TECNICAS ||--o{ EVALUACIONES_ALUMNOS : "evalua"
    VIDEOS_REFERENCIA ||--o{ EVALUACIONES_ALUMNOS : "compara_con"

    SUCURSALES {
        uuid id PK
        string nombre
        string pais
        string ciudad
        string direccion
        string idioma_predeterminado
        timestamp fecha_registro
    }

    USUARIOS {
        uuid id PK
        uuid sucursal_id FK
        string nombre_completo
        string email UK
        string password_hash
        string rol
        string idioma_preferido
        timestamp fecha_registro
    }

    TECNICAS {
        uuid id PK
        string nombre
        string nivel_cinturon
    }

    VIDEOS_REFERENCIA {
        uuid id PK
        uuid tecnica_id FK
        uuid profesor_id FK
        string url_video_gcs
        float duracion_segundos
        uuid vector_qdrant_id UK
        timestamp fecha_subida
    }

    EVALUACIONES_ALUMNOS {
        uuid id PK
        uuid alumno_id FK
        uuid tecnica_id FK
        uuid video_referencia_id FK
        string url_video_alumno
        float porcentaje_similitud
        text feedback_gemini_es
        text feedback_gemini_pt
        uuid vector_qdrant_id UK
        string estado
        timestamp fecha_evaluacion
    }
```

---

### 3. ESQUEMA DDL SQL (POSTGRESQL + POSTGREST)

```sql
-- Habilitar extensión para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. TABLA SUCURSALES
CREATE TABLE sucursales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(50) NOT NULL, -- Ej: 'Brasil', 'Colombia'
    ciudad VARCHAR(50) NOT NULL,
    direccion TEXT NOT NULL,
    idioma_predeterminado VARCHAR(5) DEFAULT 'pt' CHECK (idioma_predeterminado IN ('es', 'pt')),
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABLA USUARIOS
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sucursal_id UUID NOT NULL REFERENCES sucursales(id) ON DELETE RESTRICT,
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'profesor', 'alumno')),
    idioma_preferido VARCHAR(5) DEFAULT 'pt' CHECK (idioma_preferido IN ('es', 'pt')),
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. TABLA TÉCNICAS DE JIU-JITSU
CREATE TABLE tecnicas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL,
    nivel_cinturon VARCHAR(20) DEFAULT 'blanco' CHECK (nivel_cinturon IN ('blanco', 'azul', 'morado', 'marron', 'negro'))
);

-- 4. TABLA VIDEOS DE REFERENCIA (PATRÓN DE PROFESORES)
CREATE TABLE videos_referencia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tecnica_id UUID NOT NULL REFERENCES tecnicas(id) ON DELETE RESTRICT,
    profesor_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    url_video_gcs TEXT NOT NULL,
    duracion_segundos NUMERIC(5,2) NOT NULL,
    vector_qdrant_id UUID UNIQUE NOT NULL, -- Enlace 1:1 con Qdrant Point ID
    fecha_subida TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. TABLA EVALUACIONES DE ALUMNOS (CORREGIDA)
CREATE TABLE evaluaciones_alumnos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alumno_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tecnica_id UUID NOT NULL REFERENCES tecnicas(id) ON DELETE RESTRICT,
    video_referencia_id UUID NOT NULL REFERENCES videos_referencia(id) ON DELETE RESTRICT,
    url_video_alumno TEXT NOT NULL,
    porcentaje_similitud NUMERIC(5,2), -- Ej: 87.50%
    feedback_gemini_es TEXT,
    feedback_gemini_pt TEXT,
    vector_qdrant_id UUID UNIQUE, -- Se permite NULL en la creación inicial (asíncrono)
    estado VARCHAR(25) DEFAULT 'procesando' CHECK (estado IN ('procesando', 'en_espera_worker', 'completado', 'invalida', 'error_procesamiento', 'error')),
    fecha_evaluacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ÍNDICES PARA OPTIMIZACIÓN DE CONSULTAS POSTGREST
CREATE INDEX idx_usuarios_sucursal ON usuarios(sucursal_id);
CREATE INDEX idx_evaluaciones_alumno ON evaluaciones_alumnos(alumno_id);
CREATE INDEX idx_evaluaciones_tecnica ON evaluaciones_alumnos(tecnica_id);

-- POLÍTICAS DE SEGURIDAD RLS EXTENDIDAS (Row Level Security PARA POSTGREST)
ALTER TABLE evaluaciones_alumnos ENABLE ROW LEVEL SECURITY;

-- Política 1: El alumno ve sus propias evaluaciones
CREATE POLICY alumno_ver_sus_evaluaciones ON evaluaciones_alumnos
    FOR SELECT USING (alumno_id = current_setting('request.jwt.claim.sub', true)::uuid);

-- Política 2: Profesores y Admins ven evaluaciones de alumnos de su misma sucursal
CREATE POLICY personal_ver_evaluaciones_sucursal ON evaluaciones_alumnos
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM usuarios u_staff
            JOIN usuarios u_alumno ON u_alumno.id = evaluaciones_alumnos.alumno_id
            WHERE u_staff.id = current_setting('request.jwt.claim.sub', true)::uuid
              AND u_staff.sucursal_id = u_alumno.sucursal_id
              AND u_staff.rol IN ('profesor', 'admin')
        )
    );

```

---

### 4. DISEÑO DE COLECCIONES EN QDRANT (VECTOR DB)

En Qdrant se almacenan las firmas matemáticas numéricas extraídas por YOLO v11/26 y Qwen3-VL.

#### 4.1 Colección: `vectores_poses_jiujitsu`
* **Métrica de Distancia:** `Cosine` (Coseno) o `Euclidean` (según normalización de ángulos biomecánicos).
* **Tamaño del Vector:** 128 o 256 dimensiones (Embedding reducido de secuencia de keypoints).
* **Parámetros HNSW:**
  * `m`: 16 (conexiones por nodo).
  * `ef_construct`: 100 (precisión en la construcción del índice).

```json
{
  "name": "vectores_poses_jiujitsu",
  "vectors": {
    "size": 128,
    "distance": "Cosine"
  },
  "hnsw_config": {
    "m": 16,
    "ef_construct": 100
  }
}
```

#### 4.2 Estructura del Payload en Qdrant (Linkage con PostgreSQL)

```json
{
  "id": "c0a80121-863a-4a87-8d91-112233445566",
  "vector": [0.012, -0.451, 0.892, 0.114, "... (128 dims)"],
  "payload": {
    "postgres_id": "c0a80121-863a-4a87-8d91-112233445566",
    "tipo_entidad": "evaluacion_alumno",
    "tecnica_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "sucursal_id": "99887766-5544-3322-1100-aabbccddeeff",
    "num_frames_analizados": 150
  }
}
```

---

### 5. MECANISMO DE SINCRONIZACIÓN Y CONSULTA

1. **Captura y Análisis:** El alumno sube el video mediante la interfaz de la app. PostgREST inserta el registro inicial en `evaluaciones_alumnos` con estado `'procesando'`.
2. **Procesamiento Asíncrono (Google Colab Pro / Worker Python):**
   * YOLO v11/26 extrae la secuencia de coordenadas y ángulos biomecánicos.
   * Se genera el vector numérico definitivo.
   * Se inserta el punto vectorial en **Qdrant** utilizando el mismo `UUID` generado por PostgreSQL.
3. **Búsqueda por Similitud (Qdrant):**
   * Se consulta Qdrant para comparar el vector del alumno con los vectores de la técnica de referencia.
   * Qdrant retorna la distancia métrica / porcentaje de coincidencia biomecánica.
4. **Enriquecimiento con IA (Gemini API):**
   * Con la discrepancia detectada por Qdrant, Gemini genera el reporte cualitativo en **Español** y **Portugués**.
5. **Actualización Relacional:** Se actualiza el registro en `evaluaciones_alumnos` con el porcentaje final, los textos de feedback y estado `'completado'`.

---

### 6. CUMPLIMIENTO DE CRITERIOS MANNINO

| Criterio de Mannino | Implementación en la Arquitectura |
| :--- | :--- |
| **Integridad Referencial** | Garantizada mediante Foreign Keys `ON DELETE RESTRICT/CASCADE` en PostgreSQL. |
| **Normalización (3NF/BCNF)** | Eliminación de redundancia: datos de sucursales y usuarios aislados en tablas dedicadas. |
| **Transaccionalidad ACID** | Manejada por PostgreSQL para cobros, usuarios y cambios de roles. |
| **Rendimiento Vectorial** | Delegado a Qdrant (índices HNSW) sin sobrecargar el motor relacional. |
| **Soporte Multilingüe/Multisucursal** | Tablas relacionales con soporte i18n (`_es`, `_pt`) y filtrado por `sucursal_id`. |



--- ARCHIVO: ProyectoGrado/docs/PlanEvaluacionIteraciones.md ---
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
| C12.7 | Frame crítico resaltado en el reporte |
| C12.8 | Comparación lado a lado: video alumno ↔ video profesor |
| C12.9 | Timeline de keypoints con slider temporal |
| C12.10 | Exportar reporte a PDF |









