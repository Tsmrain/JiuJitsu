# Capítulo 1: Definición del Proyecto de Investigación

## 1.1 Definición del Problema

### 1.1.1 Situación Problemática

En la enseñanza de artes marciales, particularmente en el Jiu-Jitsu Brasileño (BJJ), la corrección técnica constituye un pilar fundamental para el aprendizaje efectivo y la prevención de lesiones. En el modelo tradicional de instrucción presencial, un único docente debe supervisar a múltiples practicantes que ejecutan técnicas de forma simultánea en parejas. Esta dinámica impone una limitación física y cognitiva inherente: la imposibilidad práctica de suministrar una supervisión masiva, exhaustiva, continua y objetiva a cada estudiante durante toda la sesión.

En la academia piloto Corpo e Mente (ubicada en las instalaciones de Knock Out Gym, Santa Cruz de la Sierra, Bolivia), se cuenta con una comunidad de aproximadamente 77 miembros registrados y una asistencia promedio diaria de 15 personas. Se evidencia una notable tasa de rotación y deserción temporal, en la cual los estudiantes interrumpen y retoman la disciplina tras varios meses de inactividad. Durante estas fases, los practicantes tienden a internalizar vicios biomecánicos recurrentes —tales como la incorrecta colocación de apoyos, alineaciones articulares desfavorables o ángulos inadecuados del torso— que eluden la observación del instructor debido a las restricciones de la supervisión simultánea. La ausencia de un instrumento visual, objetivo y persistente que permita al estudiante contrastar su ejecución con el modelo técnico de referencia impartido por el profesor conduce a una desaceleración en la curva de dominio técnico y a la consolidación prolongada de patrones de movimiento erróneos.

### 1.1.2 Situación Deseada

Se propone el desarrollo e implementación de un sistema computacional de asistencia al entrenamiento basado en visión artificial, concebido para comparar la ejecución técnica de los alumnos con un video de referencia provisto por el instructor. El sistema procesará secuencias de video capturadas en el tatami en tiempo diferido, detectará las discrepancias biomecánicas clave y generará reportes visuales con indicadores diagnósticos directos sobre los fotogramas del video del alumno. Esta retroalimentación objetiva y persistente estará disponible para el practicante a través de dispositivos móviles o terminales de consulta en la academia, empoderando el autoaprendizaje guiado y liberando tiempo docente para que el instructor concentre su labor pedagógica en correcciones tácticas y estratégicas avanzadas.

### 1.1.3 Objeto de Investigación

El objeto de investigación comprende el diseño, desarrollo e implementación de un sistema de visión por computadora basado en redes neuronales profundas para la estimación de pose humana bidimensional (2D), diseñado para detectar, cuantificar y señalar visualmente discrepancias biomecánicas en la ejecución de técnicas de artes marciales mediante comparación cinemática directa frente a un patrón de referencia, operando bajo una arquitectura distribuida (edge-cloud).

### 1.1.4 Alcance y Delimitación

* **Delimitación temporal:** La investigación se desarrollará durante el periodo académico correspondiente a la elaboración, implementación y defensa del proyecto de grado.
* **Delimitación espacial:** La recolección del corpus de video y la prueba piloto experimental se llevarán a cabo en las instalaciones de la academia Corpo e Mente (Knock Out Gym, Santa Cruz de la Sierra, Bolivia).
* **Delimitación temática y técnica:** El sistema operará con un enfoque agnóstico de comparación técnica: procesará cualquier técnica de artes marciales siempre que se disponga de un video de referencia del instructor y un video de ejecución del alumno bajo un protocolo de grabación establecido. La estimación postural se enfocará estrictamente en la extracción de puntos clave articulares (*keypoints*) en dos dimensiones (2D) y el análisis de variaciones angulares relativas a lo largo del tiempo. El sistema constituye una herramienta complementaria de autoevaluación y auditoría técnica, sin pretender sustituir el juicio pedagógico del instructor. Se excluyen del alcance el reconocimiento automático o clasificación de técnicas no catalogadas, la reconstrucción volumétrica tridimensional (3D) y la medición de variables biomecánicas de fuerza, potencia o fatiga física.

### 1.1.5 Justificación de la Investigación

