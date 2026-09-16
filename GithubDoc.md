FACULTAD DE INGENIERÍA
CARRERA: INGENIERÍA DE SISTEMAS

MODALIDAD DE GRADUACIÓN
PROYECTO DE GRADO

SISTEMA DE ANÁLISIS BIOMECÁNICO DE
APOYO PARA JIUJITSU BRASILEÑO PARA LA
ACADEMIA CORPO E MENTE

Santiago Borda Zambrana

Santa Cruz de la Sierra - Bolivia
2026

FACULTAD DE INGENIERÍA
CARRERA: INGENIERÍA DE SISTEMAS

MODALIDAD DE GRADUACIÓN
PROYECTO DE GRADO

SISTEMA DE ANÁLISIS BIOMECÁNICO DE
APOYO PARA JIUJITSU BRASILEÑO PARA LA
ACADEMIA CORPO E MENTE

Proyecto de Grado para optar al tı́tulo de Licenciado(a)
en Ingenierı́a de Sistemas

Santiago Borda Zambrana
Reg.: 2021210057

Santa Cruz de la Sierra - Bolivia
2026

AGRADECIMIENTOS

Agradezco a Dios por traerme a este mundo fuerte y saludable.
A mi madre que gracias a su amor incondicional y su esfuerzo pude estudiar, gracias
mami.
A mi abuela por alimentarme y tener siempre un plato de comida.
A mis tı́os por sus palabras y experiencias vividas para que aprenda.
A ti P@msyta por haberme acompañado y guiado.
Al jiujitsu brasileño, por enseñarme a afrontar los miedos, seguir incluso cuando no
se ve el avance, saber lidiar con la sensación de la derrota y sobre todo a no rendirme
y aprender.

“Un cinturón negro fue un cinturón blanco que no se rindió.”

ABSTRACT
TÍTULO
AUTOR

SISTEMA DE ANÁLISIS BIOMECÁNICO DE APOYO PARA JIUJITSU BRASILEÑO PARA LA ACADEMIA CORPO E MENTE
SANTIAGO BORDA ZAMBRANA

PROBLEMÁTICA
En el aprendizaje del Brazilian Jiu-Jitsu (BJJ), los alumnos principiantes enfrentan
dificultades para evaluar su rendimiento técnico de manera objetiva. Actualmente, el
progreso depende casi en su totalidad de la observación directa del profesor en tiempo
real, lo que genera problemas crı́ticos: falta de atención individualizada en clases numerosas, criterios de evaluación variables según el profesor, y una retroalimentación
diferida o nula si el error no es detectado en el momento.
OBJETIVO GENERAL
Desarrollar una aplicación móvil de apoyo para la academia Corpo e Mente que permita
a los alumnos grabar sus movimientos y compararlos automáticamente con los videos
de referencia de sus profesores. El sistema detectará de forma exacta los fallos en las
posturas del cuerpo y entregará al alumno, de manera inmediata, recomendaciones
claras y explicadas paso a paso para corregir sus errores y mejorar su aprendizaje.
CONTENIDO
El presente trabajo de investigación se ha desarrollado bajo la metodologı́a del Proceso
Unificado (UP).
CARRERA
GUÍA
DESCRIPTORES

EMAIL
FECHA

Ingenierı́a de Sistemas
Velasquez Suarez Nancy Yudy
Visión artificial, estimación de pose, inteligencia artificial generativa, base de datos vectorial, arquitectura de software, aplicación web progresiva, análisis biomecánico.
santiagobordazambrana@gmail.com
Santa Cruz de la Sierra, 2026

Resumen

En este documento se aborda la problemática que enfrentan los alumnos principiantes
de Brazilian Jiu-Jitsu (BJJ) para evaluar su rendimiento técnico de manera objetiva y
continua. Actualmente, la retroalimentación depende exclusivamente de la observación
y experiencia del profesor, lo que genera evaluaciones subjetivas. Esto provoca que el
alumno permanezca estancado en su progreso de aprendizaje por periodos prolongados.
En respuesta a esta necesidad, se propone el desarrollo de una aplicación web progresiva
(PWA) que integra inteligencia artificial y visión por computadora para analizar videos
de entrenamiento.
El desarrollo del software se divide en cuatro etapas metodológicas bajo el Proceso
Unificado (UP): Inicio, Elaboración, Construcción y Transición.

ÍNDICE GENERAL
CAPÍTULO I: DEFINICIÓN DEL PROYECTO DE INVESTIGACIÓN 1
1.1Definición del problema . . . . . . . . . . . . . . . . . . . . . . . . . . .
1.1.1 Situación problemática . . . . . . . . . . . . . . . . . . . . . . . . . . .
1.1.2 Situación deseada . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1.1.3 Objeto de investigación . . . . . . . . . . . . . . . . . . . . . . . . . . .
1.1.4 Alcance . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1.1.4.1 Alcance Funcional . . . . . . . . . . . . . . . . . . . . . . . . .
1.1.4.2 Alcance Tecnológico . . . . . . . . . . . . . . . . . . . . . . . .
1.1.4.3 Exclusiones . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1.1.5 Justificación . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1.1.5.1 Justificación Técnica y de Diseño del Producto . . . . . . . . . .
1.1.5.2 Justificación Práctica, Social y de Retención de Clientes . . . .
1.1.5.3 Justificación Económica, Institucional y de Negocio . . . . . . .

1
1
1
2
2
2
2
3
3
3
3
3

1.2Objetivos . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1.2.1 Objetivo General . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1.2.2 Objetivos Especı́ficos . . . . . . . . . . . . . . . . . . . . . . . . . . . .

5
5
5

1.3Metodologı́a . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
1.3.1 Ingenierı́a de Software (Proceso Unificado) . . . . . . . . . . . . . . . .
1.3.2 Gestión del Proyecto (Scrum) . . . . . . . . . . . . . . . . . . . . . . .

6
6
6

CAPÍTULO II: MARCO INSTITUCIONAL . . . . . . . . . . . . . . . .

7

2.1Antecedentes Institucionales . . . . . . . . . . . . . . . . . . . . . . . .

7

2.2Estructura Orgánica (Organigrama) . . . . . . . . . . . . . . . . . . . .

7

2.3Flujo del Negocio y Análisis de Procesos . . . . . . . . . . . . . . . . .

10

CAPÍTULO III: MARCO TEÓRICO Y TECNOLÓGICO

. . . . . . .

12

3.1Fundamentos Teóricos . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3.1.1 Jiu-Jitsu Brasileño (BJJ) y Análisis Biomecánico Postural . . . . . . .
3.1.2 Estimación de Pose Corporales y Profundidad Métrica Monocular . . .
3.1.3 Recuperación Aumentada por Generación (RAG) . . . . . . . . . . . .

12
12
12
12

3.2Selección y Justificación Tecnológica . . . . . . . . . . . . . . . . . . .
3.2.1 Módulo de Visión Artificial: Suite YOLO26x-Pose + YOLO26x-Depth

14
14

5

