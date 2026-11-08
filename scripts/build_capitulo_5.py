# scripts/build_capitulo_5.py
# -*- coding: utf-8 -*-
"""
Generador del Capítulo 5: Análisis y Diseño Orientado a Objetos para docs/ProyectoGrado.md
Siguiendo la metodología de Craig Larman y el patrón BCE (Boundary, Control, Entity).
"""

import sys
from pathlib import Path

def get_capitulo_5_markdown():
    return r"""
# CAPÍTULO V: ANÁLISIS Y DISEÑO ORIENTADO A OBJETOS

El presente capítulo desarrolla la fase de análisis y diseño orientado a objetos del Sistema de Análisis Biomecánico de Jiu-Jitsu Brasileño para la academia "Corpo e Mente", aplicando los patrones y principios de diseño promovidos por Craig Larman en el Proceso Unificado Ágil (*Applying UML and Patterns*).

Para cada caso de uso identificado en la matriz de trazabilidad del Capítulo IV, se construyen cinco artefactos de ingeniería:
1. **Caso de Uso Detallado:** Especificación textual exhaustiva con actores, precondiciones, postcondiciones, secuencia normal, secuencias alternativas y excepciones.
2. **Diagrama de Caso de Uso:** Representación visual de los límites del sistema, actores y relaciones.
3. **Diagrama de Clases de Diseño (Participantes):** Modelado estructural de las clases involucradas organizadas bajo el patrón **BCE (Boundary, Control, Entity)**, especificando sus atributos y métodos esenciales.
4. **Diagrama de Secuencia del Caso de Uso (Patrón BCE):** Modelado dinámico de la interacción temporal y la distribución de responsabilidades entre la capa de Frontera/Interfaz (*Boundary*), la capa de Control/Servicios (*Control*) y la capa de Dominio/Entidades (*Entity*).
5. **Diagrama de Paquetes:** Distribución modular y segregación de dependencias entre las capas arquitectónicas del sistema (Presentación, Aplicación, Dominio e Infraestructura/Persistencia).

---

## 5.1 Caso de Uso 1: Iniciar Sesión y Registro de Usuarios (UC-01)

### 5.1.1 Caso de Uso Detallado
El caso de uso describe cómo cualquier usuario (Alumno, Profesor o Administrador) ingresa sus credenciales para autenticarse, o bien crea una nueva cuenta en el sistema asociándose a una sucursal específica.

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-01** |
| **Nombre** | Iniciar Sesión y Registro de Usuarios |
| **Actores** | **Principal:** Alumno, Profesor, Administrador.<br>**Secundario:** Servicio Criptográfico `bcrypt` / PostgREST Auth. |
| **Descripción** | Permite a un usuario existente acceder a la plataforma validando su identidad de forma segura, o a un usuario nuevo registrar su perfil asignándose a una sucursal física de la academia. |
| **Precondiciones** | 1. La base de datos PostgreSQL y el servicio PostgREST se encuentran operativos.<br>2. El usuario dispone de conexión de red o acceso local al servidor del tatami. |
| **Postcondiciones** | 1. El usuario recibe un token criptográfico JWT firmado (algoritmo HS256) con una validez de 24 horas.<br>2. La interfaz de usuario almacena la sesión de forma persistente y carga la vista acorde al rol (`alumno`, `profesor` o `admin`). |

#### Secuencia Normal (Flujo Básico - Inicio de Sesión)
| Paso | Acción del Actor | Reacción del Sistema |
| :---: | :--- | :--- |
| 1 | El usuario introduce su identificador (`username` o `correo`) y su contraseña en la pantalla de acceso. | La interfaz (*Boundary*) valida en el cliente que los campos no estén vacíos y que el nombre de usuario cumpla la expresión regular `^[a-zA-Z0-9_]{3,30}$` (sin espacios en blanco). |
| 2 | El usuario pulsa el botón "Entrar al Tatami". | La interfaz envía una solicitud HTTP POST al endpoint `/api/v1/auth/login`. |
| 3 | | El controlador de autenticación (*Control*) recibe las credenciales y solicita la búsqueda del usuario a la entidad de persistencia. |
| 4 | | La entidad `Usuario` (*Entity*) recupera el registro correspondiente de PostgreSQL, incluyendo el hash seguro de la contraseña, el rol, la sucursal de pertenencia y el estado de la suscripción. |
| 5 | | El controlador (*Control*) compara la contraseña ingresada con el hash almacenado mediante la función criptográfica `bcrypt.checkpw()`. |
| 6 | | Al ser válidas, el gestor de sesiones (*Control*) genera un token JWT firmado criptográficamente que encapsula el identificador de usuario (`uid`), su rol (`rol`), sucursal (`sucursal_id`) y estado de membresía. |
| 7 | | El sistema retorna el token JWT y los datos del perfil al cliente con código de estado HTTP 200. |
| 8 | | La interfaz almacena el token en el almacenamiento local seguro y redirige al usuario al panel principal correspondiente a su rol. |

#### Secuencias Alternativas
* **2a. Registro de un nuevo usuario:**
  * 2a.1. El usuario selecciona la pestaña "Crear Cuenta", introduce su nombre completo, nombre de usuario deseado, correo, contraseña, rol elegido (`alumno` o `profesor`) y selecciona su sucursal de entrenamiento.
  * 2a.2. El controlador (*Control*) valida que el nombre de usuario no esté repetido en la base de datos.
  * 2a.3. Si el rol es `alumno`, la entidad se inicializa automáticamente con `estado_suscripcion = 'pendiente'`.
  * 2a.4. El sistema encripta la contraseña con `bcrypt`, inserta el registro en PostgreSQL y retorna la confirmación HTTP 201 con el token de sesión inicial.
* **5a. Contraseña incorrecta o usuario inexistente:**
  * 5a.1. El controlador detecta discrepancia en el hash o ausencia de usuario.
  * 5a.2. El sistema retorna un error HTTP 401 (*Unauthorized*) con el mensaje defensivo: *"Credenciales inválidas"*, sin revelar si el error fue el usuario o la contraseña para prevenir enumeración de cuentas.
* **5b. Exceso de intentos fallidos (Defensa contra Fuerza Bruta):**
  * 5b.1. Si una misma dirección IP supera los 10 intentos fallidos en un minuto, el limitador de tasa (*Rate Limiter*) intercepta la solicitud y retorna HTTP 429 (*Too Many Requests*), bloqueando temporalmente nuevos intentos.

#### Excepciones
* **E1. Base de datos no disponible:** El sistema informa amigablemente en pantalla que el servicio de datos está temporalmente inaccesible y solicita intentar más tarde.

---

### 5.1.2 Diagrama de Caso de Uso UC-01
```mermaid
flowchart LR
    subgraph Actores
        A["🥋 Alumno"]
        P["🥋 Profesor"]
        AD["🛡️ Administrador"]
    end

    subgraph Sistema_Corpo_e_Mente ["Plataforma Web Corpo e Mente"]
        UC01["UC-01: Autenticarse / Iniciar Sesión"]
        UC01_Reg["Registrar Nueva Cuenta"]
        UC01_Val["Validar Credenciales y Hash"]
        UC01_JWT["Emitir Token JWT (24h)"]
    end

    A --> UC01
    P --> UC01
    AD --> UC01

    A --> UC01_Reg
    P --> UC01_Reg

    UC01 ..> UC01_Val : <<include>>
    UC01 ..> UC01_JWT : <<include>>
    UC01_Reg ..> UC01_JWT : <<include>>
```

---

### 5.1.3 Diagrama de Clases (Patrón BCE) UC-01
El siguiente diagrama detalla las clases participantes estructuradas bajo el patrón Boundary-Control-Entity:
* **Boundary:** Componentes visuales de React (`LoginView`, `SignupView`) y el router de FastAPI (`AuthRoutes`).
* **Control:** Servicios que gobiernan la autenticación y la sesión (`AuthService`, `SessionManager`, `RateLimiter`).
* **Entity:** Modelos de datos del dominio (`Usuario`, `Sucursal`, `TokenJWT`).

```mermaid
classDiagram
    %% Boundary
    class LoginView {
        +username: String
        +password: String
        +handleSubmit()
        +displayError(msg)
    }

    class AuthRoutes {
        +login(credentials: LoginDTO) Response
        +signup(user_data: SignupDTO) Response
    }

    %% Control
    class AuthService {
        +autenticarUsuario(user_or_email, password) TokenJWT
        +registrarUsuario(data: SignupDTO) Usuario
        +verificarPassword(plain, hashed) Boolean
    }

    class SessionManager {
        +crearTokenJWT(user: Usuario) String
        +validarToken(token: String) Claims
    }

    class RateLimiter {
        +verificarLimiteIP(ip: String) Boolean
    }

    %% Entity
    class Usuario {
        +id: UUID
        +nombre_completo: String
        +username: String
        +password_hash: String
        +rol: RolUsuario
        +sucursal_id: UUID
        +estado_suscripcion: String
        +fecha_expiracion: DateTime
    }

    class Sucursal {
        +id: UUID
        +nombre: String
        +ciudad: String
        +pais: String
    }

    class TokenJWT {
        +access_token: String
        +token_type: String
        +expires_in: Integer
    }

    LoginView ..> AuthRoutes : HTTP POST
    AuthRoutes --> RateLimiter : consulta
    AuthRoutes --> AuthService : delega
    AuthService --> SessionManager : solicita token
    AuthService --> Usuario : consulta / valida
    Usuario "1" --> "1" Sucursal : pertenece_a
    SessionManager ..> TokenJWT : genera
```

---

### 5.1.4 Diagrama de Secuencia BCE UC-01
```mermaid
sequenceDiagram
    autonumber
    actor Usuario as 🥋 Practicante
    participant Boundary as 🖥️ LoginView (Boundary)
    participant API as 🚪 AuthRoutes (Boundary)
    participant RateLimit as 🛡️ RateLimiter (Control)
    participant Control as ⚙️ AuthService (Control)
    participant Session as 🔑 SessionManager (Control)
    participant Entity as 👤 Usuario (Entity)
    participant DB as 🗄️ PostgreSQL (Database)

    Usuario ->> Boundary: Ingresa username y password
    Boundary ->> API: POST /api/v1/auth/login {user, pass}
    API ->> RateLimit: verificarLimiteIP(ip_cliente)
    RateLimit -->> API: Límite OK (< 10 intentos)
    API ->> Control: autenticarUsuario(user, pass)
    Control ->> Entity: buscarPorUsernameOCorreo(user)
    Entity ->> DB: SELECT * FROM usuarios WHERE username = user
    DB -->> Entity: Registro de usuario (hash, rol, sucursal)
    Entity -->> Control: Instancia de Usuario
    Control ->> Control: verificarPassword(pass, hash_bcrypt)
    alt Contraseña Válida
        Control ->> Session: crearTokenJWT(usuario)
        Session -->> Control: Token firmado (claims: uid, rol, sucursal)
        Control -->> API: {token, usuario_info}
        API -->> Boundary: HTTP 200 OK + Payload
        Boundary -->> Usuario: Redirección exitosa a Panel Principal
    else Contraseña Inválida
        Control -->> API: Error de autenticación
        API -->> Boundary: HTTP 401 Unauthorized ("Credenciales incorrectas")
        Boundary -->> Usuario: Muestra alerta de error en pantalla
    end
```

---

### 5.1.5 Diagrama de Paquetes UC-01
```mermaid
graph TD
    subgraph Presentacion ["📦 Capa de Presentación (Frontend)"]
        UI_Login["Login.jsx / Signup.jsx"]
        UI_State["AuthContext.jsx"]
    end

    subgraph Aplicacion ["📦 Capa de Aplicación (Backend API & Control)"]
        API_Auth["auth_routes.py"]
        Ctrl_Auth["AuthService"]
        Ctrl_Session["session_manager.py"]
        Ctrl_Security["rate_limiter.py"]
    end

    subgraph Dominio ["📦 Capa de Dominio (Entidades & Reglas)"]
        Ent_User["Usuario / Roles"]
        Ent_Sucursal["Sucursal"]
    end

    subgraph Infraestructura ["📦 Capa de Infraestructura (Persistencia)"]
        Infra_DB["PostgreSQL / PostgREST"]
        Infra_Crypto["bcrypt / PyJWT"]
    end

    Presentacion --> Aplicacion
    Aplicacion --> Dominio
    Aplicacion --> Infraestructura
    Dominio --> Infraestructura
```

---

## 5.2 Caso de Uso 2: Analizar Técnica y Generar Feedback Biomecánico (UC-02)

### 5.2.1 Caso de Uso Detallado
Es el caso de uso central del proyecto: el alumno sube un video de su ejecución técnica, la Inteligencia Artificial extrae su esqueleto en 3D, lo compara contra el patrón de oro del profesor usando DTW, y genera retroalimentación pedagógica basada en los libros técnicos y las directrices del docente.

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-02** |
| **Nombre** | Analizar Técnica y Generar Feedback Biomecánico |
| **Actores** | **Principal:** Alumno.<br>**Secundario:** YOLO26 Pose/Depth (IA Visión), Qdrant (Base Vectorial), Qwen3-VL (VLM Local en MLX), Profesor (Autor del patrón). |
| **Descripción** | Valida el video subido por el alumno, extrae su estructura esquelética en 3D, calcula la similitud con el profesor de su academia y, si se detectan errores, genera una explicación correctiva citando la teoría oficial. |
| **Precondiciones** | 1. El alumno posee una sesión activa con "Pase de Tatami" vigente (`estado_suscripcion = 'activo'`).<br>2. El profesor seleccionado ha cargado previamente el patrón de referencia de la técnica en la plataforma. |
| **Postcondiciones** | 1. Se registra una nueva `Evaluacion` en PostgreSQL vinculada al alumno, con sucursal congelada históricamente.<br>2. El alumno visualiza su puntuación (0-100%), el video comparativo con articulaciones resaltadas y la corrección pedagógica en su idioma. |

#### Secuencia Normal (Flujo Básico)
| Paso | Acción del Actor | Reacción del Sistema |
| :---: | :--- | :--- |
| 1 | El alumno accede a la vista de evaluación (`VideoUploadView`), selecciona a su Profesor y la Técnica a evaluar (ej. *"Escape de 100 kilos"*). | La interfaz recupera las técnicas disponibles que poseen patrón de oro activo para ese profesor. |
| 2 | El alumno selecciona su archivo de video (.mp4 o .mov) grabado en el tatami y pulsa "Evaluar Mi Técnica". | La interfaz verifica en el navegador que el peso no supere 95 MB para garantizar una transmisión segura por el túnel Cloudflare. |
| 3 | | La interfaz transmite el archivo al backend (`POST /api/v1/evaluaciones/analizar`). |
| 4 | | El filtro Anti-SPAM (*Control*) verifica los primeros fotogramas para asegurar que el video corresponde a una persona practicando artes marciales y no a contenido ajeno. |
| 5 | | El adaptador de visión (*Control*) ejecuta `yolo26n-pose.pt` para localizar los 17 puntos clave anatómicos y `yolo26n-depth.pt` para estimar la profundidad z de cada articulación, generando la serie temporal de esqueletos 3D. |
| 6 | | El controlador consulta el `PatronReferencia` del profesor desde la base de datos relacional y vectorial. |
| 7 | | El motor biomecánico (*Control*) aplica el algoritmo DTW (*Dynamic Time Warping*) para alinear temporalmente ambas secuencias y calcula el porcentaje de similitud matemática (escala 0-100%). |
| 8 | | El motor identifica el fotograma exacto con la máxima discrepancia angular y las articulaciones en falla (ej. *"Rodilla Izquierda"*, *"Cadera"*). |
| 9 | | Al ser la similitud menor al umbral del 85%, el sistema activa el pipeline RAG en dos etapas: `Qwen3-VL-Embedding` recupera los 10 fragmentos más relevantes de Qdrant, y `Qwen3-VL-Reranker` selecciona los 3 más precisos. |
| 10 | | El orquestador ensambla la Ingesta Multimodal Triple (fotograma crítico anotado + fragmentos de manuales + `mensaje_profesor`) e invoca a `Qwen3-VL-Instruct-4B` en Apple MLX. |
| 11 | | El Juez Interno (*LLM-as-a-Judge*) valida que el texto generado tenga fidelidad factual (> 0.85) con las páginas citadas de los manuales. |
| 12 | | El sistema persiste la evaluación en PostgreSQL, congela el `sucursal_id` original del alumno y retorna el resultado completo. |
| 13 | | La interfaz (`FeedbackView`) reproduce el video con los keypoints superpuestos, muestra la nota de similitud y presenta la explicación en el idioma del alumno. |

#### Secuencias Alternativas
* **7a. Similitud alta (>= 85%):**
  * Si la ejecución del alumno coincide en un 85% o más con el profesor, el sistema clasifica la técnica como dominada. Omite el consumo de RAG y VLM, registrando la evaluación con un mensaje de felicitación y refuerzo positivo (*"¡Excelente postura! Tu técnica coincide en un 91% con el estándar del profesor"*).
* **2a. Alumno con Pase de Tatami expirado:**
  * El controlador detecta que la `fecha_expiracion` fue superada o el estado es `pendiente`. Bloquea la subida de video y muestra un aviso informando que debe renovar su pase en la academia.
* **4a. Video no relacionado con Jiu-Jitsu (Anti-SPAM):**
  * El filtro detecta ausencia de figuras humanas o poses incompatibles con deportes de combate. Rechaza la petición con HTTP 422 informando que el video no contiene una técnica reconocible.
* **11a. Falla de fidelidad o tiempo límite en el VLM (Degradación Elegante):**
  * Si el juez de IA detecta alucinaciones o el modelo supera 15 segundos de procesamiento, el sistema activa un *Graceful Fallback*: entrega al alumno el reporte biomecánico numérico exacto (articulaciones críticas y segundo del error) garantizando disponibilidad continua.

---

### 5.2.2 Diagrama de Caso de Uso UC-02
```mermaid
flowchart LR
    subgraph Actores
        AL["🥋 Alumno"]
        YOLO["👁️ YOLOv26 (Pose + Depth)"]
        QDRANT["🗂️ Qdrant Vectorial"]
        QWEN["🧠 Qwen3-VL (MLX)"]
    end

    subgraph Sistema_Analisis ["Módulo de Análisis Biomecánico"]
        UC02["UC-02: Analizar Técnica y Feedback"]
        UC02_Spam["Validar Video Anti-SPAM"]
        UC02_Pose["Extraer Esqueleto 3D (YOLO)"]
        UC02_DTW["Calcular Similitud DTW (0-100%)"]
        UC02_RAG["Recuperar Teoría RAG (Two-Stage)"]
        UC02_VLM["Generar Feedback Pedagógico (Qwen3)"]
        UC02_Judge["Validar Fidelidad (LLM-as-a-Judge)"]
    end

    AL --> UC02
    UC02 ..> UC02_Spam : <<include>>
    UC02 ..> UC02_Pose : <<include>>
    UC02 ..> UC02_DTW : <<include>>
    UC02 ..> UC02_RAG : <<extend>> (Similitud < 85%)
    UC02 ..> UC02_VLM : <<extend>> (Similitud < 85%)
    UC02_VLM ..> UC02_Judge : <<include>>

    UC02_Pose --> YOLO
    UC02_RAG --> QDRANT
    UC02_VLM --> QWEN
```

---

### 5.2.3 Diagrama de Clases (Patrón BCE) UC-02
```mermaid
classDiagram
    %% Boundary
    class VideoUploadView {
        +archivo_video: File
        +profesor_id: UUID
        +tecnica_id: UUID
        +handleUpload()
        +displayProgress()
    }

    class FeedbackView {
        +similitud: Float
        +articulaciones_falla: List
        +feedback_texto: String
        +renderVideoPlayer()
        +renderKeypointsOverlay()
    }

    class EvaluacionesRoutes {
        +analizarTecnica(file, data) ResultadoDTO
    }

    %% Control
    class EvaluacionService {
        +procesarVideo(file, tecnica_id, prof_id, alumno_id) Evaluacion
        +filtrarContenidoAntiSpam(video) Boolean
    }

    class YOLOPoseAdapter {
        +extraerSecuencia3D(video_path) Tensor3D
    }

    class DTWService {
        +alinearSecuencias(seq_alumno, seq_profesor) Float
        +identificarFrameCritico(seq_alumno, seq_prof) Int
    }

    class RAGRetriever {
        +recuperarTeoriaDosEtapas(frame, tecnica_id) List~TeoriaRAG~
    }

    class LocalVLMAdapter {
        +generarConsejo(frame, teoria, mensaje_prof) String
        +auditarFidelidad(texto, teoria) Float
    }

    %% Entity
    class Evaluacion {
        +id: UUID
        +alumno_id: UUID
        +profesor_id: UUID
        +tecnica_id: UUID
        +sucursal_id: UUID
        +porcentaje_similitud: Float
        +frame_error_idx: Integer
        +feedback_texto: String
        +fecha: DateTime
    }

    class PatronReferencia {
        +tecnica_id: UUID
        +profesor_id: UUID
        +secuencia_3d: Tensor
    }

    class TeoriaRAG {
        +texto: String
        +pagina: Integer
        +fuente: String
    }

    VideoUploadView ..> EvaluacionesRoutes : HTTP POST
    EvaluacionesRoutes --> EvaluacionService : orquesta
    EvaluacionService --> YOLOPoseAdapter : extrae poses
    EvaluacionService --> DTWService : calcula distancia
    EvaluacionService --> RAGRetriever : busca teoría
    EvaluacionService --> LocalVLMAdapter : solicita texto IA
    EvaluacionService --> Evaluacion : persiste
    EvaluacionService --> PatronReferencia : compara
    RAGRetriever ..> TeoriaRAG : retorna
    FeedbackView ..> Evaluacion : visualiza
```

---

### 5.2.4 Diagrama de Secuencia BCE UC-02
```mermaid
sequenceDiagram
    autonumber
    actor Alumno as 🥋 Alumno
    participant BoundaryUpload as 🖥️ VideoUploadView (Boundary)
    participant API as 🚪 EvaluacionesRoutes (Boundary)
    participant Control as ⚙️ EvaluacionService (Control)
    participant YOLO as 👁️ YOLOPoseAdapter (Control)
    participant DTW as 📐 DTWService (Control)
    participant RAG as 📚 RAGRetriever (Control)
    participant VLM as 🧠 LocalVLMAdapter (Control)
    participant Entity as 📋 Evaluacion (Entity)
    participant DB as 🗄️ PostgreSQL / Qdrant (Database)
    participant BoundaryFeedback as 🖥️ FeedbackView (Boundary)

    Alumno ->> BoundaryUpload: Selecciona Técnica, Profesor y sube Video.mp4
    BoundaryUpload ->> API: POST /api/v1/evaluaciones/analizar (Multipart Form)
    API ->> Control: procesarVideo(video, tecnica_id, prof_id, alumno_id)
    
    Control ->> Control: validarPaseTatamiActivo(alumno_id)
    Control ->> Control: filtrarContenidoAntiSpam(video)
    
    Control ->> YOLO: extraerSecuencia3D(video_path)
    YOLO -->> Control: Keypoints normalizados (x, y, z, conf)
    
    Control ->> DB: obtenerPatronReferencia(tecnica_id, prof_id)
    DB -->> Control: Secuencia de referencia del profesor
    
    Control ->> DTW: alinearSecuencias(seq_alumno, seq_prof)
    DTW -->> Control: Similitud = 74.5%, FrameCrítico = 142
    
    alt Similitud < 85% (Requiere Corrección Pedagógica)
        Control ->> RAG: recuperarTeoriaDosEtapas(Frame 142, tecnica_id)
        RAG ->> DB: Búsqueda Qdrant (Embedding + Reranker)
        DB -->> RAG: Top 3 páginas de manuales técnicos
        RAG -->> Control: Fragmentos teóricos validados
        
        Control ->> VLM: generarConsejo(Frame 142, teoría, mensaje_profesor)
        VLM -->> Control: Texto explicativo estructurado en ES/PT
        Control ->> VLM: auditarFidelidad(texto, teoría)
        VLM -->> Control: Fidelidad Score = 0.94 (Aprobado)
    else Similitud >= 85%
        Control ->> Control: generarMensajeFelicitacion()
    end
    
    Control ->> Entity: crearEvaluacion(datos, sucursal_congelada)
    Entity ->> DB: INSERT INTO evaluaciones_alumnos (...)
    DB -->> Entity: Confirmación UUID
    
    Control -->> API: ResultadoWorkerDTO
    API -->> BoundaryFeedback: Carga FeedbackView con datos
    BoundaryFeedback -->> Alumno: Muestra reproductor interactivo con articulaciones y consejos
```

---

### 5.2.5 Diagrama de Paquetes UC-02
```mermaid
graph TD
    subgraph Presentacion ["📦 Presentación (Frontend)"]
        P_Upload["VideoUpload.jsx"]
        P_Feedback["FeedbackView.jsx"]
        P_Player["VideoPlayerOverlay.jsx"]
    end

    subgraph Aplicacion ["📦 Aplicación (Backend API & Orquestación)"]
        A_Routes["evaluaciones_routes.py"]
        A_Facade["intelligence_facade.py"]
        A_EvalSvc["EvaluacionService"]
    end

    subgraph Dominio ["📦 Dominio (Algoritmos Biomecánicos & Reglas)"]
        D_DTW["dtw_service.py"]
        D_Norm["pose_normalizer.py"]
        D_EntEval["Evaluacion"]
        D_EntPatron["PatronReferencia"]
    end

    subgraph Infraestructura ["📦 Infraestructura (IA Local & Datos)"]
        I_YOLO["yolo_adapters.py (Ultralytics)"]
        I_VLM["local_vlm_adapter.py (MLX)"]
        I_RAG["rag_reranker.py"]
        I_Qdrant["qdrant_adapter.py"]
        I_PG["PostgreSQL / PostgREST"]
    end

    Presentacion --> Aplicacion
    Aplicacion --> Dominio
    Aplicacion --> Infraestructura
    Dominio --> Infraestructura
```

---

## 5.3 Caso de Uso 3: Gestionar Técnicas y Videos de Referencia (UC-03)

### 5.3.1 Caso de Uso Detallado
Describe cómo un profesor o administrador crea, edita y da de alta las técnicas del catálogo deportivo de la academia, asociando el video demostrativo oficial ("Patrón de Oro").

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-03** |
| **Nombre** | Gestionar Técnicas y Videos de Referencia |
| **Actores** | **Principal:** Profesor, Administrador.<br>**Secundario:** YOLOPoseAdapter, Qdrant. |
| **Descripción** | Permite registrar técnicas en el catálogo y subir videos maestros. El sistema extrae las articulaciones del profesor y las indexa para comparaciones futuras. |
| **Precondiciones** | El usuario debe estar autenticado con rol de `profesor` o `admin`. |
| **Postcondiciones** | La técnica queda activa en el catálogo global y el esqueleto 3D del profesor queda indexado en Qdrant y PostgreSQL. |

#### Secuencia Normal
1. El profesor ingresa a `ProfesorTecnicasView` y pulsa "Nueva Técnica".
2. Introduce el nombre de la técnica (ej. *"Raspado Tijera"*), nivel de cinturón (Blanco, Azul, etc.) y descripción.
3. Carga el archivo de video de su propia ejecución técnica impecable.
4. El controlador (`TecnicasService`) almacena el video en el disco local (`storage/`) y ejecuta `YOLOPoseAdapter`.
5. El sistema extrae y normaliza el esqueleto 3D del profesor a lo largo de todos los fotogramas del video.
6. El sistema guarda la secuencia canónica en PostgreSQL (`patrones_referencia`) y genera vectores indexados en Qdrant (`vectores_poses_jiujitsu`).
7. La interfaz confirma la disponibilidad de la técnica para todos los alumnos de la academia.

---

### 5.3.2 Diagrama de Caso de Uso UC-03
```mermaid
flowchart LR
    P["🥋 Profesor"]
    AD["🛡️ Administrador"]

    subgraph Modulo_Tecnicas ["Gestión de Técnicas"]
        UC03_1["Crear / Editar Técnica en Catálogo"]
        UC03_2["Subir Video de Referencia (Patrón de Oro)"]
        UC03_3["Procesar Esqueleto Canónico (YOLO)"]
        UC03_4["Indexar Patrón en Base Vectorial"]
    end

    P --> UC03_1
    P --> UC03_2
    AD --> UC03_1
    UC03_2 ..> UC03_3 : <<include>>
    UC03_3 ..> UC03_4 : <<include>>
```

---

### 5.3.3 Diagrama de Clases (Patrón BCE) UC-03
```mermaid
classDiagram
    class ProfesorTecnicasView {
        +nombre: String
        +cinturon: String
        +video_file: File
        +handleGuardarTecnica()
    }

    class TecnicasRoutes {
        +crearTecnica(data: TecnicaDTO) Response
        +subirVideoReferencia(id, file) Response
    }

    class TecnicasService {
        +guardarTecnica(data) Tecnica
        +procesarPatronOro(tecnica_id, prof_id, file) PatronReferencia
    }

    class YOLOPoseAdapter {
        +extraerSecuencia3D(path) Tensor
    }

    class Tecnica {
        +id: UUID
        +nombre: String
        +nivel_cinturon: String
        +descripcion: String
    }

    class PatronReferencia {
        +id: UUID
        +tecnica_id: UUID
        +profesor_id: UUID
        +url_video: String
        +secuencia_keypoints: Array
    }

    ProfesorTecnicasView ..> TecnicasRoutes : HTTP POST
    TecnicasRoutes --> TecnicasService : delega
    TecnicasService --> YOLOPoseAdapter : invoca
    TecnicasService --> Tecnica : administra
    TecnicasService --> PatronReferencia : genera
```

---

### 5.3.4 Diagrama de Secuencia BCE UC-03
```mermaid
sequenceDiagram
    autonumber
    actor Prof as 🥋 Profesor
    participant View as 🖥️ ProfesorTecnicasView (Boundary)
    participant API as 🚪 TecnicasRoutes (Boundary)
    participant Svc as ⚙️ TecnicasService (Control)
    participant YOLO as 👁️ YOLOPoseAdapter (Control)
    participant EntTec as 🥋 Tecnica (Entity)
    participant EntPat as 📏 PatronReferencia (Entity)
    participant DB as 🗄️ PostgreSQL / Qdrant (Database)

    Prof ->> View: Ingresa nombre, cinturón y sube VideoMaestro.mp4
    View ->> API: POST /api/v1/tecnicas (Multipart)
    API ->> Svc: procesarPatronOro(nombre, cinturon, video, prof_id)
    Svc ->> EntTec: crear(nombre, cinturon)
    EntTec ->> DB: INSERT INTO tecnicas (...)
    DB -->> EntTec: tecnica_id
    
    Svc ->> YOLO: extraerSecuencia3D(video_temp_path)
    YOLO -->> Svc: Esqueleto normalizado (3D tensor)
    
    Svc ->> EntPat: crearPatron(tecnica_id, prof_id, keypoints)
    EntPat ->> DB: Guardar en PostgreSQL y colecciones Qdrant
    DB -->> Svc: Confirmación de indexación exitosa
    
    Svc -->> API: TecnicaCreadaDTO
    API -->> View: HTTP 201 Created
    View -->> Prof: Notificación: "Técnica y Patrón de Oro guardados correctamente"
```

---

### 5.3.5 Diagrama de Paquetes UC-03
```mermaid
graph TD
    subgraph Presentacion ["Presentación (React)"]
        ProfesorTecnicas["ProfesorTecnicas.jsx"]
    end
    subgraph Aplicacion ["Aplicación (FastAPI)"]
        TecnicasRoutes["tecnicas_routes.py"]
        TecnicasService["tecnicas_service.py"]
    end
    subgraph Dominio ["Dominio"]
        EntTecnica["Tecnica"]
        EntPatron["PatronReferencia"]
    end
    subgraph Infraestructura ["Infraestructura"]
        YOLO["YOLOPoseAdapter"]
        DB_Storage["PostgreSQL / Qdrant"]
    end

    Presentacion --> Aplicacion
    Aplicacion --> Dominio
    Aplicacion --> Infraestructura
    Dominio --> Infraestructura
```

---

## 5.4 Caso de Uso 4: Gestionar Teoría RAG (UC-04)

### 5.4.1 Caso de Uso Detallado
Describe cómo un profesor enriquece el conocimiento de la Inteligencia Artificial subiendo manuales en formato PDF y redactando sus propias recomendaciones pedagógicas (`mensaje_profesor`).

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-04** |
| **Nombre** | Gestionar Teoría RAG y Mensajes del Profesor |
| **Actores** | **Principal:** Profesor.<br>**Secundario:** Qwen3-VL-Embedding (MLX), Qdrant. |
| **Descripción** | Ingesta de manuales en PDF (con texto e imágenes) y notas doctrinales asociadas a una técnica deportiva para nutrir el contexto RAG de la IA. |
| **Precondiciones** | Profesor autenticado; técnica seleccionada existente en la base de datos. |
| **Postcondiciones** | Los fragmentos del manual quedan vectorizados en 2048 dimensiones en Qdrant y el `mensaje_profesor` queda guardado en PostgreSQL. |

#### Secuencia Normal
1. El profesor abre la ventana modal de teoría (`TheoryManagerModal`) en una técnica específica.
2. Escribe una recomendación técnica directa en el campo `mensaje_profesor` (ej. *"Cerrar los codos y elevar la cadera antes de girar"*).
3. Selecciona un manual o libro oficial de Jiu-Jitsu en PDF y pulsa "Procesar Conocimiento".
4. El controlador (`KnowledgeController`) divide el documento en páginas y fragmentos semánticos, preservando diagramas y números de página.
5. El modelo multimodal `Qwen3-VL-Embedding-2B` convierte cada fragmento en un vector denso de 2048 dimensiones.
6. El sistema almacena los vectores en la colección `rag_knowledge` de Qdrant junto con los metadatos de técnica y página.
7. El sistema guarda el texto del profesor en PostgreSQL.
8. La interfaz notifica al docente que la base de conocimientos fue actualizada con éxito.

---

### 5.4.2 Diagrama de Caso de Uso UC-04
```mermaid
flowchart LR
    P["🥋 Profesor"]

    subgraph Modulo_RAG ["Gestión de Teoría RAG"]
        UC04_1["Escribir Mensaje Directo del Docente"]
        UC04_2["Cargar Manual en PDF"]
        UC04_3["Extracción de Texto y Diagramas"]
        UC04_4["Generar Vectores (Qwen3-VL-Embedding)"]
        UC04_5["Almacenar Fragmentos en Qdrant"]
    end

    P --> UC04_1
    P --> UC04_2
    UC04_2 ..> UC04_3 : <<include>>
    UC04_3 ..> UC04_4 : <<include>>
    UC04_4 ..> UC04_5 : <<include>>
```

---

### 5.4.3 Diagrama de Clases (Patrón BCE) UC-04
```mermaid
classDiagram
    class TheoryManagerModal {
        +tecnica_id: UUID
        +mensaje_profesor: String
        +archivo_pdf: File
        +handleGuardarTeoria()
    }

    class ConocimientoRoutes {
        +ingestarManual(tecnica_id, file) Response
        +actualizarMensajeProfesor(tecnica_id, msg) Response
    }

    class KnowledgeController {
        +procesarDocumentoPDF(pdf_path, tecnica_id) Integer
        +guardarMensajeProfesor(tecnica_id, texto) Boolean
    }

    class QwenEmbeddingAdapter {
        +generarEmbeddingMultimodal(texto, imagen) Vector2048
    }

    class TeoriaRAG {
        +id: UUID
        +tecnica_id: UUID
        +texto: String
        +numero_pagina: Integer
        +fuente: String
        +vector_embedding: Array
    }

    TheoryManagerModal ..> ConocimientoRoutes : HTTP POST
    ConocimientoRoutes --> KnowledgeController : delega
    KnowledgeController --> QwenEmbeddingAdapter : vectoriza
    KnowledgeController --> TeoriaRAG : crea
```

---

### 5.4.4 Diagrama de Secuencia BCE UC-04
```mermaid
sequenceDiagram
    autonumber
    actor Prof as 🥋 Profesor
    participant Modal as 🖥️ TheoryManagerModal (Boundary)
    participant API as 🚪 ConocimientoRoutes (Boundary)
    participant Ctrl as ⚙️ KnowledgeController (Control)
    participant MLX as 🧠 QwenEmbeddingAdapter (Control)
    participant Ent as 📖 TeoriaRAG (Entity)
    participant Qdrant as 🗄️ Qdrant Vectorial (Database)
    participant PG as 🗄️ PostgreSQL (Database)

    Prof ->> Modal: Escribe mensaje y selecciona ManualBJJ.pdf
    Modal ->> API: POST /api/v1/conocimiento/ingestar-manual
    API ->> Ctrl: procesarDocumentoPDF(pdf, tecnica_id)
    Ctrl ->> Ctrl: extraerPaginasYDiagramas(pdf)
    loop Por cada página del manual
        Ctrl ->> MLX: generarEmbeddingMultimodal(texto_pag, imagen_pag)
        MLX -->> Ctrl: Vector 2048 dimensiones
        Ctrl ->> Ent: instanciar(tecnica_id, texto, pag, vector)
        Ent ->> Qdrant: INSERT INTO rag_knowledge (vector, payload)
    end
    Ctrl ->> PG: UPDATE tecnicas SET mensaje_profesor = texto WHERE id = tecnica_id
    PG -->> Ctrl: Confirmado
    Ctrl -->> API: {paginas_procesadas: 48, status: "ok"}
    API -->> Modal: HTTP 200 OK
    Modal -->> Prof: Muestra: "Teoría indexada y lista para consultas RAG"
```

---

### 5.4.5 Diagrama de Paquetes UC-04
```mermaid
graph TD
    subgraph Presentacion ["Presentación"]
        Modal["TheoryManagerModal.jsx"]
    end
    subgraph Aplicacion ["Aplicación"]
        API["conocimiento_routes.py"]
        Controller["KnowledgeController"]
    end
    subgraph Dominio ["Dominio"]
        EntTeoria["TeoriaRAG"]
    end
    subgraph Infraestructura ["Infraestructura"]
        Embedding["QwenEmbeddingAdapter (MLX)"]
        Qdrant["Qdrant DB"]
        Postgres["PostgreSQL"]
    end

    Presentacion --> Aplicacion
    Aplicacion --> Dominio
    Aplicacion --> Infraestructura
    Dominio --> Infraestructura
```

---

## 5.5 Caso de Uso 5: Ver Progreso de Alumnos (UC-05)

### 5.5.1 Caso de Uso Detallado
Describe cómo los instructores supervisan la evolución deportiva de sus alumnos, analizando el histórico de evaluaciones, gráficos de rendimiento y los errores biomecánicos más frecuentes.

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-05** |
| **Nombre** | Ver Progreso de Alumnos |
| **Actores** | **Principal:** Profesor, Alumno.<br>**Secundario:** PostgreSQL con Row Level Security (RLS). |
| **Descripción** | Permite visualizar la lista de alumnos de la sede deportiva y su historial de evaluaciones biomecánicas en orden cronológico. |
| **Precondiciones** | Usuario autenticado con rol `profesor` o `alumno`. |
| **Postcondiciones** | La interfaz despliega las métricas de rendimiento filtradas estrictamente por la sucursal autorizada. |

#### Secuencia Normal
1. El profesor hace clic en el menú "Progreso de Alumnos" (`StudentProgressView`).
2. La interfaz envía una solicitud HTTP GET al endpoint `/api/v1/profesor/alumnos`.
3. El controlador (`ProgressController`) recupera el `sucursal_id` del token JWT del profesor.
4. El motor de PostgreSQL aplica Row Level Security (RLS), asegurando que solo se listen alumnos registrados en esa sucursal.
5. El sistema recupera las evaluaciones históricas de cada alumno, calculando el porcentaje promedio de similitud y ordenándolas por fecha.
6. La pantalla presenta tarjetas con la foto, nombre, nivel de cinturón, estado del Pase de Tatami y gráfica de avance técnico.
7. Al hacer clic en un alumno específico, se despliega la lista detallada de evaluaciones con acceso a la reproducción del video y los consejos de IA.

---

### 5.5.2 Diagrama de Caso de Uso UC-05
```mermaid
flowchart LR
    P["🥋 Profesor"]
    A["🥋 Alumno"]

    subgraph Modulo_Progreso ["Módulo de Progreso"]
        UC05_1["Consultar Lista de Alumnos de la Sede"]
        UC05_2["Ver Historial de Evaluaciones"]
        UC05_3["Revisar Feedback de IA y Reproducir Video"]
    end

    P --> UC05_1
    P --> UC05_2
    P --> UC05_3
    A --> UC05_2
    A --> UC05_3
```

---

### 5.5.3 Diagrama de Clases (Patrón BCE) UC-05
```mermaid
classDiagram
    class StudentProgressView {
        +alumnos: List
        +alumno_seleccionado: Usuario
        +cargarAlumnos()
        +verDetalleEvaluacion(id)
    }

    class ProgressRoutes {
        +obtenerAlumnosSucursal() List~UsuarioDTO~
        +obtenerHistorialAlumno(alumno_id) List~EvaluacionDTO~
    }

    class ProgressController {
        +listarAlumnosPorSucursal(sucursal_id) List
        +obtenerHistorialEvaluaciones(alumno_id) List
    }

    class Usuario {
        +id: UUID
        +nombre_completo: String
        +cinturon: String
        +estado_suscripcion: String
    }

    class Evaluacion {
        +id: UUID
        +fecha: DateTime
        +porcentaje_similitud: Float
        +feedback_texto: String
    }

    StudentProgressView ..> ProgressRoutes : HTTP GET
    ProgressRoutes --> ProgressController : delega
    ProgressController --> Usuario : consulta
    ProgressController --> Evaluacion : recupera historial
```

---

### 5.5.4 Diagrama de Secuencia BCE UC-05
```mermaid
sequenceDiagram
    autonumber
    actor Prof as 🥋 Profesor
    participant View as 🖥️ StudentProgressView (Boundary)
    participant API as 🚪 ProgressRoutes (Boundary)
    participant Ctrl as ⚙️ ProgressController (Control)
    participant EntUser as 👤 Usuario (Entity)
    participant EntEval as 📋 Evaluacion (Entity)
    participant DB as 🗄️ PostgreSQL (Database)

    Prof ->> View: Ingresa a "Progreso de Alumnos"
    View ->> API: GET /api/v1/profesor/alumnos (Bearer Token)
    API ->> Ctrl: listarAlumnosPorSucursal(token.sucursal_id)
    Ctrl ->> EntUser: consultarPorSucursal(sucursal_id)
    EntUser ->> DB: SELECT * FROM usuarios WHERE sucursal_id = id AND rol = 'alumno'
    DB -->> EntUser: Lista de alumnos
    
    loop Para cada alumno
        Ctrl ->> EntEval: obtenerUltimasEvaluaciones(alumno.id)
        EntEval ->> DB: SELECT * FROM evaluaciones_alumnos WHERE alumno_id = id
        DB -->> EntEval: Historial de notas y feedbacks
    end
    
    Ctrl -->> API: Listado consolidado con estadísticas
    API -->> View: HTTP 200 OK + JSON
    View -->> Prof: Despliega alumnos, barras de progreso y estado del Pase de Tatami
```

---

### 5.5.5 Diagrama de Paquetes UC-05
```mermaid
graph TD
    subgraph Presentacion ["Presentación"]
        ProgView["StudentProgress.jsx"]
    end
    subgraph Aplicacion ["Aplicación"]
        ProgRoutes["progress_routes.py"]
        ProgCtrl["ProgressController"]
    end
    subgraph Dominio ["Dominio"]
        EntUsuario["Usuario"]
        EntEvaluacion["Evaluacion"]
    end
    subgraph Infraestructura ["Infraestructura"]
        Postgres["PostgreSQL con RLS"]
    end

    Presentacion --> Aplicacion
    Aplicacion --> Dominio
    Aplicacion --> Infraestructura
    Dominio --> Infraestructura
```

---

## 5.6 Caso de Uso 6: Activar Pase de Tatami (UC-06)

### 5.6.1 Caso de Uso Detallado
Describe el control de acceso y monetización física de la academia: tras verificar el pago presencial o por QR del alumno, el profesor activa su membresía por 30 días exactos.

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-06** |
| **Nombre** | Activar Pase de Tatami (Control de Suscripciones) |
| **Actores** | **Principal:** Profesor.<br>**Secundario:** Alumno (Beneficiario). |
| **Descripción** | Otorga 30 días de acceso activo al motor de Inteligencia Artificial a un alumno que realizó el pago de su mensualidad en la recepción. |
| **Precondiciones** | Profesor autenticado; el alumno pertenece a la misma sucursal del profesor y su estado es `pendiente` o `expirado`. |
| **Postcondiciones** | La cuenta del alumno pasa a `estado_suscripcion = 'activo'` y `fecha_expiracion = NOW() + INTERVAL '30 days'`. |

#### Secuencia Normal
1. El alumno realiza el pago de su mensualidad (efectivo o QR) en el mostrador del gimnasio.
2. El profesor accede a `StudentProgressView` en su teléfono celular, localiza al alumno y pulsa el botón "Aprobar Pase de Tatami".
3. La interfaz solicita confirmación y envía una petición `PUT /api/v1/auth/usuarios/{id}/activar-pase`.
4. El controlador (`SubscriptionManager`) verifica que el profesor pertenezca a la misma sucursal física del alumno.
5. La entidad `Usuario` actualiza su registro en PostgreSQL ejecutando:
   `UPDATE usuarios SET estado_suscripcion = 'activo', fecha_expiracion = NOW() + INTERVAL '30 days' WHERE id = alumno_id`.
6. El sistema retorna la confirmación con la fecha exacta de vencimiento.
7. La interfaz del profesor actualiza la insignia del alumno de "Expirado/Pendiente" a "Pase Activo" (verde).
8. A partir de ese instante, el alumno queda habilitado para subir videos y recibir análisis de IA.

---

### 5.6.2 Diagrama de Caso de Uso UC-06
```mermaid
flowchart LR
    P["🥋 Profesor"]

    subgraph Modulo_Pase ["Control de Suscripción: Pase de Tatami"]
        UC06_1["Verificar Pago de Mensualidad"]
        UC06_2["Activar Pase por 30 Días"]
        UC06_3["Cálculo Automático de Fecha de Expiración"]
        UC06_4["Bloqueo Automático al Expirar"]
    end

    P --> UC06_1
    P --> UC06_2
    UC06_2 ..> UC06_3 : <<include>>
    UC06_3 ..> UC06_4 : <<include>>
```

---

### 5.6.3 Diagrama de Clases (Patrón BCE) UC-06
```mermaid
classDiagram
    class StudentProgressView {
        +handleAprobarPase(alumno_id)
        +renderBadgeEstado(estado)
    }

    class AuthRoutes {
        +activarPaseTatami(alumno_id) Response
    }

    class SubscriptionManager {
        +activarMembresia30Dias(profesor_id, alumno_id) Usuario
        +verificarMismaSucursal(prof_id, alumno_id) Boolean
    }

    class Usuario {
        +id: UUID
        +sucursal_id: UUID
        +estado_suscripcion: String
        +fecha_expiracion: DateTime
        +activarPor30Dias()
    }

    StudentProgressView ..> AuthRoutes : HTTP PUT
    AuthRoutes --> SubscriptionManager : coordina
    SubscriptionManager --> Usuario : actualiza estado
```

---

### 5.6.4 Diagrama de Secuencia BCE UC-06
```mermaid
sequenceDiagram
    autonumber
    actor Prof as 🥋 Profesor
    participant View as 🖥️ StudentProgressView (Boundary)
    participant API as 🚪 AuthRoutes (Boundary)
    participant Ctrl as ⚙️ SubscriptionManager (Control)
    participant Ent as 👤 Usuario (Entity)
    participant DB as 🗄️ PostgreSQL (Database)

    Prof ->> View: Pulsa "Aprobar Pase de Tatami" para el Alumno
    View ->> API: PUT /api/v1/auth/usuarios/{alumno_id}/activar-pase (Token Profesor)
    API ->> Ctrl: activarMembresia30Dias(profesor_id, alumno_id)
    Ctrl ->> Ent: verificarSucursal(profesor_id, alumno_id)
    Ent ->> DB: Validar que ambos compartan sucursal_id
    DB -->> Ctrl: Sucursal coincidente (OK)
    
    Ctrl ->> Ent: activarPor30Dias()
    Ent ->> DB: UPDATE usuarios SET estado_suscripcion = 'activo', fecha_expiracion = NOW() + '30 days' WHERE id = alumno_id
    DB -->> Ent: Filas actualizadas (1)
    
    Ctrl -->> API: {nuevo_estado: "activo", fecha_fin: "2026-12-05"}
    API -->> View: HTTP 200 OK
    View -->> Prof: Actualiza interfaz con insignia verde "Pase Activo (30 días)"
```

---

### 5.6.5 Diagrama de Paquetes UC-06
```mermaid
graph TD
    subgraph Presentacion ["Presentación"]
        StudentView["StudentProgress.jsx (Badge Pase)"]
    end
    subgraph Aplicacion ["Aplicación"]
        AuthAPI["auth_routes.py"]
        SubManager["SubscriptionManager"]
    end
    subgraph Dominio ["Dominio"]
        EntUsuario["Usuario (Membresía)"]
    end
    subgraph Infraestructura ["Infraestructura"]
        Postgres["PostgreSQL"]
    end

    Presentacion --> Aplicacion
    Aplicacion --> Dominio
    Aplicacion --> Infraestructura
    Dominio --> Infraestructura
```

---

## 5.7 Caso de Uso 7: Gestionar Sucursales y Coordenadas Geográficas (UC-07)

### 5.7.1 Caso de Uso Detallado
Describe cómo el administrador registra sedes físicas de la academia a nivel nacional o internacional, capturando coordenadas geográficas mediante mapas interactivos de OpenStreetMap.

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-07** |
| **Nombre** | Gestionar Sucursales y Coordenadas Geográficas |
| **Actores** | **Principal:** Administrador.<br>**Secundario:** Servicio Nominatim (OpenStreetMap). |
| **Descripción** | Permite dar de alta, modificar o desactivar sucursales capturando latitud, longitud y dirección automática con costo $0. |
| **Precondiciones** | Administrador autenticado con rol `admin`. |
| **Postcondiciones** | Nueva sucursal registrada en PostgreSQL disponible para asignación de nuevos alumnos y profesores. |

#### Secuencia Normal
1. El administrador ingresa a `BranchManagerView`.
2. Visualiza el mapa de Leaflet centrado en la ciudad actual y pulsa "Registrar Nueva Sede".
3. Hace clic directamente sobre la ubicación del gimnasio en el mapa interactivo o pega un enlace de Google Maps.
4. La interfaz extrae la latitud y longitud del marcador y contacta al servicio de geocodificación inversa Nominatim.
5. El sistema autorellena los campos de país, ciudad y dirección urbana aproximada.
6. El administrador introduce el nombre oficial (ej. *"Corpo e Mente - Sede Central"*) y pulsa "Guardar Sucursal".
7. El controlador valida los datos e inserta la entidad `Sucursal` en PostgreSQL.
8. La nueva sede aparece disponible en el selector de registro de usuarios.

---

### 5.7.2 Diagrama de Caso de Uso UC-07
```mermaid
flowchart LR
    AD["🛡️ Administrador"]
    OSM["🗺️ OpenStreetMap (Nominatim)"]

    subgraph Modulo_Sucursales ["Gestión de Sucursales"]
        UC07_1["Registrar Nueva Sucursal"]
        UC07_2["Seleccionar Punto en Mapa (Leaflet)"]
        UC07_3["Geocodificación Inversa Automática"]
        UC07_4["Editar / Dar de Baja Sede"]
    end

    AD --> UC07_1
    AD --> UC07_4
    UC07_1 ..> UC07_2 : <<include>>
    UC07_2 ..> UC07_3 : <<include>>
    UC07_3 --> OSM
```

---

### 5.7.3 Diagrama de Clases (Patrón BCE) UC-07
```mermaid
classDiagram
    class BranchManagerView {
        +mapaLeaflet: MapInstance
        +latitud: Float
        +longitud: Float
        +nombre: String
        +handleMapClick(lat, lng)
        +guardarSucursal()
    }

    class SucursalesRoutes {
        +listarSucursales() List~SucursalDTO~
        +crearSucursal(data: SucursalDTO) Response
    }

    class BranchController {
        +registrarSucursal(data) Sucursal
        +obtenerDireccionInversa(lat, lng) DireccionDTO
    }

    class NominatimClient {
        +reverseGeocode(lat, lng) JSON
    }

    class Sucursal {
        +id: UUID
        +nombre: String
        +pais: String
        +ciudad: String
        +direccion: String
        +latitud: Float
        +longitud: Float
    }

    BranchManagerView ..> SucursalesRoutes : HTTP POST
    SucursalesRoutes --> BranchController : delega
    BranchController --> NominatimClient : consulta geocodificación
    BranchController --> Sucursal : persiste
```

---

### 5.7.4 Diagrama de Secuencia BCE UC-07
```mermaid
sequenceDiagram
    autonumber
    actor Admin as 🛡️ Administrador
    participant MapView as 🖥️ BranchManagerView (Boundary)
    participant API as 🚪 SucursalesRoutes (Boundary)
    participant Ctrl as ⚙️ BranchController (Control)
    participant OSM as 🌐 NominatimClient (Control)
    participant Ent as 🏢 Sucursal (Entity)
    participant DB as 🗄️ PostgreSQL (Database)

    Admin ->> MapView: Hace clic sobre el mapa en la ubicación del gimnasio
    MapView ->> OSM: reverseGeocode(lat, lng)
    OSM -->> MapView: Retorna {calle: "Av. San Martín", ciudad: "Santa Cruz", pais: "Bolivia"}
    MapView -->> Admin: Muestra campos autorellenados
    
    Admin ->> MapView: Introduce nombre: "Corpo e Mente Norte" y pulsa "Guardar"
    MapView ->> API: POST /api/v1/sucursales {nombre, pais, ciudad, direccion, lat, lng}
    API ->> Ctrl: registrarSucursal(datos)
    Ctrl ->> Ent: instanciar(datos)
    Ent ->> DB: INSERT INTO sucursales (...)
    DB -->> Ent: sucursal_id
    
    Ctrl -->> API: SucursalCreadaDTO
    API -->> MapView: HTTP 201 Created
    MapView -->> Admin: Coloca el marcador oficial en el mapa y actualiza la lista
```

---

### 5.7.5 Diagrama de Paquetes UC-07
```mermaid
graph TD
    subgraph Presentacion ["Presentación"]
        BranchView["BranchManager.jsx (Leaflet)"]
    end
    subgraph Aplicacion ["Aplicación"]
        BranchRoutes["sucursales_routes.py"]
        BranchCtrl["BranchController"]
    end
    subgraph Dominio ["Dominio"]
        EntSucursal["Sucursal"]
    end
    subgraph Infraestructura ["Infraestructura"]
        OSM_Client["Nominatim OpenStreetMap"]
        Postgres["PostgreSQL"]
    end

    Presentacion --> Aplicacion
    Aplicacion --> Dominio
    Aplicacion --> Infraestructura
    Dominio --> Infraestructura
```

---

## 5.8 Caso de Uso 8: Entrar como otro Usuario / Impersonificación (UC-08)

### 5.8.1 Caso de Uso Detallado
Describe la funcionalidad de soporte técnico mediante la cual un administrador toma temporalmente la identidad de un alumno o profesor para diagnosticar incidencias técnicas, manteniendo trazabilidad de auditoría inmutable.

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-08** |
| **Nombre** | Entrar como otro Usuario (Impersonificación de Soporte) |
| **Actores** | **Principal:** Administrador.<br>**Secundario:** Usuario impersonificado (Alumno o Profesor). |
| **Descripción** | Permite al administrador asumir temporalmente el rol y la vista de otro usuario para diagnosticar problemas reportados. Muestra un banner rojo persistente de aviso. |
| **Precondiciones** | El usuario debe poseer rol de `admin` verificado en su token JWT. |
| **Postcondiciones** | 1. Se emite un token JWT temporal con el rol del usuario destino y el claim `impersonator_admin_id`.<br>2. Se inserta un registro inmutable en la tabla de auditoría (`auditoria_impersonacion`). |

#### Secuencia Normal
1. El administrador ingresa al panel de usuarios (`AdminUsersModal`) y selecciona a un alumno o profesor que reportó una falla.
2. Pulsa el botón "Entrar como este Usuario" e introduce su contraseña de administrador para reconfirmar autorización.
3. El controlador (`SessionManager`) valida la contraseña del administrador.
4. El sistema registra el evento en la tabla `auditoria_impersonacion` (fecha, hora, `admin_id`, `usuario_objetivo_id`, IP de origen).
5. El generador de sesiones emite un token JWT que asume el identificador y rol del usuario objetivo, pero incluye en su payload el claim inmutable: `impersonator_admin_id = admin_id`.
6. La interfaz recarga en el contexto del usuario objetivo y activa en el borde superior un banner rojo persistente (`ImpersonationBanner`):
   *"Modo de Soporte Activo: Has iniciado sesión como [Nombre de Usuario]. Haz clic aquí para Salir"*.
7. El administrador reproduce el fallo reportado en la vista real del alumno.
8. Al terminar, el administrador pulsa "Salir de Soporte", destruyendo el token temporal y restaurando su sesión original de Administrador.

---

### 5.8.2 Diagrama de Caso de Uso UC-08
```mermaid
flowchart LR
    AD["🛡️ Administrador"]

    subgraph Modulo_Impersonacion ["Módulo de Impersonificación y Soporte"]
        UC08_1["Seleccionar Usuario a Diagnosticar"]
        UC08_2["Reconfirmar Credenciales de Admin"]
        UC08_3["Registrar Traza en Log de Auditoría"]
        UC08_4["Emitir JWT de Impersonificación"]
        UC08_5["Mostrar Banner Persistente de Advertencia"]
        UC08_6["Restaurar Sesión de Administrador"]
    end

    AD --> UC08_1
    UC08_1 ..> UC08_2 : <<include>>
    UC08_2 ..> UC08_3 : <<include>>
    UC08_3 ..> UC08_4 : <<include>>
    UC08_4 ..> UC08_5 : <<include>>
    AD --> UC08_6
```

---

### 5.8.3 Diagrama de Clases (Patrón BCE) UC-08
```mermaid
classDiagram
    class AdminUsersModal {
        +usuarios: List
        +handleImpersonar(usuario_id)
    }

    class ImpersonationBanner {
        +usuario_nombre: String
        +handleRestaurarAdmin()
    }

    class AuthRoutes {
        +impersonarUsuario(id, admin_pass) Response
        +salirImpersonacion() Response
    }

    class SessionManager {
        +crearTokenImpersonacion(admin, objetivo) String
        +restaurarTokenAdmin(admin_id) String
    }

    class AuditoriaService {
        +registrarEvento(admin_id, target_id, accion) Void
    }

    class RegistroAuditoria {
        +id: UUID
        +admin_id: UUID
        +usuario_objetivo_id: UUID
        +fecha: DateTime
        +ip_origen: String
        +accion: String
    }

    AdminUsersModal ..> AuthRoutes : HTTP POST
    ImpersonationBanner ..> AuthRoutes : HTTP POST
    AuthRoutes --> SessionManager : genera sesión
    AuthRoutes --> AuditoriaService : audita
    AuditoriaService --> RegistroAuditoria : persiste
```

---

### 5.8.4 Diagrama de Secuencia BCE UC-08
```mermaid
sequenceDiagram
    autonumber
    actor Admin as 🛡️ Administrador
    participant Modal as 🖥️ AdminUsersModal (Boundary)
    participant API as 🚪 AuthRoutes (Boundary)
    participant Session as ⚙️ SessionManager (Control)
    participant Audit as 📝 AuditoriaService (Control)
    participant DB as 🗄️ PostgreSQL (Database)
    participant Banner as 🖥️ ImpersonationBanner (Boundary)

    Admin ->> Modal: Selecciona Alumno "Juan" y pulsa "Iniciar Sesión como Usuario"
    Modal ->> API: POST /api/v1/auth/impersonate/{juan_id} {admin_password}
    API ->> Session: validarCredencialesAdmin(admin_id, password)
    Session -->> API: Contraseña de Administrador Correcta
    
    API ->> Audit: registrarAccion(admin_id, juan_id, "INICIO_IMPERSONACION")
    Audit ->> DB: INSERT INTO auditoria_impersonacion (...)
    DB -->> Audit: Confirmado (Log Inmutable)
    
    API ->> Session: crearTokenImpersonacion(admin_id, juan_id)
    Session -->> API: Token JWT (sub: juan_id, rol: alumno, impersonator: admin_id)
    
    API -->> Modal: HTTP 200 OK + Token Temporal
    Modal ->> Banner: Activa Banner Rojo de Soporte
    Banner -->> Admin: Muestra pantalla del Alumno Juan con banner superior persistente
    
    Note over Admin, Banner: El Administrador navega y diagnostica el problema reportado
    
    Admin ->> Banner: Pulsa "Salir de Modo Soporte"
    Banner ->> API: POST /api/v1/auth/unimpersonate
    API ->> Session: restaurarTokenAdmin(admin_id)
    Session -->> API: Token original de Administrador
    API -->> Banner: HTTP 200 OK
    Banner -->> Admin: Destruye sesión temporal y regresa al Panel de Administrador
```

---

### 5.8.5 Diagrama de Paquetes UC-08
```mermaid
graph TD
    subgraph Presentacion ["Presentación"]
        AdminModal["AdminUsersModal.jsx"]
        ImpBanner["ImpersonationBanner.jsx"]
    end
    subgraph Aplicacion ["Aplicación"]
        AuthRoutes["auth_routes.py"]
        SessionMgr["SessionManager"]
        AuditSvc["AuditoriaService"]
    end
    subgraph Dominio ["Dominio"]
        EntUser["Usuario (Roles & Claims)"]
        EntAudit["RegistroAuditoria"]
    end
    subgraph Infraestructura ["Infraestructura"]
        Postgres["PostgreSQL"]
        Crypto["PyJWT"]
    end

    Presentacion --> Aplicacion
    Aplicacion --> Dominio
    Aplicacion --> Infraestructura
    Dominio --> Infraestructura
```
"""