* **Justificación teórica:** El proyecto contribuye al área de la visión artificial aplicada a las ciencias del deporte y la biomecánica motriz, validando la eficacia de algoritmos de estimación de pose bidimensional y comparación temporal de series cinemáticas en deportes de contacto con interacción cercana, proporcionando evidencia empírica en un contexto de investigación deportiva local.
* **Justificación práctica:** Proporciona a la academia Corpo e Mente una solución de software escalable y accesible que optimiza los tiempos de supervisión del cuerpo docente, mitiga la consolidación de hábitos técnicos perjudiciales y brinda a los practicantes un medio de autoevaluación objetivo y sistemático.
* **Justificación metodológica:** La investigación adopta un proceso riguroso de ingeniería de software caracterizado por un diseño modular orientado a objetos y ciclos de desarrollo iterativos e incrementales. La implementación de prácticas de aseguramiento de calidad y desarrollo guiado por pruebas (*Test-Driven Development*, TDD) garantiza la validez matemática en los cálculos de geometría articular y la sincronización algorítmica de trayectorias previas a su integración en el producto final.

---

## 1.2 Objetivos de la Investigación

### 1.2.1 Objetivo General

Desarrollar un sistema de visión artificial para la detección y comparación objetiva de discrepancias biomecánicas en la ejecución de técnicas de artes marciales, que permita a instructores y practicantes obtener retroalimentación visual diagnóstica mediante el análisis de video en tiempo diferido.

### 1.2.2 Objetivos Específicos

1. **Analizar** los requerimientos funcionales, no funcionales y pedagógicos del proceso de enseñanza-aprendizaje técnico, estableciendo un protocolo de captura de video que defina las condiciones óptimas de ángulo, distancia e iluminación para minimizar el impacto de las oclusiones corporales.
2. **Diseñar** la arquitectura de software y los modelos de datos que permitan la integración desacoplada entre la captura y preprocesamiento de video, el motor de inferencia en la nube y la entrega de reportes visuales interactivos.
3. **Implementar** los módulos computacionales de estimación de pose humana en dos dimensiones (2D), extracción secuencial de coordenadas articulares y comparación algorítmica de curvas de desviación angular respecto al video patrón del instructor.
4. **Validar** la precisión y exactitud diagnóstica del sistema mediante pruebas experimentales de concordancia frente al criterio evaluativo de instructores certificados, evaluando adicionalmente la usabilidad y adopción de la herramienta por parte de los practicantes en la academia piloto.

---

## 1.3 Metodología

La investigación se clasifica como un estudio aplicado y de desarrollo tecnológico, fundamentado en un diseño metodológico mixto: cuantitativo para la determinación de métricas de precisión articular, desviación angular y rendimiento computacional; y cualitativo para la evaluación de la experiencia de usuario y utilidad pedagógica en el entorno real de entrenamiento.

El proceso de construcción del sistema se articula a través de las siguientes dimensiones de ingeniería:

1. **Modelado y Arquitectura Orientada a Objetos:** Definición formal del dominio del problema, descomposición en componentes de alta cohesión y bajo acoplamiento para independizar el motor de visión de las capas de persistencia e interfaces de usuario.
2. **Ciclo de Desarrollo Iterativo e Incremental:** Planificación de sprints de trabajo que permitan evolucionar la solución de forma controlada, integrando retroalimentación empírica continua proveniente de las pruebas de video en el tatami.
3. **Desarrollo Guiado por Pruebas (TDD):** Implementación de una batería de pruebas unitarias y de integración previa a la codificación de la lógica algorítmica, blindando la consistencia matemática de los cálculos trigonométricos, la correspondencia temporal de keypoints y la correcta anotación gráfica de fotogramas.

---

# Capítulo 2: Marco Contextual y Análisis Organizacional

## 2.1 Descripción de la Empresa

La academia piloto objeto de este estudio es **Corpo e Mente**, un centro especializado en la enseñanza técnica de Jiu-Jitsu Brasileño (BJJ). En la sucursal analizada, ubicada en Santa Cruz de la Sierra, Bolivia, la academia opera bajo un modelo de **alianza estratégica y externalización de servicios (outsourcing)** con el gimnasio **Knock Out Gym**.

