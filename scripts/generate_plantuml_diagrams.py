# scripts/generate_plantuml_diagrams.py
# -*- coding: utf-8 -*-
"""
Genera y renderiza los 16 diagramas de PlantUML a Nivel de Análisis (Casos de Uso
y Diagramas de Secuencia bajo el patrón Entity-Control-Boundary, ECB)
para el Capítulo V de docs/ProyectoGrado.md.
"""

import urllib.request
from pathlib import Path

OUTPUT_DIR = Path("docs/diagramas")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SKINPARAM_COMMON = """skinparam shadowing false
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
skinparam UsecaseBorderColor #2B6CB0
skinparam UsecaseBackgroundColor #F7FAFC"""

DIAGRAMS = {
    # ---------------------------------------------------------
    # UC-01: Iniciar Sesión y Registro de Usuarios
    # ---------------------------------------------------------
    "cu01_caso_uso": f"""@startuml
left to right direction
{SKINPARAM_COMMON}

actor "Alumno" as AL
actor "Profesor" as PR
actor "Administrador" as AD
actor "Servicio de Identidad\\ny Acceso" as SIA

rectangle "Sistema Corpo e Mente - Identificación y Acceso" {{
    usecase "UC-01: Iniciar Sesión y\\nRegistro de Usuarios" as UC01
    usecase "Registrar Nueva Cuenta\\nde Practicante o Instructor" as UC01_Reg
    usecase "Verificar Credenciales\\nde Identificación" as UC01_Val
    usecase "Constituir Sesión\\nde Trabajo Activa" as UC01_Ses
    usecase "Controlar Umbral de\\nIntentos Fallidos" as UC01_Lim
}}

AL --> UC01
PR --> UC01
AD --> UC01

AL --> UC01_Reg
PR --> UC01_Reg

UC01 ..> UC01_Val : <<include>>
UC01 ..> UC01_Ses : <<include>>
UC01 ..> UC01_Lim : <<include>>
UC01_Reg ..> UC01_Ses : <<include>>

UC01_Val --> SIA
UC01_Ses --> SIA
@enduml""",

    "cu01_secuencia": f"""@startuml
title Diagrama de Secuencia de Análisis (ECB) — UC-01: Iniciar Sesión y Registro de Usuarios
autonumber
{SKINPARAM_COMMON}

actor "Usuario" as U
boundary "PantallaDeAcceso" as B1
control "CoordinadorDeAcceso" as C1
entity "Usuario" as E1
entity "Sucursal" as E2
entity "SesiónDeUsuario" as E3

U -> B1 : solicitarAcceso(identificador, clave)
B1 -> C1 : autenticarUsuario(identificador, clave)
C1 -> C1 : verificarIntentosPermitidos(solicitante)
C1 -> E1 : buscarPorIdentificador(identificador)
E1 --> C1 : datosDeUsuario
C1 -> E1 : validarCredenciales(clave)
E1 --> C1 : credencialesVálidas
C1 -> E2 : obtenerSedeAdscrita(usuario)
E2 --> C1 : datosDeSucursal
C1 -> E3 : iniciarSesión(usuario, rol, sucursal)
E3 --> C1 : sesiónActiva
C1 --> B1 : accesoAutorizado(sesiónActiva, perfil)
B1 --> U : presentarEntornoDeTrabajo(rol, sucursal)
@enduml""",

    # ---------------------------------------------------------
    # UC-02: Analizar Técnica y Generar Feedback Biomecánico
    # ---------------------------------------------------------
    "cu02_caso_uso": f"""@startuml
left to right direction
{SKINPARAM_COMMON}

actor "Alumno" as AL
actor "Servicio de Visión\\npor Computadora" as SVC
actor "Base de Conocimiento\\nTécnica" as BCT
actor "Servicio de Redacción\\nPedagógica" as SRP

rectangle "Sistema Corpo e Mente - Evaluación Biomecánica" {{
    usecase "UC-02: Analizar Técnica y\\nGenerar Feedback Biomecánico" as UC02
    usecase "Verificar Elegibilidad\\nde la Ejecución" as UC02_Elig
    usecase "Reconocer Postura Corporal\\ndel Practicante" as UC02_Post
    usecase "Comparar Posturas contra\\nPatrón del Profesor" as UC02_Comp
    usecase "Consultar Conocimiento\\nTécnico de Referencia" as UC02_Con
    usecase "Elaborar Corrección\\nPedagógica" as UC02_Corr
    usecase "Auditar Fidelidad\\nPedagógica del Consejo" as UC02_Aud
}}

AL --> UC02
UC02 ..> UC02_Elig : <<include>>
UC02 ..> UC02_Post : <<include>>
UC02 ..> UC02_Comp : <<include>>
UC02 ..> UC02_Con : <<extend>>\\n(Desviación Significativa)
UC02 ..> UC02_Corr : <<extend>>\\n(Desviación Significativa)
UC02_Corr ..> UC02_Aud : <<include>>

UC02_Post --> SVC
UC02_Con --> BCT
UC02_Corr --> SRP
@enduml""",

    "cu02_secuencia": f"""@startuml
title Diagrama de Secuencia de Análisis (ECB) — UC-02: Analizar Técnica
autonumber
{SKINPARAM_COMMON}

actor "Alumno" as AL
boundary "PantallaDeEvaluación" as B1
control "CoordinadorDeEvaluación" as C1
entity "Evaluación" as E1
entity "PatrónDeReferencia" as E2
entity "BibliotecaTécnica" as E3

AL -> B1 : solicitarEvaluación(profesor, técnica, video)
B1 -> C1 : crearEvaluación(alumno, profesor, técnica, video)
C1 -> E1 : crear(alumno, profesor, técnica)
E1 --> C1 : evaluaciónRegistrada
C1 -> E2 : obtenerPatrónDeReferencia(técnica, profesor)
E2 --> C1 : secuenciaDeReferencia
C1 -> C1 : compararPosturas(videoAlumno, secuenciaDeReferencia)
C1 -> E3 : buscarConocimientoTécnico(técnica, discrepancias)
E3 --> C1 : fragmentosDeConocimiento
C1 -> C1 : generarFeedbackPedagógico(discrepancias, conocimiento)
C1 -> E1 : actualizarResultado(similitud, feedback)
C1 --> B1 : evaluaciónCompletada
B1 --> AL : mostrarReporte(similitud, feedback, fotogramaCrítico)
@enduml""",

    # ---------------------------------------------------------
    # UC-03: Gestionar Técnicas y Videos de Referencia
    # ---------------------------------------------------------
    "cu03_caso_uso": f"""@startuml
left to right direction
{SKINPARAM_COMMON}

actor "Profesor" as PR
actor "Administrador" as AD
actor "Servicio de Visión\\npor Computadora" as SVC

rectangle "Sistema Corpo e Mente - Catálogo y Referencias" {{
    usecase "UC-03: Gestionar Técnicas y\\nVideos de Referencia" as UC03
    usecase "Registrar Demostración\\nde Referencia del Instructor" as UC03_Vid
    usecase "Reconocer Secuencia Postural\\ndel Instructor" as UC03_Post
    usecase "Catalogar Patrón\\nBiomecánico Oficial" as UC03_Cat
}}

PR --> UC03
AD --> UC03
PR --> UC03_Vid
UC03_Vid ..> UC03_Post : <<include>>
UC03_Post ..> UC03_Cat : <<include>>
UC03_Post --> SVC
@enduml""",

    "cu03_secuencia": f"""@startuml
title Diagrama de Secuencia de Análisis (ECB) — UC-03: Gestionar Técnicas y Referencias
autonumber
{SKINPARAM_COMMON}

actor "Profesor" as PR
boundary "PantallaDeCatálogoTécnico" as B1
control "CoordinadorDeTécnicas" as C1
entity "Técnica" as E1
entity "PatrónDeReferencia" as E2

PR -> B1 : solicitarRegistroDeTécnica(nombre, cinturón, indicaciones, videoDemostración)
B1 -> C1 : registrarTécnicaConReferencia(profesor, datosTécnica, videoDemostración)
C1 -> E1 : crear(nombre, cinturón, indicaciones)
E1 --> C1 : técnicaRegistrada
C1 -> C1 : extraerSecuenciaPostural(videoDemostración, instructorConfirmado)
C1 -> E2 : guardarPatrónOficial(técnicaRegistrada, profesor, secuenciaPostural)
E2 --> C1 : patrónVigente
C1 -> E1 : vincularPatrónVigente(patrónVigente)
C1 --> B1 : registroCompletado(técnicaRegistrada, patrónVigente)
B1 --> PR : confirmarDisponibilidadDeTécnica(técnicaRegistrada)
@enduml""",

    # ---------------------------------------------------------
    # UC-04: Gestionar Conocimiento Técnico y Directrices del Profesor
    # ---------------------------------------------------------
    "cu04_caso_uso": f"""@startuml
left to right direction
{SKINPARAM_COMMON}

actor "Profesor" as PR
actor "Servicio de Catalogación\\nde Conocimiento" as SCC
actor "Base de Conocimiento\\nTécnica" as BCT

rectangle "Sistema Corpo e Mente - Conocimiento Técnico" {{
    usecase "UC-04: Gestionar Conocimiento\\nTécnico y Directrices" as UC04
    usecase "Registrar Directriz Pedagógica\\ndel Instructor" as UC04_Msg
    usecase "Incorporar Obra Bibliográfica\\nde Referencia" as UC04_Doc
    usecase "Extraer Pasajes e\\nIlustraciones Técnicas" as UC04_Ext
    usecase "Catalogar Fragmentos para\\nConsulta Semántica" as UC04_Cat
}}

PR --> UC04
UC04 ..> UC04_Msg : <<include>>
UC04 ..> UC04_Doc : <<include>>
UC04_Doc ..> UC04_Ext : <<include>>
UC04_Ext ..> UC04_Cat : <<include>>

UC04_Ext --> SCC
UC04_Cat --> BCT
@enduml""",

    "cu04_secuencia": f"""@startuml
title Diagrama de Secuencia de Análisis (ECB) — UC-04: Gestionar Conocimiento Técnico
autonumber
{SKINPARAM_COMMON}

actor "Profesor" as PR
boundary "PantallaDeConocimientoTécnico" as B1
control "CoordinadorDeConocimiento" as C1
entity "Técnica" as E1
entity "BibliotecaTécnica" as E2

PR -> B1 : aportarMaterialDoctrinal(técnica, directrizInstructor, documentoTécnico)
B1 -> C1 : actualizarConocimientoTécnico(profesor, técnica, directrizInstructor, documentoTécnico)
C1 -> E1 : actualizarDirectrizDelInstructor(directrizInstructor)
E1 --> C1 : directrizVigente
C1 -> C1 : segmentarContenidoEIlustraciones(documentoTécnico)
C1 -> E2 : catalogarFragmentos(fuente, fragmentosExtraídos)
E2 --> C1 : fragmentosCatalogados
C1 --> B1 : conocimientoActualizado(totalFragmentos, directrizVigente)
B1 --> PR : confirmarMaterialDisponible(totalFragmentos)
@enduml""",

    # ---------------------------------------------------------
    # UC-05: Ver Progreso de Alumnos
    # ---------------------------------------------------------
    "cu05_caso_uso": f"""@startuml
left to right direction
{SKINPARAM_COMMON}

actor "Profesor" as PR
actor "Alumno" as AL

rectangle "Sistema Corpo e Mente - Seguimiento de Progreso" {{
    usecase "UC-05: Ver Progreso\\nde Alumnos" as UC05
    usecase "Consultar Practicantes\\nde la Sede" as UC05_List
    usecase "Revisar Historial Cronológico\\nde Evaluaciones" as UC05_Time
    usecase "Inspeccionar Ejecución y\\nCorrección Pedagógica" as UC05_Play
}}

PR --> UC05
PR --> UC05_List
PR --> UC05_Time
PR --> UC05_Play

AL --> UC05_Time
AL --> UC05_Play
@enduml""",

    "cu05_secuencia": f"""@startuml
title Diagrama de Secuencia de Análisis (ECB) — UC-05: Ver Progreso de Alumnos
autonumber
{SKINPARAM_COMMON}

actor "Profesor" as PR
boundary "PantallaDeProgreso" as B1
control "CoordinadorDeProgreso" as C1
entity "Usuario" as E1
entity "Evaluación" as E2

PR -> B1 : solicitarSeguimientoDeSede(sucursal)
B1 -> C1 : consultarProgresoDeAlumnos(profesor, sucursal)
C1 -> E1 : obtenerAlumnosDeSucursal(sucursal)
E1 --> C1 : listaDeAlumnos
C1 -> E2 : obtenerHistorialDeEvaluaciones(listaDeAlumnos)
E2 --> C1 : historialPorAlumno
C1 -> C1 : consolidarEvoluciónTécnica(listaDeAlumnos, historialPorAlumno)
C1 --> B1 : resumenDeProgreso(alumnos, evolución, estadoMembresía)
B1 --> PR : mostrarEvoluciónTécnica(alumnos, historialPorAlumno)
@enduml""",

    # ---------------------------------------------------------
    # UC-06: Activar Pase de Tatami
    # ---------------------------------------------------------
    "cu06_caso_uso": f"""@startuml
left to right direction
{SKINPARAM_COMMON}

actor "Profesor" as PR
actor "Administrador" as AD

rectangle "Sistema Corpo e Mente - Control de Membresías" {{
    usecase "UC-06: Activar Pase\\nde Tatami (30 Días)" as UC06
    usecase "Confirmar Pago Presencial\\nen la Academia" as UC06_Pay
    usecase "Verificar Pertenencia\\na la Misma Sede" as UC06_Sede
    usecase "Habilitar Vigencia por\\nTreinta Días" as UC06_Act
    usecase "Suspender Acceso\\nal Vencer el Periodo" as UC06_Block
}}

PR --> UC06
AD --> UC06
UC06 ..> UC06_Pay : <<include>>
UC06 ..> UC06_Sede : <<include>>
UC06 ..> UC06_Act : <<include>>
UC06 ..> UC06_Block : <<extend>>
@enduml""",

    "cu06_secuencia": f"""@startuml
title Diagrama de Secuencia de Análisis (ECB) — UC-06: Activar Pase de Tatami
autonumber
{SKINPARAM_COMMON}

actor "Profesor" as PR
boundary "PantallaDeMembresías" as B1
control "CoordinadorDeMembresías" as C1
entity "Usuario" as E1
entity "PaseDeTatami" as E2

PR -> B1 : solicitarActivaciónDePase(alumno)
B1 -> C1 : activarPaseDeTatami(profesor, alumno)
C1 -> E1 : verificarMismaSucursal(profesor, alumno)
E1 --> C1 : pertenenciaConfirmada
C1 -> E2 : habilitarPorTreintaDías(alumno, fechaActual)
E2 --> C1 : vigenciaActualizada
C1 -> E1 : actualizarEstadoDeMembresía(vigenciaActualizada)
C1 --> B1 : paseActivado(alumno, fechaVencimiento)
B1 --> PR : confirmarHabilitaciónDeAcceso(alumno, fechaVencimiento)
@enduml""",

    # ---------------------------------------------------------
    # UC-07: Gestionar Sucursales y Coordenadas Geográficas
    # ---------------------------------------------------------
    "cu07_caso_uso": f"""@startuml
left to right direction
{SKINPARAM_COMMON}

actor "Administrador" as AD
actor "Servicio de Cartografía\\ny Localización" as SCL

rectangle "Sistema Corpo e Mente - Gestión de Sedes" {{
    usecase "UC-07: Gestionar Sucursales y\\nCoordenadas Geográficas" as UC07
    usecase "Indicar Ubicación Geográfica\\nde la Sede" as UC07_Map
    usecase "Determinar Datos Administrativos\\nde la Zona" as UC07_Geo
    usecase "Registrar Sede en el\\nDirectorio Oficial" as UC07_Save
    usecase "Reasignar Practicantes\\ne Instructores" as UC07_Assign
}}

AD --> UC07
UC07 ..> UC07_Map : <<include>>
UC07_Map ..> UC07_Geo : <<include>>
UC07 ..> UC07_Save : <<include>>
UC07 ..> UC07_Assign : <<extend>>

UC07_Geo --> SCL
@enduml""",

    "cu07_secuencia": f"""@startuml
title Diagrama de Secuencia de Análisis (ECB) — UC-07: Gestionar Sucursales
autonumber
{SKINPARAM_COMMON}

actor "Administrador" as AD
boundary "PantallaDeGestiónDeSedes" as B1
control "CoordinadorDeSucursales" as C1
entity "Sucursal" as E1

AD -> B1 : indicarCoordenadasDeSede(latitud, longitud)
B1 -> C1 : consultarUbicaciónGeográfica(latitud, longitud)
C1 -> C1 : determinarDivisiónAdministrativa(latitud, longitud)
C1 --> B1 : ubicaciónPropuesta(país, ciudad, dirección)
B1 --> AD : presentarUbicaciónPropuesta(país, ciudad, dirección)
AD -> B1 : confirmarRegistroDeSede(nombre, país, ciudad, dirección, latitud, longitud)
B1 -> C1 : registrarNuevaSucursal(nombre, país, ciudad, dirección, latitud, longitud)
C1 -> E1 : crear(nombre, país, ciudad, dirección, latitud, longitud)
E1 --> C1 : sucursalRegistrada
C1 --> B1 : registroDeSedeCompletado(sucursalRegistrada)
B1 --> AD : mostrarDirectorioActualizado(sucursalRegistrada)
@enduml""",

    # ---------------------------------------------------------
    # UC-08: Entrar como Otro Usuario / Impersonificación
    # ---------------------------------------------------------
    "cu08_caso_uso": f"""@startuml
left to right direction
{SKINPARAM_COMMON}

actor "Administrador" as AD
actor "Usuario Asistido" as UA

rectangle "Sistema Corpo e Mente - Soporte Técnico" {{
    usecase "UC-08: Entrar como Otro Usuario\\n(Impersonificación de Soporte)" as UC08
    usecase "Reconfirmar Autorización\\ndel Administrador" as UC08_Auth
    usecase "Registrar Constancia de\\nAsistencia Técnica" as UC08_Audit
    usecase "Establecer Sesión Temporal\\nde Diagnóstico" as UC08_Ses
    usecase "Mantener Aviso Visible\\nde Modo Soporte" as UC08_Aviso
    usecase "Restituir Sesión Original\\ndel Administrador" as UC08_Restore
}}

AD --> UC08
UC08 --> UA
UC08 ..> UC08_Auth : <<include>>
UC08 ..> UC08_Audit : <<include>>
UC08 ..> UC08_Ses : <<include>>
UC08 ..> UC08_Aviso : <<include>>
AD --> UC08_Restore
@enduml""",

    "cu08_secuencia": f"""@startuml
title Diagrama de Secuencia de Análisis (ECB) — UC-08: Impersonificación de Soporte
autonumber
{SKINPARAM_COMMON}

actor "Administrador" as AD
boundary "PantallaDeSoporteTécnico" as B1
control "CoordinadorDeSoporte" as C1
entity "Usuario" as E1
entity "RegistroDeAuditoría" as E2
entity "SesiónDeSoporte" as E3

AD -> B1 : solicitarAsumirIdentidad(usuarioObjetivo, autorizaciónAdmin)
B1 -> C1 : iniciarModoSoporte(administrador, usuarioObjetivo, autorizaciónAdmin)
C1 -> E1 : verificarJerarquíaYAutorización(administrador, usuarioObjetivo, autorizaciónAdmin)
E1 --> C1 : operaciónAutorizada
C1 -> E2 : registrarInicioDeAsistencia(administrador, usuarioObjetivo, fechaHora)
E2 --> C1 : constanciaRegistrada
C1 -> E3 : constituirSesiónTemporal(administrador, usuarioObjetivo)
E3 --> C1 : sesiónTemporalActiva
C1 --> B1 : entornoDeSoporteHabilitado(sesiónTemporalActiva, avisoVisible)
B1 --> AD : presentarVistaDelUsuarioConAvisoDeSoporte(usuarioObjetivo)
AD -> B1 : finalizarModoSoporte()
B1 -> C1 : restituirSesiónDeAdministrador(sesiónTemporalActiva)
C1 -> E3 : cerrarSesiónTemporal()
E3 --> C1 : sesiónOriginalRestituida
C1 --> B1 : retornoConfirmado(sesiónOriginalRestituida)
B1 --> AD : presentarEntornoDeAdministración()
@enduml""",
}