3.2.1.1 Tecnologı́a Seleccionada . . . . . . . . . . . . . . . . . . . . . .
3.2.1.2 Alternativas Consideradas . . . . . . . . . . . . . . . . . . . . .
3.2.1.3 Justificación de la Selección . . . . . . . . . . . . . . . . . . . .
3.2.2 Infraestructura de Inferencia GPU en la Nube: Google Colab GPU +
Ngrok . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
3.2.2.1 Tecnologı́a Seleccionada . . . . . . . . . . . . . . . . . . . . . .
3.2.2.2 Alternativas Consideradas . . . . . . . . . . . . . . . . . . . . .
3.2.2.3 Justificación de la Selección . . . . . . . . . . . . . . . . . . . .
3.2.3 Modelo de Lenguaje Generativo: Gemini 2.5 Flash . . . . . . . . . . . .
3.2.3.1 Tecnologı́a Seleccionada . . . . . . . . . . . . . . . . . . . . . .
3.2.3.2 Alternativas Consideradas . . . . . . . . . . . . . . . . . . . . .
3.2.3.3 Justificación de la Selección . . . . . . . . . . . . . . . . . . . .
3.2.4 Base de Datos Vectorial para RAG: Qdrant Vector Database . . . . . .
3.2.4.1 Tecnologı́a Seleccionada . . . . . . . . . . . . . . . . . . . . . .
3.2.4.2 Alternativas Consideradas . . . . . . . . . . . . . . . . . . . . .
3.2.4.3 Justificación de la Selección . . . . . . . . . . . . . . . . . . . .
3.2.5 Framework Backend: FastAPI (Python 3.11+) . . . . . . . . . . . . . .
3.2.5.1 Tecnologı́a Seleccionada . . . . . . . . . . . . . . . . . . . . . .
3.2.5.2 Alternativas Consideradas . . . . . . . . . . . . . . . . . . . . .
3.2.5.3 Justificación de la Selección . . . . . . . . . . . . . . . . . . . .
3.2.6 Base de Datos Relacional: PostgreSQL en BCNF con JSONB . . . . .
3.2.6.1 Tecnologı́a Seleccionada . . . . . . . . . . . . . . . . . . . . . .
3.2.6.2 Alternativas Consideradas . . . . . . . . . . . . . . . . . . . . .
3.2.6.3 Justificación de la Selección . . . . . . . . . . . . . . . . . . . .
3.2.7 Interfaz de Usuario: Aplicación Web Progresiva (PWA) . . . . . . . . .
3.2.7.1 Tecnologı́a Seleccionada . . . . . . . . . . . . . . . . . . . . . .
3.2.7.2 Alternativas Consideradas . . . . . . . . . . . . . . . . . . . . .
3.2.7.3 Justificación de la Selección . . . . . . . . . . . . . . . . . . . .

14
14
14

CAPÍTULO IV: DEFINICIÓN DE REQUISITOS . . . . . . . . . . . . .

19

4.1Introducción . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4.1.1 Propósito . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4.1.2 Ámbito del sistema . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4.1.3 Definiciones, acrónimos y abreviaturas . . . . . . . . . . . . . . . . . .
4.1.4 Visión general del documento . . . . . . . . . . . . . . . . . . . . . . .

19
19
19
19
20

4.2Descripción general . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4.2.1 Perspectiva del producto . . . . . . . . . . . . . . . . . . . . . . . . . .
4.2.2 Funciones del Producto . . . . . . . . . . . . . . . . . . . . . . . . . . .

21
21
21

6

15
15
15
15
15
15
15
16
16
16
16
16
17
17
17
17
17
17
17
17
18
18
18
18

4.2.3 Caracterı́sticas de los Usuarios . . . . . . . . . . . . . . . . . . . . . . .
4.2.4 Restricciones . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4.2.5 Suposiciones y Dependencias . . . . . . . . . . . . . . . . . . . . . . . .
4.2.6 Requisitos Futuros . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

21
21
22
22

4.3Requisitos Especı́ficos . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4.3.1 Interfaces Externas . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4.3.1.1 Interfaces de Software . . . . . . . . . . . . . . . . . . . . . . .
4.3.1.2 Interfaces de Hardware . . . . . . . . . . . . . . . . . . . . . . .
4.3.2 Requisitos Funcionales . . . . . . . . . . . . . . . . . . . . . . . . . . .
4.3.3 Requisitos de Rendimiento . . . . . . . . . . . . . . . . . . . . . . . . .
4.3.4 Restricciones de Diseño . . . . . . . . . . . . . . . . . . . . . . . . . . .
4.3.5 Atributos del Sistema . . . . . . . . . . . . . . . . . . . . . . . . . . . .

23
23
23
23
23
24
24
24

4.4Identificación de los casos de uso . . . . . . . . . . . . . . . . . . . . . .

25

4.5Diagrama de dominio . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

26

4.6Trazabilidad Arquitectónica (Casos de Uso vs. Controladores) . . .

27

4.7Limitaciones y Trabajo Futuro . . . . . . . . . . . . . . . . . . . . . . .

28

7

CAPÍTULO I: DEFINICIÓN DEL PROYECTO
DE INVESTIGACIÓN

1.1

Definición del problema

1.1.1

Situación problemática

En la enseñanza del Jiu-Jitsu Brasileño (BJJ) dentro de la academia Corpo e Mente, los
alumnos principiantes e intermedios enfrentan dificultades significativas para evaluar y
perfeccionar su ejecución técnica de manera objetiva y continua. En el modelo tradicional, la enseñanza depende casi exclusivamente de la observación directa y presencial
del profesor durante clases grupales numerosas.
Esta dinámica genera los siguientes problemas crı́ticos:
 Atención individualizada limitada: En clases con alta afluencia de alumnos,
el profesor no puede observar la totalidad de las repeticiones ejecutadas por cada
alumno.
 Retroalimentación diferida o ausente: Si un error postural o de apalancamiento no es detectado en el instante preciso de la ejecución, el alumno tiende
a automatizar patrones de movimiento incorrectos.
 Evaluación subjetiva sin métricas cuantitativas: La corrección tradicional
carece de mediciones objetivas sobre ángulos articulares, alineación espinal o
posición del cuerpo.
 Riesgo incrementado de lesiones: La repetición continua de técnicas con
una biomecánica defectuosa expone a las articulaciones a sobrecargas y tensiones
anómalas.
 Progreso estancado fuera del aula: El alumno no dispone de herramientas
de autoevaluación guiadas fuera de los horarios de entrenamiento para comparar
su desempeño con la técnica patrón enseñada por su profesor.

1.1.2

Situación deseada

La situación deseada consiste en implementar una solución tecnológica de apoyo para
la academia Corpo e Mente basada en una aplicación web que integre visión por computadora e inteligencia artificial generativa.
Con esta solución se logrará:
1. Permitir al alumno grabar sus ejecuciones técnicas desde su dispositivo móvil en
cualquier momento.
1

