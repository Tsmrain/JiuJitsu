# scripts/update_casos_uso_analisis.py
# -*- coding: utf-8 -*-
"""
Reemplaza los apartados 5.X.1 de docs/ProyectoGrado.md con las especificaciones
a Nivel de Análisis (Esencial) según la metodología de Craig Larman (2004).
Preserva intactos todos los diagramas de diseño 5.X.2 - 5.X.5 y la sección 5.9.
"""

import re
import sys
from pathlib import Path

DOC_PATH = Path("docs/ProyectoGrado.md")

USE_CASES_ANALYSIS = {
    1: r"""### 5.1.1. Caso de Uso 1: Iniciar Sesión y Registro de Usuarios (UC-01) — Nivel de Análisis

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-01** |
| **Nombre** | Iniciar Sesión y Registro de Usuarios |
| **Actores** | **Principal:** Alumno, Profesor, Administrador.<br>**Secundario (Sistemas de Apoyo):** Servicio de Identidad y Sesión (gestión de identidad criptográfica). |
| **Descripción** | Permite a un practicante, instructor o administrador acceder a la plataforma identificándose de forma segura, o bien registrar una nueva cuenta asociada a una sucursal de la academia. |
| **Precondiciones** | El solicitante desea acceder o crear una cuenta, y dispone de conexión con el sistema. |
| **Postcondiciones** | 1. Se establece una sesión autenticada asociada al rol del usuario.<br>2. La interfaz de acceso se reemplaza por el panel de trabajo propio del rol.<br>3. Las cuentas nuevas de alumno se inician en estado "pendiente" (sujetas al Pase de Tatami). |

#### Secuencia Normal (Inicio de Sesión)
| Paso | Intención del Actor | Respuesta Observable del Sistema |
| :---: | :--- | :--- |
| 1 | Usuario solicita acceder al sistema. | Sistema presenta la pantalla de identificación. |
| 2 | Usuario aporta sus credenciales de acceso. | Sistema verifica la identidad del solicitante y determina su rol y sucursal. |
| 3 | | Sistema establece una sesión activa y presenta el panel correspondiente: de práctica (alumno), de instrucción (profesor) o de administración global. |

#### Secuencias Alternativas
* **2a. Registro de nuevo usuario:**
  * 2a.1. El solicitante pide crear una cuenta.
  * 2a.2. El sistema solicita: datos de perfil, rol deseado (alumno o profesor) y sucursal de adscripción.
  * 2a.3. El solicitante proporciona los datos.
  * 2a.4. El sistema valida que el identificador elegido no esté en uso y cumpla el formato establecido.
  * 2a.5. El sistema crea la cuenta con estado inicial correspondiente a su rol y establece la sesión.
* **2b. Credenciales inválidas:**
  * Sistema informa el rechazo sin especificar si el error corresponde al identificador o a la contraseña (previene enumeración de cuentas).
* **2c. Intentos reiterados fallidos:**
  * Sistema bloquea temporalmente al solicitante por política de seguridad.

#### Excepciones
* **E1. Servicio de identidad indisponible:** El sistema informa que la autenticación está temporalmente fuera de servicio.""",

    2: r"""### 5.2.1. Caso de Uso 2: Analizar Técnica y Generar Feedback Biomecánico (UC-02) — Nivel de Análisis

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-02** |
| **Nombre** | Analizar Técnica y Generar Feedback Biomecánico |
| **Actores** | **Principal:** Alumno.<br>**Secundario (Sistemas de Apoyo):** Servicio de Visión por Computadora (percepción de la postura), Servicio de Evaluación Cinemática (comparación del movimiento), Base de Conocimiento Técnica (bibliografía y directrices del instructor), Servicio de Redacción Pedagógica (generación del consejo). |
| **Descripción** | El alumno solicita evaluar su ejecución de una técnica; el sistema reconoce su postura corporal, la contrasta con la referencia del profesor, identifica el instante y las zonas del cuerpo con mayor desviación y, si corresponde, entrega una explicación pedagógica fundamentada en el material técnico del instructor. |
| **Precondiciones** | 1. El alumno mantiene una sesión activa con su acceso al análisis habilitado.<br>2. Existe una referencia registrada por un profesor para la técnica solicitada. |
| **Postcondiciones** | 1. La evaluación queda registrada en el historial del alumno con su grado de similitud.<br>2. El alumno conoce el instante exacto del error, las zonas corporales afectadas y, cuando aplica, una corrección pedagógica en su idioma. |

#### Secuencia Normal
| Paso | Intención del Actor | Respuesta Observable del Sistema |
| :---: | :--- | :--- |
| 1 | Alumno selecciona al profesor de su academia y la técnica a evaluar. | Sistema presenta las técnicas con referencia activa del profesor seleccionado. |
| 2 | Alumno aporta un video de su ejecución. | Sistema verifica que el material sea elegible (corresponde a práctica de Jiu-Jitsu y es de tamaño manejable). |
| 3 | | Sistema localiza al practicante dentro del video y, cuando hay más de una persona, solicita al alumno confirmar cuál es él. |
| 4 | Alumno confirma su identidad en el video. | Sistema admite la solicitud e informa al alumno que la evaluación fue recibida. |
| 5 | | Sistema reconoce la postura corporal del alumno a lo largo de la ejecución. |
| 6 | | Sistema contrasta la ejecución del alumno contra la referencia del profesor y obtiene un grado de similitud. |
| 7 | | Sistema identifica el instante del video y las zonas del cuerpo con mayor desviación respecto al patrón. |
| 8 | | Si la desviación es significativa, el sistema reúne la explicación técnica del instructor y las referencias bibliográficas pertinentes para fundamentar la corrección. |
| 9 | | Sistema presenta al alumno un informe con: grado de similitud, instante exacto del error, zonas del cuerpo afectadas y, cuando aplica, explicación pedagógica en su idioma. |
| 10 | Alumno revisa el informe y navega al instante del error. | Sistema resalta visualmente la zona del cuerpo comprometida y ofrece referencias de práctica complementaria. |

#### Secuencias Alternativas
* **2a. Material no elegible** (no corresponde a práctica de Jiu-Jitsu, formato no soportado o excede tamaño aceptable): El sistema rechaza la solicitud e invita al alumno a intentarlo nuevamente con un video adecuado.
* **2b. Acceso al análisis no habilitado:** El sistema informa que debe gestionar la habilitación de su acceso (Pase de Tatami) con su instructor.
* **3a. Solo una persona reconocida en el video:** El sistema presume la identidad y solicita al alumno una confirmación simple de un solo toque.
* **7a. Ejecución correcta** (grado de similitud por encima del umbral aceptable): El sistema felicita al alumno y le indica que dominó la técnica, sin recurrir al componente de redacción pedagógica.
* **9a. Fundamento teórico insuficiente:** Si el sistema no encuentra material técnico suficiente para sustentar una corrección, entrega únicamente el reporte biomecánico (zonas del cuerpo y segundo del error) y evita ofrecer una explicación no respaldada.

#### Excepciones
* **E1. Análisis no concluido en tiempo razonable:** El sistema informa al alumno que la evaluación continúa procesándose y que podrá consultar el resultado posteriormente desde su historial.
* **E2. No existe referencia activa para la técnica:** El sistema informa que la evaluación no puede realizarse por falta de patrón del profesor.""",

    3: r"""### 5.3.1. Caso de Uso 3: Gestionar Técnicas y Videos de Referencia (UC-03) — Nivel de Análisis

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-03** |
| **Nombre** | Gestionar Técnicas y Videos de Referencia |
| **Actores** | **Principal:** Profesor, Administrador.<br>**Secundario (Sistemas de Apoyo):** Servicio de Visión por Computadora (extracción del patrón), Repositorio de Referencias. |
| **Descripción** | El instructor mantiene el catálogo de técnicas de la academia y registra, para cada una, su propia ejecución como patrón de referencia. |
| **Precondiciones** | El usuario mantiene una sesión activa en calidad de profesor o administrador. |
| **Postcondiciones** | 1. La técnica queda disponible en el catálogo global.<br>2. Su patrón de referencia queda registrado y utilizable en futuras evaluaciones de alumnos. |

#### Secuencia Normal
| Paso | Intención del Actor | Respuesta Observable del Sistema |
| :---: | :--- | :--- |
| 1 | Profesor solicita incorporar una nueva técnica al catálogo. | Sistema presenta el formulario de alta (nombre, cinturón de referencia, indicaciones del instructor). |
| 2 | Profesor completa los datos y aporta un video de su ejecución como referencia. | Sistema admite la solicitud y analiza el material. |
| 3 | | Sistema identifica al instructor dentro del video y le solicita confirmar cuál de las personas presentes es él. |
| 4 | Profesor confirma su identidad en el video. | Sistema registra la técnica y deja su patrón de referencia disponible para las evaluaciones de alumnos. |
| 5 | Profesor puede modificar o retirar una técnica existente. | Sistema actualiza el catálogo y, si se retira, la técnica deja de ser evaluable por alumnos. |

#### Secuencias Alternativas
* **2a. Video con cobertura insuficiente del instructor:** El sistema rechaza el registro e indica que debe volver a grabar el material con el practicante plenamente visible.
* **4a. Edición sin cambio de referencia:** Si el profesor modifica solo los datos descriptivos (nombre, cinturón, mensaje), el sistema conserva el patrón ya registrado.
* **4b. Reemplazo de referencia:** Si el profesor aporta un nuevo video para una técnica existente, el sistema reemplaza el patrón previo y lo hace vigente para futuras evaluaciones.

#### Excepciones
* **E1. Dos técnicas con el mismo nombre:** El sistema alerta al profesor y solicita confirmación explícita antes de proceder.""",

    4: r"""### 5.4.1. Caso de Uso 4: Gestionar Teoría RAG y Mensajes del Profesor (UC-04) — Nivel de Análisis

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-04** |
| **Nombre** | Gestionar Teoría RAG y Mensajes del Profesor |
| **Actores** | **Principal:** Profesor.<br>**Secundario (Sistemas de Apoyo):** Servicio de Vectorización Multimodal, Base de Conocimiento Técnica. |
| **Descripción** | El instructor enriquece el conocimiento de la plataforma aportando manuales técnicos y redactando sus propias recomendaciones doctrinales para cada técnica. |
| **Precondiciones** | El profesor mantiene una sesión activa y ha seleccionado una técnica existente del catálogo. |
| **Postcondiciones** | 1. Los fragmentos del manual quedan disponibles para fundamentar las evaluaciones de los alumnos.<br>2. Las recomendaciones del profesor quedan asociadas a la técnica y prevalecen como directriz prioritaria. |

#### Secuencia Normal
| Paso | Intención del Actor | Respuesta Observable del Sistema |
| :---: | :--- | :--- |
| 1 | Profesor solicita enriquecer una técnica con material doctrinal. | Sistema presenta el espacio para redactar su recomendación y para aportar documentos. |
| 2 | Profesor redacta una recomendación directa para sus alumnos. | Sistema asocia el texto a la técnica y lo establece como directriz pedagógica prioritaria. |
| 3 | Profesor aporta uno o varios manuales técnicos de referencia. | Sistema recibe el material y procesa su contenido (texto e imágenes). |
| 4 | | Sistema prepara el material para que las evaluaciones futuras puedan fundamentarse en él. |
| 5 | Profesor consulta el estado del material aportado. | Sistema presenta los fragmentos indexados y el texto de su recomendación vigente. |
| 6 | Profesor puede retirar el material que él mismo aportó. | Sistema elimina la referencia de la base de conocimiento sin afectar aportes de otros instructores. |

#### Secuencias Alternativas
* **3a. Documento no procesable** (formato no soportado, sin texto legible): El sistema conserva el archivo, informa el inconveniente y solicita reintentar con otro material.
* **3b. Manual de gran extensión:** El sistema procesa el material en segundo plano e informa al profesor del avance, permitiéndole continuar con otras tareas.
* **6a. Retiro de toda la teoría de una técnica:** El profesor puede eliminar la totalidad del material que aportó sobre una técnica sin afectar la referencia biomecánica registrada.

#### Excepciones
* **E1. Servicio de vectorización no disponible:** El sistema conserva el archivo para que el profesor pueda reintentar el procesamiento cuando el servicio se restablezca.""",

    5: r"""### 5.5.1. Caso de Uso 5: Ver Progreso de Alumnos (UC-05) — Nivel de Análisis

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-05** |
| **Nombre** | Ver Progreso de Alumnos |
| **Actores** | **Principal:** Profesor, Alumno.<br>**Secundario (Sistemas de Apoyo):** Repositorio Histórico de Evaluaciones. |
| **Descripción** | El profesor supervisa la evolución técnica de sus alumnos a partir del histórico de evaluaciones; el alumno consulta su propio historial. |
| **Precondiciones** | El usuario mantiene una sesión activa como profesor o alumno. |
| **Postcondiciones** | El usuario visualiza el historial de evaluaciones filtrado por su ámbito de autorización (sucursal del profesor o cuenta propia del alumno). |

#### Secuencia Normal
| Paso | Intención del Actor | Respuesta Observable del Sistema |
| :---: | :--- | :--- |
| 1 | Profesor solicita revisar el progreso de sus alumnos. | Sistema presenta la lista de alumnos pertenecientes a su sede. |
| 2 | Profesor selecciona un alumno. | Sistema presenta el historial cronológico de evaluaciones del alumno con su grado de similitud y resumen de cada corrección. |
| 3 | Profesor profundiza en una evaluación. | Sistema presenta el detalle de la evaluación: video comparado, zonas del cuerpo afectadas y explicación pedagógica completa. |
| 4 | Alumno solicita consultar su propio historial. | Sistema presenta sus evaluaciones con la misma estructura que el profesor, sin acceso a otros alumnos. |

#### Secuencias Alternativas
* **2a. Alumno sin evaluaciones registradas:** El sistema informa que el alumno aún no cuenta con análisis realizados y sugiere invitarlo a subir su primera ejecución.
* **2b. Sucursal sin alumnos:** El sistema informa que no existen alumnos asignados a la sede del profesor.
* **3a. Profesor intenta acceder a un alumno de otra sede:** El sistema deniega la consulta e informa que el acceso está restringido a la propia sucursal.

#### Excepciones
* **E1. Historial no disponible:** El sistema informa indisponibilidad temporal del historial.""",

    6: r"""### 5.6.1. Caso de Uso 6: Activar Pase de Tatami (UC-06) — Nivel de Análisis

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-06** |
| **Nombre** | Activar Pase de Tatami (Control de Suscripciones) |
| **Actores** | **Principal:** Profesor.<br>**Secundario (Sistemas de Apoyo):** Repositorio de Membresías. |
| **Descripción** | El instructor habilita el acceso de un alumno a las funciones de análisis durante 30 días, tras verificar el pago de su mensualidad en la recepción de la academia. |
| **Precondiciones** | 1. El profesor mantiene una sesión activa.<br>2. El alumno pertenece a la misma sucursal del profesor y su acceso se encuentra en estado pendiente o vencido. |
| **Postcondiciones** | 1. El alumno queda habilitado para subir videos y solicitar análisis durante 30 días.<br>2. El vencimiento de su acceso queda calculado y será advertido cuando corresponda. |

#### Secuencia Normal
| Paso | Intención del Actor | Respuesta Observable del Sistema |
| :---: | :--- | :--- |
| 1 | Profesor solicita consultar los alumnos pendientes de habilitación en su academia. | Sistema presenta la lista de alumnos cuyo acceso requiere activación o renovación. |
| 2 | Profesor selecciona a un alumno tras verificar su pago. | Sistema solicita confirmación de la activación. |
| 3 | Profesor confirma la activación. | Sistema habilita el acceso del alumno por un periodo de 30 días y comunica la fecha de vencimiento. |
| 4 | Alumno ingresa a la plataforma. | Sistema reconoce su acceso como activo y le permite utilizar las funciones de análisis. |

#### Secuencias Alternativas
* **2a. Profesor intenta activar un alumno de otra sucursal:** El sistema deniega la operación por política de aislamiento entre sedes.
* **3a. Alumno con acceso aún vigente:** Si el acceso no ha expirado, la nueva activación extiende el plazo sumando 30 días adicionales al vencimiento actual.
* **3b. Alumno con acceso vencido:** La activación reinicia el plazo desde la fecha de confirmación.

#### Excepciones
* **E1. Servicio de membresías no disponible:** El sistema informa indisponibilidad y preserva el estado anterior.""",

    7: r"""### 5.7.1. Caso de Uso 7: Gestionar Sucursales y Coordenadas Geográficas (UC-07) — Nivel de Análisis

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-07** |
| **Nombre** | Gestionar Sucursales y Coordenadas Geográficas |
| **Actores** | **Principal:** Administrador.<br>**Secundario (Sistemas de Apoyo):** Servicio de Mapas y Localización (identificación geográfica de direcciones). |
| **Descripción** | El administrador mantiene el catálogo de sedes físicas de la academia, registrando su ubicación sobre un mapa para referencia de alumnos y profesores. |
| **Precondiciones** | El administrador mantiene una sesión activa con privilegios de gestión global. |
| **Postcondiciones** | 1. La nueva sede queda disponible para asignación de usuarios.<br>2. Su ubicación (país, ciudad, dirección y coordenadas) queda registrada para visualización cartográfica. |

#### Secuencia Normal
| Paso | Intención del Actor | Respuesta Observable del Sistema |
| :---: | :--- | :--- |
| 1 | Administrador solicita registrar una nueva sede. | Sistema presenta el formulario de alta con un mapa interactivo. |
| 2 | Administrador señala la ubicación de la sede sobre el mapa. | Sistema identifica la zona geográfica y propone los datos administrativos (país, ciudad, dirección aproximada). |
| 3 | Administrador completa o ajusta los datos propuestos y confirma. | Sistema registra la sede y la presenta en el catálogo con su marcador visible. |
| 4 | Administrador puede editar o retirar una sede existente. | Sistema actualiza el catálogo; si la sede tiene usuarios vinculados, el sistema solicita primero su reasignación. |

#### Secuencias Alternativas
* **2a. Administrador aporta un enlace de ubicación en lugar de señalar el mapa:** El sistema extrae las coordenadas y completa automáticamente los datos administrativos.
* **4a. Sede con usuarios vinculados:** El sistema impide la eliminación y sugiere primero reasignar a los usuarios a otra sede.
* **4b. Corrección de ubicación:** Si el administrador ajusta la posición del marcador sobre el mapa, el sistema actualiza las coordenadas de la sede sin alterar sus usuarios.

#### Excepciones
* **E1. Servicio de mapas no disponible:** El sistema permite registrar la sede con datos manuales (coordenadas provistas por el administrador).""",

    8: r"""### 5.8.1. Caso de Uso 8: Entrar como Otro Usuario / Impersonificación (UC-08) — Nivel de Análisis

| Campo | Especificación |
| :--- | :--- |
| **Identificador** | **UC-08** |
| **Nombre** | Entrar como Otro Usuario (Impersonificación de Soporte) |
| **Actores** | **Principal:** Administrador.<br>**Secundario:** Usuario impersonificado (alumno o profesor) como beneficiario de la operación. |
| **Descripción** | El administrador asume temporalmente la identidad de un usuario reportado por una incidencia técnica, para reproducir el problema desde la perspectiva real del usuario. La operación es acotada en el tiempo y visible en todo momento para quien la ejecuta. |
| **Precondiciones** | El administrador mantiene una sesión activa con privilegios globales. |
| **Postcondiciones** | 1. El administrador opera temporalmente como el usuario seleccionado, conservando evidencia de la operación (origen de la sesión temporal).<br>2. Al finalizar, la sesión original del administrador se restituye sin pérdida de estado. |

#### Secuencia Normal
| Paso | Intención del Actor | Respuesta Observable del Sistema |
| :---: | :--- | :--- |
| 1 | Administrador identifica al usuario afectado por una incidencia y solicita asumir su identidad para diagnóstico. | Sistema solicita reconfirmación de la autorización del administrador. |
| 2 | Administrador reconfirma su autorización. | Sistema registra la operación con sus datos de trazabilidad. |
| 3 | | Sistema presenta el entorno del usuario seleccionado y advierte de forma persistente y visible que se está operando como ese usuario. |
| 4 | Administrador reproduce la incidencia desde la vista real del usuario. | Sistema permite las operaciones que correspondan al rol del usuario impersonificado, sin alterar sus datos personales ni su historial. |
| 5 | Administrador solicita finalizar el modo de soporte. | Sistema cierra la sesión temporal y restituye la sesión original del administrador. |

#### Secuencias Alternativas
* **2a. Administrador cancela la operación antes de confirmar:** El sistema abandona el flujo sin alterar sesiones ni generar registros de impersonación.
* **4a. Intento de modificar el perfil del usuario impersonificado:** El sistema restringe las operaciones a la sola lectura y reproducción de la incidencia.
* **4b. Intento de impersonar a otro administrador:** El sistema bloquea la operación por política de jerarquía entre administradores.

#### Excepciones
* **E1. Pérdida de la sesión original del administrador durante la impersonación:** El sistema cierra forzosamente el modo de soporte y solicita al administrador autenticarse nuevamente.

> **Nota de trazabilidad técnica** (permanece vigente): la re-autenticación por contraseña y la persistencia formal en la tabla `auditoria_impersonacion` están registradas como deuda técnica para iteración futura; la emisión del token JWT con el claim `impersonator_admin_id` y la activación del banner defensivo sí se encuentran implementadas (ver §6.6 y §8.6)."""
}