Bajo este esquema operativo:
* **Knock Out Gym** centraliza la infraestructura física, la gestión comercial, el marketing, la administración de membresías y la recaudación económica directa de los alumnos.
* **Corpo e Mente** aporta el capital intelectual, el programa pedagógico estructurado y el capital humano especializado (instructores) para la instrucción técnica en el tatami.

Esta simbiosis permite a Corpo e Mente enfocarse exclusivamente en la excelencia técnica, mientras delega la carga administrativa y financiera al socio estratégico.

## 2.2 Descripción Organizacional de la Empresa

Dada la naturaleza del modelo de alianza descrito, la estructura organizativa de Corpo e Mente en esta sucursal es **minimalista y altamente especializada**. No existe una jerarquía administrativa interna, ya que todas las funciones de soporte, cobranza y mantenimiento son absorbidas por la estructura de Knock Out Gym.

La estructura operativa se reduce a un esquema unipersonal en el nivel técnico:

```mermaid
graph TD
    A[Administración Knock Out Gym] -->|Gestiona Inscripciones y Pagos| B(Alumnos)
    A -->|Pago de Honorarios/Comisión| C[Profesor Único Corpo e Mente]
    C -->|Instrucción Técnica y Evaluación| B
```

* **Nivel Administrativo (Externo):** Gestionado íntegramente por el personal de Knock Out Gym. Responsables del registro de nuevos miembros, cobro de mensualidades y mantenimiento de las instalaciones.
* **Nivel Técnico-Pedagógico (Interno):** Representado exclusivamente por el **Profesor Único** de Corpo e Mente. Este rol posee autonomía total sobre el diseño curricular, la ejecución de clases y la evaluación técnica, actuando como el único punto de contacto técnico para la comunidad de usuarios.

## 2.4 Manual de Funciones (Perfil Unipersonal)

Al existir un único puesto de trabajo representativo de la marca Corpo e Mente en esta sucursal, las responsabilidades se concentran en un perfil multifuncional de alto rendimiento.

**Cargo:** Profesor Único / Instructor Titular  
**Objetivo del Cargo:** Dirigir, planificar y supervisar la formación técnica, física y táctica de los practicantes de Jiu-Jitsu, garantizando la seguridad, la progresión técnica y la retención de alumnos dentro del ecosistema de Knock Out Gym.

**Funciones Principales:**
1. **Área Pedagógica:** Diseñar la currícula técnica diaria y mensual, adaptando contenidos tanto para grupos infantiles como adultos, y diferenciando entre clases grupales masivas y sesiones individuales.
2. **Área Operativa (Ejecución Integral):** Dirigir todas las fases de la sesión de entrenamiento: desde el calentamiento dirigido y movilidad articular, hasta la demostración biomecánica de la técnica del día.
3. **Área de Supervisión y Corrección:** Fiscalizar la práctica simultánea de múltiples parejas en el tatami. *Nota crítica:* Al ser el único instructor, debe rotar constantemente entre las parejas, lo que genera intervalos de tiempo donde los alumnos practican sin retroalimentación inmediata.
4. **Área Evaluativa:** Coordinar, evaluar y ejecutar los exámenes de grado para las distintas categorías de edad y niveles de cinturón, validando la progresión técnica.
5. **Área de Coordinación Interinstitucional:** Mantener comunicación fluida con la administración de Knock Out Gym para reportar asistencia, gestionar bajas temporales y analizar el comportamiento de la comunidad (los 77 miembros registrados).

## 2.5 Flujo del Negocio

### 2.5.1 Flujo Comercial y de Recaudación

El proceso financiero sigue una ruta triangular que separa la captación del cliente de la prestación del servicio técnico:

1. **Captación y Cobro:** El interesado acude a las instalaciones de Knock Out Gym, se registra en su sistema administrativo y cancela su membresía directamente en la recepción del gimnasio. El dinero ingresa a las cuentas de Knock Out.
2. **Asignación de Servicio:** El gimnasio otorga al alumno el acceso al área de tatami asignada contractualmente a Corpo e Mente.
3. **Compensación Económica:** Knock Out Gym liquida de forma periódica (mensual o por comisión) los honorarios correspondientes al Profesor Único de Corpo e Mente por los servicios de enseñanza prestados a la base de usuarios activa.