def render_plantuml(name: str, puml_code: str) -> bool:
    png_path = OUTPUT_DIR / f"{name}.png"
    print(f"Renderizando {name}...", end=" ")

    try:
        req = urllib.request.Request(
            "https://kroki.io/plantuml/png",
            data=puml_code.encode("utf-8"),
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            png_bytes = response.read()
            png_path.write_bytes(png_bytes)
            print(f"[OK] {len(png_bytes)} bytes guardados en {png_path}")
            return True
    except Exception as e:
        print(f"[Fallo Kroki: {e}]. Intentando servidor PlantUML oficial...", end=" ")

    try:
        import zlib

        compressed = zlib.compress(puml_code.encode("utf-8"))[2:-4]
        mapping = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
        res = []
        for i in range(0, len(compressed), 3):
            b1 = compressed[i]
            b2 = compressed[i + 1] if i + 1 < len(compressed) else 0
            b3 = compressed[i + 2] if i + 2 < len(compressed) else 0
            res.append(mapping[b1 >> 2])
            res.append(mapping[((b1 & 0x3) << 4) | (b2 >> 4)])
            res.append(mapping[((b2 & 0xF) << 2) | (b3 >> 6)])
            res.append(mapping[b3 & 0x3F])
        encoded = "".join(res)
        url = f"http://www.plantuml.com/plantuml/png/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
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