2. Extraer automáticamente la postura corporal del alumno y compararla de forma
analı́tica con la técnica patrón registrada por el profesor.
3. Identificar desajustes articulares y generar reportes pedagógicos estructurados
(análisis postural, riesgo de lesión y corrección paso a paso).
4. Entregar retroalimentación objetiva, inmediata y fundamentada en literatura especializada de BJJ, acelerando la curva de aprendizaje técnico y reduciendo el
riesgo de lesiones.

1.1.3

Objeto de investigación

El objeto de investigación es el proceso de evaluación y corrección biomecánica postural de técnicas de Jiu-Jitsu Brasileño mediante visión por computadora y modelos de
lenguaje orquestados bajo arquitecturas de recuperación de información.

1.1.4

Alcance

1.1.4.1

Alcance Funcional

 Gestión de Usuarios y Roles: Perfiles para Alumnos (evaluación técnica) y
Profesores (administración de técnicas patrón y fuentes de conocimiento). El
sistema implementa autenticación con PBKDF2-HMAC-SHA256 y validación de
roles contra la tabla usuarios (rol IN (’alumno’, ’profesor’)).
 Registro de Técnicas Patrón: Carga de videos de referencia del profesor y
extracción de posturas corporales patrón.
 Evaluación Biomecánica: Comparación postural entre el video del alumno y
el patrón del maestro para calcular desajustes angulares.
 Búsqueda en Literatura Técnica: Procesamiento e ingesta semántica de manuales y libros de BJJ para fundamentar la retroalimentación.
 Sı́ntesis Pedagógica Estructurada: Generación de reportes explicativos organizados en Análisis Postural, Riesgo de Lesión, Guı́a Paso a Paso y Resumen
Ejecutivo.
 Interfaz Web de Usuario: Aplicación accesible para la carga de videos, consulta de resultados e historial de avance.

1.1.4.2

Alcance Tecnológico

 Aplicación Web y Servidor de Procesamiento: Arquitectura cliente-servidor
orientada a servicios para la captura de video, procesamiento de imágenes y almacenamiento de información.

2

 Modelos de Inteligencia Artificial: YOLO26x-Pose + YOLO26x-Depth para
estimación de pose 3D (17 keypoints COCO), Qwen3-VL-Embedding-2B para vectorización densa de 2048 dimensiones, Gemini 2.5 Flash para sı́ntesis pedagógica
estructurada en JSON.

1.1.4.3

Exclusiones

 El sistema no sustituye la evaluación presencial formal ni el criterio del maestro
para la graduación de cinturones.
 No realiza diagnósticos médicos o clı́nicos fisioterapéuticos de rehabilitación.

1.1.5

Justificación

1.1.5.1

Justificación Técnica y de Diseño del Producto

Desde una perspectiva operativa, el proyecto se justifica al diseñar una solución tecnológica modular y optimizada, cuya infraestructura central delega de forma inteligente
el procesamiento de datos a la nube. Esto permite que el producto final funcione de
manera ágil y fluida en cualquier dispositivo móvil comercial, sin exigir inversiones en
equipos o hardware costosos por parte de los alumnos o la academia. Asimismo, el
sistema almacena de forma ordenada la información transaccional de los usuarios y las
respuestas automatizadas, asegurando la integridad, confidencialidad y consistencia de
los datos para futuras auditorı́as o reportes administrativos de desempeño.
1.1.5.2

Justificación Práctica, Social y de Retención de Clientes

El análisis comercial de la sucursal revela un problema crı́tico de pérdida de clientes
activos (Churn Rate). La comunidad digital de la sucursal registra una base histórica
latente de 79 miembros, pero el tatami sostiene una asistencia promedio real de solo 15
alumnos. Esta brecha expone una tasa de inactividad o abandono del 81%, provocada
por la frustración de los principiantes al no recibir atención individualizada en clases
masivas (el cuello de botella operativo), el estancamiento fuera del aula y el temor
a sufrir lesiones por malas posturas. La implementación de esta plataforma actúa
directamente como una estrategia de fidelización y retención de clientes. Al proveer
al cliente un asistente de entrenamiento virtual disponible las 24 horas para corregir
sus errores basándose en las guı́as oficiales de la escuela, se elimina la barrera de la
frustración inicial. Esto democratiza la atención personalizada, acelera el progreso del
practicante y mitiga los riesgos de abandono, incentivando a que la masa de clientes
inactivos regrese a consumir el servicio presencial de forma recurrente.
1.1.5.3

Justificación Económica, Institucional y de Negocio

Actualmente, el principal generador de ingresos de la sucursal anfitriona (Knockout
Gym) es un modelo paquetizado de 300 Bs mensuales por acceso ilimitado, donde el
Jiu-Jitsu interactúa con otras disciplinas de manera indirecta dentro de un control
de accesos centralizado (administrado mediante sistemas tradicionales como Microsoft
3

Access y lectores de huella locales). Dado que Knockout controla el flujo de caja global
y Corpo e Mente no tiene injerencia en la cobranza diaria de este punto, la academia
necesita consolidar un factor de valor agregado y diferenciación comercial exclusiva para
justificar su permanencia, aumentar su poder de negociación frente al gimnasio y captar
un mayor porcentaje de los ingresos del paquete.
Más allá de este caso de estudio local, la viabilidad económica del proyecto radica
en su capacidad de Escalabilidad y Comercialización Internacional bajo un modelo
de negocio de Software como Servicio (SaaS). El sistema no está diseñado como una
herramienta aislada, sino como un producto empaquetado listo para ser monetizado en
el mercado global de las artes marciales mediante dos vı́as de ingresos:
 Modelos de Licenciamiento por Volumen: Venta de licencias anuales a
academias y redes de dojos de cualquier paı́s, parametrizadas y cobradas según
la capacidad de alumnos registrados en su base de datos (Slots de usuarios).
 Contratos de Soporte y Actualizaciones de Contenido: Cobros anuales
recurrentes por soporte técnico, mantenimiento y la actualización constante del
catálogo de conocimientos y videotutoriales con profesores de alto rango internacional.

De este modo, el proyecto pasa de ser un gasto operativo a convertirse en un activo
tecnológico de alta rentabilidad que eleva el valor de mercado de Corpo e Mente y abre
una nueva lı́nea de ingresos digitales escalables.

4

1.2

Objetivos

1.2.1

Objetivo General

Desarrollar un sistema de apoyo para el análisis biomecánico de movimientos en JiuJitsu Brasileño para la academia Corpo e Mente, mediante visión por computadora e
inteligencia artificial, que permita evaluar objetivamente las ejecuciones técnicas de los
alumnos y proporcionar retroalimentación pedagógica estructurada en tiempo real.

1.2.2

Objetivos Especı́ficos

1. Analizar y especificar los requerimientos del sistema y casos de uso para el registro
de patrones técnicos y la evaluación biomecánica.
2. Implementar el módulo de visión por computadora para la detección y extracción
de posturas corporales a partir de videos de entrenamiento.
3. Desarrollar el algoritmo de comparación biomecánica para computar las diferencias angulares articulares entre la ejecución del alumno y la técnica patrón del
profesor.
4. Construir el motor de búsqueda semántica para recuperar información explicativa
desde literatura especializada de Jiu-Jitsu Brasileño.
5. Integrar el modelo de lenguaje generativo para elaborar reportes de retroalimentación pedagógica en análisis postural, riesgo de lesión, guı́a paso a paso
y resumen ejecutivo.
6. Desarrollar una interfaz web intuitiva y responsiva que permita la interacción
eficiente entre profesores y alumnos.
7. Validar la solución mediante pruebas unitarias, de integración y funcionales.