### 2.5.2 Flujo Operativo de la Clase Diaria (El Cuello de Botella Crítico)

La dinámica interna de la clase revela la necesidad urgente de apoyo tecnológico debido a la limitación de recursos humanos:

1. **Ingreso al Tatami:** El Profesor Único y los alumnos activos (promedio de 15 diarios) acceden al espacio asignado.
2. **Fase de Calentamiento:** El profesor dirige personalmente los ejercicios de movilidad y acondicionamiento. Durante esta fase, su atención está dividida entre demostrar y asegurar que nadie se lesione.
3. **Explicación de la Técnica:** El profesor demuestra la biomecánica de la técnica del día (ej. escape de la montada), utilizando a un alumno avanzado como apoyo visual.
4. **Práctica Simultánea en Parejas:** Los ~15 alumnos se dividen en ~7-8 parejas. Una persona ejecuta la técnica y la otra la recibe.
5. **El Cuello de Botella Crítico:**
   * El Profesor Único debe pasar pareja por pareja corrigiendo detalles finos.
   * Mientras corrige a la **Pareja A**, las **Parejas B, C, D, E, F, G y H** quedan sin supervisión directa.
   * Si un alumno comete un error biomecánico en ese intervalo, lo repite varias veces hasta que el profesor llega, fijando el vicio motor.
   * Este problema se agrava exponencialmente con los **alumnos intermitentes** (que vuelven tras 3-5 meses), quienes han perdido la memoria motriz y requieren correcciones constantes que el profesor único no puede cubrir simultáneamente para todos.

---

# Capítulo 3: Marco Teórico e Ingeniería de Selección

## 3.1 Ingeniería de Selección de Modelos de Estimación de Pose (HPE)

Para la extracción del esqueleto anatómico de los practicantes, se evaluaron tres arquitecturas de vanguardia en visión artificial: MediaPipe Pose (Google), OpenPose (CMU) y Ultralytics YOLO26-Pose. La evaluación se fundamentó en criterios de latencia en inferencia remota, robustez ante oclusiones corporales severas originadas por el contacto estrecho y facilidad de integración en una canalización (*pipeline*) de software basada en Python.

### 3.1.1 Matriz Comparativa de Modelos Core de Visión

| Criterio Técnico | MediaPipe Pose | OpenPose (Baseline) | Ultralytics YOLO26-Pose |
| :--- | :--- | :--- | :--- |
| **Enfoque de Red** | Top-down (Monorregión) | Bottom-up (Campos de Afinidad Part Affinity Fields) | Single-Shot Retainers (End-to-End) |
| **Inferencia en CPU** | Alta eficiencia (Mobile) | Inviable ($< 3$ FPS) | Optimizada (Hasta 43% más rápida) |
| **Manejo de Oclusión** | Deficiente en contacto (pérdida de *keypoints*) | Alto costo computacional | Excelente (Alineación por STAL y pérdida progresiva) |
| **Post-procesamiento** | No requiere | Requiere NMS pesado y enlace algebraico | NMS-Free nativo (Cero latencia post-red) |
| **Formato de Exportación** | Propietario (`.tflite`) | Complejo (C++ nativo / Caffe) | Altamente versátil (`.pt`, `ONNX`, `TensorRT`) |

### 3.1.2 Justificación de la Elección de YOLO26-Pose

Se determinó la selección de YOLO26-Pose a partir de dos ventajas arquitecturales determinantes para el dominio de estudio:

1. **Inferencia End-to-End libre de NMS (Non-Maximum Suppression):** A diferencia de las iteraciones previas de la familia YOLO o de arquitecturas basadas en agrupamiento como OpenPose, YOLO26 efectúa la predicción directa de las coordenadas articulares sin demandar una etapa posterior de supresión de no máximos. Dicho factor elimina cuellos de botella algorítmicos en el backend local y confiere estabilidad a los tiempos de inferencia en la nube sobre Google Colab Pro.
2. **Algoritmo STAL (Small-Target-Aware Label Assignment):** Durante las transiciones en el suelo características del Jiu-Jitsu, determinados segmentos anatómicos distales (como muñecas, tobillos o pies en posiciones de sumisión o guardia) ocupan una fracción reducida de píxeles en el fotograma. El mecanismo STAL incrementa sustancialmente la cobertura de etiquetas positivas asignadas a objetos y coyunturas de escala reducida, mitigando el parpadeo (*jitter*) o la desconexión del grafo esquelético ante deformaciones complejas.

