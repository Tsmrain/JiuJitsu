# scripts/generate_plantuml_diagrams.py
# -*- coding: utf-8 -*-
"""
Genera y renderiza los 16 diagramas de PlantUML (Casos de Uso y Secuencia)
para el Capítulo 5 de docs/ProyectoGrado.md.
"""

import os
import sys
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path("docs/diagramas")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SKINPARAM_COMMON = """
skinparam shadowing false
skinparam monochrome false
skinparam defaultFontName Arial
skinparam roundcorner 6
skinparam ArrowColor #2B6CB0
skinparam ActorBorderColor #C53030
skinparam ActorBackgroundColor #FFF5F5
skinparam BoundaryBorderColor #2B6CB0
skinparam BoundaryBackgroundColor #EBF8FF
skinparam ControlBorderColor #2F855A
skinparam ControlBackgroundColor #F0FFF4
skinparam EntityBorderColor #D69E2E
skinparam EntityBackgroundColor #FFFFF0
skinparam DatabaseBorderColor #4A5568
skinparam DatabaseBackgroundColor #EDF2F7
skinparam UsecaseBorderColor #2B6CB0
skinparam UsecaseBackgroundColor #F7FAFC
"""

DIAGRAMS = {
    # ---------------------------------------------------------
    # UC-01: Autenticarse e Iniciar Sesión / Registro
    # ---------------------------------------------------------
    "cu01_caso_uso": """@startuml
left to right direction
""" + SKINPARAM_COMMON + """

actor "Alumno" as AL
actor "Profesor" as PR
actor "Administrador" as AD

rectangle "Sistema Corpo e Mente - Autenticación" {
    usecase "UC-01: Iniciar Sesión" as UC01
    usecase "Registrar Nueva Cuenta" as UC01_Reg
    usecase "Validar Credenciales y Hash" as UC01_Val
    usecase "Emitir Token JWT (24h)" as UC01_JWT
    usecase "Verificar Límite de Intentos (Rate Limit)" as UC01_Rate
}

AL --> UC01
PR --> UC01
AD --> UC01

AL --> UC01_Reg
PR --> UC01_Reg

UC01 ..> UC01_Val : <<include>>
UC01 ..> UC01_JWT : <<include>>
UC01 ..> UC01_Rate : <<include>>
UC01_Reg ..> UC01_JWT : <<include>>
@enduml""",

    "cu01_secuencia": """@startuml
autonumber
""" + SKINPARAM_COMMON + """

actor "Practicante" as Actor
boundary "LoginView" as View
boundary "AuthRoutes" as API
control "RateLimiter" as Rate
control "AuthService" as Svc
control "SessionManager" as Session
entity "Usuario" as Ent
database "PostgreSQL" as DB

Actor -> View : Ingresar username y password
View -> API : POST /api/v1/auth/login [username, password]
API -> Rate : verificarLimiteIP(ip_cliente)
Rate --> API : Límite de intentos correcto

API -> Svc : autenticarUsuario(username, password)
Svc -> Ent : buscarPorUsername(username)
Ent -> DB : SELECT * FROM usuarios WHERE username = :user
DB --> Ent : Registro con hash, rol y sucursal
Ent --> Svc : Instancia de Usuario

Svc -> Svc : verificarPassword(password, hash_bcrypt)

alt Credenciales Válidas
    Svc -> Session : crearTokenJWT(usuario)
    Session --> Svc : Token firmado con HS256 (uid, rol, sucursal)
    Svc --> API : Token y datos de perfil
    API --> View : HTTP 200 OK [token, user_info]
    View --> Actor : Acceso concedido al panel principal
else Credenciales Inválidas
    Svc --> API : Error de autenticación
    API --> View : HTTP 401 Unauthorized ("Credenciales incorrectas")
    View --> Actor : Alerta de error en pantalla
end
@enduml""",

    # ---------------------------------------------------------
    # UC-02: Analizar Técnica y Generar Feedback Biomecánico
    # ---------------------------------------------------------
    "cu02_caso_uso": """@startuml
left to right direction
""" + SKINPARAM_COMMON + """

actor "Alumno" as AL
actor "YOLOv26 Pose y Depth" as YOLO
actor "Qdrant Vector DB" as QDRANT
actor "Qwen3-VL MLX" as QWEN

rectangle "Sistema Corpo e Mente - Análisis Biomecánico" {
    usecase "UC-02: Analizar Técnica y Generar Feedback" as UC02
    usecase "Validar Video (Filtro Anti-SPAM)" as UC02_Spam
    usecase "Extraer Esqueleto 3D (x, y, z)" as UC02_Pose
    usecase "Calcular Similitud DTW (0-100%)" as UC02_DTW
    usecase "Recuperar Teoría en Dos Etapas (RAG)" as UC02_RAG
    usecase "Generar Corrección con VLM Local" as UC02_VLM
    usecase "Auditar Fidelidad (Juez de IA)" as UC02_Judge
}

AL --> UC02
UC02 ..> UC02_Spam : <<include>>
UC02 ..> UC02_Pose : <<include>>
UC02 ..> UC02_DTW : <<include>>
UC02 ..> UC02_RAG : <<extend>>\\n(Similitud < 85%)
UC02 ..> UC02_VLM : <<extend>>\\n(Similitud < 85%)
UC02_VLM ..> UC02_Judge : <<include>>

UC02_Pose --> YOLO
UC02_RAG --> QDRANT
UC02_VLM --> QWEN
@enduml""",

    "cu02_secuencia": """@startuml
autonumber
""" + SKINPARAM_COMMON + """

actor "Alumno" as Alumno
boundary "VideoUploadView" as ViewUpload
boundary "EvaluacionesRoutes" as API
control "EvaluacionService" as Svc
control "YOLOPoseAdapter" as YOLO
control "DTWService" as DTW
control "RAGRetriever" as RAG
control "LocalVLMAdapter" as VLM
entity "Evaluacion" as Ent
database "PostgreSQL / Qdrant" as DB
boundary "FeedbackView" as ViewFeedback

Alumno -> ViewUpload : Selecciona Técnica, Profesor y Video.mp4
ViewUpload -> API : POST /api/v1/evaluaciones/analizar
API -> Svc : procesarVideo(video, tecnica_id, prof_id, alumno_id)

Svc -> Svc : validarPaseTatamiActivo(alumno_id)
Svc -> Svc : filtrarContenidoAntiSpam(video)

Svc -> YOLO : extraerSecuencia3D(video_temp_path)
YOLO --> Svc : Keypoints y profundidad normalizados (x, y, z)

Svc -> DB : obtenerPatronReferencia(tecnica_id, prof_id)
DB --> Svc : Secuencia canónica del profesor

Svc -> DTW : alinearSecuencias(seq_alumno, seq_profesor)
DTW --> Svc : Similitud = 74.5%, FrameCrítico = 142

alt Similitud < 85% (Requiere Corrección Pedagógica)
    Svc -> RAG : recuperarTeoriaDosEtapas(Frame 142, tecnica_id)
    RAG -> DB : Búsqueda Qdrant (Embedding + Reranker)
    DB --> RAG : Top 3 páginas de manuales técnicos
    RAG --> Svc : Fragmentos teóricos seleccionados
    
    Svc -> VLM : generarConsejo(Frame 142, teoría, mensaje_profesor)
    VLM --> Svc : Texto explicativo estructurado en ES/PT
    Svc -> VLM : auditarFidelidad(texto, teoría)
    VLM --> Svc : Fidelidad Score = 0.94 (Aprobado)
else Similitud >= 85%
    Svc -> Svc : generarMensajeFelicitacion()
end

Svc -> Ent : crearEvaluacion(datos, sucursal_congelada)
Ent -> DB : INSERT INTO evaluaciones_alumnos (...)
DB --> Ent : Confirmación UUID

Svc --> API : ResultadoWorkerDTO
API --> ViewFeedback : Carga FeedbackView con datos
ViewFeedback --> Alumno : Despliega video interactivo, articulaciones y corrección
@enduml""",

    # ---------------------------------------------------------
    # UC-03: Gestionar Técnicas y Videos de Referencia
    # ---------------------------------------------------------
    "cu03_caso_uso": """@startuml
left to right direction
""" + SKINPARAM_COMMON + """

actor "Profesor" as PR
actor "Administrador" as AD
actor "YOLOv26 Pose" as YOLO

rectangle "Sistema Corpo e Mente - Catálogo y Referencias" {
    usecase "UC-03: Gestionar Técnicas del Catálogo" as UC03
    usecase "Subir Video de Referencia (Patrón de Oro)" as UC03_Vid
    usecase "Extraer Esqueleto Canónico 3D" as UC03_Yolo
    usecase "Indexar Secuencia en Base de Datos" as UC03_Idx
}

PR --> UC03
AD --> UC03
PR --> UC03_Vid
UC03_Vid ..> UC03_Yolo : <<include>>
UC03_Yolo ..> UC03_Idx : <<include>>
UC03_Yolo --> YOLO
@enduml""",

    "cu03_secuencia": """@startuml
autonumber
""" + SKINPARAM_COMMON + """

actor "Profesor" as Prof
boundary "ProfesorTecnicasView" as View
boundary "TecnicasRoutes" as API
control "TecnicasService" as Svc
control "YOLOPoseAdapter" as YOLO
entity "Tecnica" as EntTec
entity "PatronReferencia" as EntPat
database "PostgreSQL / Qdrant" as DB

Prof -> View : Ingresa nombre, cinturón y sube VideoReferencia.mp4
View -> API : POST /api/v1/tecnicas (Multipart Form)
API -> Svc : procesarPatronOro(nombre, cinturon, video, prof_id)

Svc -> EntTec : crear(nombre, cinturon)
EntTec -> DB : INSERT INTO tecnicas (...)
DB --> EntTec : tecnica_id

Svc -> YOLO : extraerSecuencia3D(video_temp_path)
YOLO --> Svc : Esqueleto 3D normalizado a lo largo del video

Svc -> EntPat : crearPatron(tecnica_id, prof_id, keypoints)
EntPat -> DB : INSERT INTO patrones_referencia y Qdrant vectores
DB --> Svc : Indexación exitosa

Svc --> API : TecnicaCreadaDTO
API --> View : HTTP 201 Created
View --> Prof : Mensaje: "Técnica y Patrón de Oro guardados con éxito"
@enduml""",

    # ---------------------------------------------------------
    # UC-04: Gestionar Teoría RAG
    # ---------------------------------------------------------
    "cu04_caso_uso": """@startuml
left to right direction
""" + SKINPARAM_COMMON + """

actor "Profesor" as PR
actor "Qwen3-VL Embedding" as QWEN_EMB
actor "Qdrant DB" as QDRANT

rectangle "Sistema Corpo e Mente - Conocimiento RAG" {
    usecase "UC-04: Gestionar Teoría y Manuales RAG" as UC04
    usecase "Escribir Mensaje Directo del Docente" as UC04_Msg
    usecase "Cargar Manual en PDF" as UC04_PDF
    usecase "Extracción de Texto y Diagramas" as UC04_Extract
    usecase "Generar Vectores (2048 dimensiones)" as UC04_Emb
    usecase "Indexar en Colección rag_knowledge" as UC04_Store
}

PR --> UC04
UC04 ..> UC04_Msg : <<include>>
UC04 ..> UC04_PDF : <<include>>
UC04_PDF ..> UC04_Extract : <<include>>
UC04_Extract ..> UC04_Emb : <<include>>
UC04_Emb ..> UC04_Store : <<include>>

UC04_Emb --> QWEN_EMB
UC04_Store --> QDRANT
@enduml""",

    "cu04_secuencia": """@startuml
autonumber
""" + SKINPARAM_COMMON + """

actor "Profesor" as Prof
boundary "TheoryManagerModal" as Modal
boundary "ConocimientoRoutes" as API
control "KnowledgeController" as Ctrl
control "QwenEmbeddingAdapter" as MLX
entity "TeoriaRAG" as Ent
database "PostgreSQL / Qdrant" as DB

Prof -> Modal : Escribe mensaje y selecciona ManualBJJ.pdf
Modal -> API : POST /api/v1/conocimiento/ingestar-manual
API -> Ctrl : procesarDocumentoPDF(pdf, tecnica_id)
Ctrl -> Ctrl : extraerPaginasYDiagramas(pdf)

loop Por cada página del manual
    Ctrl -> MLX : generarEmbeddingMultimodal(texto_pag, imagen_pag)
    MLX --> Ctrl : Vector numérico de 2048 dimensiones
    Ctrl -> Ent : instanciar(tecnica_id, texto, pag, vector)
    Ent -> DB : INSERT INTO Qdrant(rag_knowledge)
end

Ctrl -> DB : UPDATE tecnicas SET mensaje_profesor = :texto WHERE id = :tecnica_id
DB --> Ctrl : Confirmación en base de datos

Ctrl --> API : [paginas_procesadas: 48, status: "ok"]
API --> Modal : HTTP 200 OK
Modal --> Prof : Notificación: "Teoría indexada y lista para consultas RAG"
@enduml""",

    # ---------------------------------------------------------
    # UC-05: Ver Progreso de Alumnos
    # ---------------------------------------------------------
    "cu05_caso_uso": """@startuml
left to right direction
""" + SKINPARAM_COMMON + """

actor "Profesor" as PR
actor "Alumno" as AL

rectangle "Sistema Corpo e Mente - Progreso y Evaluaciones" {
    usecase "UC-05: Ver Progreso de Alumnos" as UC05
    usecase "Consultar Lista de Alumnos de la Sede" as UC05_List
    usecase "Ver Línea de Tiempo de Evaluaciones" as UC05_Time
    usecase "Reproducir Video con Corrección de IA" as UC05_Play
}

PR --> UC05
PR --> UC05_List
PR --> UC05_Time
PR --> UC05_Play

AL --> UC05_Time
AL --> UC05_Play
@enduml""",

    "cu05_secuencia": """@startuml
autonumber
""" + SKINPARAM_COMMON + """

actor "Profesor" as Prof
boundary "StudentProgressView" as View
boundary "ProgressRoutes" as API
control "ProgressController" as Ctrl
entity "Usuario" as EntUser
entity "Evaluacion" as EntEval
database "PostgreSQL (RLS)" as DB

Prof -> View : Ingresa a "Progreso de Alumnos"
View -> API : GET /api/v1/profesor/alumnos (Bearer Token)
API -> Ctrl : listarAlumnosPorSucursal(token.sucursal_id)

Ctrl -> EntUser : consultarPorSucursal(sucursal_id)
EntUser -> DB : SELECT * FROM usuarios WHERE sucursal_id = :id AND rol = 'alumno'
DB --> EntUser : Lista de alumnos de la sede

loop Por cada alumno
    Ctrl -> EntEval : obtenerUltimasEvaluaciones(alumno.id)
    EntEval -> DB : SELECT * FROM evaluaciones_alumnos WHERE alumno_id = :id ORDER BY fecha DESC
    DB --> EntEval : Historial con notas y feedbacks
end

Ctrl --> API : Listado consolidado con estadísticas
API --> View : HTTP 200 OK + JSON
View --> Prof : Despliega alumnos, métricas de similitud y estado del Pase de Tatami
@enduml""",

    # ---------------------------------------------------------
    # UC-06: Activar Pase de Tatami
    # ---------------------------------------------------------
    "cu06_caso_uso": """@startuml
left to right direction
""" + SKINPARAM_COMMON + """

actor "Profesor" as PR

rectangle "Sistema Corpo e Mente - Pase de Tatami" {
    usecase "UC-06: Activar Pase de Tatami (30 Días)" as UC06
    usecase "Verificar Pago en Recepción (Efectivo/QR)" as UC06_Pay
    usecase "Calcular Fecha de Expiración (+30 días)" as UC06_Calc
    usecase "Actualizar Estado a 'activo'" as UC06_Act
    usecase "Bloqueo Automático al Expirar" as UC06_Block
}

PR --> UC06
UC06 ..> UC06_Pay : <<include>>
UC06 ..> UC06_Calc : <<include>>
UC06 ..> UC06_Act : <<include>>
UC06 ..> UC06_Block : <<include>>
@enduml""",

    "cu06_secuencia": """@startuml
autonumber
""" + SKINPARAM_COMMON + """

actor "Profesor" as Prof
boundary "StudentProgressView" as View
boundary "AuthRoutes" as API
control "SubscriptionManager" as Ctrl
entity "Usuario" as Ent
database "PostgreSQL" as DB

Prof -> View : Pulsa botón "Aprobar Pase de Tatami" para el alumno
View -> API : PUT /api/v1/auth/usuarios/{alumno_id}/activar-pase (Token Profesor)
API -> Ctrl : activarMembresia30Dias(profesor_id, alumno_id)

Ctrl -> Ent : verificarMismaSucursal(profesor_id, alumno_id)
Ent -> DB : Validar coincidencia de sucursal_id
DB --> Ctrl : Sucursal coincide (Autorizado)

Ctrl -> Ent : activarPor30Dias()
Ent -> DB : UPDATE usuarios SET estado_suscripcion = 'activo', fecha_expiracion = NOW() + '30 days' WHERE id = :alumno_id
DB --> Ent : Filas actualizadas = 1

Ctrl --> API : [nuevo_estado: "activo", fecha_expiracion: "2026-12-05"]
API --> View : HTTP 200 OK
View --> Prof : Cambia la insignia del alumno a "Pase Activo (30 días)" (Verde)
@enduml""",

    # ---------------------------------------------------------
    # UC-07: Gestionar Sucursales y Coordenadas Geográficas
    # ---------------------------------------------------------
    "cu07_caso_uso": """@startuml
left to right direction
""" + SKINPARAM_COMMON + """

actor "Administrador" as AD
actor "OpenStreetMap (Nominatim)" as OSM

rectangle "Sistema Corpo e Mente - Gestión de Sedes" {
    usecase "UC-07: Gestionar Sucursales y Ubicación" as UC07
    usecase "Seleccionar Ubicación en Mapa (Leaflet)" as UC07_Map
    usecase "Geocodificación Inversa Automática" as UC07_Geo
    usecase "Guardar Coordenadas y Dirección" as UC07_Save
    usecase "Asignar Alumnos y Profesores a la Sede" as UC07_Assign
}

AD --> UC07
UC07 ..> UC07_Map : <<include>>
UC07_Map ..> UC07_Geo : <<include>>
UC07 ..> UC07_Save : <<include>>
UC07 ..> UC07_Assign : <<extend>>

UC07_Geo --> OSM
@enduml""",

    "cu07_secuencia": """@startuml
autonumber
""" + SKINPARAM_COMMON + """

actor "Administrador" as Admin
boundary "BranchManagerView" as MapView
boundary "SucursalesRoutes" as API
control "BranchController" as Ctrl
control "NominatimClient" as OSM
entity "Sucursal" as Ent
database "PostgreSQL" as DB

Admin -> MapView : Hace clic sobre el mapa interactivo en la ubicación del gimnasio
MapView -> OSM : reverseGeocode(latitud, longitud)
OSM --> MapView : Retorna [calle, ciudad, pais]
MapView --> Admin : Muestra formulario con dirección autocompletada

Admin -> MapView : Introduce nombre de sede y pulsa "Guardar Sucursal"
MapView -> API : POST /api/v1/sucursales [nombre, pais, ciudad, direccion, lat, lng]
API -> Ctrl : registrarSucursal(datos)
Ctrl -> Ent : instanciar(datos)
Ent -> DB : INSERT INTO sucursales (...)
DB --> Ent : sucursal_id confirmado

Ctrl --> API : SucursalCreadaDTO
API --> MapView : HTTP 201 Created
MapView --> Admin : Despliega el marcador oficial en el mapa y añade la sede al catálogo
@enduml""",

    # ---------------------------------------------------------
    # UC-08: Entrar como otro Usuario / Impersonificación
    # ---------------------------------------------------------
    "cu08_caso_uso": """@startuml
left to right direction
""" + SKINPARAM_COMMON + """

actor "Administrador" as AD

rectangle "Sistema Corpo e Mente - Soporte Técnico" {
    usecase "UC-08: Entrar como otro Usuario (Impersonar)" as UC08
    usecase "Reconfirmar Clave de Administrador" as UC08_Auth
    usecase "Registrar Traza en Log de Auditoría" as UC08_Audit
    usecase "Emitir Token JWT con Identidad Asumida" as UC08_JWT
    usecase "Activar Banner Rojo de Advertencia" as UC08_Banner
    usecase "Restaurar Sesión Original de Admin" as UC08_Restore
}

AD --> UC08
UC08 ..> UC08_Auth : <<include>>
UC08 ..> UC08_Audit : <<include>>
UC08 ..> UC08_JWT : <<include>>
UC08 ..> UC08_Banner : <<include>>
AD --> UC08_Restore
@enduml""",

    "cu08_secuencia": """@startuml
autonumber
""" + SKINPARAM_COMMON + """

actor "Administrador" as Admin
boundary "AdminUsersModal" as Modal
boundary "AuthRoutes" as API
control "SessionManager" as Session
control "AuditoriaService" as Audit
database "PostgreSQL" as DB
boundary "ImpersonationBanner" as Banner

Admin -> Modal : Selecciona al Alumno "Juan" y pulsa "Iniciar Sesión como Usuario"
Modal -> API : POST /api/v1/auth/impersonate/{juan_id} [admin_password]
API -> Session : validarCredencialesAdmin(admin_id, password)
Session --> API : Contraseña de Administrador Correcta

API -> Audit : registrarEvento(admin_id, juan_id, "INICIO_IMPERSONACION")
Audit -> DB : INSERT INTO auditoria_impersonacion (...)
DB --> Audit : Registro inmutable guardado

API -> Session : crearTokenImpersonacion(admin_id, juan_id)
Session --> API : Token JWT temporal (sub: juan_id, rol: alumno, impersonator: admin_id)

API --> Modal : HTTP 200 OK + Token Temporal
Modal -> Banner : Carga la vista del Alumno y activa Banner Rojo
Banner --> Admin : Muestra pantalla del Alumno con aviso superior de soporte

Note over Admin, Banner : El Administrador navega y diagnostica la falla reportada

Admin -> Banner : Pulsa "Salir de Modo Soporte"
Banner -> API : POST /api/v1/auth/unimpersonate
API -> Session : restaurarTokenAdmin(admin_id)
Session --> API : Token original de Administrador restaurado
API --> Banner : HTTP 200 OK
Banner --> Admin : Destruye sesión temporal y regresa al panel de Administrador
@enduml""",
}