def update_proyecto_grado():
    doc_path = Path("docs/ProyectoGrado.md")
    if not doc_path.exists():
        print(f"Error: {doc_path} no existe.")
        sys.exit(1)

    content = doc_path.read_text(encoding="utf-8")

    # 1. Actualizar la Tabla de Contenido si hace falta
    toc_old = "* **Referencias Bibliográficas**"
    toc_cap5 = """* **CAPÍTULO V: ANÁLISIS Y DISEÑO ORIENTADO A OBJETOS**
  * 5.1 Caso de Uso 1: Iniciar Sesión y Registro de Usuarios (UC-01)
  * 5.2 Caso de Uso 2: Analizar Técnica y Generar Feedback Biomecánico (UC-02)
  * 5.3 Caso de Uso 3: Gestionar Técnicas y Videos de Referencia (UC-03)
  * 5.4 Caso de Uso 4: Gestionar Teoría RAG (UC-04)
  * 5.5 Caso de Uso 5: Ver Progreso de Alumnos (UC-05)
  * 5.6 Caso de Uso 6: Activar Pase de Tatami (UC-06)
  * 5.7 Caso de Uso 7: Gestionar Sucursales y Coordenadas Geográficas (UC-07)
  * 5.8 Caso de Uso 8: Entrar como otro Usuario / Impersonificación (UC-08)
* **Referencias Bibliográficas**"""

    if "CAPÍTULO V:" not in content[:1500]:
        content = content.replace(toc_old, toc_cap5, 1)

    # 2. Insertar Capítulo 5 antes de # Referencias Bibliográficas
    target_split = "# Referencias Bibliográficas"
    if target_split in content:
        parts = content.split(target_split, 1)
        capitulo_5_text = get_capitulo_5_markdown()
        new_content = parts[0] + capitulo_5_text + "\n---\n\n# Referencias Bibliográficas" + parts[1]
    else:
        new_content = content + "\n\n" + get_capitulo_5_markdown()

    doc_path.write_text(new_content, encoding="utf-8")
    print(f"Capítulo 5 generado exitosamente en {doc_path}")

if __name__ == "__main__":
    update_proyecto_grado()