---

## 3.2 Extracción de Características y Cinemática Vectorial Bidimensional (2D)

Tras la detección de los 17 puntos articulares del estándar COCO por parte de YOLO26-Pose, se estructura un espacio formal euclidiano para el análisis biomecánico de las trayectorias.

### 3.2.1 Formalismo Matemático para el Análisis Angular

Cada articulación de interés se modela como un vértice dinámico inmerso en un espacio vectorial $\mathbb{R}^2$. Para cuantificar la conformación de una articulación central $B$ conectada a sus vértices adyacentes proximal $A$ y distal $C$, se construyen los vectores de segmento corporal correspondientes:

$$\vec{u} = \vec{BA} = (x_A - x_B, \, y_A - y_B)$$

$$\vec{v} = \vec{BC} = (x_C - x_B, \, y_C - y_B)$$

La magnitud del ángulo interarticular $\theta(t)$ en el instante de tiempo o fotograma $t$ se obtiene a través del producto escalar euclidiano y la función arco coseno:

$$\theta(t) = \arccos\left( \frac{\vec{u} \cdot \vec{v}}{\Vert{}\vec{u}\Vert{} \, \Vert{}\vec{v}\Vert{}} \right) = \arccos\left( \frac{(x_A - x_B)(x_C - x_B) + (y_A - y_B)(y_C - y_B)}{\sqrt{(x_A - x_B)^2 + (y_A - y_B)^2} \; \sqrt{(x_C - x_B)^2 + (y_C - y_B)^2}} \right)$$

**Justificación de invarianza:** La formulación vectorial asegura invarianza matemática frente a traslaciones en el plano y variaciones de escala geométrica. Por consiguiente, divergencias en la distancia focal o posición relativa de los practicantes respecto a la cámara no alteran la estimación angular, facultando una comparación directa y robusta entre el video del profesor y el del alumno.

---

## 3.3 Algoritmo de Aislamiento y Priorización del Ejecutor (Target Isolation)

Dada la co-presencia inevitable de dos cuerpos en interacción física dentro del encuadre (alumno ejecutor y compañero de apoyo o receptor pasivo), es indispensable aislar las coordenadas esqueléticas del sujeto activo. Se contrastaron dos alternativas de ingeniería para su resolución en el backend:

* **Alternativa A: Clasificación por área de Bounding Box:** Asignación del rol de ejecutor a la silueta con mayor envolvente en píxeles. Resulta errática en fases de suelo donde el receptor suele quedar posicionado por encima del ejecutor.
* **Alternativa B (Seleccionada): Filtro de Varianza Cinemática Acumulada (Kinematic Variance Filter):** Detección del sujeto activo mediante la energía de movimiento temporal.

### 3.3.1 Formalismo Matemático del Aislamiento Cinemático

En técnicas de defensa y escape en el tatami, el sujeto receptor adopta un rol de contención predominantemente estático o isométrico, en tanto que el ejecutor despliega aceleraciones angulares y traslaciones significativas de su centro de gravedad. El sistema evalúa la varianza temporal de las coordenadas del centroide $(\bar{x}, \bar{y})$ de cada individuo detectado durante una ventana inicial de $N$ fotogramas ($N = 30$):

$$\sigma^2_{x} = \frac{1}{N}\sum_{t=1}^{N}(x_t - \bar{x})^2, \quad \sigma^2_{y} = \frac{1}{N}\sum_{t=1}^{N}(y_t - \bar{y})^2$$

$$V_{\text{total}} = \sigma^2_{x} + \sigma^2_{y}$$