5

1.3

Metodologı́a

1.3.1

Ingenierı́a de Software (Proceso Unificado)

Para el desarrollo del software se adopta la metodologı́a del Proceso Unificado (UP),
guiada por casos de uso, centrada en la arquitectura de software e iterativa e incremental. Su ciclo de vida comprende cuatro fases:
1. Fase de Inicio (Inception): Definición de los objetivos del proyecto, delimitación del alcance y evaluación de factibilidad.
2. Fase de Elaboración (Elaboration): Especificación detallada de casos de uso,
diseño de la arquitectura en capas y prototipado del motor biomecánico.
3. Fase de Construcción (Construction): Desarrollo iterativo de los componentes del servidor (FastAPI), modelos de inteligencia artificial (YOLO26x en Colab GPU, Qwen3-VL-Embedding-2B, Gemini 2.5 Flash), pipeline RAG (Qdrant
+ PostgreSQL BCNF) e interfaz web progresiva (PWA).
4. Fase de Transición (Transition): Pruebas del sistema, optimización de componentes y despliegue final para la academia Corpo e Mente.

1.3.2

Gestión del Proyecto (Scrum)

La gestión operativa del proyecto se alinea con el marco ágil Scrum, organizando el
trabajo en iteraciones cortas denominadas Sprints:
 Planificación Temporal y Cronograma: El desarrollo del proyecto contempla una duración total de un (1) año, iniciando las actividades de investigación
y desarrollo en febrero de 2026 y finalizando con el despliegue y validación en
diciembre de 2026.
 Product Backlog: Lista priorizada de requisitos y funcionalidades del sistema.
 Sprints: Ciclos de trabajo de 2 semanas para la entrega de incrementos funcionales probados del software.
 Aseguramiento de Calidad: Desarrollo guiado por pruebas para validar el
correcto funcionamiento de la lógica de negocio e interfaces.
 Control de Versiones: Gestión del código fuente mediante control de versiones
y gestión de entornos de trabajo.

6

CAPÍTULO II: MARCO INSTITUCIONAL

2.1

Antecedentes Institucionales

La academia Corpo e Mente (asociada al centro de entrenamiento KnockOut Training Center ) es una institución especializada en la enseñanza y perfeccionamiento de
artes marciales y deportes de contacto, destacando principalmente en la disciplina del
Jiu-Jitsu Brasileño (BJJ) y Judó. Fundada con el propósito de fomentar la disciplina
fı́sica, mental y el desarrollo deportivo integral bajo la dirección técnica del maestro
Humberto Tavares, la academia ofrece programas de formación orientados a practicantes de diversos niveles de experiencia, desde principiantes hasta competidores de
alto rendimiento.

Figura 1: Logotipos Institucionales: Academia Corpo e Mente y KnockOut Training
Center

2.2

Estructura Orgánica (Organigrama)

La estructura organizacional que rige el funcionamiento de la academia se presenta en
la Figura 2, detallando la jerarquı́a internacional de la asociación y su descentralización
operativa dentro del territorio boliviano, con especial énfasis en el nodo correspondiente
al objeto de estudio.
El modelo responde a una estructura mixta (lineal-funcional) que opera bajo un
esquema descentralizado de matriz-filial y alianzas estratégicas de infraestructura corporativa. A continuación, se describen los niveles y componentes que integran esta
estructura:
 1. Nivel Estratégico Internacional (Sede Matriz - Brasil): Representa
la máxima autoridad doctrinaria y metodológica de la escuela, liderada a nivel

7

global por el fundador Master Humberto Tavares. Este nivel se encarga de emitir
los lineamientos técnicos oficiales y validar las certificaciones internacionales de
grados ante entes reguladores globales como la International Brazilian Jiu-Jitsu
Federation (IBJJF). Su relación con la filial nacional es estrictamente doctrinal y
de auditorı́a técnica, sin interferencia directa en la gestión financiera local.
 2. Nivel de Coordinación Nacional (Corpo e Mente - Estructura Central Bolivia): Estructura encargada de centralizar la personerı́a de la marca
en el paı́s. Está dirigida por la Dirección General / Representante Nacional,
unidad de la cual dependen las áreas funcionales de Gestión de Afiliaciones e
Inscripciones (responsable del ecosistema digital en la plataforma Smoothcomp)
y la Coordinación de Eventos y Selectivos (encargada de la logı́stica de torneos
inter-academias). Este nivel supervisa de manera directa la Red de Sucursales distribuidas en la ciudad de Santa Cruz de la Sierra (Sucursal UFC Gym, Sucursal
3 Pasos al Frente, Sucursal UAGRM y la célula del Programa en KnockOut).
 3. El Gimnasio Independiente (Convenio Proveedor Externo - KnockOut Gym): KnockOut Gym opera como un ente administrativo y legalmente
independiente a Corpo e Mente. La relación institucional se define mediante una
Alianza Estratégica de Tercerización de Infraestructura (Outsourcing) bajo un
formato horario especı́fico. KnockOut Gym funge como el agente de recaudación
y cobro de membresı́as mensuales de los alumnos de Jiu-Jitsu, asumiendo el riesgo
comercial del espacio y ejecutando posteriormente el desembolso económico correspondiente (por horas de clase o porcentaje acordado) hacia el cuerpo docente
de la academia. KnockOut Gym no posee participación alguna en la toma de
decisiones organizacionales, metodológicas o de graduaciones de Corpo e Mente,
limitándose contractualmente al alquiler del espacio fı́sico del tatami.
 4. Estructura Operativa Interna (Célula Operativa Nocturna - Sucursal KnockOut): Representa el alcance fı́sico e institucional donde se acota el
despliegue del sistema de software desarrollado. Debido a la naturaleza de la
alianza con el gimnasio anfitrión, la operación se simplifica en una estructura
lineal de turno único enfocado en el horario nocturno.

– Profesor Encargado (Prof. Miguel Baigorria - Cinturón Negro):
Unidad responsable del desarrollo técnico, la planificación de las clases, la
supervisión de la seguridad y el enlace operativo con la administración de
KnockOut Gym. En el contexto del sistema BJJ Biomechanics, este puesto
asume de forma exclusiva el rol de Profesor, encargándose de alimentar el
catálogo de técnicas patrón, cargar videos de referencia cinemática y gestionar el repositorio semántico del motor RAG.
– Alumnos y Atletas de BJJ (Turno Noche): Usuarios finales del programa de entrenamiento nocturno. Dentro del alcance del software, asumen
el rol de Alumno, interactuando con la Aplicación Web Progresiva (PWA)
para registrar sus ejecuciones y recibir la retroalimentación biomecánica automatizada orientada a optimizar su curva de aprendizaje.
8

