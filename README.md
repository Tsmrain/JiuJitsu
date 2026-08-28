<!-- ========================================== -->
<!-- PÁGINA 1: PORTADA PRINCIPAL               -->
<!-- ========================================== -->

<div align="center">

<img src="./assets/upsa_logo.png" alt="Universidad Privada de Santa Cruz de la Sierra" width="280">

<br>

### FACULTAD DE INGENIERÍA
### CARRERA: INGENIERÍA DE SISTEMAS

<br>

### MODALIDAD DE GRADUACIÓN
## PROYECTO DE GRADO

<br>

## APLICACIÓN WEB CON INTELIGENCIA ARTIFICIAL PARA ANALIZAR VIDEOS DE ENTRENAMIENTO DE ARTES MARCIALES EN BRAZILIAN JIU-JITSU PARA PRACTICANTES DE LA ACADEMIA CORPO & MENTE BOLIVIA

<br><br>

### **Santiago Borda Zambrana**

<br>

**Santa Cruz de la Sierra - Bolivia**  
**2026**

</div>

<br>

---

<br>

<!-- ========================================== -->
<!-- PÁGINA 2: CARÁTULA INTERIOR / HOJA DE TÍTULO -->
<!-- ========================================== -->

<div align="center">

<img src="./assets/upsa_logo.png" alt="Universidad Privada de Santa Cruz de la Sierra" width="280">

<br>

### FACULTAD DE INGENIERÍA
### CARRERA: INGENIERÍA DE SISTEMAS

<br>

### MODALIDAD DE GRADUACIÓN
## PROYECTO DE GRADO

<br>

## APLICACIÓN WEB CON INTELIGENCIA ARTIFICIAL PARA ANALIZAR VIDEOS DE ENTRENAMIENTO DE ARTES MARCIALES EN BRAZILIAN JIU-JITSU PARA PRACTICANTES DE LA ACADEMIA CORPO & MENTE BOLIVIA

<br>

**Proyecto de Grado para optar al título de Licenciado en Ingeniería de Sistemas**

<br><br>

### **Santiago Borda Zambrana**
**Reg.: 2021210057**

<br>

**Santa Cruz de la Sierra - Bolivia**  
**2026**

</div>

<br>

---

<br>

## Tabla de Contenido