El algoritmo asocia la etiqueta de *Ejecutor Objetivo* al identificador de seguimiento (*tracking ID*) que exhibe el valor supremo de $V_{\text{total}}$ en la serie analizada. Las trayectorias del sujeto secundario son enmascaradas en las matrices subsiguientes, previniendo perturbaciones en la cuantificación del error biomecánico.

---

## 3.4 Sincronización Temporal de Movimientos Heterogéneos

La cadencia y velocidad de ejecución entre el docente experto y el alumno presentan asimetrías temporales sistemáticas. Para el alineamiento de las series temporales de ángulos articulares se evaluaron dos estrategias:

```mermaid
graph LR
    A[Resampleo Lineal] -->|Fuerza duraciones idénticas frame a frame| B(Destruye la física del movimiento)
    C[Alineación Temporal DTW] -->|Empareja hitos cinemáticos por costo mínimo| D(Preserva la dinámica temporal real)
```

1. **Resampleo Lineal Dinámico:** Forzamiento algebraico de correspondencia marco a marco por interpolación. Se desestimó debido a la asunción errónea de velocidades de ejecución constantes en sujetos humanos.
2. **Alineación Temporal Dinámica (Dynamic Time Warping - DTW) (Seleccionada):** Determina una ruta óptima de emparejamiento sobre una matriz de distancias locales de orden $M \times K$, siendo $M$ el número de fotogramas de la referencia docente y $K$ el de la ejecución del practicante. El algoritmo minimiza recursivamente la distancia acumulada:

$$D(i, j) = \text{dist}\big(\theta_{\text{prof}}(i), \, \theta_{\text{alum}}(j)\big) + \min\Big\{D(i-1, j), \, D(i, j-1), \, D(i-1, j-1)\Big\}$$

**Justificación técnica:** DTW permite la convergencia sobre hitos biomecánicos críticos (p. ej., el ápice angular de elevación pélvica durante un puente defensivo) con independencia de desfases cronológicos absolutos, acomodando las diferencias de fluidez motriz entre practicantes avanzados y novatos.

---

## 3.5 Arquitectura de Datos e Infraestructura de Cómputo (Cloud-Edge)

En correspondencia con las restricciones de implementación del proyecto (entorno de desarrollo local, capacidades de aceleración por GPU en la nube y visualización orientada al usuario móvil), se estableció un patrón de cómputo asíncrono con persistencia desacoplada.

### 3.5.1 Topología del Flujo de Datos

```mermaid
sequenceDiagram
    participant App as Cliente Móvil (PWA)
    participant Edge as Laptop Backend (FastAPI)
    participant Drive as Google Drive Storage
    participant Colab as Google Colab Pro (YOLO26 + DTW)

    App->>Edge: Carga de Video vía HTTPS
    Edge->>Drive: Publicación de archivo estructurado (ID_ALUMNO_TECNICA_FECHA.mp4)
    Drive-->>Colab: Detección por demonio de escaneo (FS Mount)
    Note over Colab: Inferencia YOLO26-Pose + DTW + Anotación visual (Δθ > 15°)
    Colab->>Drive: Depósito de video renderizado (_PROCESADO.mp4) + Métricas JSON
    Drive-->>Edge: Sincronización automática de resultados
    Edge-->>App: Notificación y visualización de auditoría
```

### 3.5.2 Justificación de la Infraestructura Seleccionada

1. **Google Drive como Middleware de Persistencia Desacoplada:** La interconexión mediante almacenamiento compartido elude la necesidad de túneles bidireccionales continuos (e.g., WebSockets persistentes o gRPC sobre IP pública), cuya estabilidad se ve severamente afectada en redes de gimnasios o entornos de conectividad residencial.
2. **Despacho Asíncrono de Inferencia:** El servidor edge local en FastAPI funciona como un receptor y despachador ligero con sobrecarga computacional mínima. El entorno en la nube (Google Colab Pro) opera mediante un demonio en segundo plano que monitorea el volumen montado, procesa los análisis cinemáticos con aceleración por GPU y renderiza indicadores visuales cuando las discrepancias angulares superan el umbral de tolerancia prescrito ($\Delta\theta > 15^\circ$). El resultado queda disponible para descarga diferida, ofreciendo tolerancia a desconexiones transitorias y mitigando el consumo de recursos de cómputo en la máquina local.