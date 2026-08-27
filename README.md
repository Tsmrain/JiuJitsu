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

## APLICACIÓN WEB CON INTELIGENCIA ARTIFICIAL PARA ANALIZAR VIDEOS DE ENTRENAMIENTO DE ARTES MARCIALES EN BRAZILIAN JIU-JITSU PARA PRINCIPIANTES DE CINTURÓN BLANCO

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

## APLICACIÓN WEB CON INTELIGENCIA ARTIFICIAL PARA ANALIZAR VIDEOS DE ENTRENAMIENTO DE ARTES MARCIALES EN BRAZILIAN JIU-JITSU PARA PRINCIPIANTES DE CINTURÓN BLANCO

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
- [Capítulo II: Descripción de la Entidad (Corpo & Mente Bolivia)](#capítulo-ii-descripción-de-la-entidad-corpo--mente-bolivia)
  - [2.1 Descripción de la Organización](#21-descripción-de-la-organización)
  - [2.2 Estructura Organizacional](#22-estructura-organizacional)
  - [2.3 Mapeo de la Infraestructura Tecnológica Actual](#23-mapeo-de-la-infraestructura-tecnológica-actual)
  - [2.4 Flujo del Proceso de Enseñanza (El Core del Negocio)](#24-flujo-del-proceso-de-enseñanza-el-core-del-negocio)
    - [2.4.1 Identificación y Justificación Matemática del Cuello de Botella](#241-identificación-y-justificación-matemática-del-cuello-de-botella)
- [Capítulo III: Marco Tecnológico y Selección de Componentes](#capítulo-iii-marco-tecnológico-y-selección-de-componentes)
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

El objeto de estudio comprende la aplicación articulada de técnicas de **Visión por Computadora** (estimación de poses corporales mediante MediaPipe), **procesamiento digital de imágenes** (OpenCV), **procesamiento elástico en la nube** (*Serverless Cloud Computing*) y **algoritmos de alineación de series temporales** (*Dynamic Time Warping*, DTW) para la evaluación asincrónica automatizada de la calidad técnica deportiva y el suministro de retroalimentación biomecánica adaptativa mediante imágenes clave anotadas.

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
2. **Diseñar** una arquitectura híbrida de cómputo que integre cubos de almacenamiento (*Huawei Cloud Object Storage Service - OBS*) con servicios de cómputo ligero bajo demanda (*FunctionGraph* o *Cloud Container Instance*) para aislar el hardware local de cargas computacionales pesadas de forma económicamente sostenible.
3. **Implementar** algoritmos de alineación temporal (*Dynamic Time Warping*) y formulaciones geométricas vectoriales para calcular la desviación matemática entre el esqueleto de referencia del profesor y el del estudiante.
4. **Construir** una interfaz de usuario interactiva y liviana que presente la imagen estática anotada mediante OpenCV con la señalización precisa del error biomecánico y la descripción textual del fallo técnico.
5. **Validar** el impacto del sistema mediante un diseño experimental de pre-test y post-test con atletas de la academia, cuantificando la reducción en la tasa de errores técnicos cometidos.

---

## 1.3 Metodología

Con base en las directrices metodológicas de Craig Larman (2004), la investigación adopta el **Proceso Unificado (UP)** adaptado a un marco de trabajo ágil iterativo e incremental. El ciclo de desarrollo se estructura en cuatro fases disciplinadas, orientadas a la mitigación sistemática de riesgos tecnológicos:

* **Fase de Inicio (*Inception*):** Delimitación rigurosa del alcance del proyecto, identificación y priorización de riesgos tecnológicos críticos (tales como la latencia de red en la carga móvil y las fluctuaciones tarifarias en la nube) y consolidación de los requerimientos de negocio de la academia.
* **Fase de Elaboración (*Elaboration*):** Mitigación de los riesgos arquitectónicos de mayor impacto. Se formaliza la arquitectura base y el Modelo de Dominio. Se valida la factibilidad técnica construyendo un prototipo funcional que conecte la captura móvil con el almacenamiento en la nube (*OBS*) sin provocar estrés térmico en el cliente.
* **Fase de Construcción (*Construction*):** Desarrollo modular y desacoplado de los componentes de cómputo. Implementación de los microservicios sin servidor (*Serverless* con *FunctionGraph*), codificación del motor matemático de detección de errores (DTW con restricciones de banda), integración de los algoritmos de anotación digital sobre imágenes con OpenCV y desarrollo del frontend web reactivo en *Streamlit*.
* **Fase de Transición (*Transition*):** Despliegue del aplicativo en el entorno operativo real de Corpo & Mente Bolivia. Ejecución de los ensayos experimentales con los alumnos de la academia, recolección de las matrices numéricas de error pre-test y post-test para su posterior contrastación estadística, y redacción de las conclusiones formales del estudio.

---

# Capítulo II: Descripción de la Entidad (Corpo & Mente Bolivia)

## 2.1 Descripción de la Organización

**Corpo & Mente Bolivia** es un centro de entrenamiento especializado en la instrucción de artes marciales y acondicionamiento físico, situado en la ciudad de Santa Cruz de la Sierra, Bolivia. Creado con el propósito de fomentar el desarrollo biopsicosocial y atlético de sus miembros, se ha posicionado como una institución referente en la enseñanza del Jiu-Jitsu Brasileño (BJJ) a nivel regional. 

La entidad sustenta su propuesta de valor sobre dos pilares complementarios: la excelencia en la técnica deportiva y la preservación de la salud del practicante. El centro alberga una población heterogénea de usuarios que comprende divisiones infantiles, practicantes adultos recreativos y atletas de alto rendimiento con participación en certámenes competitivos departamentales, nacionales e internacionales.

## 2.2 Estructura Organizacional

La estructura operativa de la institución se ajusta a un modelo lineal-funcional, diseñado para garantizar la adecuada prestación de servicios deportivos y la supervisión técnica constante. Los niveles jerárquicos se distribuyen de la siguiente forma:

* **Dirección General / Head Coach:** Máxima autoridad técnica y administrativa. Responsable de la visión estratégica institucional, la capacitación continua del cuerpo docente y la homologación curricular del plan de enseñanza del BJJ.
* **Cuerpo de Instructores:** Profesionales del área deportiva encargados de conducir las clases, fiscalizar la ejecución biomecánica directa de los estudiantes en el tatami y registrar la evolución técnica de los mismos.
* **Área de Recepción y Atención al Cliente:** Unidad administrativa encargada del control de contratos, cobro de membresías, registro de asistencias y soporte operativo.
* **Estudiantes y Practicantes:** Usuarios receptores del servicio, constituyendo el núcleo del proceso pedagógico y los destinatarios directos de la solución tecnológica proyectada.

---

## 2.3 Mapeo de la Infraestructura Tecnológica Actual

El análisis de viabilidad técnica requiere examinar el estado de madurez de los sistemas informáticos presentes en Corpo & Mente Bolivia. La institución opera actualmente bajo una infraestructura descentralizada y de carácter estrictamente local:

* **Gestión de Datos y Membresías (Backend Local):** El control administrativo de legajos de estudiantes, datos de contacto, planes suscritos y cobranzas se gestiona de manera aislada mediante una base de datos relacional de escritorio implementada en *Microsoft Access*. La herramienta carece de mecanismos de sincronización en la nube, respaldo automatizado o interfaces de consulta remota para el cuerpo de instructores.
* **Control de Acceso Biométrico (Hardware de Entrada):** En el punto de transición hacia el área de entrenamiento (tatami), la academia cuenta con un sensor periférico de lectura de huellas dactilares. El dispositivo valida el estado administrativo del usuario consultando la base de datos local de recepción.
* **Mecanismo de Validación Física (Sistema de Tickets):** Al validarse la identidad biométrica y confirmarse la vigencia de la cuota, el terminal emite un ticket físico impreso en papel térmico. Este comprobante opera como credencial física de acceso diario; el alumno debe portarlo al tatami y entregarlo personalmente al instructor a cargo como evidencia de habilitación formal y mecanismo de control de aforo antes del inicio de la sesión.
* **Diagnóstico de Madurez Tecnológica:** Si bien la gestión de procesos es eminentemente local y analógica, la presencia de un circuito que combina software (*Microsoft Access*) con hardware periférico (*sensores biométricos* e impresoras térmicas) constata que tanto el personal como los usuarios poseen familiaridad con flujos asistidos por computadora. Esta circunstancia mitiga sustancialmente la resistencia al cambio y confirma la factibilidad de incorporar una interfaz web para la recepción de diagnósticos biomecánicos.

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

El diagnóstico evidencia que el instructor presencial ha superado su límite fisiológico y cognitivo de supervisión simultánea. La solución informática planteada no pretende sustituir la instrucción del profesor, sino extender su capacidad evaluativa a través de un canal de **auditoría biomecánica asincrónica**. Al grabarse desde sus teléfonos móviles, los estudiantes podrán recibir retroalimentación visual objetiva y precisa, descongestionando el tatami y garantizando rigor técnico en todos los niveles.

---

# Capítulo III: Marco Tecnológico y Selección de Componentes

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
* **Estrategia de Mitigación de Oclusiones:** Si bien MediaPipe presenta desafíos ante el contacto corporal estrecho característico de las luchas en el suelo, el sistema mitiga esta limitación implementando un protocolo de captura en condiciones de "laboratorio técnico": el alumno se graba de forma individual y asincrónica desde un ángulo predefinido. Asimismo, el algoritmo evalúa el vector de confiabilidad ($C \in [0.0, 1.0]$) reportado por el modelo. Cuando el factor de confianza desciende de $C < 0.5$ producto de una oclusión momentánea, el backend activa un **Filtro de Kalman** cinemático que interpola la posición anatómica a partir de los cuadros adyacentes, preservando la continuidad métrica.

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
* **Optimización Mediante Ventana de Sakoe-Chiba:** Para neutralizar la complejidad temporal cuadrática nativa del algoritmo ($O(N^2)$)—la cual elevaría el consumo de CPU en la función *Serverless*—se implementa la restricción geométrica de la **Ventana de Sakoe-Chiba**. Esta técnica acota la exploración de la trayectoria óptima a una banda diagonal estrecha alrededor del eje principal de la matriz de costo. Al restringir el espacio de búsqueda, se transforma el orden de complejidad computacional a un régimen cuasi-lineal $O(N)$, asegurando tiempos de ejecución en *FunctionGraph* de pocos cientos de milisegundos.

---

## 3.4 Procesamiento Digital de Imágenes y Generación del Entregable

Tras identificarse el fotograma exacto donde la discrepancia geométrica excede el umbral de tolerancia técnica determinado por el profesor, el sistema debe estructurar y retornar el diagnóstico al usuario final de forma instantánea.

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
* **Control Estricto de Costos de Salida de Datos:** Un archivo de imagen JPG procesado y comprimido con OpenCV promedia escasos **~80 KB**. La transmisión de 80 KB hacia el dispositivo móvil del estudiante elimina cualquier riesgo de sobrecosto por volumen de salida (*Data Egress*). Para una proyección de 2,700 consultas mensuales en la academia, el tráfico mensual demandado es inferior a 250 MB, implicando un gasto inferior a $0.02 USD al mes y blindando el límite presupuestario trimestral establecido.
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

El sistema se denomina formalmente **«Ecosistema de Auditoría Biomecánica Asincrónica para Jiu-Jitsu Brasileño»**. Su alcance operativo comprende:

1. La captura de video desde teléfonos móviles por parte de los practicantes en el tatami.
2. La carga y persistencia en cubos elásticos de almacenamiento en la nube (*Huawei Cloud OBS*).
3. La ejecución remota sin servidor (*Serverless*) de los módulos de extracción de coordenadas articulares (*MediaPipe Pose*) y sincronización de series de tiempo (*DTW* con ventana de Sakoe-Chiba).
4. El procesamiento digital de imágenes (*OpenCV*) para inyectar marcadores de color sobre la coordenada del error biomecánico detectado.
5. El despliegue visual inmediato del fotograma clave anotado e indicadores estadísticos a través de un cliente web liviano (*Streamlit*).

**Exclusiones explícitas:** Se excluye el procesamiento local de video en los dispositivos de los usuarios, el análisis multi-persona en tiempo real durante combates libres (*rolling/spárring*) y cualquier dictamen de orden médico, traumatológico o fisioterapéutico.

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

El software se estructura como un sistema distribuido híbrido *Edge-Cloud* que convive de manera asincrónica con la actual infraestructura administrativa local de Corpo & Mente Bolivia (base de datos en *Microsoft Access* y torniquete biométrico). El aplicativo no interfiere con la recaudación ni control de acceso, operando de manera independiente como una plataforma pedagógica accesible desde los teléfonos inteligentes de los practicantes.

### 4.2.2 Funciones del Producto

* **Gestión de Técnicas Maestras:** Permite a la Dirección Técnica subir los videos patrón que conforman el currículo oficial y derivar sus moldes biomecánicos.
* **Ingestión Móvil de Entrenamientos:** Facilita la carga rápida de grabaciones de video realizadas por los alumnos durante sus sesiones en el tatami.
* **Auditoría Biomecánica en la Nube:** Ejecuta de forma elástica la detección de puntos clave, la normalización de dimensiones corporales y la alineación matemática temporal.
* **Anotación Automatizada de Fallas:** Localiza el fotograma de máxima discrepancia e inyecta la señalética gráfica sobre la articulación defectuosa.
* **Visualización de Reportes Técnicos:** Entrega al estudiante el fotograma estático de falla y su evolución técnica histórica de forma inmediata y con mínimo consumo de datos.

### 4.2.3 Características de los Usuarios

* **Instructor / Head Coach:** Profesional con dominio experto en biomecánica de combate y competencias informáticas de usuario final. Precisa de una interfaz ágil para la administración de las técnicas maestras de referencia.
* **Estudiante / Practicante:** Grupo diverso en edades y contexturas físicas (infantiles, adultos aficionados y competidores avanzados). Acceden a la plataforma desde sus propios teléfonos celulares empleando redes móviles comerciales (4G/LTE/5G) dentro de las instalaciones del centro.

### 4.2.4 Restricciones

* **Presupuesto Operativo Máximo:** El consumo total facturable por servicios de Huawei Cloud (almacenamiento en OBS y cómputo en *FunctionGraph*) debe mantenerse por debajo de los **$30 USD trimestrales**.
* **Aislamiento del Hardware Local:** Queda terminantemente restringido el uso intensivo de la memoria RAM, la CPU o aceleradores gráficos locales del cliente para tareas de inferencia de modelos de visión artificial.
* **Condiciones de Conectividad:** El sistema debe operar eficientemente bajo las condiciones asimétricas de ancho de banda y velocidades de carga (*Upload*) prevalentes en las redes de telefonía móvil de Santa Cruz de la Sierra.

### 4.2.5 Suposiciones y Dependencias

* Se asume que el alumno registrará sus movimientos bajo el protocolo establecido de "laboratorio técnico" (encuadre lateral despejado y sin oclusiones externas por terceros en la escena).
* El funcionamiento del sistema depende de la disponibilidad del servicio *FunctionGraph* y de los contenedores Linux de Huawei Cloud para la ejecución de la biblioteca *MediaPipe Pose*.

### 4.2.6 Requisitos Futuros

* Integración mediante servicios web (API REST) con la base de datos de administración en *Microsoft Access* para sincronizar de manera automatizada las membresías activas.
* Extensión hacia modelos de seguimiento simultáneo multi-persona en plano general durante fases de combate real (*rolling* o spárring libre).

---

## 4.3 Requisitos Específicos

### 4.3.1 Interfaces Externas

#### 4.3.1.1 Interfaces de Software
* **Capa de Presentación Web:** Interfaz gráfica desarrollada en *Streamlit*, alojada elásticamente en la nube. Esta interfaz actúa como un cliente liviano desacoplado que consume, mediante peticiones HTTP asincrónicas, los microservicios lógicos de visión por computadora alojados de forma nativa en el entorno de ejecución (*Runtime Python 3.9+*) de Huawei Cloud *FunctionGraph*.
* **Motor Serverless:** Huawei Cloud *FunctionGraph*, responsable de procesar la lógica matemática cinemática y la inyección gráfica sobre las imágenes.

#### 4.3.1.2 Interfaces de Hardware
* **Dispositivo de Captura:** Sensor óptico integrado en teléfonos inteligentes comerciales (resolución mínima recomendada: 720p a 30 cuadros por segundo).
* **Terminal de Consulta:** Teléfonos celulares inteligentes de gama de entrada o computadoras portátiles de la academia sin tarjetas gráficas dedicadas.

---

### 4.3.2 Requisitos Funcionales

| Código | Requisito Funcional | Descripción Detallada |
| :---: | :--- | :--- |
| **RF-01** | Registro de Técnica Maestra | El sistema deberá permitir al instructor registrar una técnica deportiva asignándole un identificador único y cargando un video patrón ejecutor en formato MP4 o MOV. |
| **RF-02** | Normalización Antropomórfica | El sistema deberá calcular la distancia interclavicular de los sujetos en el video para normalizar escalarmente la matriz de coordenadas, permitiendo la comparación directa entre adultos, niños y diversas contexturas. |
| **RF-03** | Sincronización Temporal Dinámica | El backend deberá aplicar el algoritmo DTW optimizado con una Ventana de Sakoe-Chiba para alinear de forma no lineal las secuencias temporales del video del alumno con las del video maestro. |
| **RF-04** | Extracción de Fotograma Clave | El sistema deberá aislar el fotograma específico donde la distancia euclidiana o la diferencia angular de las articulaciones alcance el pico máximo de desviación respecto al umbral maestro. |
| **RF-05** | Inyección Gráfica de Anotación (OpenCV) | El sistema deberá dibujar automáticamente un círculo de color rojo (radio de 15 píxeles) centrado en la coordenada espacial exacta $(X, Y)$ del nodo articular donde se validó el fallo técnico. |
| **RF-06** | Despliegue de Diagnóstico Estático | La interfaz web en Streamlit deberá renderizar la imagen JPG procesada (cuyo peso máximo no superará los 80 KB) de manera inmediata tras la finalización del cómputo serverless. |
| **RF-07** | Restricción de Ingestión en el Cliente | La interfaz web en Streamlit implementará un módulo de validación en el lado del cliente que restringirá la carga de archivos a una duración máxima de 10 segundos y aplicará un filtro de advertencia si el archivo supera los 5 MB, optimizando el canal de subida ante redes móviles locales. |

---

### 4.3.3 Requisitos de Rendimiento

| Código | Requisito de Rendimiento | Métrica y Criterio de Aceptación |
| :---: | :--- | :--- |
| **RP-01** | Latencia de Inferencia en la Nube | El tiempo total de procesamiento en la nube (extracción de puntos clave con MediaPipe, sincronización DTW y anotación con OpenCV) para una secuencia estándar de 10 segundos de video no deberá exceder de **4.0 segundos** en *FunctionGraph*. |
| **RP-02** | Eficiencia en Transferencia de Salida (*Egress*) | El volumen del paquete de datos de respuesta emitido desde la nube hacia el teléfono del practicante no deberá superar los **100 KB** por consulta, garantizando una carga rápida bajo enlaces móviles de baja velocidad. |

---

### 4.3.4 Restricciones de Diseño

* **Licenciamiento y Librerías de Código Abierto:** La lógica de cálculo biomecánico y de manipulación de matrices visuales debe implementarse exclusivamente con herramientas de software libre bajo licencias permisivas (*Apache 2.0* o *BSD*), adoptándose formalmente el ecosistema conformado por `NumPy`, `MediaPipe` y `OpenCV-Python`.

---

### 4.3.5 Atributos del Sistema

* **Disponibilidad:** La arquitectura *Serverless* garantizará una disponibilidad del servicio del **99.9%**, aprovechando la infraestructura elástica y redundante provista por la plataforma Huawei Cloud.
* **Usabilidad y Ergonomía Térmica:** La interfaz web de consulta operará de manera pasiva mediante el despliegue de hipertexto e imágenes estáticas pre-procesadas. Queda prohibida la ejecución de hilos de cómputo en segundo plano (*Web Workers / Background JavaScript*) en el terminal del usuario, minimizando la demanda sobre la batería y previniendo el estrés térmico en teléfonos inteligentes de gama baja durante los entrenamientos en el tatami.