Figura 2: Organigrama Estructural de KnockOut Training Center
9

2.3

Flujo del Negocio y Análisis de Procesos

El flujo operativo tradicional para la atención y formación de los alumnos dentro de la
academia sigue una serie de pasos secuenciales desde su registro administrativo hasta
el entrenamiento en el tatami.

Figura 3: Diagrama del Flujo del Negocio de la Academia y Detección del Cuello de
Botella
El proceso operativo ilustrado en la Figura 3 comprende las siguientes etapas:
1. El alumno se dirige a la administración para solicitar información o renovar su
membresı́a.
2. La administración muestra el catálogo de disciplinas disponibles (BJJ, Judó).
3. El alumno selecciona la disciplina de su preferencia (foco principal en BJJ).
4. El alumno realiza el pago de la disciplina seleccionada en la recepción.
5. La administración registra el pago en el sistema contable.
6. La administración entrega el recibo o comprobante de inscripción al alumno.
7. El alumno ingresa al área de entrenamiento y entrega el comprobante de pago al
profesor asignado.
8. El profesor imparte la clase técnica y guı́a el entrenamiento del alumno.
9. Cuello de Botella Identificado (Evaluación del Practicante): La evaluación personalizada de posturas y ejecuciones biomecánicas por parte del profesor
constituye un punto crı́tico de estrangulamiento. Debido al número de alumnos
10

por clase y al tiempo limitado del entrenamiento presencial, el profesor no puede
realizar una retroalimentación continua e individualizada para cada repetición
técnica.
El sistema de software propuesto viene a resolver directamente este cuello de botella,
permitiendo que la evaluación técnica sea automatizada mediante visión artificial e
inteligencia artificial.
El cuello de botella identificado (evaluación personalizada) es resuelto directamente
por el caso de uso CU-02 (Evaluar Ejecución Biomecánica con Sı́ntesis Pedagógica), implementado en el controlador EvaluacionController y expuesto vı́a POST /api/v1/alumno/evaluaciones.

11

CAPÍTULO III: MARCO TEÓRICO Y
TECNOLÓGICO

3.1

Fundamentos Teóricos

3.1.1

Jiu-Jitsu Brasileño (BJJ) y Análisis Biomecánico Postural

El Jiu-Jitsu Brasileño es un deporte de combate y arte marcial centrado en la lucha
cuerpo a cuerpo (grappling), donde la victoria se logra mediante el dominio de posiciones
de control o la aplicación de técnicas de sometimiento (palancas articulares y estrangulamientos). La efectividad de una técnica radica en principios fı́sicos fundamentales:
aprovechamiento de palancas cinemáticas, alineación de ejes articulares, gestión del
centro de masa corporal y optimización del apalancamiento mecánico.
El análisis biomecánico en el BJJ estudia el movimiento corporal y las fuerzas involucradas durante la ejecución de las técnicas. La evaluación de los ángulos articulares en
puntos crı́ticos (hombros, codos, caderas, rodillas y tobillos) permite determinar cuantitativamente si la ejecución de un alumno coincide con el patrón ideal dictado por el
profesor o si presenta desviaciones que comprometan la eficacia técnica o incrementen
el riesgo de lesiones.

3.1.2

Estimación de Pose Corporales y Profundidad Métrica
Monocular

La estimación de pose es una rama de la visión por computadora encargada de identificar y rastrear la posición espacial de nodos articulares anatómicos (keypoints) en
fotogramas de video. Combinada con la estimación de profundidad métrica monocular,
es posible reconstruir las coordenadas cinemáticas en tres dimensiones R3 (X, Y, Z) en
metros reales absolutos, sin necesidad de emplear cámaras fı́sicas o sensores infrarrojos
RGB-D costosos.
La fusión geométrica se realiza mediante muestreo bilineal: para cada keypoint
2D (x, y) detectado por YOLO26x-Pose, se escala a las coordenadas del mapa de
profundidad (x d, y d) y se extrae la componente Z métrica: Z = depth map[y d, x d],
expresada en metros reales. La matriz resultante es una MatrizEsqueletica de dominio
con puntos Punto3D(x, y, z).

3.1.3

Recuperación Aumentada por Generación (RAG)

El pipeline RAG implementado consta de 5 etapas:
1. Fragmentación semántica: ChunkerSemanticoBJJ con RecursiveCharacterTextSplitter (chunk size=1000, chunk overlap=200).
12

2. Vectorización: Qwen3-VL-Embedding-2B (2048 dimensiones, normalizado).
3. Almacenamiento vectorial: Qdrant local (colección ’bjj knowledge’, métrica Cosine, búsqueda KNN con filtro por id tecnica).
4. Persistencia relacional: PostgreSQL BCNF (tabla fuentes conocimiento con id documento
para agrupar chunks).
5. Generación: Gemini 2.5 Flash con salida JSON estricta (4 claves).

13

3.2

Selección y Justificación Tecnológica

En esta sección se describen en detalle las tecnologı́as seleccionadas para la implementación del sistema informático, presentando el análisis comparativo y la justificación
técnica de cada elección frente a otras alternativas existentes en el mercado.

3.2.1

Módulo de Visión Artificial: Suite YOLO26x-Pose +
YOLO26x-Depth

3.2.1.1

Tecnologı́a Seleccionada

Se seleccionó la suite combinada de **YOLO26x-Pose** (detección de 17 articulaciones
anatómicas COCO) y **YOLO26x-Depth** (mapa de profundidad métrica monocular
en metros reales absolutos).
3.2.1.2

Alternativas Consideradas

 MediaPipe Pose (Google): Modelo liviano optimizado para dispositivos móviles
y detección de personas individuales.
 OpenPose: Framework académico de alta precisión para detección multipersona
basado en campos de afinidad corporal (PAFs).

3.2.1.3

Justificación de la Selección

Criterio
Contacto Corporal

Profundidad 3D

Velocidad / Latencia

YOLO26x Pose +
Depth (Elegido)
Alto desempeño en
agarres y oclusión.
Profundidad
métrica real Z
vı́a YOLO Depth.
Inferencia
sincrónica
en
tiempo real sobre
GPU.

MediaPipe Pose

OpenPose

Falla con solapamiento de dos
personas.
Sin
profundidad
métrica real absoluta.
Muy rápida en
móvil.

Bueno pero muy
lento en CPU.
Requiere
calibración compleja.
Latencia
elevada
(baja velocidad).

Tabla 1: Cuadro Comparativo de Tecnologı́as de Estimación de Pose y Profundidad
En Jiu-Jitsu Brasileño, dos practicantes interactúan en contacto fı́sico estrecho,
generando oclusiones constantes de extremidades. MediaPipe fue descartado debido
a su baja tolerancia al solapamiento corporal y pérdida de seguimiento en posiciones de
suelo. OpenPose fue descartado por requerir un consumo excesivo de memoria y latencias altas. La combinación de **YOLO26x-Pose + YOLO26x-Depth** permite obtener
coordenadas reales (X, Y, Z) en metros dentro del espacio tridimensional sin requerir