def apply_analysis_use_cases():
    content = DOC_PATH.read_text(encoding="utf-8")
    
    # 1. Ajustar el párrafo introductorio de Capítulo 5 para reflejar la dualidad Análisis/Diseño
    old_intro_p1 = r"1\. \*\*Caso de Uso Detallado:\*\* Especificación textual exhaustiva con actores, precondiciones, postcondiciones, secuencia normal, secuencias alternativas y excepciones\."
    new_intro_p1 = r"1. **Caso de Uso Detallado (Nivel de Análisis / Esencial):** Especificación textual estructurada según la metodología de Craig Larman (2004, Cap. 6), orientada a capturar la intención del actor y la respuesta observable del sistema bajo el vocabulario del dominio de Jiu-Jitsu Brasileño, abstrayéndose de clases o motores tecnológicos concretos."
    
    content, count_intro = re.subn(old_intro_p1, new_intro_p1, content)
    print(f"Introducción Cap. V actualizada: {count_intro} reemplazo(s).")
    
    # 2. Reemplazar cada sección 5.X.1 por la versión de análisis
    for i in range(1, 9):
        pattern = rf"(### 5\.{i}\.1.*?)(\n---\n\n### 5\.{i}\.2)"
        new_text = USE_CASES_ANALYSIS[i]
        
        # Realizar reemplazo asegurando que se capture todo entre 5.i.1 y 5.i.2
        def replacer(match, text=new_text):
            return text + match.group(2)
            
        content, count = re.subn(pattern, replacer, content, flags=re.DOTALL)
        assert count == 1, f"Error al reemplazar sección 5.{i}.1 (coincidencias={count})"
        print(f"Sección 5.{i}.1 reemplazada exitosamente por Nivel de Análisis.")
        
    DOC_PATH.write_text(content, encoding="utf-8")
    print("Documento ProyectoGrado.md actualizado exitosamente con casos de uso esenciales.")

if __name__ == "__main__":
    apply_analysis_use_cases()