def render_plantuml(name: str, puml_code: str):
    png_path = OUTPUT_DIR / f"{name}.png"
    print(f"Renderizando {name}...", end=" ")
    
    # Intentar con Kroki
    try:
        req = urllib.request.Request(
            "https://kroki.io/plantuml/png",
            data=puml_code.encode("utf-8"),
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            }
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            png_bytes = response.read()
            png_path.write_bytes(png_bytes)
            print(f"[OK] {len(png_bytes)} bytes guardados en {png_path}")
            return True
    except Exception as e:
        print(f"[Fallo Kroki: {e}]. Intentando servidor PlantUML oficial...", end=" ")
        
    # Fallback con plantuml.com usando codificación deflate
    try:
        import zlib
        # Codificación PlantUML estándar
        compressed = zlib.compress(puml_code.encode("utf-8"))[2:-4]
        # Mapeo PlantUML
        mapping = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
        res = []
        for i in range(0, len(compressed), 3):
            b1 = compressed[i]
            b2 = compressed[i+1] if i+1 < len(compressed) else 0
            b3 = compressed[i+2] if i+2 < len(compressed) else 0
            res.append(mapping[b1 >> 2])
            res.append(mapping[((b1 & 0x3) << 4) | (b2 >> 4)])
            res.append(mapping[((b2 & 0xF) << 2) | (b3 >> 6)])
            res.append(mapping[b3 & 0x3F])
        encoded = "".join(res)
        url = f"http://www.plantuml.com/plantuml/png/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            png_bytes = response.read()
            png_path.write_bytes(png_bytes)
            print(f"[OK Fallback] {len(png_bytes)} bytes guardados en {png_path}")
            return True
    except Exception as e2:
        print(f"[ERROR Total: {e2}]")
        return False

def main():
    exitos = 0
    for name, puml_code in DIAGRAMS.items():
        if render_plantuml(name, puml_code):
            exitos += 1
    print(f"\nTotal renderizados: {exitos} de {len(DIAGRAMS)}")

if __name__ == "__main__":
    main()