14

sensores hardware RGB-D. La inferencia de YOLO26x-Pose + YOLO26x-Depth se delega a Google Colab Pro (GPU NVIDIA T4/A100) mediante un servidor Flask expuesto
por túnel Ngrok. El backend FastAPI local consume el endpoint POST /inferir y recibe
keypoints 3d + frame base64. Si el túnel no está disponible, el sistema usa AdaptadorYOLO con MockYOLOEngine como fallback (ver src/infrastructure/adapters/yolo adapter.py).

3.2.2

Infraestructura de Inferencia GPU en la Nube: Google
Colab GPU + Ngrok

3.2.2.1

Tecnologı́a Seleccionada

Se seleccionó un servidor de inferencia remoto alojado en **Google Colab** respaldado
por procesadores GPU (NVIDIA T4 / A100), comunicado con la aplicación backend a
través de un túnel seguro **Ngrok**.
3.2.2.2

Alternativas Consideradas

 Procesamiento Local en CPU/GPU del Servidor Backend: Ejecutar los
modelos de visión artificial en la misma máquina que aloja la base de datos y la
API.
 Servicios Cloud Pagos Dedicados (AWS SageMaker / GCP Vertex AI):
Instancias de inferencia de modelos en la nube con costos por hora elevados.

3.2.2.3

Justificación de la Selección

La inferencia sincrónica de YOLO26x-Pose y YOLO26x-Depth requiere aceleración
GPU intensiva. El uso de **Google Colab GPU** permite delegar la carga pesada
de cálculo a la nube sin incurrir en los costos fijos de servidores locales con tarjetas
gráficas costosas ni en la facturación de servicios como AWS SageMaker. El túnel
**Ngrok** garantiza la comunicación cifrada y transparente con la API REST principal en FastAPI. El túnel Ngrok se configura en colab backend.ipynb celda 5, y su
URL se inyecta en .env como COLAB TUNNEL URL.

3.2.3

Modelo de Lenguaje Generativo: Gemini 2.5 Flash

3.2.3.1

Tecnologı́a Seleccionada

Se seleccionó el modelo de lenguaje generativo Gemini 2.5 Flash de Google.
3.2.3.2

Alternativas Consideradas

 OpenAI GPT-4o / GPT-3.5 Turbo: Modelos comerciales de lenguaje de alto
uso general.
 Anthropic Claude 3.5 Sonnet: Modelo enfocado en razonamiento lógico y
código.

15

 Modelos Locales (Llama 3 / Qwen): Modelos de código abierto ejecutados
en servidores propios.

3.2.3.3

Justificación de la Selección

Criterio
Latencia y Costo
Salida Estructurada

Ventana de Contexto

Gemini 2.5 Flash
(Elegido)
Excelente relación
velocidad/costo.
Garantı́a estricta
de JSON Schema.

GPT-4o

Muy amplia para
ingesta RAG.

Adecuada.

Costo por token elevado.
Soporta JSON pero
mayor latencia.

Modelos
Locales
(Llama 3)
Requiere GPUs de
gran memoria.
Inestable en esquemas JSON complejos.
Limitada
según
hardware.

Tabla 2: Cuadro Comparativo de Modelos del Lenguaje (LLM)
Se seleccionó Gemini 2.5 Flash debido a su soporte nativo para forzar respuestas
bajo esquemas JSON estrictos (garantizando los cuatro bloques pedagógicos requeridos:
Análisis Postural, Riesgo de Lesión, Paso a Paso y Resumen Ejecutivo), combinado con
una velocidad de respuesta superior y costos operativos reducidos en comparación con
GPT-4o. El adaptador GeminiServiceAdapter (src/infrastructure/adapters/gemini adapter.py)
fuerza la respuesta mediante un prompt que exige JSON válido con 4 claves exactas.
Si el parseo falla, se usa un fallback dict determinista para evitar alucinaciones.

3.2.4

Base de Datos Vectorial para RAG: Qdrant Vector Database

3.2.4.1

Tecnologı́a Seleccionada

Se seleccionó la base de datos vectorial especializada **Qdrant**.
3.2.4.2

Alternativas Consideradas

 pgvector (Extensión PostgreSQL): Extensión relacional para vectores.
 Pinecone: Servicio de base de datos vectorial 100% gestionado en la nube.
 ChromaDB / FAISS (Meta): Almacenes de vectores embebidos en memoria.

3.2.4.3

Justificación de la Selección

Tecnologı́a seleccionada: Qdrant Vector Database (contenedor Docker bjj qdrant, puerto
6333).
Frente a pgvector: la extensión pgvector restringe los ı́ndices HNSW/IVFFlat a un
máximo de 2000 dimensiones. Dado que Qwen3-VL-Embedding-2B produce vectores
de 2048 dimensiones, Qdrant es la única alternativa que permite indexación eficiente
con filtros de metadatos (id tecnica, id documento).
16

Frente a Pinecone: Qdrant se ejecuta on-premise vı́a Docker, garantizando soberanı́a
de datos y costo cero operativo.

3.2.5

Framework Backend: FastAPI (Python 3.11+)

3.2.5.1

Tecnologı́a Seleccionada

Se seleccionó el framework FastAPI en lenguaje Python 3.11+.
3.2.5.2

Alternativas Consideradas

 Django: Framework Web monolı́tico ”baterı́as incluidas”.
 Flask: Microframework minimalista para Python.
 Node.js (Express.js): Entorno de ejecución en JavaScript ası́ncrono.

3.2.5.3

Justificación de la Selección

FastAPI se eligió por su alto rendimiento basado en asyncio y Starlette (comparable
a Node.js), su validación automática de datos con Pydantic y la generación automática
de documentación interactiva (OpenAPI/Swagger). Frente a Django, FastAPI es infinitamente más ligero para construir arquitecturas de microservicios y APIs REST limpias
en capas. Frente a Node.js, permite integrar directamente las bibliotecas nativas de inteligencia artificial y ciencia de datos de Python. El servidor se expone vı́a uvicorn
en el puerto 8000 (configurable vı́a API PORT). Monta la PWA en /static y sirve el
index.html en /.

3.2.6

Base de Datos Relacional: PostgreSQL en BCNF con
JSONB

3.2.6.1

Tecnologı́a Seleccionada

Se seleccionó PostgreSQL estructurado en Tercera Forma Normal (3FN / BCNF) con
soporte de columnas de tipo JSONB.
3.2.6.2

Alternativas Consideradas

 MySQL / MariaDB: Sistema relacional tradicional popular.
 MongoDB: Base de datos orientada a documentos NoSQL.

3.2.6.3

Justificación de la Selección

PostgreSQL proporciona integridad referencial estricta para entidades transaccionales
(Usuarios, Profesores, Registro de Pagos, Técnicas Patrón), soportando simultáneamente
el tipo de dato nativo JSONB para almacenar las respuestas pedagógicas complejas
emitidas por la IA en la tabla de evaluaciones del alumno. PostgreSQL almacena
17

