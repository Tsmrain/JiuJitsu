# Capítulo 1: Definición del Proyecto de Investigación

## 1.1 Definición del Problema

### 1.1.1 Situación Problemática

En la enseñanza de artes marciales, particularmente en el Jiu-Jitsu Brasileño (BJJ), la corrección técnica constituye un pilar fundamental para el aprendizaje efectivo y la prevención de lesiones musculoesqueléticas. En el modelo tradicional de instrucción presencial, el docente supervisa de manera simultánea a múltiples practicantes durante sesiones de entrenamiento en pareja. Esta dinámica impone una restricción física operativa: la imposibilidad de suministrar retroalimentación inmediata, exhaustiva y cuantitativa a cada practicante de forma continua.

En la academia piloto Corpo e Mente (instalaciones de Knock Out Gym, Santa Cruz de la Sierra, Bolivia), la comunidad asciende a 77 miembros registrados, con una concurrencia media diaria de 15 practicantes. Se evidencia una notable tasa de rotación y deserción temporal, en la cual los estudiantes suspenden y retoman la disciplina tras periodos prolongados de inactividad. A lo largo de estas transiciones, los estudiantes tienden a consolidar vicios biomecánicos recurrentes —tales como alineaciones articulares desfavorables, trayectorias erróneas de palanca o ángulos deficitarios en el torso— que eluden la observación del instructor debido a los límites de supervisión visual simultánea. La carencia de un instrumento objetivo de contraste visual que compare la cinemática del practicante frente a un patrón canónico de ejecución conduce a una desaceleración en la curva de dominio motor y a la asimilación persistente de incorrecciones técnicas.

### 1.1.2 Situación Deseada

Se propone el desarrollo y despliegue de un sistema computacional de asistencia al entrenamiento sustentado en visión artificial, concebido para contrastar la ejecución cinemática de los alumnos con un patrón biomecánico de referencia predefinido. El sistema procesará secuencias de video registradas durante las sesiones de entrenamiento, cuantificará las discrepancias articulares críticas y generará reportes visuales con marcadores diagnósticos sobre las regiones de error. Dicha retroalimentación será accesible tanto desde dispositivos móviles personales como en estaciones de visualización en tatami, fomentando el autoaprendizaje guiado y optimizando la dedicación del instructor hacia la corrección táctica y estratégica de nivel avanzado.

### 1.1.3 Objeto de Investigación

El objeto de investigación comprende el diseño, estructuración y validación experimental de un sistema de visión por computadora fundamentado en modelos de redes neuronales convolucionales y transformadores para la estimación de pose humana tridimensional o bidimensional. Dicho sistema está orientado a detectar, parametrizar y señalar discrepancias biomecánicas en la cinemática de técnicas complejas de artes marciales, operando bajo una arquitectura híbrida de computación distribuida (*edge-cloud*).

### 1.1.4 Alcance y Delimitación

* **Delimitación temporal:** La investigación abarca el periodo cronológico correspondiente al ciclo académico de diseño, desarrollo y defensa del proyecto de grado.
* **Delimitación espacial:** Las pruebas experimentales y la recolección del corpus de video se circunscriben a las instalaciones de la academia Corpo e Mente (Santa Cruz de la Sierra, Bolivia).
* **Delimitación temática y técnica:** El alcance analítico se enfoca en técnicas canónicas de control posicional y defensa en suelo (específicamente, técnicas de transición y escape como el escape de la montada). La estimación postural se restringe a la extracción de puntos articulares (*keypoints*) anatómicos principales en planos bidimensionales y su contraste cinemático relativo. El sistema actúa en calidad de herramienta complementaria de diagnóstico y no reemplaza el criterio pedagógico ni la prescripción técnica del docente titular. Se excluye la clasificación automática de técnicas arbitrarias no catalogadas y la medición de magnitudes fisiológicas o de fuerza isométrica.

### 1.1.5 Justificación de la Investigación

* **Justificación teórica:** El trabajo contribuye al cuerpo de conocimiento de la visión por computadora y el procesamiento digital de señales aplicado a la biomecánica deportiva, extendiendo la aplicación de algoritmos de estimación de pose hacia disciplinas de contacto cuerpo a cuerpo con altas tasas de oclusión visual intercorporal, área escasamente documentada en el contexto académico regional.
* **Justificación práctica:** Aporta una solución tecnológica directamente transferible a la academia Corpo e Mente, optimizando la gestión pedagógica del aula, mitigando riesgos lesivos por técnica deficiente y proveyendo un mecanismo reproducible de auto-entrenamiento supervisado.
* **Justificación metodológica:** La investigación implementa un proceso riguroso de ingeniería de software con arquitectura orientada a objetos y ciclos de desarrollo iterativos e incrementales. La incorporación de prácticas de verificación formal y desarrollo guiado por pruebas (*Test-Driven Development*, TDD) garantiza la validez numérica, reproducibilidad y estabilidad de los algoritmos de cálculo angular y alineamiento temporal de trayectorias cinemáticas previo a su integración con interfaces de usuario.

---

## 1.2 Objetivos de la Investigación

### 1.2.1 Objetivo General

Desarrollar un sistema de visión artificial para la detección automática y comparación cuantitativa de discrepancias biomecánicas en la ejecución de técnicas de artes marciales, que permita a instructores y practicantes acceder a retroalimentación cinemática estructurada mediante el procesamiento de video en tiempo diferido.

### 1.2.2 Objetivos Específicos

1. **Analizar** los requerimientos funcionales y no funcionales del proceso de corrección técnica y biomecánica en academias de artes marciales, catalogando los patrones articulares críticos y las restricciones de oclusión características del dominio de estudio.
2. **Diseñar** la arquitectura de software distribuida, los modelos de dominio y las estructuras de datos necesarias para articular la captura de video en borde, el procesamiento cinemático en infraestructura remota y la persistencia de métricas comparativas.
3. **Implementar** los módulos algorítmicos de estimación de pose humana, extracción de secuencias de coordenadas esqueléticas y cálculo de divergencias angulares y temporales respecto a las trayectorias canónicas de referencia.
4. **Validar** la exactitud diagnóstica y la concordancia del sistema mediante pruebas experimentales frente a evaluaciones emitidas por instructores certificados, determinando métricas formales de precisión, sensibilidad y usabilidad del prototipo.

---

## 1.3 Metodología

La investigación se enmarca como un estudio aplicado de desarrollo tecnológico con diseño experimental y enfoque metodológico mixto: cuantitativo para la medición del error articular, desviación angular media y latencia de inferencia; y cualitativo para la evaluación de la experiencia de usuario y utilidad pedagógica en campo.

El marco operativo de ingeniería contempla la articulación armónica de tres directrices:

1. **Modelado y arquitectura de sistemas:** Aplicación de principios de análisis y diseño orientado a objetos y patrones arquitectónicos limpios para la delimitación desacoplada de capas de dominio, aplicación e infraestructura.
2. **Ciclo de gestión ágil:** Planificación de entregas e incrementos funcionales mediante iteraciones estructuradas, posibilitando la calibración progresiva de los algoritmos de visión ante grabaciones reales con variaciones de iluminación y perspectiva.
3. **Aseguramiento de calidad y verificación:** Empleo de desarrollo guiado por pruebas (*Test-Driven Development*) para blindar la consistencia matemática en las transformaciones trigonométricas, algoritmos de alineación temporal (*Dynamic Time Warping*) y generación de diagnósticos visuales.