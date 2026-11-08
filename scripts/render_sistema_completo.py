# scripts/render_sistema_completo.py
# -*- coding: utf-8 -*-
"""
Renderiza los 3 diagramas del sistema completo a PNG usando Kroki / PlantUML.
"""

import urllib.request
import zlib
from pathlib import Path

OUTPUT_DIR = Path("docs/diagramas")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DIAGRAMS = {
    "sistema_completo_actividad": """@startuml Diagrama_Actividad_Sistema_Completo
title Diagrama de Actividad con Carriles — Flujo Completo de Análisis Biomecánico (UC-02)

skinparam shadowing false
skinparam defaultFontName Arial
skinparam roundcorner 8
skinparam ArrowColor #2B6CB0
skinparam ActivityBorderColor #2B6CB0
skinparam ActivityBackgroundColor #F7FAFC
skinparam ActivityDiamondBorderColor #C53030
skinparam ActivityDiamondBackgroundColor #FFF5F5

|#E6F3FF|👤 Alumno|
start
:Iniciar sesión en la plataforma\\n(username o email + contraseña);
:Seleccionar Instructor de su sucursal;
:Seleccionar Técnica a evaluar;
:Grabar y seleccionar video de ejecución;

|#FFF3E0|🖥️ Frontend (React 19 + Vite Proxy)|
:Validar peso del archivo (<95 MB);
:Enviar video a POST /evaluaciones/validar-spam;

|#F0FFF4|⚙️ Backend (FastAPI)|
:Verificar JWT y Pase de Tatami activo;
if (¿Suscripción activa?) then (No)
  :Responder HTTP 403 Forbidden;
  |#E6F3FF|👤 Alumno|
  :Ver mensaje de Pase expirado;
  stop
else (Sí)
endif

|#FFEBEE|👁️ IA de Visión (YOLO + ViCoS)|
:Extraer primeras muestras de frames;
:Clasificador ViCoS MLP (16 posiciones);
if (¿Es Jiu-Jitsu? ratio >= 0.60) then (No)
  |#F0FFF4|⚙️ Backend (FastAPI)|
  :Rechazar HTTP 422;
  |#E6F3FF|👤 Alumno|
  :Ver "Video no es de BJJ";
  stop
else (Sí)
endif

|#F0FFF4|⚙️ Backend (FastAPI)|
:Guardar video temporal en /tmp/corpocmente_videos;
:POST /evaluaciones/primer-frame (extracción inicial);

|#FFEBEE|👁️ IA de Visión (YOLO + ViCoS)|
:YOLO26n-pose sobre frame inicial;
:Deduplicar bboxes (IoU > 0.50, quimeras, reflejos < 10%);

|#F0FFF4|⚙️ Backend (FastAPI)|
:Crear SessionStateManager (estado=CREATED);

|#FFF3E0|🖥️ Frontend (React 19 + Vite Proxy)|
if (¿Cuántas personas detectadas?) then (= 1)
  :Mostrar "¿Eres tú en el video?";
else (>= 2)
  |#E6F3FF|👤 Alumno|
  :Seleccionar silueta interactiva (bounding box);
endif

|#F0FFF4|⚙️ Backend (FastAPI)|
:POST /evaluaciones/{session_id}/seleccionar-persona\\n(estado=PERSONA_SELECTED);
:POST /evaluaciones/analizar;
:Crear registro Evaluacion (estado='procesando');
:Congelar sucursal_id histórico del alumno;

|#FFEBEE|👁️ IA de Visión (YOLO + ViCoS)|
:Extraer secuencia temporal 3D por persona;
:Tracking competitivo multi-atleta (IoU + proximidad);
:Opcional: depth-map para resolver oclusiones;

|#FFF9C4|🧠 IA de Conocimiento (DTW + Qwen)|
:PoseNormalizer → vector canónico de 46 dims\\n(34 posiciones + 12 ángulos);
:DTW multidimensional (dtaidistance);

|#E8F5E9|🗄️ Persistencia (PostgreSQL + Qdrant)|
:Recuperar secuencia del patrón activo\\n(get_patron_activo);
:SELECT patron_activo_id + Qdrant scroll;

|#FFF9C4|🧠 IA de Conocimiento (DTW + Qwen)|
:Alinear secuencias (maestro vs alumno);
:Calcular similitud (0-100%);
:Identificar frame crítico + articulaciones;

if (¿Similitud < 85.0%?) then (Sí — requiere corrección)
  |#FFF9C4|🧠 IA de Conocimiento (DTW + Qwen)|
  :Qwen3-VL-Embedding-2B (MLX):\\nvectorizar frame crítico + query textual\\n(2048 dims);
  
  |#E8F5E9|🗄️ Persistencia (PostgreSQL + Qdrant)|
  :Qdrant búsqueda híbrida Dense + BM25:
  :Retornar top-20 candidatos filtrados por técnica_id\\n+ alcance='global';
  
  |#FFF9C4|🧠 IA de Conocimiento (DTW + Qwen)|
  :Qwen3-VL-Reranker-2B (Cross-Encoder):
  :Seleccionar top-3 fragmentos;
  :Incluir mensaje_profesor (instructor_message);
  
  :Qwen3-VL-Instruct-4B (MLX 4-bit):
  :Generar corrección JSON {summary, correction}
  :en idioma del alumno (ES/PT/EN);
  
  :LLM-as-a-Judge (fidelidad factual);
  
  if (¿Faithfulness >= 0.85?) then (Sí)
    :Aprobar respuesta pedagógica;
  else (No)
    :Activar Graceful Fallback;
    :Reporte biomecánico numérico\\nsin texto generativo;
  endif
else (No — técnica dominada)
  |#FFF9C4|🧠 IA de Conocimiento (DTW + Qwen)|
  :Generar mensaje de felicitación;
endif

|#F0FFF4|⚙️ Backend (FastAPI)|
:Generar frame crítico anotado (OpenCV)\\narticulaciones en rojo + banner técnico;
:Guardar meta_{id}.json con timestamp_error_segundos;

|#E8F5E9|🗄️ Persistencia (PostgreSQL + Qdrant)|
:UPDATE evaluaciones_alumnos
:estado='completado', porcentaje_similitud;
:Registrar feedback en tabla;

|#FFF3E0|🖥️ Frontend (React 19 + Vite Proxy)|
:Polling GET /evaluaciones/{id} cada 3s;

|#F0FFF4|⚙️ Backend (FastAPI)|
:Leer meta_{id}.json (timestamp + articulaciones);
:Traducir nombres de articulaciones al idioma;
:Retornar JSON con video URLs + feedback;

|#FFF3E0|🖥️ Frontend (React 19 + Vite Proxy)|
:Renderizar FeedbackView:
:Video Maestro + Video Alumno\\n+ Tarjeta IA + Enlace YouTube + Modal Frame;

|#E6F3FF|👤 Alumno|
:Revisar feedback y saltar al segundo del error;
:Ver articulaciones afectadas en modal;

stop

@enduml""",

    "sistema_completo_clases": """@startuml Diagrama_Clases_Sistema_Completo
title Diagrama de Clases del Sistema Completo — Corpo e Mente BJJ

skinparam shadowing false
skinparam defaultFontName Arial
skinparam roundcorner 8
skinparam ArrowColor #2B6CB0
skinparam ClassBorderColor #2B6CB0
skinparam ClassBackgroundColor #F7FAFC
skinparam ClassHeaderBackgroundColor #EBF8FF
skinparam ClassFontStyle bold

'======================================================
' CAPA DE FRONTERA (BOUNDARY) - FRONTEND
'======================================================
package "🌐 Capa de Presentación (Frontend React 19)" as Frontend {

  class App <<Boundary>> {
    +user: Usuario
    +idioma: String
    +appState: State
    +handleUploadStart(data)
    +handleLanguageChange(lang)
    +onImpersonate(user, admin)
  }

  class LoginModal <<Boundary>> {
    +loginUserOrEmail: String
    +loginPassword: String
    +signupRol: String
    +handleLoginSubmit()
    +handleSignupSubmit()
  }

  class VideoUpload <<Boundary>> {
    +profesores: List
    +tecnicas: List
    +selectedFile: File
    +sessionData: Session
    +handleFile(file)
    +handleSubmit()
    +handleDrag(event)
  }

  class FeedbackView <<Boundary>> {
    +result: AnalisisResultDTO
    +showFrameModal: Boolean
    +renderMarkdownFeedback()
    +jumpToError(timestamp)
    +openFrameModal()
  }

  class StudentProgress <<Boundary>> {
    +evaluaciones: List
    +fetchEvaluaciones()
    +renderVideoPlayer()
  }

  class LibraryView <<Boundary>> {
    +query: String
    +resultados: List
    +activeTab: String
    +handleSearch()
    +fetchManuales()
  }

  class ProfesorTecnicas <<Boundary>> {
    +alumnos: List
    +tecnicas: List
    +pendientes: List
    +handleActivarPase(alumno_id)
    +handleGuardarTecnica()
  }

  class AdminSucursales <<Boundary>> {
    +sucursales: List
    +usuarios: List
    +handleGoogleMapsUrlChange(url)
    +handleImpersonate(user_id)
  }

  class TheoryManagerModal <<Boundary>> {
    +tecnica_id: UUID
    +chunks: List
    +mensaje_profesor: String
    +handleDeleteAll()
  }

  class SelectorPersonaVideo <<Boundary>> {
    +sessionData: Session
    +selectedPersonaIdx: Int
    +onSelect(idx)
  }
}

'======================================================
' CAPA DE FRONTERA (BOUNDARY) - BACKEND API
'======================================================
package "🚪 Capa de Frontera (API FastAPI)" as API {

  class AuthRoutes <<Boundary>> {
    +login(req: LoginRequest) LoginResponse
    +signup(req: SignupRequest) LoginResponse
    +get_mi_perfil(auth) LoginResponse
    +impersonate_user(user_id, auth)
    +listar_sucursales() List
    +crear_sucursal(req, auth)
    +activar_pase_tatami(alumno_id, req, auth)
    +cambiar_sucursal_usuario(user_id, req, auth)
    +parse_gmaps_link(req, auth)
  }

  class EvaluacionesRoutes <<Boundary>> {
    +analizar_video(background, tecnica_id, video, ...) Dict
    +obtener_primer_frame(video, auth) Dict
    +confirmar_seleccion_persona(session_id, request, auth) Dict
    +validar_spam(video, auth) Dict
    +consultar_evaluacion(evaluacion_id, auth) Dict
    +buscar_en_biblioteca(req, auth) Dict
    +ingerir_archivo_teoria(request, background, archivo, ...) Dict
    +listar_teoria(tecnica_id, solo_mios, auth) Dict
    +eliminar_teoria(tecnica_id, auth) Dict
  }

  class TecnicasRoutes <<Boundary>> {
    +listar_tecnicas(profesor_id) List
    +crear_tecnica(req, background, auth) TecnicaResponse
    +actualizar_tecnica(id, req, background, auth)
    +registrar_patron_tecnica(id, background, session_id, ...)
    +consultar_patron_activo(tecnica_id, auth)
  }

  class ComparacionesRoutes <<Boundary>> {
    +comparar_video_a_video(background, video_alumno, ...) Dict
    +leer_comparacion(comparacion_id, auth) Dict
    +descargar_video_comparacion(id, auth) FileResponse
  }
}

'======================================================
' CAPA DE CONTROL (APPLICATION)
'======================================================
package "⚙️ Capa de Aplicación (Servicios y Casos de Uso)" as Application {

  class IntelligenceAnalysisFacade <<Control>> {
    -yolo: YOLOPoseAdapter
    -qdrant: QdrantVectorAdapter
    -gemini: LocalVLMAdapter
    -qwen: QwenEmbeddingAdapter
    +ejecutar_analisis_completo(video_path, tecnica_id, ...) AnalisisResultDTO
  }

  class IngestKnowledgeUseCase <<Control>> {
    -qdrant_rag: QdrantRAGAdapter
    -db: PostgrestClient
    +execute(tecnica_id, contenido_texto, ...) IngestionResponse
  }

  class DeleteTheoryUseCase <<Control>> {
    -db: PostgrestClient
    -qdrant_rag: QdrantRAGAdapter
    +execute(tecnica_id, profesor_id) Dict
  }

  class ListTheoryUseCase <<Control>> {
    -db: PostgrestClient
    +execute(tecnica_id, profesor_id) List
  }

  class VideoComparisonService <<Control>> {
    +crear_comparacion(comparacion_id, ...) String
    +obtener_comparacion(id, token) Dict
    +procesar_comparacion_video_a_video(id, ...) Void
  }

  class InstructorMessageIngestion <<Control>> {
    +sincronizar_mensaje_profesor(tecnica_id, mensaje) Int
  }

  class MultimodalRAGService <<Control>> {
    +construir_query_textual_rag(tecnica_nombre, discrepancias) String
    +obtener_evidencias_rag_multimodal(...) List
    +formatear_evidencias_texto(evidencias) String
    +incluir_mensaje_profesor(evidencias, qdrant, tecnica_id, limit) List
  }

  class RagVideoIngestion <<Control>> {
    +indexar_frames_video_rag(tecnica_id, video_path, ...) Int
  }
}

'======================================================
' CAPA DE DOMINIO - SERVICIOS
'======================================================
package "📐 Capa de Dominio (Servicios)" as DomainServices {

  class HybridRetriever <<Control>> {
    +DEFAULT_K_RRF = 60
    +fusionar_rrf(densos, bm25, top_k, k_rrf) List
    +recuperar(query_texto, qdrant, qwen, ...) List
  }

  class Qwen3VLRerankerCrossEncoder <<Control>> {
    +MODEL_ID = "mlx-community/Qwen3-VL-Reranker-2B-4bit"
    +rerank_pairs(query, documents, instruction) List
    +get_instance() Tuple
  }

  class SessionStateManager <<Control>> {
    +crear_sesion(session_id, video_path, ...) Dict
    +seleccionar_persona(session_id, idx) Dict
    +iniciar_operacion(session_id, tecnica_id) Dict
    +finalizar_operacion(session_id, exito, error) Dict
  }

  class GlossaryService <<Control>> {
    +cargar_glosario(force_reload) Dict
    +obtener_sinonimos_multilingues(texto) Set
    +expandir_query_con_glosario(query) String
  }

  class PromptStrategy <<Interface>> {
    +construir_prompt_evaluacion(tecnica, discrepancias, mensaje) String
  }

  class SpanishPromptStrategy {
    +construir_prompt_evaluacion(...) String
  }

  class PortuguesePromptStrategy {
    +construir_prompt_evaluacion(...) String
  }

  class EnglishPromptStrategy {
    +construir_prompt_evaluacion(...) String
  }
}

'======================================================
' CAPA DE DOMINIO - BIOMECÁNICA
'======================================================
package "🦴 Capa de Dominio (Biomecánica)" as Biomechanics {

  class DTWComparator <<Control>> {
    +comparar_secuencias_con_dtw(seq_maestro, seq_alumno, ...) Dict
    +detectar_articulaciones_criticas(vec_m, vec_a, top_k) List
    +resumen_alineacion(alineacion, max_items) List
  }

  class PoseNormalizer <<Control>> {
    +VECTOR_DIM = 46
    +normalizar(kpts_flat) Dict
    +similitud_esqueletos(a, b, w_pos, w_ang) Dict
    +articulaciones_criticas(a, b, top_k) List
  }
}

'======================================================
' CAPA DE DOMINIO - ENTIDADES
'======================================================
package "📦 Capa de Dominio (Entidades)" as Entities {

  class Usuario <<Entity>> {
    +id: UUID
    +nombre_completo: String
    +username: String
    +email: String
    +password_hash: String
    +rol: RolUsuario
    +sucursal_id: UUID
    +idioma_preferido: String
    +avatar_url: String
    +estado_suscripcion: String
    +fecha_expiracion: DateTime
  }

  class Sucursal <<Entity>> {
    +id: UUID
    +nombre: String
    +pais: String
    +ciudad: String
    +direccion: String
    +latitud: Float
    +longitud: Float
  }

  class Tecnica <<Entity>> {
    +id: UUID
    +nombre: String
    +nivel_cinturon: String
    +mensaje_profesor: String
    +patron_activo_id: UUID
  }

  class Evaluacion <<Entity>> {
    +id: UUID
    +alumno_id: UUID
    +tecnica_id: UUID
    +sucursal_id: UUID
    +porcentaje_similitud: Float
    +feedback_gemini_es: String
    +feedback_summary: String
    +estado: String
    +fecha_evaluacion: DateTime
  }

  class PatronReferencia <<Entity>> {
    +tecnica_id: UUID
    +profesor_id: UUID
    +secuencia_3d: List
    +patron_id: UUID
  }

  class TeoriaRAG <<Entity>> {
    +id: UUID
    +tecnica_id: UUID
    +profesor_id: UUID
    +chunk_index: Int
    +contenido_texto: String
    +qdrant_point_id: UUID
    +fuente_tipo: String
  }

  class EsqueletoBiomecanico <<Entity>> {
    +frame_idx: Int
    +keypoints133: List
    +angulos_articulares: Dict
    +to_vector_array() List
  }

  class AnalisisResultDTO <<Entity>> {
    +similitud: Float
    +feedback: String
    +feedback_summary: String
    +frame_critico_path: String
    +timestamp_error_segundos: Float
    +articulaciones_criticas: List
    +nombres_articulaciones_criticas: List
  }

  class TokenJWT <<Entity>> {
    +access_token: String
    +token_type: String
    +expires_in: Int
  }
}

'======================================================
' CAPA DE INFRAESTRUCTURA - IA
'======================================================
package "🤖 Capa de Infraestructura (IA Local)" as InfrastructureAI {

  class YOLOPoseAdapter <<Adapter>> {
    +extraer_secuencia(video_path, persona_idx_inicial) Dict
    +extraer_frame_y_dibujar_error(...) String
    +extraer_keypoints(video_path) List
    +extraer_frame_limpio(video_path, idx, out) String
  }

  class LocalSpamFilter <<Adapter>> {
    +validar_es_jiujitsu(video_path) Boolean
  }

  class QwenEmbeddingAdapter <<Adapter>> {
    +MODEL_ID
    +generar_embedding_texto(texto) List
    +generar_embedding_imagen(image_path, prompt) List
    +generar_embeddings_texto_lote(textos) List
  }

  class LocalVLMAdapter <<Adapter>> {
    +MODEL_NAME = "mlx-community/Qwen3-VL-4B-Instruct-4bit"
    +generar_texto_feedback(prompt, frame, evidencias, idioma) Dict
    +reescribir_query_cognitiva(query) String
    +evaluar_fidelidad_grounding(respuesta, contexto, mensaje) Dict
  }
}

'======================================================
' CAPA DE INFRAESTRUCTURA - PERSISTENCIA
'======================================================
package "🗄️ Capa de Infraestructura (Persistencia)" as InfrastructurePersistence {

  class PostgrestClient <<Adapter>> {
    +get(table, params, token) Dict
    +post(table, data, token) Dict
    +patch(table, filters, data, token) Dict
    +delete(table, filters, token) Dict
    +rpc(function_name, params, token) Dict
  }

  class QdrantVectorAdapter <<Adapter>> {
    +asegurar_coleccion(vector_size) Void
    +guardar_patron_secuencia(tecnica_id, patron_id, ...) Int
    +obtener_secuencia_referencia(tecnica_id, patron_id) List
    +buscar_maxima_diferencia(esqueletos, tecnica_id) VectorSearchResultDTO
    +recuperar_evidencias_rag_multimodal(...) List
    +obtener_mensaje_profesor_rag(tecnica_id) List
  }

  class QdrantRAGAdapter <<Adapter>> {
    +ingestar_desde_respuesta(data, tecnica_id, ...) Dict
    +recuperar_contexto(query_embedding, tecnica_id, top_k) List
    +buscar_biblioteca(query_embedding, limit) List
    +buscar_biblioteca_multimodal(text_vec, image_vec, alpha, limit) List
    +eliminar_puntos(point_ids) Int
    +eliminar_mensaje_profesor(tecnica_id) Void
  }
}

'======================================================
' CAPA DE INFRAESTRUCTURA - VIDEO
'======================================================
package "🎥 Capa de Infraestructura (Video)" as InfrastructureVideo {

  class ComparadorVisual <<Adapter>> {
    +generar_video_comparacion(video_alumno, video_maestro, alineacion, output_path, ...) String
  }
}

'======================================================
' RELACIONES ENTRE CLASES
'======================================================

' Frontend → API (HTTP)
App ..> LoginModal : abre
App ..> VideoUpload : renderiza
App ..> FeedbackView : renderiza
App ..> StudentProgress : renderiza
App ..> LibraryView : renderiza
App ..> ProfesorTecnicas : renderiza
App ..> AdminSucursales : renderiza

VideoUpload ..> SelectorPersonaVideo : usa
ProfesorTecnicas ..> TheoryManagerModal : abre

' API → Application
AuthRoutes --> PostgrestClient : usa
AuthRoutes --> TokenJWT : genera
EvaluacionesRoutes --> IntelligenceAnalysisFacade : invoca
EvaluacionesRoutes --> IngestKnowledgeUseCase : invoca
EvaluacionesRoutes --> ListTheoryUseCase : invoca
EvaluacionesRoutes --> DeleteTheoryUseCase : invoca
EvaluacionesRoutes --> SessionStateManager : controla
TecnicasRoutes --> PostgrestClient : usa
TecnicasRoutes --> RagVideoIngestion : invoca
ComparacionesRoutes --> VideoComparisonService : invoca

' Application → Domain Services
IntelligenceAnalysisFacade --> YOLOPoseAdapter : usa
IntelligenceAnalysisFacade --> QdrantVectorAdapter : consulta
IntelligenceAnalysisFacade --> LocalVLMAdapter : genera
IntelligenceAnalysisFacade --> QwenEmbeddingAdapter : vectoriza
IntelligenceAnalysisFacade --> DTWComparator : compara
IntelligenceAnalysisFacade --> HybridRetriever : recupera
IntelligenceAnalysisFacade --> Qwen3VLRerankerCrossEncoder : rerank
IntelligenceAnalysisFacade --> MultimodalRAGService : orquesta

' Application → Entities
IngestKnowledgeUseCase --> TeoriaRAG : crea
IngestKnowledgeUseCase --> QdrantRAGAdapter : vectoriza
ListTheoryUseCase --> PostgrestClient : consulta
DeleteTheoryUseCase --> PostgrestClient : borra
DeleteTheoryUseCase --> QdrantRAGAdapter : purga

' Domain Services → Entities & Biomechanics
IntelligenceAnalysisFacade ..> AnalisisResultDTO : retorna
DTWComparator ..> PoseNormalizer : usa
PoseNormalizer ..> EsqueletoBiomecanico : procesa

' Domain Entities relationships
Usuario "1" --> "1" Sucursal : pertenece_a
Usuario "1" --> "*" Evaluacion : realiza
Tecnica "1" --> "*" Evaluacion : evaluada_en
Tecnica "1" --> "*" PatronReferencia : tiene
Tecnica "1" --> "*" TeoriaRAG : referencia
Evaluacion "1" --> "1" PatronReferencia : compara_con
Evaluacion "1" --> "1" AnalisisResultDTO : genera

' Infrastructure relationships
HybridRetriever --> QdrantVectorAdapter : consulta
HybridRetriever --> GlossaryService : expande
Qwen3VLRerankerCrossEncoder --> QwenEmbeddingAdapter : reutiliza
LocalVLMAdapter ..> YOLOPoseAdapter : recibe frames

' Prompt Strategies
PromptStrategy <|.. SpanishPromptStrategy
PromptStrategy <|.. PortuguesePromptStrategy
PromptStrategy <|.. EnglishPromptStrategy
IntelligenceAnalysisFacade --> PromptStrategy : utiliza

@enduml""",

    "sistema_completo_casos_uso": """@startuml Diagrama_Casos_Uso_Sistema_Completo
title Diagrama de Casos de Uso — Sistema Completo Corpo e Mente

left to right direction

skinparam shadowing false
skinparam defaultFontName Arial
skinparam roundcorner 8
skinparam ArrowColor #2B6CB0
skinparam ActorBorderColor #C53030
skinparam ActorBackgroundColor #FFF5F5
skinparam UsecaseBorderColor #2B6CB0
skinparam UsecaseBackgroundColor #F7FAFC
skinparam PackageBorderColor #2F855A
skinparam PackageBackgroundColor #F0FFF4

' ============================================
' ACTORES
' ============================================
actor "🥋 Alumno" as AL
actor "🥋 Profesor" as PR
actor "🛡️ Administrador" as AD

actor "👁️ YOLOv26\\n(Pose + Depth + Seg)" as YOLO
actor "🧠 Qwen3-VL\\n(Embedding + Reranker + Instruct)" as QWEN
actor "🔍 Qdrant\\nVector DB" as QDRANT
actor "🗄️ PostgreSQL\\n(RLS + pgcrypto)" as PG
actor "🌐 Cloudflare Tunnel" as CF
actor "🗺️ Nominatim\\n(OpenStreetMap)" as OSM

' ============================================
' SUBSISTEMA: AUTENTICACIÓN (UC-01)
' ============================================
package "🔐 Subsistema de Autenticación" as S1 {
  usecase "UC-01: Iniciar Sesión\\ny Registro de Usuarios" as UC01
  usecase "Validar Credenciales\\n(bcrypt + Rate Limit)" as UC01_VAL
  usecase "Emitir Token JWT\\n(HS256, 24h)" as UC01_JWT
}

' ============================================
' SUBSISTEMA: ANÁLISIS BIOMECÁNICO (UC-02)
' ============================================
package "🎯 Subsistema de Análisis Biomecánico" as S2 {
  usecase "UC-02: Analizar Técnica y\\nGenerar Feedback Biomecánico" as UC02
  usecase "Validar Video\\n(Anti-SPAM ViCoS)" as UC02_SPAM
  usecase "Seleccionar Persona\\nen Frame Inicial" as UC02_PERSONA
  usecase "Extraer Esqueleto 3D\\n(x,y,z)" as UC02_POSE
  usecase "Calcular Similitud DTW\\n(0-100%)" as UC02_DTW
  usecase "Recuperar Teoría RAG\\n(Two-Stage)" as UC02_RAG
  usecase "Generar Corrección\\nde IA (VLM Local)" as UC02_VLM
  usecase "Auditar Fidelidad\\n(LLM-as-a-Judge)" as UC02_JUDGE
}

' ============================================
' SUBSISTEMA: GESTIÓN DE TÉCNICAS (UC-03)
' ============================================
package "📋 Subsistema de Gestión de Técnicas" as S3 {
  usecase "UC-03: Gestionar Técnicas\\ny Videos de Referencia" as UC03
  usecase "Subir Video de Referencia\\n(Patrón de Oro)" as UC03_VIDEO
  usecase "Extraer Esqueleto\\nCanónico 3D" as UC03_YOLO
  usecase "Indexar Patrón\\nen PostgreSQL+Qdrant" as UC03_INDEX
}

' ============================================
' SUBSISTEMA: GESTIÓN RAG (UC-04)
' ============================================
package "📚 Subsistema de Conocimiento RAG" as S4 {
  usecase "UC-04: Gestionar Teoría RAG\\ny Mensajes del Profesor" as UC04
  usecase "Escribir Mensaje Directo\\n(mensaje_profesor)" as UC04_MSG
  usecase "Cargar Manual PDF\\n(Texto + Diagramas)" as UC04_PDF
  usecase "Vectorizar con Qwen3-VL\\n(2048 dims)" as UC04_EMB
  usecase "Indexar en Qdrant\\nColección rag_knowledge" as UC04_STORE
}

' ============================================
' SUBSISTEMA: PROGRESO (UC-05)
' ============================================
package "📊 Subsistema de Progreso y Evaluaciones" as S5 {
  usecase "UC-05: Ver Progreso\\nde Alumnos" as UC05
  usecase "Consultar Lista de\\nAlumnos por Sucursal" as UC05_LIST
  usecase "Ver Historial\\nde Evaluaciones" as UC05_HIST
  usecase "Reproducir Video con\\nCorrección de IA" as UC05_PLAY
}

' ============================================
' SUBSISTEMA: PASE DE TATAMI (UC-06)
' ============================================
package "🥋 Subsistema de Pase de Tatami" as S6 {
  usecase "UC-06: Activar Pase\\nde Tatami (30 Días)" as UC06
  usecase "Verificar Pago\\nen Recepción" as UC06_PAY
  usecase "Calcular Fecha\\nde Expiración (+30d)" as UC06_CALC
  usecase "Bloqueo Automático\\nal Expirar" as UC06_BLOCK
}

' ============================================
' SUBSISTEMA: SUCURSALES (UC-07)
' ============================================
package "🗺️ Subsistema de Gestión de Sucursales" as S7 {
  usecase "UC-07: Gestionar Sucursales\\ny Coordenadas Geográficas" as UC07
  usecase "Seleccionar Ubicación\\nen Mapa Leaflet" as UC07_MAP
  usecase "Geocodificación\\nInversa (Nominatim)" as UC07_GEO
  usecase "Guardar Coordenadas\\n(lat, lng)" as UC07_SAVE
}

' ============================================
' SUBSISTEMA: SOPORTE TÉCNICO (UC-08)
' ============================================
package "🔧 Subsistema de Soporte Técnico" as S8 {
  usecase "UC-08: Entrar como\\nOtro Usuario" as UC08
  usecase "Reconfirmar Clave\\nAdministrador" as UC08_AUTH
  usecase "Registrar Auditoría\\n(deuda técnica)" as UC08_AUDIT
  usecase "Emitir JWT con\\nimpersonator_admin_id" as UC08_JWT
  usecase "Activar Banner\\nRojo de Soporte" as UC08_BANNER
  usecase "Restaurar Sesión\\nOriginal" as UC08_RESTORE
}

' ============================================
' RELACIONES ACTORES → CASOS DE USO
' ============================================

AL --> UC01
PR --> UC01
AD --> UC01

AL --> UC02
AL --> UC05
AL --> UC04

PR --> UC03
PR --> UC04
PR --> UC05
PR --> UC06

AD --> UC03
AD --> UC06
AD --> UC07
AD --> UC08

' ============================================
' RELACIONES INCLUDE / EXTEND
' ============================================

' UC-01
UC01 ..> UC01_VAL : <<include>>
UC01 ..> UC01_JWT : <<include>>

' UC-02
UC02 ..> UC02_SPAM : <<include>>
UC02 ..> UC02_PERSONA : <<include>>
UC02 ..> UC02_POSE : <<include>>
UC02 ..> UC02_DTW : <<include>>
UC02 ..> UC02_RAG : <<extend>>\\n(Similitud < 85%)
UC02 ..> UC02_VLM : <<extend>>\\n(Similitud < 85%)
UC02_VLM ..> UC02_JUDGE : <<include>>

' UC-03
UC03 --> UC03_VIDEO
UC03_VIDEO ..> UC03_YOLO : <<include>>
UC03_YOLO ..> UC03_INDEX : <<include>>

' UC-04
UC04 ..> UC04_MSG : <<include>>
UC04 ..> UC04_PDF : <<include>>
UC04_PDF ..> UC04_EMB : <<include>>
UC04_EMB ..> UC04_STORE : <<include>>

' UC-05
UC05 ..> UC05_LIST : <<include>>
UC05 ..> UC05_HIST : <<include>>
UC05 ..> UC05_PLAY : <<extend>>

' UC-06
UC06 ..> UC06_PAY : <<include>>
UC06 ..> UC06_CALC : <<include>>
UC06 ..> UC06_BLOCK : <<extend>>

' UC-07
UC07 ..> UC07_MAP : <<include>>
UC07_MAP ..> UC07_GEO : <<include>>
UC07 ..> UC07_SAVE : <<include>>

' UC-08
UC08 ..> UC08_AUTH : <<include>>
UC08 ..> UC08_JWT : <<include>>
UC08 ..> UC08_BANNER : <<include>>
AD --> UC08_RESTORE

' ============================================
' RELACIONES SISTEMA → ACTORES SECUNDARIOS
' ============================================

UC02_POSE --> YOLO
UC02_RAG --> QDRANT
UC02_VLM --> QWEN
UC02_SPAM --> YOLO

UC03_YOLO --> YOLO
UC03_INDEX --> QDRANT
UC03_INDEX --> PG

UC04_EMB --> QWEN
UC04_STORE --> QDRANT

UC01_VAL --> PG
UC01_JWT --> PG

UC05_LIST --> PG
UC05_HIST --> PG

UC06_CALC --> PG

UC07_GEO --> OSM
UC07_SAVE --> PG

' Cloudflare Tunnel como actor externo de exposición
AL ..> CF : HTTPS
PR ..> CF : HTTPS
AD ..> CF : HTTPS

@enduml"""
}

def render_plantuml(name: str, puml_code: str):
    png_path = OUTPUT_DIR / f"{name}.png"
    print(f"Renderizando {name}...", end=" ")
    
    # Kroki POST
    try:
        req = urllib.request.Request(
            "https://kroki.io/plantuml/png",
            data=puml_code.encode("utf-8"),
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            }
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            png_bytes = response.read()
            png_path.write_bytes(png_bytes)
            print(f"[OK Kroki] {len(png_bytes)} bytes guardados en {png_path}")
            return True
    except Exception as e:
        print(f"[Fallo Kroki: {e}]. Intentando servidor PlantUML oficial...", end=" ")

    # Fallback plantuml.com
    try:
        compressed = zlib.compress(puml_code.encode("utf-8"))[2:-4]
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
        with urllib.request.urlopen(req, timeout=20) as response:
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