- [Capítulo I: Definición del Proyecto de Investigación](#capítulo-i-definición-del-proyecto-de-investigación)
  - [1.1 Definición del Problema](#11-definición-del-problema)
    - [1.1.1 Situación Problemática](#111-situación-problemática)
    - [1.1.2 Situación Deseada](#112-situación-deseada)
    - [1.1.3 Objeto de Investigación](#113-objeto-de-investigación)
    - [1.1.4 Alcance](#114-alcance)
    - [1.1.5 Justificación](#115-justificación)
  - [1.2 Objetivos](#12-objetivos)
    - [1.2.1 Objetivo General](#121-objetivo-general)
    - [1.2.2 Objetivos Específicos](#122-objetivos-específicos)
  - [1.3 Metodología](#13-metodología)
    - [1.3.1 Criterios de Aceptación de la Fase de Transición](#131-criterios-de-aceptación-de-la-fase-de-transición)
- [Capítulo II: Descripción de la Entidad (Corpo & Mente Bolivia)](#capítulo-ii-descripción-de-la-entidad-corpo--mente-bolivia)
  - [2.1 Descripción de la Organización](#21-descripción-de-la-organización)
  - [2.2 Estructura Organizacional](#22-estructura-organizacional)
  - [2.3 Mapeo de la Infraestructura Tecnológica Actual](#23-mapeo-de-la-infraestructura-tecnológica-actual)
  - [2.4 Flujo del Proceso de Enseñanza (El Core del Negocio)](#24-flujo-del-proceso-de-enseñanza-el-core-del-negocio)
    - [2.4.1 Identificación y Justificación Matemática del Cuello de Botella](#241-identificación-y-justificación-matemática-del-cuello-de-botella)
- [Capítulo III: Marco Teórico y Selección de Componentes Tecnológicos](#capítulo-iii-marco-teórico-y-selección-de-componentes-tecnológicos)
  - [3.1 Estimación de Poses Corporales (Pose Estimation)](#31-estimación-de-poses-corporales-pose-estimation)
    - [3.1.1 Análisis Comparativo de Extractores de Poses](#311-análisis-comparativo-de-extractores-de-poses)
    - [3.1.2 Justificación Técnica de la Elección: MediaPipe Pose](#312-justificación-técnica-de-la-elección-mediapipe-pose)
  - [3.2 Infraestructura y Cómputo en la Nube (Cloud Computing)](#32-infraestructura-y-cómputo-en-la-nube-cloud-computing)
    - [3.2.1 Análisis Comparativo de Proveedores Cloud y Modelos de Cómputo](#321-análisis-comparativo-de-proveedores-cloud-y-modelos-de-cómputo)
    - [3.2.2 Justificación Técnica de la Elección: Huawei Cloud (FunctionGraph + OBS)](#322-justificación-técnica-de-la-elección-huawei-cloud-functiongraph--obs)
  - [3.3 Algoritmos de Alineación Temporal Biomecánica](#33-algoritmos-de-alineación-temporal-biomecánica)
    - [3.3.1 Análisis Comparativo de Algoritmos de Comparación de Series](#331-análisis-comparativo-de-algoritmos-de-comparación-de-series)
    - [3.3.2 Justificación Técnica de la Elección: Dynamic Time Warping (DTW)](#332-justificación-técnica-de-la-elección-dynamic-time-warping-dtw)
  - [3.4 Procesamiento Digital de Imágenes y Generación del Entregable](#34-procesamiento-digital-de-imágenes-y-generación-del-entregable)
    - [3.4.1 Análisis Comparativo de Tecnologías de Salida Visual](#341-análisis-comparativo-de-tecnologías-de-salida-visual)
    - [3.4.2 Justificación Técnica de la Elección: Procesamiento Digital con OpenCV](#342-justificación-técnica-de-la-elección-procesamiento-digital-con-opencv)
  - [3.5 Interfaz de Usuario y Entorno de Despliegue](#35-interfaz-de-usuario-y-entorno-de-despliegue)
    - [3.5.1 Análisis Comparativo de Frameworks Web](#351-análisis-comparativo-de-frameworks-web)
    - [3.5.2 Justificación Técnica de la Elección: Streamlit](#352-justificación-técnica-de-la-elección-streamlit)
- [Capítulo IV: Definición de Requisitos](#capítulo-iv-definición-de-requisitos)
  - [4.1 Introducción](#41-introducción)
    - [4.1.1 Propósito](#411-propósito)
    - [4.1.2 Ámbito del Sistema](#412-ámbito-del-sistema)
    - [4.1.3 Definiciones, Acrónimos y Abreviaturas](#413-definiciones-acrónimos-y-abreviaturas)
    - [4.1.4 Visión General del Documento](#414-visión-general-del-documento)
  - [4.2 Descripción General](#42-descripción-general)
    - [4.2.1 Perspectiva del Producto](#421-perspectiva-del-producto)
    - [4.2.2 Funciones del Producto](#422-funciones-del-producto)
    - [4.2.3 Características de los Usuarios](#423-características-de-los-usuarios)
    - [4.2.4 Restricciones](#424-restricciones)
    - [4.2.5 Suposiciones y Dependencias](#425-suposiciones-y-dependencias)
    - [4.2.6 Requisitos Futuros](#426-requisitos-futuros)
  - [4.3 Requisitos Específicos](#43-requisitos-específicos)
    - [4.3.1 Interfaces Externas](#431-interfaces-externas)
    - [4.3.2 Requisitos Funcionales](#432-requisitos-funcionales)
    - [4.3.3 Requisitos de Rendimiento](#433-requisitos-de-rendimiento)
    - [4.3.4 Restricciones de Diseño](#434-restricciones-de-diseño)
    - [4.3.5 Atributos del Sistema](#435-atributos-del-sistema)
  - [4.4 Identificación de los Casos de Uso](#44-identificación-de-los-casos-de-uso)
  - [4.5 Diagrama de Dominio](#45-diagrama-de-dominio)

---

# Capítulo I: Definición del Proyecto de Investigación

## 1.1 Definición del Problema

### 1.1.1 Situación Problemática

En la academia **Corpo & Mente Bolivia**, ubicada en Santa Cruz de la Sierra, la enseñanza del Jiu-Jitsu Brasileño (BJJ) se fundamenta en un modelo analógico tradicional. El instructor demuestra una técnica compleja (por ejemplo, un pasaje de guardia o una finalización articular) y posteriormente supervisa de forma simultánea a grupos de 15 a 30 alumnos. Esta asimetría formativa genera los siguientes inconvenientes críticos:

1. **Saturación del canal de retroalimentación:** El instructor no puede evaluar de manera minuciosa ni en tiempo real los ángulos anatómicos ni la alineación biomecánica exacta de cada pareja de estudiantes en el tatami.
2. **Sesgo de autopercepción:** Los practicantes ejecutan movimientos con errores imperceptibles para sí mismos (inadecuado aislamiento de articulaciones, ángulos de cadera deficientes), lo que estanca su progresión técnica, genera frustración y eleva significativamente el riesgo de lesiones musculoesqueléticas.
3. **Limitación del hardware del usuario:** Los alumnos que intentan registrar sus progresos en video carecen de herramientas locales accesibles. Los modelos comerciales convencionales de Visión por Computadora exigen estaciones de trabajo equipadas con Unidades de Procesamiento Gráfico (GPU) dedicadas de alto costo, inaccesibles para el entorno informático del estudiante promedio boliviano (laptops de gama de entrada o teléfonos celulares inteligentes con capacidad de cómputo gráfico limitada).

### 1.1.2 Situación Deseada

Se proyecta el diseño e implementación de un ecosistema de software adaptativo y multiplataforma sustentado sobre una arquitectura en la nube (*Huawei Cloud*), orientado a actuar como un asistente virtual biomecánico asincrónico. En este escenario ideal:

* **Adaptabilidad de cátedra:** El profesor de Corpo & Mente carga un único video patrón con la ejecución canónica de la técnica, el cual se procesa en la nube para extraer un esqueleto matemático de referencia.
* **Carga móvil accesible:** Los estudiantes graban sus ejecuciones directamente desde sus dispositivos móviles en el tatami y las cargan a la plataforma de forma ágil y liviana.
* **Diagnóstico de precisión:** El sistema sincroniza las series temporales del video del estudiante con respecto al video maestro mediante algoritmos de Envoltura Temporal Dinámica (*Dynamic Time Warping*, DTW), detectando desviaciones geométricas exactas.
* **Retroalimentación visual directa y ligera:** El sistema consolida un registro histórico de progresión técnica del practicante. En lugar de transmitir pesados archivos de video que saturen el ancho de banda móvil, genera y despliega un **fotograma clave de falla anotado** (*annotated keyframe*). Este consiste en una imagen fija del instante exacto del error con un indicador visual (círculo de color inyectado mediante procesamiento digital de imágenes) sobre la articulación defectuosa y una alerta textual concisa. Todo el procesamiento pesado se delega a microservicios remotos bajo demanda, permitiendo una experiencia fluida sin comprometer la capacidad térmica ni energética del dispositivo local.

### 1.1.3 Objeto de Investigación

El objeto de estudio comprende la aplicación articulada de técnicas de **Visión por Computadora** (estimación de poses corporales mediante MediaPipe), **procesamiento digital de imágenes** (OpenCV), **procesamiento elástico en la nube** (*Serverless Cloud Computing*) y **algoritmos de alineación de series temporales** (*Dynamic Time Warping*, DTW) para la evaluación asincrónica automatizada de la calidad técnica deportiva y el suministro de retroalimentación biomecánica adaptativa mediante imágenes clave anotadas. Conviene puntualizar que el extractor de poses corporales (MediaPipe Pose) es una herramienta de visión artificial de propósito general que no clasifica ni identifica el tipo de deporte o disciplina marcial; el "conocimiento" biomecánico específico de Jiu-Jitsu Brasileño reside exclusivamente en el catálogo curricular de técnicas maestras y reglas deterministas de error configurado por el Head Coach, y no en una red neuronal pre-entrenada para reconocer artes marciales. En consecuencia, el sistema opera comparando esqueletos cinemáticos contra un molde de referencia seleccionado manualmente por el practicante (ver Sección 4.1.2 y requisito RF-07), sin interpretar ni clasificar la disciplina por sí mismo.

### 1.1.4 Alcance

* **Límite Funcional:** El sistema posibilitará la carga asincrónica de videos en formato estándar (`.mp4`, `.mov`) capturados desde terminales móviles, la extracción automatizada de 33 puntos clave corporales, la alineación temporal no lineal con respecto al video patrón, el cómputo de discrepancias vectoriales angulares y la generación automatizada de una imagen estática editada con un marcador sobre la falla biomecánica, desplegada a través de una interfaz web liviana (*Streamlit*).
* **Límite de Datos:** La validación algorítmica preliminar y las pruebas de estrés del módulo de extracción de poses se sustentarán en conjuntos de datos abiertos de BJJ (tales como el dataset de *ViCoS Lab*). Por su parte, la evaluación adaptativa real se efectuará exclusivamente con los videos de referencia cargados por los instructores de Corpo & Mente Bolivia y las ejecuciones prácticas de sus alumnos.
* **Exclusiones:** El sistema no realizará diagnósticos médicos, traumatológicos ni fisioterapéuticos de lesiones; tampoco ejecutará renderizado tridimensional inmersivo ni procesamiento de video en tiempo real sobre hardware local de baja gama. La interacción en el dispositivo del cliente se limitará a la recepción de matrices numéricas procesadas e imágenes optimizadas previamente en la nube.

### 1.1.5 Justificación

#### Justificación Técnica
Demuestra la viabilidad de democratizar la inteligencia artificial aplicada al deporte mediante arquitecturas híbridas (*Edge-Cloud*). Se resuelve la restricción del hardware del usuario final delegando la extracción matemática y la manipulación de la imagen a microservicios elásticos en la nube, operando bajo un costo marginal estrictamente controlado e inferior a los $30 USD trimestrales.

#### Justificación Económica y Social
Proporciona a las academias deportivas de Santa Cruz de la Sierra un factor diferenciador de vanguardia tecnológica a bajo costo. Desde la perspectiva del practicante, optimiza la curva de aprendizaje motriz, disminuye la necesidad de contratar sesiones privadas personalizadas de alto costo y mitiga la incidencia de lesiones articulares causadas por la repetición de posturas viciadas.

---

## 1.2 Objetivos

### 1.2.1 Objetivo General

Desarrollar un sistema de software adaptativo en la nube para la evaluación biomecánica y el análisis de errores en la ejecución de técnicas de Jiu-Jitsu Brasileño, que sirva como herramienta de retroalimentación asincrónica visual para los practicantes de la academia **Corpo & Mente Bolivia**, mediante el uso de estimación de poses y procesamiento distribuido.

### 1.2.2 Objetivos Específicos

1. **Analizar** los requerimientos de interacción biomecánica y el flujo operativo técnico dentro de la academia Corpo & Mente Bolivia.
2. **Diseñar** una arquitectura híbrida de cómputo que integre cubos de almacenamiento (*Huawei Cloud Object Storage Service - OBS*) con servicios de cómputo ligero bajo demanda (*FunctionGraph*) para aislar el hardware local de cargas computacionales pesadas de forma económicamente sostenible.
3. **Implementar** el pipeline matemático biomecánico integrando la normalización antropomórfica de coordenadas articulares, la compensación cinemática de oclusiones mediante Filtro de Kalman y la sincronización temporal no lineal mediante *Dynamic Time Warping* (DTW) con restricción de ventana de Sakoe-Chiba para cuantificar las desviaciones frente al patrón de referencia.
4. **Construir** una interfaz de usuario interactiva y liviana que presente la imagen estática anotada mediante OpenCV con la señalización precisa del error biomecánico y la descripción textual del fallo técnico basada en reglas deterministas.
5. **Evaluar** longitudinalmente el impacto del sistema en la progresión técnica de los practicantes a partir de los registros históricos acumulados en la plataforma, contrastando estadísticamente las evaluaciones iniciales de cada atleta contra sus registros más recientes mediante la **prueba no paramétrica de rangos con signo de Wilcoxon para muestras pareadas** (verificando previamente el supuesto de normalidad con la prueba de **Shapiro-Wilk**, o aplicando la prueba t de Student para muestras relacionadas si los datos presentan distribución normal), a fin de determinar si existe una reducción estadísticamente significativa ($p < 0.05$) en la magnitud de los errores biomecánicos con el tiempo.
6. **Medir** la tasa de adopción y uso continuado del sistema entre los practicantes de la academia durante el periodo de validación, contrastando los resultados empíricos frente a los umbrales cuantitativos propuestos como meta de validación operativa (al menos 50% de estudiantes con token activo completando cargas de video y al menos 30% de retención en sesiones posteriores), como indicador formal de viabilidad y aceptación práctica en el tatami.

---

## 1.3 Metodología

Con base en las directrices metodológicas de Craig Larman (2004), la investigación adopta el **Proceso Unificado (UP)** adaptado a un marco de trabajo ágil iterativo e incremental. El ciclo de desarrollo se estructura en cuatro fases disciplinadas, orientadas a la mitigación sistemática de riesgos tecnológicos:

* **Fase de Inicio (*Inception*):** Delimitación rigurosa del alcance del proyecto, identificación y priorización de riesgos tecnológicos críticos (tales como la latencia de red en la carga móvil y las fluctuaciones tarifarias en la nube) y consolidación de los requerimientos de negocio de la academia.
* **Fase de Elaboración (*Elaboration*):** Mitigación de los riesgos arquitectónicos de mayor impacto. Se formaliza la arquitectura base y el Modelo de Dominio. Se valida la factibilidad técnica construyendo un prototipo funcional que conecte la captura móvil con el almacenamiento en la nube (*OBS*) sin provocar estrés térmico en el cliente.
* **Fase de Construcción (*Construction*):** Desarrollo modular y desacoplado de los componentes de cómputo. Implementación de los microservicios sin servidor (*Serverless* con *FunctionGraph*), codificación del motor matemático de detección de errores (DTW con restricciones de banda), integración de los algoritmos de anotación digital sobre imágenes con OpenCV y desarrollo del frontend web reactivo en *Streamlit*.
* **Fase de Transición (*Transition*):** Despliegue del aplicativo en el entorno operativo real de Corpo & Mente Bolivia. Recolección continua de los resultados analíticos en el historial de progresión técnica de los practicantes a lo largo del periodo de prueba, contrastación estadística longitudinal entre las evaluaciones iniciales y finales de cada atleta mediante la prueba de rangos con signo de Wilcoxon para muestras pareadas (o t de Student según la verificación previa de normalidad con Shapiro-Wilk), y contrastación de las métricas de adopción real y retención de uso en el tatami frente a las metas de validación cuantitativas definidas para la redacción de las conclusiones formales del estudio.

### 1.3.1 Criterios de Aceptación de la Fase de Transición

Con el objetivo de dotar a la fase experimental de rigor metodológico y proveer un marco objetivo de contrastación científica durante la defensa del proyecto, se establecen los siguientes criterios cuantitativos de aceptación. Se deja explícitamente establecido que estos valores constituyen las **metas de validación propuestas** para la evaluación del sistema y no resultados preexistentes consolidados, dado que el aplicativo se encuentra en fase previa a su despliegue operativo en el tatami:

1. **Protocolo de Inferencia Estadística y Rigor Biomecánico:**
   * *Verificación de Supuestos:* Dado que la muestra esperada de atletas participantes de una sola academia real será acotada ($N < 30$ sujetos esperados durante la prueba piloto) y no resulta metodológicamente admisible asumir normalidad en la distribución de las discrepancias angulares motrices, se aplicará en primera instancia la **prueba de Shapiro-Wilk** con un nivel de significancia $\alpha = 0.05$ sobre las diferencias pareadas.
   * *Selección del Estadístico de Contraste:* Al preverse el no cumplimiento del supuesto de normalidad en muestras reducidas de rendimiento deportivo, el método principal de contraste será la **prueba no paramétrica de rangos con signo de Wilcoxon para muestras pareadas**, comparando la mediana de desviación angular del primer registro de cada practicante frente a la mediana de su registro más reciente. En caso de que la prueba de Shapiro-Wilk no rechace la normalidad ($p \ge 0.05$), se aplicará alternativamente la **prueba paramétrica t de Student para muestras relacionadas**.
   * *Criterio de Aceptación:* Se considerará validada la hipótesis de efectividad pedagógica si el contraste exhibe una reducción estadísticamente significativa en el error angular ($p < 0.05$), evidenciando una mejora técnica objetiva asociada a la retroalimentación asincrónica del sistema.

2. **Criterio Cuantitativo de Adopción y Retención en el Tatami:**
   * *Tasa Mínima de Activación y Carga Inicial:* Al menos el **50% de los practicantes con Código de Activación (token) vigente** durante el periodo de validación deberán completar exitosamente al menos una carga de video y recibir su reporte anotado.
   * *Tasa Mínima de Retención (Uso Recurrente):* Al menos el **30% de los practicantes que realizaron una primera carga** deberán volver a utilizar la plataforma en una o más sesiones subsiguientes de entrenamiento (tasa de retención tras el primer uso).
   * *Fundamentación de Negocio:* Estos umbrales se sustentan en la literatura sobre adopción de tecnologías digitales en disciplinas deportivas presenciales —donde la fricción asociada a la grabación en clase suele mermar el compromiso digital—, fijando un estándar cuantitativo reproducible y defendible para dictaminar la viabilidad práctica y la aceptación del producto en Corpo & Mente Bolivia.

---

# Capítulo II: Descripción de la Entidad (Corpo & Mente Bolivia)

## 2.1 Descripción de la Organización

**Corpo & Mente Bolivia** es una escuela independiente de Jiu-Jitsu Brasileño (BJJ), fundada y dirigida por su Head Coach en la ciudad de Santa Cruz de la Sierra, Bolivia. Si bien su sede principal opera dentro de las instalaciones de la academia de artes marciales **Knock Out**, Corpo & Mente constituye una entidad jurídica y operativamente autónoma que mantiene sucursales activas en diversos centros deportivos de la ciudad, tales como el gimnasio **UFC**, la academia **3 Pasos al Frente** y otros establecimientos asociados.

La organización cuenta con un padrón histórico acumulado de **72 miembros inscritos** a lo largo de su trayectoria. No obstante, la asistencia efectiva presenta una naturaleza irregular y fluctuante, propia de las dinámicas de las academias de artes marciales: un núcleo de alumnos entrena de forma constante, mientras que otros asisten de manera intermitente o retoman las clases tras periodos de inactividad prolongados que pueden extenderse hasta tres meses. La comunicación institucional entre el Head Coach y los practicantes se canaliza principalmente a través de una **comunidad oficial de WhatsApp**, la cual funciona como medio primario de coordinación de horarios, avisos operativos y convocatorias.

La entidad sustenta su propuesta de valor sobre dos pilares complementarios: la excelencia en la técnica deportiva y la preservación de la salud integral del practicante. Su población activa comprende divisiones infantiles, practicantes adultos recreativos y atletas de alto rendimiento con participación en certámenes competitivos departamentales, nacionales e internacionales.

## 2.2 Estructura Organizacional

La estructura operativa de la institución se ajusta a un modelo lineal-funcional, diseñado para garantizar la adecuada prestación de servicios deportivos y la supervisión técnica constante. Los niveles jerárquicos se distribuyen de la siguiente forma:

* **Dirección General / Head Coach:** Máxima autoridad técnica y pedagógica. Responsable de la visión estratégica institucional, la capacitación continua del cuerpo docente, la homologación curricular del plan de enseñanza del BJJ y la definición exclusiva de las técnicas maestras de referencia y el catálogo de reglas biomecánicas de error en el sistema de software.
* **Cuerpo de Instructores:** Profesionales del área deportiva encargados de conducir las sesiones prácticas, supervisar la ejecución biomecánica directa de los estudiantes en el tatami y orientar a los alumnos en el uso de la herramienta de auditoría asincrónica.
* **Área de Recepción y Atención al Cliente:** Unidad administrativa encargada del control de contratos, cobro de membresías, registro de asistencias y soporte operativo.
* **Estudiantes y Practicantes:** Usuarios receptores del servicio, constituyendo el núcleo del proceso pedagógico y los destinatarios directos de la solución tecnológica proyectada.

---

## 2.3 Mapeo de la Infraestructura Tecnológica Actual

El análisis de viabilidad técnica requiere examinar el estado de madurez de los sistemas informáticos presentes en Corpo & Mente Bolivia. La institución opera actualmente bajo una infraestructura descentralizada y de carácter estrictamente local:

* **Gestión de Datos y Membresías (Backend Local):** El control administrativo de legajos de estudiantes, datos de contacto, planes suscritos y cobranzas se gestiona de manera aislada mediante una base de datos relacional de escritorio implementada en *Microsoft Access*. La herramienta carece de mecanismos de sincronización en la nube, respaldo automatizado o interfaces de consulta remota para el cuerpo de instructores.
* **Control de Acceso Biométrico (Hardware de Entrada):** En el punto de transición hacia el área de entrenamiento (tatami), la academia cuenta con un sensor periférico de lectura de huellas dactilares. El dispositivo valida el estado administrativo del usuario consultando la base de datos local de recepción.
* **Mecanismo de Validación Física (Sistema de Tickets):** Al validarse la identidad biométrica y confirmarse la vigencia de la cuota, el terminal emite un ticket físico impreso en papel térmico. Este comprobante opera como credencial física de acceso diario; el alumno debe portarlo al tatami y entregarlo personalmente al instructor a cargo como evidencia de habilitación formal y mecanismo de control de aforo antes del inicio de la sesión.
* **Canal de Comunicación Digital (WhatsApp):** El Head Coach administra una comunidad oficial de WhatsApp que agrupa a los 72 miembros registrados de la academia. Este canal digital funciona como el medio primario de coordinación de horarios, avisos operativos, difusión de contenido técnico complementario y convocatorias a entrenamientos o competiciones. La existencia de este canal confirma que la totalidad de la base de usuarios dispone de dispositivos inteligentes con conectividad a internet.
* **Diagnóstico de Madurez Tecnológica:** Si bien la gestión administrativa es eminentemente local y analógica, la presencia de un circuito que combina software (*Microsoft Access*) con hardware periférico (*sensores biométricos* e impresoras térmicas), complementado por el uso cotidiano de una comunidad de WhatsApp como canal institucional, constata que tanto el personal como los usuarios poseen familiaridad con flujos asistidos por computadora y se encuentran habituados a la interacción digital desde dispositivos móviles. Estas circunstancias mitigan sustancialmente la resistencia al cambio y validan la factibilidad de introducir una interfaz web para la recepción de diagnósticos biomecánicos.

---

## 2.4 Flujo del Proceso de Enseñanza (El Core del Negocio)

La sesión formativa habitual dentro de Corpo & Mente Bolivia sigue una secuencia pedagógica tradicional, estructurada en cinco etapas sucesivas:

```mermaid
flowchart TD
    F1["Fase 1: Validación y Control de Acceso<br/>Recepción de tickets físicos por el instructor"] --> F2["Fase 2: Acondicionamiento Físico<br/>Calentamiento y movilidad articular (15-20 min)"]
    F2 --> F3["Fase 3: Cátedra Técnica Presencial<br/>Demostración del movimiento por el Head Coach"]
    F3 --> F4["Fase 4: Ejecución Colectiva en Parejas<br/>Práctica mecanizada en el tatami (Cuello de botella)"]
    F4 --> F5["Fase 5: Retroalimentación Asimétrica<br/>Supervisión concentrada en novatos / Desatención de avanzados"]

    classDef bottleneck fill:#ffe6e6,stroke:#cc0000,stroke-width:2px;
    class F4 bottleneck;
```

**Figura 2.1**  
*Diagrama de Flujo del Proceso Pedagógico Actual en Tatami de Corpo & Mente Bolivia.*

1. **Fase de Recepción y Control de Acceso:** El instructor recolecta los comprobantes impresos suministrados por la recepción, verificando que los 15 a 30 alumnos presentes cumplan con las disposiciones administrativas previas.
2. **Fase de Acondicionamiento Físico:** Se desarrolla una rutina colectiva de elevación de temperatura muscular, estiramiento dinámico y movilidad articular (15 a 20 minutos) destinada a preparar el sistema neuromuscular para esfuerzos mecánicos intensos.
3. **Fase de Cátedra Técnica:** Los estudiantes forman un semicírculo alrededor del instructor principal, quien desglosa biomecánicamente la técnica del día (por ejemplo, una transición desde *X-Guard*) sobre un compañero de demostración, explicando verbalmente los puntos de palanca, agarres (*grips*) y trayectorias angulares requeridas.
4. **Fase de Ejecución en Parejas (Mecanización):** Los alumnos se distribuyen por parejas y reproducen de forma sincrónica el movimiento expuesto. El docente abandona el rol de instructor magistral para asumir un rol de supervisor itinerante a lo largo de la superficie del tatami.

### 2.4.1 Identificación y Justificación Matemática del Cuello de Botella

Es precisamente en la **Fase de Ejecución en Parejas** donde se suscita el colapso del modelo pedagógico analógico, debido a las limitaciones cuantitativas de tiempo y capacidad de cobertura humana:

* **Asimetría del Feedback Itinerante:** Considerando una clase promedio de 20 estudiantes (10 parejas en simultáneo) y un segmento de práctica técnica activa de 30 minutos netos, el docente dispone, en el mejor de los casos teóricos, de un máximo de:
  
  $$\text{Tiempo por Pareja} = \frac{30 \text{ minutos}}{10 \text{ parejas}} = 3 \text{ minutos por pareja}$$
  
  Asumiendo desplazamientos continuos e instantáneos sin tiempos muertos. En términos reales, el acompañamiento suele ser inferior a los 90 segundos efectivos por estudiante.
* **Sesgo de Priorización Pedagógica:** Ante la escasez crítica de tiempo, el docente prioriza a los estudiantes novatos (*cinturones blancos*), ya que carecen de patrones motores consolidados, exhiben errores estructurales evidentes y presentan una vulnerabilidad sustancialmente mayor frente a lesiones musculoesqueléticas.
* **Desatención Sistemática de Practicantes Avanzados:** La focalización en los principiantes conduce a que los alumnos graduados reciban lapsos de observación prácticamente nulos. En este segmento, las incorrecciones técnicas no son gruesas sino milimétricas (desviaciones angulares de cadera de pocos grados o deficiente orientación de los vectores de fuerza). Estos fallos sutiles terminan fijándose involuntariamente en la memoria neuromuscular del atleta, estancando su potencial competitivo y generando frustración técnica.

* **Resolución y Validación Matemática del Cuello de Botella Mediante Cómputo Concurrente:** Frente al límite físico estrictamente secuencial del docente ($T_{\text{secuencial}} = 30 \text{ minutos}$ distribuidos a razón de $\leq 90 \text{ segundos}$ por estudiante), la solución asincrónica en la nube introduce un modelo de procesamiento elástico masivamente paralelo. Considerando que las $P = 10$ parejas (20 alumnos) capturen y carguen sus videos al concluir simultáneamente la serie de mecanización técnica, el tiempo global de respuesta del sistema distribuido se formula como:

  $$T_{\text{sistema}} = \max_{i=1}^{P} \left( t_{\text{subida}, i} + t_{\text{serverless}, i} + t_{\text{bajada}, i} \right)$$

  Bajo las condiciones operativas especificadas ($t_{\text{subida}} \approx 2.5\text{ s}$ para videos de hasta 5 MB en redes 4G/LTE, $t_{\text{serverless}} \leq 4.0\text{ s}$ en *FunctionGraph* y $t_{\text{bajada}} \approx 0.2\text{ s}$ para el fotograma anotado de $\sim 80\text{ KB}$), el tiempo total de procesamiento concurrente no supera los **$6.7\text{ segundos}$**. Al ejecutarse cada análisis en instancias elásticas desacopladas e independientes de *FunctionGraph*, las 10 parejas reciben su retroalimentación visual anotada en menos de $7\text{ segundos}$ de forma simultánea, transformando un proceso secuencial saturado de $30\text{ minutos}$ en una respuesta analítica casi instantánea, descongestionando efectivamente el tatami.

El diagnóstico confirma que el docente presencial ha superado su límite cognitivo de supervisión itinerante. El asistente tecnológico no reemplaza la pedagogía del profesor, sino que amplifica su capacidad de auditoría mediante un canal visual asincrónico y objetivo.

---

# Capítulo III: Marco Teórico y Selección de Componentes Tecnológicos

Este capítulo establece los fundamentos tecnológicos y algoritmos base que sustentan el ecosistema de software propuesto. Se aplica un enfoque analítico comparativo mediante matrices de decisión ponderadas para justificar formalmente la selección de cada componente tecnológico frente a las alternativas disponibles en el mercado científico y comercial.

## 3.1 Estimación de Poses Corporales (*Pose Estimation*)

La extracción de esqueletos articulares (puntos clave o *landmarks*) a partir de fuentes de video digital constituye el núcleo del análisis biomecánico. A fin de asegurar la sostenibilidad económica y el escalamiento elástico del sistema en la nube, se requiere un extractor computacionalmente eficiente que prescinda de hardware gráfico dedicado masivo.

### 3.1.1 Análisis Comparativo de Extractores de Poses

Se contrastan las tres tecnologías más representativas del estado del arte: **MediaPipe Pose** (Google), **OpenPose** (Carnegie Mellon University) y **YOLOv8-Pose** (Ultralytics).

**Tabla 3.1**  
*Matriz de Selección para Estimación de Poses*

| Criterios de Selección | Peso (%) | MediaPipe Pose | OpenPose | YOLOv8-Pose |
| :--- | :---: | :---: | :---: | :---: |
| Densidad de Puntos Clave (Anatomía) | 25% | 5 (33 puntos) | 4 (25 puntos) | 3 (17 puntos) |
| Eficiencia en CPU (Costo en Nube) | 30% | 5 (Ultra liviano) | 1 (Exige GPU) | 3 (Moderado) |
| Licenciamiento y Restricciones | 20% | 5 (Apache 2.0) | 1 (Comercial pago) | 2 (AGPL-3.0) |
| Robustez en Modelos de Suelo | 25% | 3 (Regular) | 4 (Bueno) | 4 (Bueno) |
| **Puntaje Ponderado Total** | **100%** | **4.50** | **2.50** | **3.05** |

*Nota*. Escala de evaluación: 1 (Deficiente) al 5 (Excelente). Ponderación sobre base de 100%.

### 3.1.2 Justificación Técnica de la Elección: MediaPipe Pose

El análisis multicriterio posiciona a **MediaPipe Pose** como la alternativa superior, alcanzando una valoración ponderada de **4.50 / 5.00**.

* **Ventaja Anatómica:** MediaPipe extrae 33 puntos clave frente a los 17 detectados por YOLOv8. Estos nodos adicionales incorporan la topología completa de tobillos y pies, áreas anatómicas indispensables dentro del Jiu-Jitsu para evaluar ganchos de control, pasos de guardia y distribución del equilibrio.
* **Justificación del Descarte de Alternativas:** OpenPose se descarta debido a su arquitectura convolucional pesada de tipo *Bottom-Up*, la cual demanda aceleración por hardware (Nvidia CUDA) para alcanzar rendimientos aceptables, lo que elevaría la infraestructura cloud a costos prohibitivos. A su vez, YOLOv8-Pose se desestima por su licencia restrictiva AGPL-3.0 y su baja resolución articular (17 nodos), insuficiente para el seguimiento biomecánico fino.
* **Estrategia de Mitigación de Oclusiones:** En el Jiu-Jitsu Brasileño, la práctica técnica se desarrolla inherentemente en parejas (replicando fielmente la Fase 4 de mecanización en tatami descrita en la Sección 2.4), lo que genera contacto físico estrecho y oclusiones parciales inevitables debidas a los agarres y la superposición de extremidades. El sistema asume esta realidad operativa mediante un protocolo de captura en "laboratorio técnico" que estandariza el encuadre (toma lateral fija, iluminación homogénea y ambos practicantes dentro de cuadro), sin desnaturalizar el entrenamiento con compañero ni exigir condiciones irreales de ejecución en solitario. Para resolver las oclusiones anatómicas en video real de entrenamiento, el algoritmo monitorea el vector de confiabilidad articular ($C \in [0.0, 1.0]$) reportado por MediaPipe. Cuando la visibilidad de una articulación desciende de $C < 0.5$ producto de un agarre o cruce corporal, el backend activa un **Filtro de Kalman cinemático** (formalizado en el RF-08) que modela la inercia y los vectores de velocidad para interpolar con rigor matemático la trayectoria espacial a partir de los cuadros adyacentes, preservando la continuidad métrica indispensable para la posterior alineación con DTW. Sin embargo, para salvaguardar la validez física del modelo frente a oclusiones completas y prolongadas (propias de inmovilizaciones o controles laterales estáticos), se define un límite máximo continuo de interpolación (1.5 segundos o 45 fotogramas a 30 fps como parámetro configurable); superado este umbral, el filtro cesa la predicción inercial y activa el flujo de rechazo formalizado en los requisitos RF-08 y RF-11 para salvaguardar la integridad pedagógica y estadística de los datos del practicante evitando contaminar su historial longitudinal con cinemáticas ficticias, asumiendo técnicamente que el cómputo serverless ejecutado hasta el punto de interrupción ya ha sido facturado por milisegundos de CPU.

---

## 3.2 Infraestructura y Cómputo en la Nube (*Cloud Computing*)

A fin de respetar la restricción presupuestaria de operar con un costo inferior a los $30 USD trimestrales, la arquitectura no puede depender de servidores dedicados encendidos permanentemente (IaaS). Se precisa un modelo de cómputo elástico, reactivo y orientado a eventos (*Serverless*).

### 3.2.1 Análisis Comparativo de Proveedores Cloud y Modelos de Cómputo

Se analizan los entornos *Serverless* y de almacenamiento de objetos distribuidos provistos por **Huawei Cloud**, **Amazon Web Services (AWS)** y **Google Cloud Platform (GCP)**.

**Tabla 3.2**  
*Matriz de Selección de Infraestructura Cloud*

| Criterios de Selección | Peso (%) | Huawei Cloud | AWS | Google Cloud |
| :--- | :---: | :---: | :---: | :---: |
| Modelo de Costo (Serverless) | 35% | 5 (FunctionGraph) | 4 (Lambda) | 4 (Cloud Functions) |
| Tarifa de Salida de Datos (*Egress*) | 30% | 5 (Bajo costo regional) | 2 (Altas tasas) | 3 (Moderado) |
| Herramientas Nativas de Video | 15% | 3 (Genéricas) | 5 (Rekognition) | 5 (Video Intelligence) |
| Soporte Local y Alianzas Académicas | 20% | 5 (Presencia en Bolivia) | 2 (Indirecto) | 2 (Automatizado) |
| **Puntaje Ponderado Total** | **100%** | **4.80** | **3.35** | **3.55** |

*Nota*. Evaluación técnica adaptada a los requerimientos de tráfico regional y presupuesto en Bolivia.

### 3.2.2 Justificación Técnica de la Elección: Huawei Cloud (FunctionGraph + OBS)

**Huawei Cloud** obtiene el liderazgo comparativo con una calificación de **4.80 / 5.00**, sustentado en sus ventajas de costos y presencia institucional en Bolivia.

* **Eficiencia del Paradigma Serverless:** Se desestima el uso de plataformas complejas de aprendizaje profundo continuo (tales como ModelArts) para la fase de inferencia cotidiana, redirigiendo la carga hacia *FunctionGraph*. Cuando un estudiante carga un archivo de video al contenedor de *Object Storage Service* (OBS), se dispara un disparador (*trigger*) asincrónico que inicializa la función *Serverless*. Ésta procesa el flujo mediante MediaPipe y DTW en cuestión de milisegundos y finaliza de inmediato. El costo se limita rigurosamente a los milisegundos de CPU consumidos, eliminando gastos por tiempos ociosos.
* **Justificación del Descarte de Alternativas:** Las herramientas analíticas de video de AWS (Rekognition) y Google Cloud (Video Intelligence) fueron desestimadas debido a que operan a un nivel de abstracción semántico macroscópico (reconocen categorías generales como "tatami" o "persona practicando deporte"), siendo incapaces de calcular discrepancias angulares articulares en grados. Adicionalmente, las tarifas de transferencia de salida (*Egress Data*) aplicadas por AWS y GCP hacia operadoras sudamericanas resultan sensiblemente elevadas respecto a la estructura tarifaria de Huawei Cloud.

---

## 3.3 Algoritmos de Alineación Temporal Biomecánica

En la ejecución motriz deportiva, dos atletas jamás ejecutarán una misma secuencia bajo idéntica duración ni sincronía temporal estricta; el instructor puede completar un movimiento en 4 segundos y el estudiante en 7 segundos. Resulta imprescindible aplicar una alineación no lineal de las series temporales antes de cuantificar cualquier error biomecánico.

### 3.3.1 Análisis Comparativo de Algoritmos de Comparación de Series

Se contrastan el algoritmo **Dynamic Time Warping (DTW)**, la **Distancia Euclidiana Directa (ED)** y arquitecturas de **Redes Neuronales Recurrentes / Secuenciales (LSTM / Transformers)**.

**Tabla 3.3**  
*Matriz de Selección para Alineación Temporal*

| Criterios de Selección | Peso (%) | Dynamic Time Warping (DTW) | Distancia Euclidiana | Redes LSTM / Transformers |
| :--- | :---: | :---: | :---: | :---: |
| Flexibilidad ante Longitudes Variables | 30% | 5 (Excelente) | 1 (Incompatible) | 4 (Buena) |
| Explicabilidad Matemática (Caja Blanca) | 25% | 5 (Vectores y ángulos claros) | 5 (Trivial) | 1 (Caja negra/Pesos ocultos) |
| Volumen de Datos Requerido | 25% | 5 (Cero muestras previas) | 5 (Cero muestras) | 1 (Exige miles de muestras) |
| Eficiencia y Complejidad de Cómputo | 20% | 4 (Optimizado $O(N)$) | 5 (Instantáneo) | 2 (Inferencia pesada) |
| **Puntaje Ponderado Total** | **100%** | **4.80** | **3.80** | **2.15** |

*Nota*. Evaluación basada en la adaptabilidad a nuevas técnicas deportivas sin re-entrenamiento neuronal.

### 3.3.2 Justificación Técnica de la Elección: Dynamic Time Warping (DTW)

El algoritmo **DTW** se erige como la solución idónea con una calificación de **4.80 / 5.00**, preservando la capacidad adaptativa esencial del sistema.

* **Naturaleza Adaptativa sin Re-entrenamiento:** Al sustentarse en la optimización matemática clásica (programación dinámica para localizar el camino de mínimo costo en una matriz de distancias acumuladas), DTW no demanda conjuntos de entrenamiento masivos. Si el instructor de Corpo & Mente decide incorporar una técnica novedosa o variante no contemplada previamente, el software la asimila de forma inmediata requiriendo únicamente el video patrón como nuevo molde cinemático.
* **Normalización Antropomórfica:** El enfoque solventa las diferencias de complexión física entre practicantes (niños, mujeres y adultos). Antes del análisis matricial, el algoritmo ejecuta una normalización geométrica vectorial tomando como longitud unitaria de referencia la distancia interclavicular o la altura del tronco. De este modo, la comparación no se basa en coordenadas pixelares absolutas, sino en relaciones angulares y proporciones relativas. Una extensión del codo a 45° representa el mismo valor métrico en un infante de 25 kg que en un adulto de 95 kg.
* **Invariancia Traslacional y Métrica de Entrada:** Para garantizar que la comparación no se vea afectada por la posición espacial de los practicantes en el tatami (traslación en X, Y), el motor matemático no alimenta al DTW con las coordenadas absolutas de MediaPipe. Previa a la ejecución del DTW, el sistema transforma las coordenadas (X,Y,Z) en una **serie temporal de ángulos articulares relativos** (ej. ángulo entre hombro-codo-muñeca) y vectores de huesos normalizados. El DTW se ejecuta exclusivamente sobre estas series de ángulos, garantizando que la métrica de error biomecánico sea invariante a la ubicación espacial del practicante.
* **Optimización Mediante Ventana de Sakoe-Chiba Configurable:** Para neutralizar la complejidad temporal cuadrática nativa del algoritmo ($O(N^2)$)—la cual elevaría el consumo de CPU en la función *Serverless*—se implementa la restricción geométrica de la **Ventana de Sakoe-Chiba**. Esta técnica acota la exploración de la trayectoria óptima a una banda diagonal de ancho $w$ alrededor del eje principal de la matriz de costo. En el presente diseño se define como **valor por defecto recomendado** una restricción formal equivalente al **15% de la longitud temporal de la secuencia ($w = 0.15 \cdot N$)**. Para una grabación estándar de hasta 6 segundos a 30 cuadros por segundo ($N \approx 180$ fotogramas), este valor fija una ventana de tolerancia de $w \approx \pm 27$ cuadros ($\pm 0.9\text{ segundos}$). No obstante, este valor no opera como una constante rígida en código, sino como un **parámetro configurable del backend** (adaptable por técnica o por rango de duración del video patrón y almacenable como atributo `ventanaSakoeChiba` en la entidad `TecnicaMaestra` del modelo de dominio, sección 4.5), lo que otorga la flexibilidad de calibrar ventanas más estrechas para transiciones explosivas o más holgadas para ejecuciones lentas sin modificar el código fuente. Esta parametrización absorbe con rigor las variaciones de cadencia motriz entre el profesor y el alumno, reduciendo el espacio de búsqueda a un régimen estrictamente cuasi-lineal $O(N)$ con tiempos de cómputo algorítmico de apenas $80 \text{ a } 150\text{ ms}$ en *FunctionGraph*.

---

## 3.4 Procesamiento Digital de Imágenes y Generación del Entregable

En términos operativos, el sistema no emite un juicio subjetivo ni cualitativo sobre la calidad de la ejecución: su criterio de evaluación consiste estrictamente en medir la desviación angular de cada articulación respecto al video patrón maestro y contrastarla cuantitativamente contra el umbral de tolerancia técnica definido por el Head Coach para esa técnica específica. Una vez identificado el fotograma exacto donde dicha discrepancia excede el umbral tolerado, el sistema debe estructurar y retornar el diagnóstico al usuario final de forma instantánea.

### 3.4.1 Análisis Comparativo de Tecnologías de Salida Visual

Se evalúa la estrategia de **Renderizado de Video Completo Editado** (mediante *FFmpeg / MoviePy*) frente al paradigma de **Extracción de Fotograma Clave de Falla Anotado** (mediante *OpenCV*).

**Tabla 3.4**  
*Matriz de Selección para el Entregable Visual*

| Criterios de Selección | Peso (%) | OpenCV (Fotograma Clave Anotado) | FFmpeg (Video Renderizado) |
| :--- | :---: | :---: | :---: |
| Ancho de Banda Consumido (*Egress*) | 40% | 5 (~80 KB por JPG) | 1 (~15 MB por MP4) |
| Eficacia Pedagógica Deportiva | 25% | 5 (Congela el punto de error) | 3 (Dinámico y fugaz) |
| Carga de Cómputo en la Nube | 20% | 5 (Edición inmediata en RAM) | 1 (Re-codificación H.264 lenta) |
| Experiencia en Interfaz Móvil | 15% | 5 (Despliegue instantáneo) | 2 (Demoras por almacenamiento en búfer) |
| **Puntaje Ponderado Total** | **100%** | **5.00** | **1.75** |

*Nota*. Evaluación técnica ponderada para mitigar el consumo de datos y la latencia en dispositivos móviles.

### 3.4.2 Justificación Técnica de la Elección: Procesamiento Digital con OpenCV

La selección del **Fotograma Clave Anotado con OpenCV** alcanza una ponderación perfecta de **5.00 / 5.00**, maximizando la viabilidad operativa y económica del proyecto.

* **Arquitectura de Cómputo Eficiente:** Renderizar un video completo anotado obligaría a invocar procesos de codificación H.264 pesados, consumiendo valiosos segundos de cómputo en la nube y generando archivos de más de 15 MB. Con OpenCV, la función *Serverless* aísla en memoria el fotograma correspondiente al pico de desviación angular, extrae la tupla de coordenadas espaciales $(X, Y)$ de la articulación deficiente (por ejemplo, la rodilla) e inyecta directamente sobre la matriz de píxeles un círculo marcador de color rojo junto con una etiqueta textual.
* **Control Estricto de Costos de Salida de Datos:** Un archivo de imagen JPG procesado y comprimido con OpenCV promedia escasos **~80 KB** (con un techo máximo garantizado de **100 KB** según el requisito RP-02). La transmisión de esta carga hacia el dispositivo móvil del estudiante elimina cualquier riesgo de sobrecosto por volumen de salida (*Data Egress*). Para el volumen operacional regular de la academia (entre 200 y 350 consultas mensuales), el consumo mensual demandado oscila con exactitud entre **16.0 MB** ($200 \times 80\text{ KB}$) y **28.0 MB** ($350 \times 80\text{ KB}$), alcanzando a lo sumo 35.0 MB bajo el tamaño límite de 100 KB. Incluso bajo un escenario de estrés extremo con 2,700 consultas mensuales proyectadas, el tráfico transferido se sitúa entre **216 MB** ($2,700 \times 80\text{ KB}$) y **270 MB** ($2,700 \times 100\text{ KB}$). En todos los escenarios evaluados, el gasto por transferencia de salida es inferior a los $0.03 USD mensuales (considerando la tarifa regional de Huawei Cloud de ~$0.08 USD/GB), blindando con exactitud matemática el presupuesto operativo trimestral establecido (< $30 USD).
* **Valor Pedagógico sin Fricción:** En las artes marciales de agarre como el BJJ, las posiciones de dominio (guardias, montadas, controles laterales) son esencialmente estructuras biomecánicas estáticas de presión. Un video en movimiento oculta la fracción de segundo donde falló el ángulo. El fotograma estático opera como una auditoría visual quirúrgica: el practicante consulta su teléfono en el tatami y reconoce inmediatamente el círculo sobre el miembro mal posicionado, facilitando la asimilación e intervención motriz instantánea.

---

## 3.5 Interfaz de Usuario y Entorno de Despliegue

La aplicación de cara al usuario debe comportarse como un cliente ultra liviano, capaz de desplegarse fluidamente en smartphones de gama de entrada y laptops convencionales comúnmente utilizados por los practicantes de la academia.

### 3.5.1 Análisis Comparativo de Frameworks Web

Se comparan **Streamlit**, el esquema **Flask + React.js** y **Dash (Plotly)**.

**Tabla 3.5**  
*Matriz de Selección del Framework Web Frontend*

| Criterios de Selección | Peso (%) | Streamlit (Seleccionado) | Flask + React.js | Dash (Plotly) |
| :--- | :---: | :---: | :---: | :---: |
| Velocidad de Construcción | 30% | 5 (Python nativo / Ágil) | 2 (Lenta / Múltiples entornos) | 4 (Moderada) |
| Consumo de RAM en Cliente Móvil | 35% | 5 (Bajo / Renderizado HTML simple) | 4 (Variable / Paquete JS pesado) | 2 (Elevado por graficación) |
| Integración Visual de Imágenes | 20% | 5 (Directa y nativa) | 4 (Demanda componentes a medida) | 3 (Enfocado a series analíticas) |
| Facilidad de Desacoplamiento | 15% | 5 (Enlace directo a servicios) | 3 (Requiere API REST intermedia) | 4 (Moderada) |
| **Puntaje Ponderado Total** | **100%** | **5.00** | **3.30** | **3.05** |

*Nota*. Escala de evaluación: 1 (Deficiente) al 5 (Excelente). Ponderación total: 100%.

### 3.5.2 Justificación Técnica de la Elección: Streamlit

**Streamlit** es ratificado con una puntuación máxima de **5.00 / 5.00**.

* **Preservación del Hardware del Cliente y Ergonomía Térmica:** Dado que el producto final consiste en una imagen fija pre-procesada en la nube y un conjunto reducido de métricas numéricas en formato texto, Streamlit provee un entorno idóneo. La interfaz opera como un visor ligero que no delega en el navegador móvil la ejecución de módulos de decodificación de video, transformaciones espaciales en *Canvas 3D* ni complejas rutinas de procesamiento en JavaScript. Esto minimiza el consumo de memoria RAM, protege la autonomía de la batería y previene el sobrecalentamiento de terminales de gama modesta en el entorno del gimnasio.

---

# Capítulo IV: Definición de Requisitos

## 4.1 Introducción

### 4.1.1 Propósito

El propósito del presente documento es especificar formal, exhaustiva y rigurosamente los **requisitos funcionales y no funcionales** que rigen la construcción del asistente virtual biomecánico asincrónico para la academia Corpo & Mente Bolivia. Este pliego técnico define el marco contractual base entre los investigadores, los desarrolladores y el tribunal evaluador para las fases de Construcción y Transición del ciclo de vida del software.

### 4.1.2 Ámbito del Sistema

El sistema de evaluación y retroalimentación biomecánica para la academia Corpo & Mente Bolivia comprende en su alcance operativo:

1. La captura de video desde teléfonos móviles por parte de los practicantes en el tatami.
2. La carga y persistencia en cubos elásticos de almacenamiento en la nube (*Huawei Cloud OBS*).
3. La ejecución remota sin servidor (*Serverless*) de los módulos de extracción de coordenadas articulares (*MediaPipe Pose*) y sincronización de series de tiempo (*DTW* con ventana de Sakoe-Chiba).
4. El procesamiento digital de imágenes (*OpenCV*) para inyectar marcadores de color sobre la coordenada del error biomecánico detectado.
5. El despliegue visual inmediato del fotograma clave anotado e indicadores estadísticos a través de un cliente web liviano (*Streamlit*).

**Exclusiones explícitas:** Se excluye el acceso público abierto o anónimo (el sistema restringe el procesamiento exclusivamente a practicantes autorizados mediante un token de acceso para salvaguardar el presupuesto de cómputo en la nube), el procesamiento local de video en los dispositivos de los usuarios, el análisis multi-persona en tiempo real durante combates libres (*rolling/spárring*) y cualquier dictamen de orden médico, traumatológico o fisioterapéutico. Asimismo, se excluye explícitamente cualquier módulo de reconocimiento o clasificación automática de la técnica deportiva a partir del video; esta es una **decisión de diseño deliberada** para mantener la solución dentro de la estricta restricción presupuestaria de **$30 USD trimestrales**, toda vez que un clasificador de acciones entrenado requeriría una infraestructura de cómputo y un volumen de datos sustancialmente superiores. En su lugar, el sistema delega la identificación de la técnica al propio estudiante mediante selección manual guiada desde el catálogo curricular web previo a la carga del archivo (RF-07).

### 4.1.3 Definiciones, Acrónimos y Abreviaturas

* **BJJ (*Brazilian Jiu-Jitsu*):** Jiu-Jitsu Brasileño. Arte marcial y deporte de combate centrado en técnicas de agarre, derribos, transiciones en el suelo y sumisiones mecánicas.
* **DTW (*Dynamic Time Warping*):** Envoltura Temporal Dinámica. Algoritmo no lineal para medir la similitud y alinear secuencias que evolucionan a diferentes velocidades.
* **OBS (*Object Storage Service*):** Servicio de almacenamiento de objetos escalable y seguro provisto por la plataforma Huawei Cloud.
* **FunctionGraph:** Servicio de computación *Serverless* orientada a eventos provisto por Huawei Cloud, el cual ejecuta código sin necesidad de aprovisionar ni administrar instancias de servidores.
* **Keyframe (Fotograma Clave):** Cuadro estático individual extraído de una secuencia de video que captura un momento biomecánico significativo.
* **Oclusión:** Obstrucción física o visual de una articulación corporal ocasionada por la superposición de extremidades propias o del compañero de entrenamiento.

### 4.1.4 Visión General del Documento

La estructura de este capítulo sigue el estándar internacional de especificación de requerimientos: la sección 4.2 presenta la perspectiva general del producto y el perfil de sus usuarios; la sección 4.3 detalla los requisitos específicos (interfaces, funcionales, de rendimiento y de calidad).

---

## 4.2 Descripción General

### 4.2.1 Perspectiva del Producto

El software se estructura como un sistema distribuido híbrido *Edge-Cloud* que convive de manera asincrónica con la actual infraestructura administrativa local de Corpo & Mente Bolivia (base de datos en *Microsoft Access* y torniquete biométrico). Esta coexistencia responde a una **decisión de arquitectura deliberada** sustentada en la siguiente secuencia de diseño:

1. El software de escritorio en *Microsoft Access* constituye un **sistema administrativo legado fuera del alcance del proyecto**, operado localmente en recepción para cobranzas y aforo físico.
2. Intentar una sincronización en tiempo real contra *Access* implicaría introducir dependencias técnicas críticas, vulnerabilidades de conectividad y sobrecargas de mantenimiento que escapan al control del equipo de desarrollo (carencia de APIs nativas, dependencia de túneles de red locales y riesgo de inestabilidad operativa).
3. En consecuencia, se optó conscientemente por el **aislamiento de datos** como **estrategia de mitigación de riesgo** a corto plazo, implementando una **base de datos relacional independiente en la nube (PostgreSQL gestionado en Cloud)**. Bajo este enfoque, el practicante crea una cuenta web dedicada en la plataforma pedagógica, totalmente desacoplada del sistema de recepción.
4. Cualquier mecanismo de interoperabilidad o sincronización automatizada entre ambos mundos queda formalmente diferido a la sección 4.2.6 (*Requisitos Futuros*).

Bajo este marco de aislamiento deliberado, la coexistencia de una cuenta de usuario web junto con un token de activación mensual responde a una clara separación arquitectónica de responsabilidades: la **cuenta web en PostgreSQL** resuelve la **identidad digital persistente y el historial técnico del estudiante** (permitiendo que el atleta conserve sus evaluaciones acumuladas a lo largo del tiempo, incluso si suspende temporalmente sus entrenamientos), mientras que el **Código de Activación Mensual (Token de Acceso)** resuelve de forma exclusiva la **protección del presupuesto operativo en la nube**, impidiendo que usuarios inactivos, externos o con cuotas impagas ejecuten cómputo serverless costoso. Este desacoplamiento salvaguarda el crédito financiero de Huawei Cloud sin introducir dependencias tecnológicas frágiles con la recepción de la academia.

### 4.2.2 Funciones del Producto

* **Gestión de Técnicas Maestras:** Permite exclusivamente al Head Coach registrar los videos patrón que conforman el currículo oficial, especificando su categoría técnica y su posición de origen para catalogar variantes sin ambigüedad ni nombres duplicados, definiendo además el catálogo de reglas biomecánicas deterministas y la calibración de la ventana temporal.
* **Ingestión Móvil de Entrenamientos:** Facilita al estudiante explorar el catálogo curricular estructurado jerárquicamente en dos niveles (agrupado primero por categoría técnica y luego por posición de origen, ej. "Llave de Brazo → [Montada, Guardia Cerrada, Side Control]") para seleccionar con precisión la variante exacta a evaluar sin ambigüedad, y cargar de forma rápida la grabación de su ejecución en pareja desde el tatami bajo una doble capa de control de tamaño y duración.
* **Auditoría Biomecánica en la Nube:** Ejecuta de forma elástica la detección de puntos clave corporales con MediaPipe, la compensación cinemática de oclusiones con Filtro de Kalman (con interrupción controlada ante oclusiones prolongadas), la normalización antropomórfica y la sincronización temporal con DTW.
* **Anotación Automatizada de Fallas:** Localiza el fotograma de máxima discrepancia e inyecta la señalética gráfica sobre la articulación defectuosa mediante OpenCV.
* **Generación de Explicación Pedagógica:** Formula una explicación textual comprensible sobre la causa motriz del error (el "por qué"), generada de forma determinista mediante reglas predefinidas para cada técnica sin recurrir a IA generativa.
* **Visualización de Reportes Técnicos:** Entrega al estudiante el fotograma estático de falla, la explicación textual del error y su evolución técnica histórica acumulada de forma inmediata y con mínimo consumo de datos.

### 4.2.3 Características de los Usuarios

* **Head Coach / Director Técnico:** Máxima autoridad pedagógica con dominio experto en biomecánica de combate y competencias informáticas de usuario final. Posee la facultad exclusiva de registrar y calibrar las técnicas maestras curriculares y su catálogo asociado de reglas de error.
* **Estudiante / Practicante:** Alumnos de diversos niveles y contexturas físicas con membresía activa en la academia. Acceden a la plataforma desde sus propios teléfonos inteligentes empleando redes móviles comerciales (4G/LTE/5G) para seleccionar técnicas, cargar videos de práctica en pareja y consultar sus diagnósticos biomecánicos.

### 4.2.4 Restricciones

* **Presupuesto Operativo Máximo:** El consumo total facturable por servicios de Huawei Cloud (almacenamiento en OBS y cómputo en *FunctionGraph*) debe mantenerse por debajo de los **$30 USD trimestrales**.
* **Aislamiento del Hardware Local:** Queda terminantemente restringido el uso intensivo de la memoria RAM, la CPU o aceleradores gráficos locales del cliente para tareas de inferencia de modelos de visión artificial.
* **Condiciones de Conectividad:** El sistema debe operar eficientemente bajo las condiciones asimétricas de ancho de banda y velocidades de carga (*Upload*) prevalentes en las redes de telefonía móvil de Santa Cruz de la Sierra.

### 4.2.5 Suposiciones y Dependencias

* Se asume que el alumno registrará la ejecución técnica junto a su compañero de entrenamiento bajo el protocolo de "laboratorio técnico" (encuadre lateral fijo donde ambos practicantes permanecen dentro de cuadro y sin interferencia de terceros en la escena). Se asume la presencia de oclusiones anatómicas parciales normales derivadas del agarre y contacto físico entre ambos practicantes, las cuales son compensadas algorítmicamente en el backend mediante el Filtro de Kalman cinemático (RF-08).
* El funcionamiento del sistema depende de la disponibilidad del servicio *FunctionGraph* y de los contenedores Linux de Huawei Cloud para la ejecución de la biblioteca *MediaPipe Pose*.
* **Control de Acceso y Salvaguarda de Costos Cloud (Regla de Negocio RN-01):** Para impedir que usuarios externos o estudiantes inactivos consuman saldo de cómputo en *Huawei Cloud*, el sistema web exige que el practicante ingrese un **Código de Activación Mensual (Token de Acceso)** para habilitar el formulario de carga de video. Este token es emitido periódicamente por el Head Coach (a través de la comunidad oficial de WhatsApp) o entregado impreso en la recepción junto con el ticket físico diario a los alumnos con membresía vigente. La interfaz web en *Streamlit* valida la vigencia del token antes de autorizar cualquier transferencia de archivos hacia *Huawei Cloud OBS*, bloqueando peticiones no autorizadas y blindando el presupuesto operativo de la nube.

### 4.2.6 Requisitos Futuros

* Integración mediante servicios web (API REST) con la base de datos de administración en *Microsoft Access* para sincronizar de manera automatizada las membresías activas.
* Extensión hacia modelos de seguimiento simultáneo multi-persona en plano general durante fases de combate real (*rolling* o spárring libre).

---

## 4.3 Requisitos Específicos

### 4.3.1 Interfaces Externas

#### 4.3.1.1 Software
* **Capa de Presentación Web:** Interfaz gráfica desarrollada en *Streamlit*, alojada elásticamente en la nube. Esta interfaz actúa como un cliente liviano desacoplado que consume, mediante peticiones HTTP asincrónicas, los microservicios lógicos de visión por computadora alojados de forma nativa en el entorno de ejecución (*Runtime Python 3.9+*) de Huawei Cloud *FunctionGraph*. Para optimizar el canal de subida móvil y proteger la memoria del servidor frente a cargas masivas indeseadas (`st.file_uploader`), la capa web implementa una doble barrera de control: (1) a nivel de servidor web mediante la directiva `maxUploadSize = 5` en el archivo de configuración `.streamlit/config.toml`, permitiendo que el navegador intercepte y rechace archivos que excedan los 5 MB antes de consumir ancho de banda de subida, y (2) a nivel de código de aplicación Python para verificar que la duración efectiva del video no supere los 6 segundos.
* **Motor Serverless:** Huawei Cloud *FunctionGraph*, responsable de procesar la lógica matemática cinemática y la inyección gráfica sobre las imágenes.

#### 4.3.1.2 Hardware
* **Dispositivo de Captura:** Sensor óptico integrado en teléfonos inteligentes comerciales (resolución mínima recomendada: 720p a 30 cuadros por segundo).
* **Terminal de Consulta:** Teléfonos celulares inteligentes de gama de entrada o computadoras portátiles de la academia sin tarjetas gráficas dedicadas.

---

### 4.3.2 Requisitos Funcionales

| Código | Requisito Funcional | Descripción Detallada |
| :---: | :--- | :--- |
| **RF-01** | Registro de Técnica Maestra y Reglas Biomecánicas | El sistema deberá permitir exclusivamente al Head Coach registrar una técnica deportiva especificando obligatoriamente su categoría técnica (ej. "Llave de Brazo", "Estrangulación", "Pasaje de Guardia") y su posición de origen (ej. "Montada", "Guardia Cerrada", "Side Control"), validando que no exista previamente en el catálogo otra técnica con dicha combinación exacta para evitar nombres duplicados y catalogar variantes legítimas; asimismo, permitirá cargar su video patrón ejecutor en formato MP4 o MOV y asociar un catálogo de reglas biomecánicas deterministas que vinculan cada articulación y umbral angular con su correspondiente explicación pedagógica en lenguaje claro. |
| **RF-02** | Normalización Antropomórfica | El sistema deberá calcular la distancia interclavicular de los sujetos en el video para normalizar escalarmente la matriz de coordenadas, permitiendo la comparación directa entre adultos, niños y diversas contexturas. |
| **RF-03** | Sincronización Temporal Dinámica | El backend deberá aplicar el algoritmo DTW optimizado con una Ventana de Sakoe-Chiba parametrizada con un valor por defecto recomendado del 15% de la longitud temporal ($w = 0.15 \cdot N$), permitiendo su configuración flexible en el backend como parámetro adaptable por técnica o por duración del video patrón para alinear de forma no lineal las secuencias temporales del alumno y del maestro. El cálculo de la matriz de distancia del DTW se realizará exclusivamente sobre las series temporales de ángulos articulares relativos y no sobre las coordenadas espaciales absolutas, garantizando invariancia traslacional. |
| **RF-04** | Extracción de Fotograma Clave | El sistema deberá aislar el fotograma específico donde la distancia euclidiana o la diferencia angular de las articulaciones alcance el pico máximo de desviación respecto al umbral maestro. |
| **RF-05** | Inyección Gráfica de Anotación (OpenCV) | El sistema deberá dibujar automáticamente un círculo de color rojo (radio de 15 píxeles) centrado en la coordenada espacial exacta $(X, Y)$ del nodo articular donde se validó el fallo técnico. |
| **RF-06** | Despliegue de Diagnóstico Estático y Causa Técnica | La interfaz web en Streamlit deberá renderizar la imagen JPG procesada (cuyo peso no superará los 80 KB) junto con la explicación textual del error generada por el motor de reglas de manera inmediata tras la finalización del cómputo serverless. |
| **RF-07** | Selección Jerárquica de Técnica y Doble Capa de Restricción de Carga | La interfaz web en Streamlit deberá presentar el catálogo curricular agrupado jerárquicamente en dos niveles (primero por categoría técnica y luego por posición de origen) para la selección manual de la variante a evaluar; asimismo, implementará una doble capa de control de ingesta de video: (1) a nivel de servidor web mediante la directiva `maxUploadSize` (fijada en **5 MB** en `.streamlit/config.toml`) para que el navegador aborte la transferencia de archivos sobredimensionados antes de saturar el enlace de subida o la memoria del servidor, y (2) a nivel de código de aplicación Python para verificar que la duración efectiva del video grabado en pareja no exceda los **6 segundos**. |
| **RF-08** | Compensación Cinemática por Oclusión y Límite de Validez | El backend en FunctionGraph deberá implementar un Filtro de Kalman cinemático que se active automáticamente sobre los puntos articulares cuya confiabilidad reportada sea $C < 0.5$, interpolando la trayectoria a partir de cuadros adyacentes; no obstante, si una articulación permanece ocluida ($C < 0.5$) de forma continua por más de un umbral máximo configurable (establecido con un valor de referencia inicial de 1.5 segundos o 45 fotogramas a 30 fps), el filtro cesará la interpolación inercial y marcará dicho tramo como 'no computable' para evitar la generación de cinemáticas ficticias, derivando el procesamiento al requisito RF-11. |
| **RF-09** | Validación de Token de Membresía | La interfaz web deberá validar la vigencia del Código de Activación Mensual (Token de Acceso) del estudiante antes de autorizar la transferencia del archivo de video hacia el almacenamiento en la nube (Huawei Cloud OBS), impidiendo el consumo no autorizado de recursos serverless. |
| **RF-10** | Generación de Explicación Textual Determinista | El backend en FunctionGraph deberá consultar el catálogo de reglas biomecánicas registrado en el RF-01 y, en función de la articulación afectada, la desviación angular calculada y la técnica analizada, seleccionar de forma determinista el mensaje explicativo sobre la causa técnica del fallo (el "por qué" del error), almacenándolo en el campo `descripcionError` sin recurrir a IA generativa ni modelos de lenguaje libre. |
| **RF-11** | Rechazo por Oclusión Prolongada y Protección de Integridad de Datos | El sistema deberá interrumpir el cómputo del diagnóstico cuando un tramo de oclusión continua supere el umbral máximo de validez definido en el RF-08, notificando al estudiante mediante un mensaje explícito en pantalla ("No fue posible calcular el diagnóstico: oclusión prolongada de la articulación durante la ejecución. Vuelve a grabar con mejor ángulo de cámara.") en lugar de renderizar fotogramas con datos inexactos, registrando el intento como fallido y abortando la ejecución para evitar contaminar el historial de progresión del atleta con cinemáticas ficticias. (Nota técnica: Aunque el cómputo serverless ejecutado hasta el punto de detección de oclusión ya fue facturado por milisegundos de CPU, esta lógica de rechazo prioriza la validez pedagógica y estadística de los datos longitudinales del estudiante sobre el ahorro marginal de cómputo). |
| **RF-12** | Consulta de Historial de Progresión Técnica | La interfaz web en Streamlit deberá permitir al estudiante autenticado consultar de forma interactiva su historial acumulativo de evaluaciones biomecánicas (`HistorialProgresion`), visualizando la evolución cronológica de su puntuación técnica global (`puntuacionGlobal`) y la tasa de reducción de errores (`cantidadErrores`) a lo largo de sus sucesivas sesiones de entrenamiento en el tatami. |

---

### 4.3.3 Requisitos de Rendimiento

| Código | Requisito de Rendimiento | Métrica y Criterio de Aceptación |
| :---: | :--- | :--- |
| **RP-01** | Latencia de Inferencia en la Nube | El tiempo total de procesamiento en la nube (extracción de puntos clave con MediaPipe, compensación por Kalman, sincronización DTW y anotación con OpenCV) para una secuencia estandarizada de hasta **6 segundos** de video ($\sim 180$ fotogramas a 30 fps) no deberá exceder de **4.0 segundos** en *FunctionGraph*, contemplando un margen seguro ante arranques en frío (*cold starts*) de la plataforma. |
| **RP-02** | Eficiencia en Transferencia de Salida (*Egress*) | El volumen del paquete de datos de respuesta emitido desde la nube hacia el teléfono del practicante no deberá superar los **100 KB** por consulta, garantizando una carga rápida bajo enlaces móviles de baja velocidad. |

---

### 4.3.4 Restricciones de Diseño

* **Licenciamiento y Librerías de Código Abierto:** La lógica de cálculo biomecánico y de manipulación de matrices visuales debe implementarse exclusivamente con herramientas de software libre bajo licencias permisivas (*Apache 2.0* o *BSD*), adoptándose formalmente el ecosistema conformado por `NumPy`, `MediaPipe` y `OpenCV-Python`.

---

### 4.3.5 Atributos del Sistema

* **Disponibilidad:** La arquitectura *Serverless* garantizará una disponibilidad del servicio del **99.9%**, aprovechando la infraestructura elástica y redundante provista por la plataforma Huawei Cloud.
* **Usabilidad y Ergonomía Térmica:** La interfaz web de consulta operará de manera pasiva mediante el despliegue de hipertexto e imágenes estáticas pre-procesadas. Queda prohibida la ejecución de hilos de cómputo en segundo plano (*Web Workers / Background JavaScript*) en el terminal del usuario, minimizando la demanda sobre la batería y previniendo el estrés térmico en teléfonos inteligentes de gama baja durante los entrenamientos en el tatami.

---

## 4.4 Identificación de los Casos de Uso

De acuerdo con las directrices metodológicas del Proceso Unificado (Craig Larman, 2004), los casos de uso representan exclusivamente interacciones directas entre los actores humanos y el sistema. En este sentido, los procesos puramente algorítmicos e inferencias ejecutadas en el backend (normalización de escala, compensación cinemática de oclusiones mediante Filtro de Kalman, alineación no lineal mediante DTW e inyección gráfica de anotaciones con OpenCV) no constituyen casos de uso aislados, sino que son subtareas y flujos de eventos internos gatillados por el **CU-02: Cargar Video de Ejecución**.

El siguiente diagrama presenta la vista arquitectónica de los casos de uso identificados:

```mermaid
graph LR
    subgraph Actores
        HC(("Head Coach"))
        E(("Estudiante"))
    end

    subgraph Sistema["Sistema de Análisis Biomecánico"]
        CU01["CU-01: Registrar Técnica Maestra y Reglas"]
        CU02["CU-02: Cargar Video de Ejecución"]
        CU03["CU-03: Consultar Diagnóstico Visual y Causa"]
        CU04["CU-04: Consultar Historial de Progresión"]
    end

    HC --> CU01
    E --> CU02
    E --> CU03
    E --> CU04
```

**Figura 4.1**
*Diagrama de Casos de Uso del Sistema de Análisis Biomecánico (Corpo & Mente Bolivia).*

A continuación, se presenta la trazabilidad entre las historias de usuario, los requisitos funcionales y los casos de uso derivados:

**Tabla 4.1**
*Matriz de Identificación de Historias de Usuario y Casos de Uso*

| Nro | Historia de Usuario | Req | CU | Descripción Caso de Uso |
| :---: | :--- | :---: | :---: | :--- |
| 1 | Como Head Coach, quiero registrar una técnica maestra especificando su categoría y posición de origen junto a su catálogo de reglas de error subiendo un video patrón para que el sistema extraiga el molde cinemático y configure las explicaciones pedagógicas sin nombres duplicados. | RF-01 | CU-01 | Registrar Técnica Maestra y Reglas |
| 2 | Como estudiante, quiero seleccionar una técnica del catálogo curricular jerárquico y subir el video de mi ejecución en pareja con mi compañero desde mi celular para que el sistema audite mi técnica. | RF-02, RF-03, RF-04, RF-05, RF-07, RF-08, RF-09, RF-10, RF-11 | CU-02 | Cargar Video de Ejecución |
| 3 | Como estudiante, quiero ver el fotograma anotado junto a la explicación textual de la causa de mi fallo técnico para comprender por qué me equivoqué y saber cómo corregirlo. | RF-06, RF-10 | CU-03 | Consultar Diagnóstico Visual y Causa |
| 4 | Como estudiante, quiero consultar mi historial de análisis para visualizar mi progreso y la reducción de errores biomecánicos a lo largo del tiempo. | RF-12 | CU-04 | Consultar Historial de Progresión |

*Nota*. El caso de uso CU-02 encapsula internamente el flujo completo de procesamiento automatizado: selección jerárquica de la técnica y doble capa de restricción de video de hasta 6 segundos y 5 MB (RF-07), validación de vigencia del token de membresía en cliente (RF-09), normalización antropomórfica del esqueleto (RF-02), compensación cinemática de oclusiones articulares mediante Filtro de Kalman con límite de validez (RF-08), flujo de interrupción y rechazo pedagógico ante oclusión continua prolongada (RF-11), sincronización temporal mediante DTW con ventana configurable (RF-03), detección del fotograma de error máximo (RF-04), inyección gráfica de la anotación de fallo con OpenCV (RF-05) y selección determinista del mensaje pedagógico explicativo a partir del catálogo de reglas (RF-10). Estos procesos constituyen el flujo de eventos interno del sistema y no representan interacciones independientes con actores humanos (Larman, 2004). El CU-04 implementa directamente la consulta del historial de progresión técnica (RF-12), permitiendo la evaluación longitudinal del atleta.

---

## 4.5 Diagrama de Dominio

El Modelo de Dominio conceptual identifica las entidades principales del ecosistema, sus atributos descriptivos y las relaciones estructurales con su cardinalidad correspondiente. Conforme al análisis organizacional presentado en el Capítulo II, la entidad raíz del modelo corresponde a la academia (EscuelaBJJ), la cual contextualiza la totalidad de los actores y recursos del sistema.

```mermaid
classDiagram
    class EscuelaBJJ {
        +id: UUID
        +nombre: String
        +sede: String
        +ciudad: String
        +comunidadWhatsApp: String
    }

    class UsuarioAcademia {
        <<abstract>>
        +id: UUID
        +nombreCompleto: String
        +telefonoWhatsApp: String
        +correoElectronico: String
        +fechaRegistro: Date
    }

    class HeadCoach {
        +gradoCinturon: String
        +licenciaFederativa: String
    }

    class Estudiante {
        +gradoCinturon: String
        +pesoKg: Float
        +estadoMembresia: String
    }

    class CodigoActivacion {
        +id: UUID
        +token: String
        +fechaEmision: Date
        +fechaExpiracion: Date
        +estado: String
    }

    class TecnicaMaestra {
        +id: UUID
        +nombre: String
        +categoriaTecnica: String
        +posicionOrigen: String
        +ventanaSakoeChiba: Float
        +videoURL: String
        +fechaCarga: Date
    }

    class ReglaBiomecanica {
        +id: UUID
        +articulacionClave: String
        +umbralAngularTolerado: Float
        +descripcionError: String
    }

    class VideoEjecucion {
        +id: UUID
        +fechaCaptura: DateTime
        +duracionSegundos: Float
        +pesoMB: Float
        +videoURL: String
    }

    class AnalisisBiomecanico {
        +id: UUID
        +fechaProcesamiento: DateTime
        +desviacionAngularMaxima: Float
        +articulacionAfectada: String
        +estadoComputo: String
    }

    class FotogramaAnotado {
        +id: UUID
        +imagenURL: String
        +coordenadaErrorX: Integer
        +coordenadaErrorY: Integer
        +explicacionCausa: String
    }

    class HistorialProgresion {
        +id: UUID
        +puntuacionGlobal: Float
        +cantidadErrores: Integer
        +fechaUltimaEvaluacion: Date
    }

    EscuelaBJJ "1" *-- "1..*" UsuarioAcademia : nuclea
    UsuarioAcademia <|-- HeadCoach : es-un
    UsuarioAcademia <|-- Estudiante : es-un

    HeadCoach "1" -- "0..*" CodigoActivacion : emite
    CodigoActivacion "0..*" -- "0..1" Estudiante : es-asignado-a
    
    HeadCoach "1" -- "1..*" TecnicaMaestra : homologa
    TecnicaMaestra "1" *-- "1..*" ReglaBiomecanica : define-criterio

    Estudiante "1" -- "0..*" VideoEjecucion : graba-y-carga
    TecnicaMaestra "1" -- "0..*" VideoEjecucion : evalua-contra

    VideoEjecucion "1" -- "1" AnalisisBiomecanico : procesa-en-nube
    AnalisisBiomecanico "1" -- "0..1" FotogramaAnotado : genera-anotacion
    
    AnalisisBiomecanico "0..*" --o "1" HistorialProgresion : consolida
    Estudiante "1" *-- "1" HistorialProgresion : registra-evolucion
```

**Figura 4.2**
*Modelo de Dominio Conceptual del Sistema de Análisis Biomecánico (Corpo & Mente Bolivia).*

**Descripción de las Entidades:**

* **EscuelaBJJ:** Entidad organizativa raíz que representa a la academia Corpo & Mente Bolivia y sus sucursales (Knock Out, UFC, 3 Pasos al Frente, entre otras). Contextualiza la totalidad de los actores humanos y los recursos pedagógicos del sistema, nucleando mediante composición a los usuarios de la institución.
* **UsuarioAcademia:** Superclase abstracta que encapsula los atributos comunes de identidad y contacto (nombre, WhatsApp, email) compartidos por HeadCoach y Estudiante, aplicando la regla de generalización "Es-Un" (Is-A) y disyunción completa.
* **HeadCoach:** Especialización de UsuarioAcademia que representa al Head Coach / Director Técnico, profesional con potestad exclusiva para registrar y homologar las técnicas de referencia curriculares, emitir códigos de activación mensual y calibrar el catálogo de reglas biomecánicas de error en el sistema.
* **Estudiante:** Especialización de UsuarioAcademia que representa al practicante de BJJ registrado en la plataforma web (mediante un esquema de persistencia independiente en PostgreSQL en la nube) que graba y carga videos de sus ejecuciones en pareja y consulta los diagnósticos visuales generados.
* **CodigoActivacion:** Credencial temporal de acceso (Token de Activación Mensual) emitida periódicamente por el Head Coach a favor de un estudiante con membresía vigente. Sus atributos registran identificador, código alfanumérico, fecha de emisión, fecha de expiración y su `estado` operativo (`vigente`, `expirado` o `revocado`). Es este atributo de estado el que evalúa formalmente el requisito RF-09 antes de autorizar cualquier transferencia de video hacia la nube.
* **TecnicaMaestra:** Video patrón homologado por el Head Coach con la ejecución canónica de una técnica específica del currículo oficial, asociado a un catálogo de reglas de error deterministas. Incorpora los atributos estructurados `categoriaTecnica` (ej. "Llave de Brazo", "Pasaje de Guardia", "Estrangulación") y `posicionOrigen` (ej. "Montada", "Guardia Cerrada", "Side Control", "De Pie"), conformándose su `nombre` como la combinación única de ambos para catalogar con precisión variantes legítimas sin ambigüedad. Admite opcionalmente el parámetro `ventanaSakoeChiba` para calibrar el ancho de banda del algoritmo DTW según la dinámica de la técnica. A nivel de persistencia en PostgreSQL, esta entidad posee un índice de unicidad compuesto (Unique Constraint) sobre los atributos `(categoriaTecnica, posicionOrigen)`, garantizando contractualmente que no existan duplicados en el catálogo curricular.
* **ReglaBiomecanica:** Entidad conceptual que modela el catálogo de errores deterministas. Posee una relación de composición fuerte con TecnicaMaestra; si la técnica se elimina del catálogo, sus reglas biomecánicas asociadas se destruyen en cascada.
* **VideoEjecucion:** Grabación capturada por el estudiante junto a su compañero desde su dispositivo móvil en el tatami, la cual se somete al análisis biomecánico evaluándose contra la técnica maestra de referencia.
* **AnalisisBiomecanico:** Resultado del procesamiento en la nube que contiene la desviación angular máxima detectada, la articulación involucrada y el estado del cómputo.
* **FotogramaAnotado:** Imagen JPG estática resultante del procesamiento con OpenCV, conteniendo el círculo marcador sobre la coordenada exacta del error técnico y la explicación pedagógica textual (`explicacionCausa`) sobre la causa motriz del fallo generada de manera determinista por el motor de reglas (RF-10).
* **HistorialProgresion:** Registro acumulativo que consolida los sucesivos análisis biomecánicos de un estudiante, permitiendo registrar la evolución cronológica de su desempeño técnico y la reducción de fallos a lo largo del tiempo.

**Relaciones y Cardinalidad:**

| Relación | Cardinalidad | Interpretación |
| :--- | :---: | :--- |
| EscuelaBJJ → UsuarioAcademia | 1 : 1..* | Una escuela nuclea al menos un usuario (Head Coach o Estudiante). |
| UsuarioAcademia → HeadCoach / Estudiante | 1 : 1 (subclases) | Generalización disjunta y completa. Todo usuario es un Head Coach o un Estudiante. |
| HeadCoach → CodigoActivacion | 1 : 0..* | El Head Coach emite cero o más códigos de activación. |
| CodigoActivacion → Estudiante | 0..* : 0..1 | Un código específico es asignado a exactamente un estudiante (o a ninguno si está en el pool de tokens sin reclamar), resolviendo la trazabilidad de la membresía. |
| HeadCoach → TecnicaMaestra | 1 : 1..* | El Head Coach registra una o más técnicas maestras. |
| TecnicaMaestra → ReglaBiomecanica | 1 : 1..* | Composición fuerte. Cada técnica define obligatoriamente uno o más umbrales angulares y mensajes pedagógicos. |
| Estudiante → VideoEjecucion | 1 : 0..* | Un estudiante carga cero o más videos. |
| TecnicaMaestra → VideoEjecucion | 1 : 0..* | Una técnica maestra sirve de referencia para cero o más videos. |
| VideoEjecucion → AnalisisBiomecanico | 1 : 1 | Cada video genera exactamente un análisis. |
| AnalisisBiomecanico → FotogramaAnotado | 1 : 0..1 | **Cardinalidad corregida:** Un análisis produce cero o un fotograma. Es 0 si el sistema aborta por oclusión prolongada (RF-11), evitando registros huérfanos o nulos. |
| AnalisisBiomecanico → HistorialProgresion | 0..* : 1 | Cero o más análisis alimentan el historial. |
| Estudiante → HistorialProgresion | 1 : 1 | Cada estudiante posee exactamente un registro histórico acumulativo. |