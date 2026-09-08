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