exclusivamente metadatos relacionales (usuarios, profesores, técnicas patron, evaluaciones alumno, fuentes conocimiento). La persistencia vectorial se delega ı́ntegramente
a Qdrant. La columna JSONB consejo pedagogico en evaluaciones alumno almacena
el objeto estructurado de 4 claves generado por Gemini.

3.2.7

Interfaz de Usuario: Aplicación Web Progresiva (PWA)

3.2.7.1

Tecnologı́a Seleccionada

Se seleccionó una **Aplicación Web Progresiva (PWA)** desarrollada con HTML5,
JavaScript moderno y CSS3.
3.2.7.2

Alternativas Consideradas

 Desarrollo Nativo Móvil (Swift para iOS / Kotlin para Android): Aplicaciones compiladas especı́ficas para cada plataforma.
 Frameworks Multiplataforma (React Native / Flutter): Aplicaciones nativas compiladas desde un solo código fuente.

3.2.7.3

Justificación de la Selección

Una **PWA** permite a los alumnos y profesores utilizar la aplicación directamente
desde el navegador de su teléfono móvil o computadora sin necesidad de descargas ni
comisiones en tiendas de aplicaciones (Google Play / App Store). Ofrece acceso directo
a la cámara del dispositivo para la grabación de videos, soporte para funcionamiento offline mediante Service Workers e instalación directa en la pantalla de inicio, reduciendo
significativamente los costos de mantenimiento multiplataforma. La PWA implementa
un Service Worker (frontend/service-worker.js) con estrategia NetworkFirst para rutas /api/* y CacheFirst para assets estáticos. El manifest.json permite instalación en
pantalla de inicio.

18

CAPÍTULO IV: DEFINICIÓN DE REQUISITOS

4.1

Introducción

4.1.1

Propósito

El propósito de este capı́tulo es especificar de manera formal y detallada los requisitos
funcionales, no funcionales y de sistema para la Aplicación Web Progresiva (PWA)
de análisis biomecánico de Jiu-Jitsu Brasileño para la academia Corpo e Mente. Este
documento sirve como contrato de requerimientos bajo la norma IEEE 830 y como base
para el diseño arquitectónico y desarrollo de los casos de uso bajo el Proceso Unificado
(UP).

4.1.2

Ámbito del sistema

El sistema denominado BJJ Biomechanics es una plataforma de software clienteservidor orientada al ámbito deportivo y educativo. Permite a la academia Corpo
e Mente digitalizar el catálogo de técnicas patrón de sus profesores, procesar videos
de alumnos mediante inferencia 3D en la nube (YOLO26x Pose + Depth en Google
Colab GPU), realizar comparaciones angulares cinemáticas, consultar repositorios de
literatura técnica mediante RAG (Qdrant Vector Database) y generar sintetizaciones
pedagógicas explicativas utilizando modelos del lenguaje (Gemini 2.5 Flash).

4.1.3

Definiciones, acrónimos y abreviaturas

 BJJ: Brazilian Jiu-Jitsu (Jiu-Jitsu Brasileño).
 PWA: Progressive Web App (Aplicación Web Progresiva).
 UP: Unified Process (Proceso Unificado).
 SRS / ERS: Especificación de Requisitos de Software (norma IEEE 830).
 Keypoint: Punto de referencia o nodo articular anatómico (hombro, codo, rodilla,
etc.).
 RAG: Retrieval-Augmented Generation (Generación Aumentada por Recuperación).
 LLM: Large Language Model (Gran Modelo de Lenguaje).
 Profesor: Rol del sistema (Instructor). Usuario experto que graba patrones y
administra conocimiento.
 Alumno: Rol del sistema (Practicante). Usuario que graba sus ejecuciones para
ser evaluado.

19

 Técnica Patrón: Matriz 3D canónica de la ejecución ideal, procesada y almacenada en base de datos.
 Consejo Pedagógico: Estructura JSONB de 4 claves generada por Gemini con
la retroalimentación técnica.
 JSONB: Tipo de dato nativo de PostgreSQL para almacenar documentos JSON
binarios.

4.1.4

Visión general del documento

El resto de este capı́tulo organiza la descripción general del producto, las caracterı́sticas
de los usuarios, las restricciones técnicas, la especificación detallada de los requisitos de
software/hardware, la identificación formal de los casos de uso y la especificación del
diagrama del modelo de dominio.

20

4.2

Descripción general

4.2.1

Perspectiva del producto

El sistema es una solución independiente de arquitectura desacoplada en 5 capas (Presentación, Aplicación, Servicios, Dominio e Infraestructura). Funciona como un ecosistema donde la interfaz PWA móvil se conecta mediante APIs REST con el servidor
backend FastAPI, delegando la inferencia de visión artificial a un cluster GPU en Google
Colab a través de un túnel seguro Ngrok.

4.2.2

Funciones del Producto

Las funciones principales que ofrece el software son:
1. Gestión de Técnicas Patrón (CU-01): Carga de videos de profesores, extracción de matriz esquelética (X, Y, Z) y registro de vectores de referencia.
2. Evaluación Biomecánica Autónoma (CU-02): Comparación cinemática del
alumno frente al patrón, cálculo de desviaciones angulares y generación del reporte pedagógico en 4 áreas (Análisis Postural, Riesgo de Lesión, Paso a Paso y
Resumen Ejecutivo).
3. Gestión de Catálogo y Usuarios (CU-03): Administración de profesores,
disciplinas y fuentes bibliográficas de BJJ.
4. Consulta de Historial y Progreso (CU-04): Visualización del registro de
evaluaciones pasadas del alumno.

4.2.3

Caracterı́sticas de los Usuarios

 Alumno (Usuario Final): Practicante de BJJ con nivel técnico principiante
o intermedio. Requiere una interfaz intuitiva en su teléfono móvil para grabar
ejecuciones y recibir explicaciones sencillas sin tecnicismos complejos. Rol en BD:
’alumno’.
 Profesor (Usuario Experto): Maestro encargado de grabar los videos patrones
de las técnicas, supervisar el catálogo e interpretar desajustes avanzados. Asume
todas las funciones de gestión interna. Rol en BD: ’profesor’.
 Administradora: Rol organizacional EXTERNO al software (inscripciones, cobros). No implementado como rol de sistema. Sus funciones de gestión de catálogo
son asumidas por el Profesor.

4.2.4

Restricciones

 Dependencia de conectividad a Internet para el envı́o de videos y recepción de
análisis.

21

 Requerimiento de aceleración por GPU (Google Colab) para la ejecución sincrónica
de YOLO26x-Pose y YOLO26x-Depth.
 Lı́mite de resolución y formato de video soportado (MP4/WebM hasta 1080p).

4.2.5

Suposiciones y Dependencias

 Se asume que el alumno graba el video con iluminación adecuada y encuadre
completo de su cuerpo.
 Dependencia de la disponibilidad del túnel Ngrok y la instancia activa de Google
Colab GPU para la inferencia de visión artificial.
 Dependencia de la API de Google Gemini para la generación de la sı́ntesis pedagógica.

4.2.6

Requisitos Futuros

 Soporte para análisis biomecánico en tiempo real vı́a streaming de video.
 Módulo de comparación multi-persona para entrenamientos de combate en vivo
(sparring).
 Integración con dispositivos vestibles (wearables) para medición de aceleración e
impacto.

22

4.3

Requisitos Especı́ficos

4.3.1

Interfaces Externas

4.3.1.1

Interfaces de Software

 Google Colab GPU / Ngrok Tunnel API: Interfaz HTTP REST para envı́o
de imágenes/fotogramas y recepción de mapas de pose 3D (X, Y, Z).
 Google Gemini API: API de modelos de lenguaje para sı́ntesis estructurada
bajo JSON Schema.
 Qdrant Vector DB API: Interfaz de búsqueda de vecinos más cercanos (HNSW)
sobre vectores de 2048d.
 PostgreSQL Database Driver: Conexión relacional SQL vı́a psycopg2 / SQLAlchemy.

4.3.1.2

Interfaces de Hardware

 Cámara del Dispositivo Móvil: Captura de video a 30 FPS o superior en
resolución mı́nima de 720p.
 Servidor GPU Cloud: Servidor con tarjeta gráfica NVIDIA (T4 o superior)
para inferencia de modelos en la nube.

4.3.2

Requisitos Funcionales

 RF-01 (Registro de Patrón): El sistema debe permitir al Profesor subir un
video de demostración técnica y extraer la matriz de articulaciones 3D mediante
YOLO26x.
 RF-02 (Cálculo de Desviación Angular): El sistema calcula la diferencia angular entre keypoints del alumno y el patrón usando CalculadoraBiomecanica (producto punto + arcocoseno con clamping numérico). Implementado en
src/domain/models.py.
 RF-03 (Búsqueda Semántica RAG): El sistema debe recuperar pasajes relevantes de manuales de BJJ almacenados en Qdrant (vector 2048d) usando Qwen3VL-Embedding.
 RF-04 (Sı́ntesis Pedagógica Structured JSON): Gemini 2.5 Flash genera
un reporte con 4 claves obligatorias. Forzado por prompt estricto en GeminiServiceAdapter.generar consejo(). Si el parseo falla, se usa fallback dict determinista.
 RF-05 (Almacenamiento Histórico): El diagnóstico se almacena en evaluaciones alumno.consejo pedagogico (JSONB con 4 claves obligatorias: analisis postural, riesgo lesion, paso a paso, resumen ejecutivo) usando psycopg2.extras.Json.
Implementado en PostgresHistorialRepository.guardar evaluacion().

23

4.3.3

Requisitos de Rendimiento

 RNF-01 (Tiempo de Respuesta): El análisis completo de un video (inferencia
YOLO, embedding Qwen, RAG Qdrant, generación Gemini) debe completarse en
menos de 15 segundos asumiendo túnel Ngrok estable.
 RNF-02 (Concurrencia): FastAPI mediante Uvicorn debe soportar 50 solicitudes ası́ncronas simultáneas, delegando carga de GPU a Colab o encolando
peticiones.

4.3.4

Restricciones de Diseño

 Arquitectura estricta en 5 capas bajo patrones GRASP y principios SOLID.
 Modelo de base de datos relacional normalizado en 3FN/BCNF.

4.3.5

Atributos del Sistema

 Usabilidad: Interfaz limpia sin tecnicismos complejos para el alumno.
 Mantenibilidad: Cobertura de pruebas unitarias e integración con pytest.
 Seguridad: Autenticación segura y protección de datos personales de los alumnos.

24

4.4

Identificación de los casos de uso

La Tabla 3 resume los casos de uso principales identificados en el sistema bajo la
metodologı́a del Proceso Unificado.
Código
CU-01
CU-02
CU-03
CU-04
CU-05

Nombre del Caso de Uso
Registrar Patrón de Técnica
Evaluar Ejecución Biomecánica con Sı́ntesis
Pedagógica
Gestionar Catálogo de Técnicas y Profesores
Consultar Historial de Evaluaciones y Progreso
Ingestar Literatura Técnica en Base de Datos
Vectorial

Actor Principal
Profesor
Alumno

Prioridad
Alta
Alta

Profesor
Alumno
Profesor

Media
Media
Baja

Tabla 3: Identificación de Casos de Uso del Sistema (Alineado con roles de BD)

25

4.5

Diagrama de dominio

El Modelo de Dominio ilustrado en la Figura 4 representa las entidades conceptuales
del negocio y sus relaciones fundamentales.
DIAGRAMA DEL MODELO DE DOMINIO DEL NEGOCIO
 Profesor (1) −→ (∗) TecnicaPatron: Registra patrones de movimiento
(CU-01).
 TecnicaPatron (1) −→ (1) MatrizEsqueletica: Estructura de dominio
con puntos 3D.
 Alumno (1) −→ (∗) EvaluacionAlumno: Realiza ejecuciones de
entrenamiento (CU-02).
 EvaluacionAlumno (∗) −→ (1) TecnicaPatron: Se compara contra el
patrón.
 EvaluacionAlumno (1) −→ (1) ConsejoPedagogico: Estructura
JSONB de 4 claves persistida en BD.
 FuenteConocimiento (∗) −→ (1) EvaluacionAlumno: Aporta chunks
recuperados vı́a Qdrant.

Figura 4: Representación Conceptual del Diagrama de Dominio del Sistema

26

4.6

Trazabilidad Arquitectónica (Casos de Uso vs.
Controladores)

La Tabla 4 mapea cada caso de uso definido en el modelo del sistema con el controlador FastAPI responsable de su orquestación y el módulo de persistencia/adaptador
involucrado.
CU
CU-01
CU-02
CU-03

Controlador
TecnicaController / RegistrarTecnicaController
EvaluacionController

CU-04

ProfesorController
TecnicaController
—

CU-05

FuenteController

+

Endpoint API
Repositorio
POST
PostgresTecnicaRepository
/api/v1/profesor/tecnicas
POST
PostgresHistorialRepository
/api/v1/alumno/evaluaciones
GET/POST/PUT/DELETE
PostgresProfesorRepository
/api/v1/profesor/profesores
GET
PostgresHistorialRepository
/api/v1/alumno/{id}/progreso
POST
PostgresFuenteConocimientoRepository
/api/v1/profesor/fuentes + QdrantAdapter

Tabla 4: Matriz de Trazabilidad: Casos de Uso a Implementación Arquitectónica

27

4.7

Limitaciones y Trabajo Futuro

La implementación actual presenta las siguientes limitaciones documentadas (Deuda
Técnica) que quedan fuera del alcance de este proyecto de grado, planteándose como
trabajo futuro:
 Autenticación mediante tokens JWT (actualmente la API asume sesión por ID).
 Soporte para análisis en streaming (WebSockets).
 Doble sistema de embeddings (Gemini 768d legacy + Qwen 2048d canónico). El
adaptador Gemini deberı́a removerse de IEmbeddingService.
 Manejo de concurrencia extrema en GPU (requiere balanceador de carga o colas
Redis/Celery para escalar).

28

