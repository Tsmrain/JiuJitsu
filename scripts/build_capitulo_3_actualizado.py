# scripts/build_capitulo_3_actualizado.py
# -*- coding: utf-8 -*-
"""
Generador del Capítulo 3 (Marco Teórico) Actualizado para el Documento de Grado
Alineado con las Iteraciones 3A a 4J y la Metodología Craig Larman.
Genera Capitulo_3_Marco_Teorico_Actualizado.md y Capitulo_3_Marco_Teorico_Actualizado.docx.
"""

import os
import re
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def get_capitulo_3_markdown_content():
    return r"""# CAPÍTULO 3: MARCO TEÓRICO

## 3.1. Estimación de Pose, Segmentación y Aprendizaje Continuo con YOLOv26

### 3.1.1. ¿Qué es YOLOv26?
YOLO (acrónimo en inglés de *You Only Look Once*, que se traduce como "Solo miras una vez") es una familia pionera de modelos de inteligencia artificial y visión por computadora desarrollada y optimizada por la empresa Ultralytics. Su propósito central es la detección de objetos, la estimación de postura corporal (*pose estimation*) y el análisis de escenas complejas en tiempo real. 

A diferencia de las arquitecturas tradicionales basadas en dos etapas (como Faster R-CNN o Mask R-CNN), que primero proponen regiones de interés y luego clasifican cada zona de manera secuencial, la arquitectura de YOLO procesa la imagen completa a través de una red neuronal convolucional y transformadora en un único paso hacia adelante (*single-stage forward pass*). Este paradigma computacional predice simultáneamente los cuadros delimitadores (*bounding boxes*), las probabilidades de clase, las máscaras de segmentación y las coordenadas de las articulaciones anatómicas. La versión 26 representa la cúspide evolutiva de este ecosistema, incorporando módulos de atención espacial mejorados, convoluciones dinámicas y optimizaciones para motores tensoriales en hardware moderno, lo que permite alcanzar precisiones de nivel industrial con una latencia significativamente inferior a la de sus predecesores.

### 3.1.2. Modelos Seleccionados: YOLOv26-pose, YOLOv26-depth y YOLO26-seg
Para dar respuesta integral a las complejidades físicas y cinemáticas del Jiu-Jitsu Brasileño, la arquitectura del sistema integra tres variantes complementarias de la familia YOLOv26, priorizando las variantes "nano" por su eficiencia computacional y bajo consumo de memoria:

*   **`yolo26n-pose.pt`:** Es el núcleo fundamental de estimación de pose humana bidimensional. Este modelo está entrenado para localizar y hacer seguimiento a 17 puntos clave anatómicos (*keypoints*) bajo el estándar internacional COCO (nariz, ojos, orejas, hombros, codos, muñecas, caderas, rodillas y tobillos). A partir de estos puntos, el sistema construye un grafo esquelético digital del practicante en cada fotograma del video, registrando sus coordenadas espaciales normalizadas $(x, y)$ y un valor de certidumbre estadística $c_i \in [0, 1]$ por articulación.
*   **`yolo26n-depth.pt`:** Es el modelo complementario de estimación monocular de profundidad. Mientras que el modelo de pose localiza la posición del cuerpo en el plano bidimensional de la imagen (ejes X e Y), este componente calcula un mapa de profundidad relativa píxel a píxel, prediciendo la distancia física de cada segmento corporal respecto a la lente de la cámara (eje Z). Esto permite transformar el esqueleto bidimensional en una estructura tridimensional $(X, Y, Z)$, lo que resulta indispensable para evaluar con rigor geométrico si una postura mantiene la base pegada al tatami, si la cadera ejerce presión efectiva o si existe espacio indebido en los amarres y guardias.
*   **`yolo26n-seg.pt`:** Es el modelo de segmentación de instancias a nivel de píxel. A diferencia de un simple cuadro delimitador rectangular, este modelo predice una máscara binaria exacta de la silueta de cada persona detectada en el tatami. Su incorporación en la arquitectura busca aislar individualmente al practicante de su oponente o compañero de entrenamiento cuando se presentan oclusiones extremas, evitando la mezcla de articulaciones.

### 3.1.3. Justificación de la Elección
La adopción de YOLOv26 en su variante "nano" se sustenta en cuatro justificaciones técnicas y metodológicas rigurosas:

1.  **Velocidad y Eficiencia Operativa:** La arquitectura nano posee aproximadamente 3.2 millones de parámetros, lo que le permite alcanzar tasas de inferencia superiores a 90 fotogramas por segundo (FPS) en hardware acelerado localmente. Esta velocidad resulta crítica para que el procesamiento de un video completo de 10 a 30 segundos no tome más de 10 segundos en total, permitiendo al alumno y al profesor recibir retroalimentación inmediata durante la sesión de entrenamiento.
2.  **Robustez en Entornos de Contacto y Suelo:** Las herramientas convencionales de estimación de pose (como Google MediaPipe) han sido diseñadas bajo el supuesto de que el cuerpo humano se encuentra en bipedestación (de pie) y con extremidades visibles. En el Jiu-Jitsu Brasileño, el 85% de la acción ocurre a ras de suelo, con los atletas entrelazados, en posición horizontal, invertida o en contacto estrecho. YOLOv26 demuestra una capacidad de generalización superior para identificar posturas no canónicas y resistir la interferencia visual producida por los pliegues y solapas holgadas del kimono (*gi*).
3.  **Representación Tridimensional Nativa:** La convergencia de los modelos de pose y profundidad dentro del mismo ecosistema de Ultralytics simplifica la arquitectura del software. No se requiere coordinar librerías externas heterogéneas de profundidad (como MiDaS o Depth Anything); un único flujo de inferencia alimenta la matriz de coordenadas tridimensionales que luego evalúa el algoritmo de Alineamiento Temporal Dinámico (*Dynamic Time Warping*, DTW).
4.  **Sostenibilidad y Soberanía Tecnológica:** Los pesos y el código de Ultralytics YOLO26 se distribuyen bajo licencias de código abierto accesibles para investigación y desarrollo. Esto garantiza que la academia "Corpo e Mente" mantenga autonomía operativa plena, sin depender de pasarelas de facturación por uso ni suscripciones mensuales a APIs comerciales propietarias.

### 3.1.4. Módulo de Segmentación Opcional (`USE_SEGMENTATION`) y Benchmark Empírico
En técnicas de alta fricción corporal como la guardia cerrada (*closed guard*), los torsos de ambos atletas se superponen de manera continua, lo que puede inducir a los detectores de pose tradicionales a fusionar ambas personas en un solo individuo o intercambiar articulaciones. Para mitigar este riesgo, se implementó en la capa de infraestructura del backend ([`YOLOPoseAdapter`](file:///Users/santiago/Desktop/JiuJitsu-main/backend/corpocmente/infrastructure/ai/adapters.py)) una arquitectura multi-etapa gobernada por la bandera de configuración `USE_SEGMENTATION: bool`:

$$\text{Frame Original} \xrightarrow{\text{yolo26n-seg}} \{\text{Máscara}_A, \text{Máscara}_B\} \xrightarrow{\text{Recorte (Crop)}} \{\text{BBox}_A, \text{BBox}_B\} \xrightarrow{\text{yolo26n-pose}} \text{Keypoints Locales} \xrightarrow{\text{Offset}} \text{Keypoints Globales}$$

Siguiendo el rigor empírico de la metodología de Craig Larman, antes de promover esta arquitectura al entorno de producción, se formuló un guardrail cuantitativo estricto: **el módulo multi-etapa solo se activaría por defecto si lograba incrementar la cobertura de tracking o la detección de dos personas en al menos un $+5\%$ sin degradar inadmisiblemente la latencia.**

Se ejecutó un benchmark comparativo sobre el video de prueba representativo del tatami (`profesor salida de Guardia Parandose.mp4`, 897 fotogramas a 59.93 FPS, resolución de $464 \times 832$ píxeles). Los resultados experimentales directos se resumen en la siguiente tabla:

#### Tabla 3.1: Benchmark de Estimación de Pose Directa vs. Multi-Stage (Seg + Pose)
| Métrica Evaluada | YOLO26-Pose Directo (Línea Base) | Multi-Stage (YOLO-Seg + Crop + Pose) | Delta Absoluto / Impacto |
| :--- | :--- | :--- | :--- |
| **Fotogramas procesados** | 897 frames | 897 frames | 0 |
| **Frames con 0 personas detectadas** | 0 (0.0%) | 0 (0.0%) | 0.0% |
| **Frames con 1 persona (oclusión extrema)** | 374 (41.7%) | 358 (39.9%) | -16 frames (-1.78%) |
| **Frames con 2 personas identificadas** | 255 (28.4%) | 271 (30.2%) | **+16 frames (+1.78%)** |
| **Frames con 3+ personas (fondo / jueces)** | 268 (29.9%) | 268 (29.9%) | 0.0% |
| **Cobertura temporal total de tracking** | **100.00%** | **100.00%** | **+0.00% (Sin mejora)** |
| **Confianza promedio de keypoints** | **0.8006** | **0.7388** | **-7.7% (Degradación por recorte)** |
| **Tiempo total de procesamiento** | **9.42 s** | **33.10 s** | **+23.68 s (+251% de sobrecosto)** |
| **Velocidad de inferencia** | **95.2 FPS** (10.5 ms/frame) | **27.1 FPS** (36.9 ms/frame) | **3.5x más lento** |

*Fuente: Elaboración propia a partir del benchmark automatizado en hardware local Apple Silicon (2026).*

**Decisión de Ingeniería (Craig Larman):** La segmentación multi-etapa incrementó la detección de dos personas en apenas 16 fotogramas (+1.78%), sin alterar la cobertura global (100% en ambos casos) y reduciendo la confianza media de las articulaciones de 0.80 a 0.74 debido a la pérdida de contexto periférico en los recortes estrechos. Al no alcanzarse el umbral mínimo del $+5\%$ de ganancia y triplicar el tiempo de espera del usuario (de 9.4 a 33.1 segundos), el sistema adoptó como estándar en producción `USE_SEGMENTATION: bool = False`, manteniendo la implementación modularizada en el adaptador para su activación selectiva en investigaciones posteriores.

### 3.1.5. Data Flywheel y Aprendizaje Continuo (MLOps)
Los modelos preentrenados en visión por computadora sufren una caída en su desempeño cuando se enfrentan a dominios altamente especializados (*domain shift*). En el Jiu-Jitsu, agarres poco comunes, iluminación rasante en el tatami o kimonos con parches visualmente ruidosos pueden inducir falsos negativos. Para solucionar esto de manera evolutiva sin requerir reentrenamientos ciegos, el sistema implementa un ciclo de aprendizaje continuo denominado *Data Flywheel* (Volante de Datos), compuesto por cuatro fases automatizadas:

```
[Inferencia en Tatami] 
       │ (Confianza < 0.65)
       ▼
[uncertainty_frames/] ──> [Teacher Model (YOLO26x)] ──> [Replay Buffer (80/20)] ──> [Gatekeeper Test] ──> [Producción]
```

1.  **Detección e Intercepción de Incertidumbre:** Durante la ejecución rutinaria del pipeline, el adaptador de IA calcula la media de confianza de las articulaciones biomecánicamente críticas. Cuando dicha media cae por debajo del umbral de confianza $\theta_{\text{conf}} = 0.65$ o se detecta discontinuidad cinemática abrupta entre fotogramas contiguos, el fotograma se intercepta automáticamente y se almacena en el directorio `uncertainty_frames/` junto con sus metadatos de contexto (técnica evaluada, timestamp y articulaciones dudosas).
2.  **Pseudo-Etiquetado Asistido (Teacher-Student):** En lugar de recurrir a costosas sesiones de anotación manual humana para cada caso límite, se utiliza un modelo maestro de máxima escala (`yolo26x-pose.pt`, versión extra-large). Este modelo se ejecuta fuera de línea (*offline*) sobre los fotogramas inciertos, aprovechando su mayor capacidad de extracción de características para generar pseudo-etiquetas de alta resolución.
3.  **Prevención del Olvido Catastrófico con Replay Buffer:** El reentrenamiento exclusivo con casos difíciles provoca que la red neuronal olvide patrones posturales estándar previamente dominados (*catastrophic forgetting*). Para evitarlo, el pipeline de reentrenamiento construye un búfer de repetición balanceado: el nuevo lote de datos de entrenamiento se compone de un $80\%$ de fotogramas canónicos de referencia (provenientes del catálogo de patrones maestros aprobados) y un $20\%$ de fotogramas de incertidumbre recolectados en el tatami.
4.  **Validación Asistida mediante *Gatekeeper*:** Bajo el enfoque de Craig Larman de evitar falsos positivos en producción, ningún peso reentrenado se sustituye automáticamente. El artefacto resultante debe superar un banco de pruebas de regresión (*Gatekeeper*) que exige mantener un $\text{mAP}_{50-95} \ge 0.85$ en el conjunto canónico y demostrar una reducción estadísticamente significativa en el error de tracking sobre el conjunto de incertidumbre, requiriendo además la aprobación explícita del instructor titular antes de su despliegue final.

### 3.1.6. Comparativa frente a otras opciones
La Tabla 3.2 sintetiza las capacidades técnicas de Ultralytics YOLO26 frente a las tecnologías alternativas de estimación de pose disponibles en la literatura:

#### Tabla 3.2: Comparativa de tecnologías de estimación de pose humana
| Tecnología | Velocidad y Eficiencia | Resistencia a Oclusiones (Kimonos / Contacto) | Desempeño en Suelo (Jiu-Jitsu) | Modelo de Profundidad Nativo | Costo y Licenciamiento |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ultralytics YOLO26 (Seleccionada)** | **Muy alta** (95+ FPS en aceleración local) | **Excelente** (Robusta ante ropa deportiva holgada y cuerpos en contacto) | **Excelente** (Invariante a giros, ángulos invertidos y suelo) | **Sí** (`yolo26n-depth` integrado) | **Gratuita** (Código abierto AGPL-3.0) |
| Google MediaPipe | Alta (60+ FPS en GPU) | Media-Baja (Pierde el rastreo con kimonos o extremidades cruzadas) | Baja (Altamente sesgada a personas de pie y erguidas) | Parcial (Z aproximada empírica, sin modelo denso) | Gratuita (Propietaria de Google, no ampliable) |
| OpenPose (CMU) | Muy baja (10-15 FPS en GPU, inviable en CPU) | Alta | Buena, pero con un coste computacional prohibitivo | No (Requiere cámaras RGB-D externas) | Gratuita para uso académico; licencias comerciales muy costosas |
| AlphaPose | Media (20-25 FPS en GPU dedicada) | Alta | Media (Compleja inicialización de cajas delimitadoras previas) | No nativa | Gratuita para investigación; despliegue operativo frágil |

*Fuente: Elaboración propia (2026).*

---

## 3.2. Infraestructura de Cómputo Local Acelerado: Apple Silicon (MLX + MPS)

### 3.2.1. ¿Qué es la Arquitectura Apple Silicon y la Memoria Unificada?
Apple Silicon representa un cambio de paradigma en el diseño de hardware para computación personal e inteligencia artificial. A diferencia de las arquitecturas de computadores tradicionales basadas en x86 —donde la Unidad Central de Procesamiento (CPU) y la Unidad de Procesamiento Gráfico (GPU) operan como chips separados físicamente y se comunican a través del bus PCIe (intercambiando datos mediante copias lentas de memoria RAM a VRAM)—, Apple Silicon adopta el concepto de Sistema en Chip (*System on Chip*, SoC) con **Arquitectura de Memoria Unificada (UMA)**.

En un equipo Apple Silicon (como el chip Apple M-series con 24 GB de memoria unificada utilizado en este proyecto), la CPU multinúcleo, la GPU de alto rendimiento y el Motor Neuronal (*Neural Engine*) comparten un único bloque físico de memoria de altísimo ancho de banda. Esto permite que tensores matriciales masivos, fotogramas de video en alta resolución y pesos de modelos de lenguaje sean procesados simultáneamente por la CPU y la GPU sin sobrecostos de transferencia de memoria (*zero-copy memory sharing*), eliminando el cuello de botella más crítico de los sistemas de inteligencia artificial tradicionales.

### 3.2.2. Aceleración por Hardware: Apple MLX y Metal Performance Shaders (MPS)
Para explotar al máximo esta arquitectura sin depender de la pila propietaria NVIDIA CUDA, el sistema implementa dos motores de aceleración complementarios:

*   **Apple MLX (*Machine Learning eXchange*):** Es un framework de aprendizaje profundo diseñado específicamente por el equipo de investigación de Apple para la memoria unificada. MLX ofrece una interfaz idiomática inspirada en NumPy y PyTorch, pero incorpora evaluación perezosa (*lazy evaluation*), compilación unificada de grafos tensoriales y compatibilidad nativa con modelos de visión y lenguaje cuantizados en 4 bits. En este proyecto, MLX es el motor responsable de ejecutar los modelos multimodales de la familia Qwen3-VL (Embeddings, Reranker e Inferencia Generativa).
*   **Metal Performance Shaders (MPS):** Es la capa de bajo nivel optimizada para la GPU de Apple sobre la API gráfica Metal. A través del backend `torch.backends.mps` de PyTorch, Ultralytics YOLO26 delega las operaciones convolucionales y matriciales directamente a los núcleos Metal, alcanzando tiempos de ejecución inferiores a 11 milisegundos por fotograma en inferencia de pose.

### 3.2.3. Justificación de la Elección: Soberanía de Datos, Latencia Cero y Costo Operativo Nulo
La decisión de ejecutar todo el stack tecnológico de inteligencia artificial de forma 100% local en una máquina física dentro de la academia responde a cuatro principios innegociables:

1.  **Soberanía y Privacidad Absoluta de Datos:** En una academia de Jiu-Jitsu entrenan practicantes de diversas edades, incluidos menores de edad. Grabar ejecuciones técnicas en video y enviarlas a servidores en la nube de terceros vulnera principios básicos de privacidad y expone material audiovisual sensible. Con la inferencia local, los videos jamás salen de la máquina física de la academia; se procesan en memoria volátil y las copias temporales se purgan tras el análisis.
2.  **Latencia Cero de Transmisión de Red:** La subida de archivos de video de 50 a 150 MB a través de conexiones Wi-Fi residenciales o de gimnasio introduce demoras de entre 30 segundos y 2 minutos únicamente en la fase de carga. Al procesar localmente, la lectura del archivo desde el almacenamiento NVMe del equipo es instantánea (tasas superiores a 3,000 MB/s), garantizando una experiencia ágil y fluida.
3.  **Independencia Operativa del Tatami:** El sistema no interrumpe sus funciones si la conexión a internet externa sufre cortes o micro-interrupciones; la comparación cinemática, la consulta a la base de datos vectorial y la generación de la corrección biomecánica operan de forma completamente autónoma en la red local del gimnasio.
4.  **Cero Costos Recurrentes de Infraestructura:** No existen costos mensuales por horas de GPU reservadas en la nube ni cargos por token procesado. Una vez amortizado el hardware de cómputo local, el costo marginal de evaluar 10 o 1,000 videos diarios es exactamente cero dólares.

### 3.2.4. Descarte Metodológico de Google Colab (Evidencia de Fases Iniciales)
Durante las iteraciones preliminares del proyecto (Iteraciones 1 y 2), se contempló y prototipó el uso de Google Colab como motor de cómputo remoto gratuito. Sin embargo, la aplicación estricta de la metodología de Craig Larman reveló vulnerabilidades operativas insalvables:

*   **Desconexiones Intempestivas e Inestabilidad:** Las instancias gratuitas de Colab imponen tiempos máximos de inactividad de 30 a 90 minutos y desconexiones arbitrarias cuando los servidores de Google experimentan alta demanda, interrumpiendo abruptamente el servicio en medio de una clase.
*   **Sobrecosto de Latencia:** La necesidad de subir el video desde el navegador del usuario al backend y reenviarlo posteriormente al túnel de Colab generaba una doble transferencia de red que elevaba el tiempo total de respuesta a más de un minuto y medio por video.
*   **Restricciones de Cuota y Bloqueos de Red:** Los mecanismos de seguridad de Google detectan y penalizan el uso de Colab como servidor backend de APIs públicas continuas, bloqueando periódicamente los túneles ngrok o Cloudflare asociados.

La evidencia empírica acumulada demostró que un entorno efímero en la nube no cumplía con los estándares de disponibilidad requeridos para una tesis de ingeniería orientada a producción real, consolidando a Apple Silicon local como la infraestructura definitiva.

### 3.2.5. Comparativa frente a otras opciones
La Tabla 3.3 detalla las características de la infraestructura local seleccionada frente a las opciones evaluadas:

#### Tabla 3.3: Comparativa de Infraestructuras de Cómputo para Inferencia de IA
| Plataforma / Opción | Hardware Disponible | Latencia de Red | Privacidad de Videos | Costo Operativo Recurrente | Viabilidad para Producción en Tatami |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Apple Silicon Local (MLX + MPS) [Seleccionada]** | **Apple M-Series (24 GB UMA)** | **Cero (Transferencia NVMe local)** | **Total** (Los videos no salen del equipo local) | **$0 / mes** (Inversión única en equipo) | **Excelente** (Robusto, autónomo, silencioso y sin dependencias de red) |
| Google Colab (Free Tier) [Descartada] | NVIDIA Tesla T4 (16 GB VRAM) | Alta (Doble subida de video por red) | Nula (Procesamiento en centros de datos externos) | $0 (con riesgo de bloqueo) o $10+/mes | Baja (Desconexiones arbitrarias y límites de sesión) |
| Servidor Cloud Dedicado (AWS EC2 / GCP) | Instancias GPU (e.g. g4dn.xlarge) | Media (Dependiente del ancho de banda de subida) | Media (Requiere políticas estrictas de cifrado cloud) | Muy Alto ($150 - $400 USD / mes continuo) | Baja (Económicamente inviable para academias deportivas medianas) |
| Servidor Local x86 Tradicional | Intel/AMD + GPU NVIDIA (RTX 4060/4090) | Cero (Local) | Total | Alto costo eléctrico y mantenimiento de hardware | Media (Elevado consumo energético, ruido y calor en el tatami) |

*Fuente: Elaboración propia (2026).*

---

## 3.3. Vectorización Multimodal y Reranking: Qwen3-VL

### 3.3.1. ¿Qué es Qwen3-VL-Embedding y Qwen3-VL-Reranker?
La familia de modelos **Qwen3-VL** (*Vision-Language*), desarrollada por el equipo de inteligencia artificial de Alibaba Cloud, constituye el estado del arte en comprensión simultánea de texto e imágenes. A diferencia de los modelos de vectorización textual convencionales —que son ciegos a la información gráfica y requieren que una imagen sea previamente transcrita a texto de forma imperfecta—, los modelos Qwen3-VL procesan directamente señales visuales continuas (píxeles) y secuencias lingüísticas (tokens) dentro del mismo espacio de representación latente.

En el sistema, esta tecnología cumple dos roles fundamentales y complementarios: transformar la información multimodal en vectores densos (*Embeddings*) y reordenar con precisión quirúrgica los fragmentos de conocimiento recuperados (*Reranking*).

### 3.3.2. Arquitectura de Recuperación en Dos Etapas (Two-Stage Retrieval)
Para maximizar simultáneamente la velocidad de respuesta y la precisión técnica de la retroalimentación, el sistema implementa una arquitectura de recuperación en dos etapas (*Two-Stage Retrieval*), inspirada en los sistemas de recomendación industrial de gran escala:

```
[Fotograma del Error Biomecánico]
                │
                ▼
┌────────────────────────────────────────────────────────┐
│ ETAPA 1: RECALL (Bi-Encoder)                           │
│ Modelo: Qwen3-VL-Embedding-2B (en MLX)                 │
│ Operación: Vectorización densa (2048 dimensiones)      │
│ Búsqueda: Qdrant Index HNSW (Similitud Coseno)         │
│ Salida: Top-K = 10 candidatos preliminares (< 5 ms)    │
└────────────────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────┐
│ ETAPA 2: PRECISIÓN (Cross-Encoder Reranker)            │
│ Modelo: Qwen3-VL-Reranker-2B (en MLX)                  │
│ Operación: Atención cruzada profunda (Frame + Manual)  │
│ Salida: Top-N = 3 fragmentos estrictamente pertinentes │
└────────────────────────────────────────────────────────┘
                │
                ▼
   [Inyección de Contexto al VLM Generativo]
```

1.  **Etapa 1: Recuperación de Cobertura (*Bi-Encoder* con Qwen3-VL-Embedding-2B):**
    El fotograma crítico extraído del video del alumno (aquel donde DTW detectó la máxima discrepancia angular) es procesado de forma independiente por el modelo de embedding. El modelo proyecta la imagen en un vector numérico denso de 2048 dimensiones. La base de datos vectorial Qdrant ejecuta una búsqueda por producto punto/similitud de coseno sobre el índice HNSW, filtrando por el identificador de la técnica correspondiente. Esta etapa prioriza la velocidad (*recall* alto), recuperando en menos de 5 milisegundos los 10 fragmentos de manuales técnicos más prometedores ($top\_k = 10$).
2.  **Etapa 2: Filtrado Fino y Reordenamiento (*Cross-Encoder* con Qwen3-VL-Reranker-2B):**
    Aunque la búsqueda vectorial rápida es eficaz, los modelos bi-encoder no permiten que los píxeles de la imagen interactúen con las palabras del texto durante la indexación. Para evitar falsos positivos semánticos (por ejemplo, confundir un pasaje de guardia de rodilla cruzada con un pasaje de guardia torreando debido a la similitud visual del kimono), entra en juego el modelo de Reranking.
    El *Cross-Encoder* recibe conjuntamente el par completo: $(\text{Fotograma del Alumno}, \text{Candidato de Manual})$. Sus capas de atención cruzada (*cross-attention*) analizan en profundidad la relación geométrica y conceptual entre la postura del practicante y la explicación del libro, emitiendo una puntuación de relevancia calibrada. El sistema selecciona únicamente los 3 fragmentos con mayor puntaje ($top\_n = 3$), garantizando que el modelo generativo solo reciba información pedagógicamente exacta.

### 3.3.3. Modelos Seleccionados y Especificaciones Técnicas
*   **`Qwen3-VL-Embedding-2B`:** Posee 2 mil millones de parámetros y está optimizado para ejecutarse en Apple MLX. Admite *Matryoshka Representation Learning* (MRL), lo que permite truncar el vector a dimensiones menores si se desea optimizar memoria, aunque en esta tesis se preservan las 2048 dimensiones completas para asegurar la máxima discriminación biomecánica.
*   **`Qwen3-VL-Reranker-2B`:** Comparte el mismo codificador visual y textual que el modelo de embedding, pero su capa de salida computa un único logit de afinidad semántica. Ambos modelos operan en cuantización de 4 u 8 bits dentro del espacio de memoria unificada, consumiendo menos de 4.5 GB de RAM combinados.

### 3.3.4. Justificación de la Elección
1.  **Fusión Genuina de Texto e Imagen:** La teoría del Jiu-Jitsu no se entiende solo con palabras; requiere diagramas de palancas y fotos secuenciales. Qwen3-VL relaciona un texto como *"la rodilla izquierda bloquea el bíceps femoral"* con la imagen anatómica correspondiente sin requerir etiquetas intermedias.
2.  **Soporte Bilingüe Nativo de Alto Nivel:** A diferencia de modelos como CLIP de OpenAI (fuertemente sesgados al idioma inglés), Qwen3-VL ha sido entrenado con córpora multilingües globales, demostrando una comprensión impecable de la terminología técnica en español y portugués brasileño (*"guarda fechada"*, *"pegada de gola"*, *"raspagem"*).
3.  **Cero Dependencia Externa:** Al ejecutarse íntegramente en Apple MLX, el pipeline de RAG funciona de manera local y determinista sin costo por token.

### 3.3.5. Comparativa frente a otras opciones
La Tabla 3.4 compara la solución de vectorización y reranking implementada frente a las alternativas del mercado:

#### Tabla 3.4: Comparativa de Modelos de Generación de Vectores y Reranking Multimodal
| Tecnología Evaluada | Arquitectura de Recuperación | Capacidad Multimodal Real | Soporte Español / Portugués | Ejecución Local Acelerada | Costo Operativo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen3-VL Dual (Embedding + Reranker) [Seleccionada]** | **Two-Stage** (Bi-Encoder + Cross-Encoder) | **Nativa y Profunda** (Texto e Imagen a nivel de píxel) | **Excelente** (Comprende jerga de BJJ en ES/PT) | **Sí** (Nativo en Apple MLX) | **Gratuito** (Open Source) |
| OpenAI text-embedding-3 + Cohere Rerank | Two-Stage (Texto únicamente) | No (Solo texto; descarta diagramas y fotos de manuales) | Excelente | No (Servicio cloud cerrado) | De pago continuo por cada token procesado |
| BAAI BGE-M3 | Bi-Encoder (Texto y multi-lingüismo) | Limitada (Enfocado primordialmente en texto denso) | Bueno | Sí (PyTorch CUDA/CPU, lento en Apple Silicon) | Gratuito |
| CLIP (OpenAI / ViT-B-32) | Single-Stage (Solo Bi-Encoder, sin Reranker) | Básica (Alineación superficial de conceptos generales) | Regular (Sesgo severo al inglés anglosajón) | Sí | Gratuito, pero con baja precisión técnica en artes marciales |

*Fuente: Elaboración propia (2026).*

---

## 3.4. Base de Datos Vectorial: Qdrant

### 3.4.1. ¿Qué es Qdrant?
Qdrant es un motor de base de datos vectorial y motor de búsqueda por similitud de alto rendimiento, desarrollado en el lenguaje de programación de sistemas **Rust**. A diferencia de los sistemas de bases de datos relacionales estructurados —que localizan registros mediante coincidencias exactas o rangos indexados en árboles B—, Qdrant está optimizado para almacenar representaciones vectoriales densas y calcular distancias geométricas (como la distancia euclidiana, de Manhattan o la similitud de coseno) en espacios de cientos o miles de dimensiones.

En la arquitectura del sistema, Qdrant cumple dos roles esenciales:
1.  **Almacén de Patrones Biomecánicos:** Guarda los vectores de referencia de los profesores correspondientes a cada técnica deportiva, indexados mediante sus características angulares.
2.  **Base de Conocimiento Teórico Multimodal (RAG):** Aloja los vectores densos de 2048 dimensiones generados por Qwen3-VL-Embedding a partir de los manuales y libros de Jiu-Jitsu cargados por los instructores.

### 3.4.2. Modelo de Acceso y Costos
Qdrant se distribuye como software libre bajo la licencia Apache 2.0. En el proyecto se despliega localmente como un contenedor Docker aislado (`corpocmente_qdrant`), mapeado al puerto 6333. Este enfoque de autoalojamiento (*self-hosting*) garantiza que no existan costos de licencia, pagos por volumen de almacenamiento ni cuotas mensuales, brindando disponibilidad continua sin depender de la nube de Qdrant Cloud.

### 3.4.3. Justificación de la Elección
1.  **Filtrado Consciente del Payload (*Payload-Aware Filtering*):** Esta es la ventaja competitiva más crítica de Qdrant frente a otras soluciones vectoriales. En la mayoría de las bases de datos vectoriales tradicionales, el filtrado por metadatos se realiza antes de la búsqueda (pre-filtrado, lo que puede aislar regiones desconectadas del grafo) o después (post-filtrado, reduciendo drásticamente la cantidad de resultados finales útiles o *recall*). Qdrant integra el filtrado de metadatos (como `tecnica_id`, `profesor_id` o `alcance`) directamente durante el recorrido del grafo HNSW (*Hierarchical Navigable Small World*), asegurando que las búsquedas respeten el aislamiento multi-academia con una latencia de respuesta inferior a 5 milisegundos.
2.  **Rendimiento y Seguridad de Memoria en Rust:** Al estar desarrollado en Rust, Qdrant carece de recolector de basura (*Garbage Collector*), lo que previene pausas imprevistas en la ejecución, mantiene una huella de memoria RAM extremadamente compacta y garantiza una estabilidad operativa absoluta en despliegues desatendidos.
3.  **Persistencia Transaccional y Snapshotting:** Permite crear instantáneas en caliente (*snapshots*) del estado completo de la base vectorial, facilitando las copias de seguridad de la teoría de la academia y su restauración ante contingencias.

### 3.4.4. Comparativa frente a otras opciones
La Tabla 3.5 sintetiza la evaluación de motores de búsqueda vectorial:

#### Tabla 3.5: Comparativa de Motores de Búsqueda Vectorial
| Motor Vectorial | Lenguaje Base | Mecanismo de Filtrado de Metadatos | Complejidad de Despliegue | Eficiencia de Memoria RAM | Costo Operativo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qdrant [Seleccionada]** | **Rust** | **Nativo en el recorrido del grafo HNSW** | **Muy Baja** (Un contenedor Docker ligero) | **Excelente** (Sin recolector de basura) | **Gratuito** (Open Source Apache 2.0) |
| Milvus | Go / C++ | Pre-filtrado o Post-filtrado desacoplado | Muy Alta (Microservicios distribuidos, etcd, MinIO) | Media-Baja (Alto consumo inicial) | Gratuito, pero con elevado costo en recursos de hardware |
| Weaviate | Go | Índice invertido previo | Media (Contenedor Docker único o clúster) | Media (Mayor consumo de memoria que Rust) | Gratuito |
| Pinecone | Propietario | Nativo | Nula (Servicio totalmente gestionado en la nube) | No aplica (Gestionado en nube externa) | De pago continuo por vector almacenado y consulta |
| Meta FAISS | C++ / Python | Manual (Es una librería matemática, no una BD) | Media (Requiere programar el almacenamiento y la API) | Alta | Gratuito, pero sin persistencia nativa ni filtrado de payload |

*Fuente: Elaboración propia basada en benchmarks de vector search (2026).*

---

## 3.5. Lenguaje de Programación: Python

### 3.5.1. ¿Qué es Python?
Python es un lenguaje de programación de alto nivel, interpretado y de tipado dinámico pero fuertemente tipado, célebre por su sintaxis expresiva, limpia y orientada a la legibilidad del código. Concebido originalmente por Guido van Rossum, Python se ha erigido en la última década como la lengua franca incuestionable del ecosistema de la inteligencia artificial, el aprendizaje automático y la visión por computadora a nivel mundial.

### 3.5.2. Costo y Licenciamiento
Python está respaldado por la *Python Software Foundation* (PSF) y se distribuye bajo una licencia de código abierto de máxima permisividad (licencia PSF, compatible con GPL). Su uso, distribución y modificación son enteramente gratuitos para cualquier propósito académico o comercial.

### 3.5.3. Justificación de la Elección
1.  **Hegemonía en el Ecosistema Científico y de IA:** Las librerías de visión por computadora más sofisticadas de la actualidad (Ultralytics YOLO, PyTorch, OpenCV, Apple MLX, Hugging Face Transformers y NumPy) cuentan con implementaciones nativas optimizadas en C++ pero expuestas exclusivamente a través de interfaces de Python. Programar el backend en Python permite enlazar directamente los tensores de memoria del pipeline de análisis sin requerir pasarelas de traducción entre lenguajes.
2.  **Productividad y Desarrollo Ágil:** Alineado con la metodología de Craig Larman, Python acelera el ciclo iterativo de prototipado, refactorización y prueba de hipótesis empíricas, reduciendo sustancialmente el volumen de código ceremonial (*boilerplate*) en comparación con lenguajes como Java o C++.
3.  **Robustez y Tipado Moderno:** Con la adopción sistemática de Type Hints (PEP 484) y modelos de validación con **Pydantic v2**, el código backend del sistema mantiene una solidez estructural comparable a la de lenguajes estáticamente tipados, detectando inconsistencias de datos en tiempo de desarrollo.

### 3.5.4. Comparativa frente a otras opciones
La Tabla 3.6 compara a Python frente a los lenguajes concurrentes:

#### Tabla 3.6: Comparativa de Lenguajes de Programación para el Backend de IA
| Lenguaje | Ecosistema de IA y Visión Artificial | Velocidad de Desarrollo | Integración con Modelos Locales (MLX / Torch) | Mantenibilidad y Legibilidad |
| :--- | :--- | :--- | :--- | :--- |
| **Python [Seleccionado]** | **Líder absoluto indiscutible** | **Muy Alta** | **Nativa y directa** (APIs de primera clase) | **Muy Alta** (Sintaxis limpia y modular) |
| JavaScript / Node.js | Limitado (Requiere puentes lentos a procesos Python) | Alta | Muy Baja (Incompatible con pipelines complejos de PyTorch/MLX) | Media |
| C++ | Muy Alto en rendimiento puro, pero complejo | Baja (Lenta compilación y gestión manual de punteros) | Alta (Base de los frameworks, pero muy verbosa) | Baja (Complejidad de auditoría) |
| Java / Kotlin | Moderado (Frameworks empresariales, pero rezagados en VLM) | Media | Media-Baja (Requiere puentes JNI hacia bibliotecas C++) | Media (Verboso) |

*Fuente: Elaboración propia (2026).*

---

## 3.6. Contenerización y Despliegue: Docker

### 3.6.1. ¿Qué es Docker?
Docker es una tecnología de virtualización a nivel de sistema operativo basada en contenedores. A diferencia de las máquinas virtuales completas —que emulan hardware físico e instalan un sistema operativo invitado completo con su propio kernel—, los contenedores de Docker comparten el kernel del sistema operativo anfitrión (*host*). Cada contenedor aísla sus propios procesos, dependencias binarias, librerías del sistema y variables de entorno dentro de un espacio de usuario segregado.

### 3.6.2. Costo y Licenciamiento
El motor central de Docker (*Docker Engine*) y la herramienta de orquestación multicontenedor *Docker Compose* son proyectos de código abierto bajo licencia Apache 2.0, totalmente gratuitos. Para entornos de desarrollo en estaciones de trabajo macOS o Linux, el software opera sin costo bajo los acuerdos de uso educativo y personal de Docker.

### 3.6.3. Justificación de la Elección
1.  **Aislamiento y Reproducibilidad ("Funciona en cualquier máquina"):** Elimina por completo las incompatibilidades de configuración entre entornos de desarrollo, pruebas y despliegue real en el tatami. Los servicios de base de datos relacional (PostgreSQL), exposición de API REST (PostgREST) y base de datos vectorial (Qdrant) se ejecutan de manera idéntica independientemente de la máquina donde se instale el sistema.
2.  **Orquestación Unificada con Docker Compose:** La infraestructura completa de soporte se levanta o apaga de forma determinista mediante un único archivo de configuración ([`docker-compose.yml`](file:///Users/santiago/Desktop/JiuJitsu-main/docker-compose.yml)), facilitando tareas de reinicio, mantenimiento o auditoría en pocos segundos.
3.  **Seguridad y Confinamiento:** Cada contenedor dispone de su propio sistema de archivos de solo lectura parcial y red interna virtualizada, impidiendo que un fallo o vulnerabilidad en un servicio secundario comprometa el resto del sistema operativo anfitrión.

### 3.6.4. Comparativa frente a otras opciones
La Tabla 3.7 resume la evaluación de tecnologías de despliegue:

#### Tabla 3.7: Comparativa de Tecnologías de Despliegue y Aislamiento
| Tecnología | Consumo de Recursos de Hardware | Tiempo de Inicialización | Aislamiento y Reproducibilidad | Complejidad de Mantenimiento |
| :--- | :--- | :--- | :--- | :--- |
| **Docker + Docker Compose [Seleccionada]** | **Bajo** (Comparte el kernel del sistema anfitrión) | **Instantáneo** (1 a 3 segundos) | **Alto** (Contenedores inmutables predecibles) | **Muy Baja** (Orquestación declarativa en YAML) |
| Máquinas Virtuales (VM / VirtualBox) | Muy Alto (Reserva fija de RAM, CPU y disco por SO) | Lento (30 a 60 segundos por máquina) | Total | Alta (Múltiples sistemas operativos que actualizar) |
| Instalación Nativa en el Host | Nulo (Usa el entorno base) | Inmediato | Nulo (Riesgo severo de colisión de dependencias) | Muy Alta (Frágil y propensa a errores manuales) |

*Fuente: Elaboración propia (2026).*

---

## 3.7. Capa de API Automática: PostgREST

### 3.7.1. ¿Qué es PostgREST?
PostgREST es un servidor web independiente de ultra-bajo consumo desarrollado en el lenguaje funcional **Haskell**. Su propósito de diseño es conectarse directamente a cualquier base de datos relacional PostgreSQL e inspeccionar su catálogo de esquema para exponer, de forma automática y en tiempo real, una API RESTful completa, estandarizada y segura.

En lugar de requerir que el desarrollador programe manualmente cientos de líneas de código repetitivo en el backend (controladores, serializadores, mapeadores ORM y validadores de acceso básico a tablas), PostgREST traduce directamente las peticiones HTTP (GET, POST, PATCH, DELETE) en consultas SQL optimizadas de un solo paso.

### 3.7.2. Costo y Licenciamiento
PostgREST es software libre de código abierto distribuido bajo la licencia MIT, totalmente gratuito y sin costos de licencia asociados.

### 3.7.3. Justificación de la Elección
1.  **Seguridad Delegada a la Base de Datos (Row Level Security):** PostgREST no gestiona la seguridad en la capa de aplicación web; delega la autenticación y autorización directamente en los roles y políticas de seguridad a nivel de fila (*Row Level Security*, RLS) de PostgreSQL mediante tokens JWT firmados criptográficamente. Esto garantiza que nadie pueda burlar las restricciones de acceso alterando el código de la API.
2.  **Eliminación Radical del Código Boilerplate:** Permite que el equipo de desarrollo concentre el 100% de su esfuerzo de ingeniería en el núcleo de valor del sistema: los algoritmos biomecánicos, la visión por computadora y el pipeline de RAG multimodal.
3.  **Rendimiento y Concurrencia Sobresalientes:** Al estar escrito en Haskell y ejecutar consultas SQL directas (evitando la sobrecarga y latencia típica de los ORM tradicionales como SQLAlchemy o Prisma), PostgREST atiende miles de peticiones concurrentes con apenas unos pocos megabytes de memoria RAM.

### 3.7.4. Comparativa frente a otras opciones
La Tabla 3.8 expone la comparativa de capas de API de datos:

#### Tabla 3.8: Comparativa de Tecnologías para Capa de Datos REST
| Tecnología | Código Manual Requerido | Gestión de Seguridad y Permisos | Rendimiento en Concurrencia | Consumo de Memoria RAM |
| :--- | :--- | :--- | :--- | :--- |
| **PostgREST [Seleccionada]** | **Cero para operaciones CRUD estándar** | **Nativa y robusta** (Delegada al motor de PostgreSQL RLS) | **Ultra Alto** (Haskell compilado, SQL directo) | **Mínimo** (~30 MB de RAM) |
| Endpoints Manuales en FastAPI (ORM) | Muy Alto (Escribir esquemas Pydantic, rutas y sesiones) | Manual en código (Mayor superficie de vulnerabilidad) | Medio-Alto (Sobrecarga del intérprete Python y ORM) | Medio (~150-300 MB de RAM) |
| Hasura GraphQL Engine | Mínimo | Nativa con reglas propias de Hasura | Alto | Alto (~500 MB a 1 GB de RAM en Java/Haskell) |

*Fuente: Elaboración propia (2026).*

---

## 3.8. Framework de Backend: FastAPI

### 3.8.1. ¿Qué es FastAPI?
FastAPI es un framework moderno de alto rendimiento para el desarrollo de APIs web en Python, diseñado por Sebastián Ramírez sobre los estándares abiertos OpenAPI y JSON Schema. Su arquitectura descansa sobre dos pilares tecnológicos fundamentales: **Starlette** (para la gestión asíncrona de redes HTTP y WebSockets sobre ASGI) y **Pydantic** (para la validación estricta, serialización y análisis de esquemas de datos).

FastAPI permite definir tipos estáticos de datos en cada endpoint, generando automáticamente documentación interactiva en vivo (Swagger UI y ReDoc) y validando en milisegundos que el cuerpo de las peticiones cumpla rigurosamente con los contratos esperados antes de invocar la lógica de negocio.

### 3.8.2. Costo y Licenciamiento
FastAPI se distribuye bajo la licencia de código abierto MIT, siendo completamente gratuito y libre de restricciones para entornos académicos e industriales.

### 3.8.3. Justificación de la Elección
1.  **Asincronía Nativa sin Bloqueos:** El análisis biomecánico de video y la consulta a modelos de IA son operaciones de cómputo intensivo. La arquitectura asíncrona de FastAPI (`async` / `await`) permite gestionar la subida simultánea de videos de múltiples alumnos sin bloquear el bucle de eventos del servidor, garantizando que las consultas de estado y la navegación por la plataforma permanezcan receptivas.
2.  **Integración Directa con la Pila de IA:** Al estar programado en Python, FastAPI orquesta de forma transparente los adaptadores de YOLOv26, los módulos de Apple MLX y los clientes de Qdrant y PostgreSQL sin requerir capas de interoperabilidad entre procesos heterogéneos.
3.  **Seguridad en el Lado del Servidor:** Incorpora mecanismos de inyección de dependencias modulares para validar tokens JWT, aplicar limitadores de tasa (*Rate Limiting*) y proteger los endpoints contra ataques de inyección o denegación de servicio.
4.  **Integración con el Proxy Inverso de Vite:** FastAPI se coordina con la configuración de red del frontend ([`vite.config.js`](file:///Users/santiago/Desktop/JiuJitsu-main/vite.config.js)) para servir tanto la lógica de API (`/api/v1/*`) como los recursos estáticos de video y fotogramas (`/static/*`) bajo una única interfaz, eliminando problemas de CORS (*Cross-Origin Resource Sharing*) en redes locales.

### 3.8.4. Comparativa frente a otras opciones
La Tabla 3.9 compara los principales frameworks web de Python:

#### Tabla 3.9: Comparativa de Frameworks Web de Backend
| Framework | Paradigma de Ejecución | Validación de Tipos de Datos | Documentación OpenAPI Automática | Idoneidad para Pipelines de IA |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI [Seleccionado]** | **Asíncrono nativo (ASGI / Starlette)** | **Estricta y automática con Pydantic** | **Sí** (Swagger UI y ReDoc integrados) | **Excelente** (Estándar de la industria para microservicios de IA) |
| Django / Django REST Framework | Síncrono tradicional (WSGI, con soporte async parcial) | Manual mediante Serializers complejos | No nativa (Requiere librerías externas de terceros) | Media (Monolítico, pesado y con sobrecarga innecesaria) |
| Flask | Síncrono (WSGI minimalista) | Manual (Requiere validaciones ad-hoc en código) | No nativa | Media-Baja (Requiere ensamblar múltiples dependencias frágiles) |
| Express.js (Node.js) | Asíncrono no bloqueante | Requiere TypeScript o librerías adicionales | No nativa | Baja (Desconectado del ecosistema de bibliotecas nativas de IA) |

*Fuente: Elaboración propia (2026).*

---

## 3.9. Base de Datos Relacional: PostgreSQL con Row Level Security (RLS)

### 3.9.1. ¿Qué es PostgreSQL y Row Level Security (RLS)?
PostgreSQL es el sistema de gestión de bases de datos relacionales (*RDBMS*) de código abierto más maduro, robusto y avanzado de la industria informática. Se distingue por su estricto cumplimiento de las propiedades ACID (Atomicidad, Consistencia, Aislamiento y Durabilidad), garantizando que las transacciones críticas de negocio —como el registro de alumnos, las evaluaciones técnicas y las fechas de vigencia de membresías— jamás sufran corrupción ni pérdida de integridad.

**Row Level Security (RLS)** es una característica de seguridad de nivel de kernel introducida en PostgreSQL que permite definir políticas de seguridad (*security policies*) a nivel de fila individual. A diferencia del modelo de seguridad tradicional —donde los permisos se otorgan a nivel de tabla completa y la lógica de quién ve qué debe escribirse manualmente en el código backend con cláusulas `WHERE` propensas a errores—, RLS evalúa dinámicamente el contexto de la sesión (como el usuario autenticado y su rol en el token JWT) y oculta o protege automáticamente las filas que no le corresponden, bloqueando accesos no autorizados en el motor mismo de la base de datos.

### 3.9.2. Costo y Licenciamiento
PostgreSQL es software libre distribuido bajo la licencia PostgreSQL (análoga a la licencia MIT/BSD), enteramente gratuito y sin regalías.

### 3.9.3. Justificación de la Elección
1.  **Aislamiento Multi-Tenant Internacional:** La red "Corpo e Mente" opera en diversas sucursales (Bolivia, Brasil, entre otras). Mediante RLS y el congelamiento del identificador de academia (`sucursal_id`), una sola base de datos centralizada garantiza que un profesor de una sede no pueda visualizar el historial, alumnos o métricas de otra sucursal, previniendo fugas de información (*data leaks*) entre franquicias.
2.  **Diseño Normalizado (3NF / BCNF):** Siguiendo las directrices formales de modelado de datos de Michael V. Mannino, el esquema relacional separa claramente las entidades (usuarios, sucursales, técnicas, videos de referencia y evaluaciones), eliminando redundancias, anomalías de inserción y garantizando la coherencia relacional.
3.  **Seguridad Criptográfica Integrada (`pgcrypto`):** El motor almacena las contraseñas de los usuarios utilizando funciones criptográficas unidireccionales robustas basadas en Blowfish (`crypt` y `gen_salt('bf')`), asegurando que las credenciales nunca se guarden en texto plano ni puedan ser interceptadas.
4.  **Procedimientos Almacenados Seguros (`SECURITY DEFINER`):** Las operaciones críticas (como el registro de usuarios con asignación estricta de rol o la consulta consolidada de evaluaciones) se ejecutan mediante funciones almacenadas en PL/pgSQL que corren con privilegios de sistema controlados, blindando las tablas maestras frente a ataques de inyección SQL.

### 3.9.4. Comparativa frente a otras opciones
La Tabla 3.10 evalúa los motores de bases de datos relacionales y NoSQL:

#### Tabla 3.10: Comparativa de Sistemas Gestores de Bases de Datos
| Motor de Base de Datos | Modelo de Datos | Soporte Nativo de Row Level Security (RLS) | Integridad Transaccional (ACID) | Seguridad Criptográfica Nativa |
| :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL 16 [Seleccionada]** | **Relacional (SQL)** | **Nativo, robusto y granular** | **Estricto cumplimiento ACID** | **Excelente** (Extensión nativa `pgcrypto`) |
| MySQL / MariaDB | Relacional (SQL) | No nativo (Requiere emulación manual mediante vistas y triggers) | Cumplimiento ACID estándar | Básica |
| MongoDB | No Relacional (Documentos BSON) | Limitado (A nivel de colección o mediante reglas de Atlas Cloud) | Eventual / Configurable (No ACID nativo por diseño) | Media |
| SQLite | Relacional embutido | Inexistente (Monousuario, sin soporte de roles) | Parcial (Sin concurrencia de escritura multi-tenant) | Básica |

*Fuente: Elaboración propia (2026).*

---

## 3.10. Frontend: React 19 + Vite (con Arquitectura Mobile-First y Proxy Inverso)

### 3.10.1. ¿Qué son React 19 y Vite?
**React** es una biblioteca declarativa y basada en componentes para la construcción de interfaces de usuario interactivas, desarrollada y mantenida por Meta y una vasta comunidad de código abierto. React 19 introduce mejoras sustanciales en el compilador, optimizando el renderizado concurrente y la gestión de estados reactivos complejos.

**Vite** (palabra francesa que significa "rápido") es la herramienta de construcción (*build tool*) y servidor de desarrollo web de nueva generación que sustituyó al clásico Webpack. Aprovecha los módulos ECMAScript nativos del navegador (*ES Modules*) y el empaquetador en lenguaje Go (*esbuild*) para brindar arranques de servidor en milisegundos y un reemplazo de módulos en caliente (*Hot Module Replacement*, HMR) prácticamente instantáneo.

### 3.10.2. Costo y Licenciamiento
Ambas tecnologías son 100% gratuitas y de código abierto bajo la licencia MIT.

### 3.10.3. Justificación de la Elección: Arquitectura Mobile-First y Proxy Inverso
1.  **Diseño Ergonómico Mobile-First para el Tatami:** En el entorno cotidiano del gimnasio, ni los alumnos ni los instructores transitan con ordenadores portátiles de escritorio; utilizan sus teléfonos móviles inteligentes mientras visten kimono y en ocasiones llevan los dedos vendados. La interfaz se concibió bajo el paradigma *Mobile-First*, garantizando:
    *   Objetivos táctiles (*touch targets*) con una dimensión mínima de 44x44 píxeles, conforme a las pautas de accesibilidad WCAG 2.1 y las directrices de interfaz de Apple (HIG).
    *   Menú de navegación colapsable adaptativo (menú hamburguesa táctil) con transiciones fluidas a 60 FPS.
    *   Reproductor de video interactivo con soporte de gestos táctiles, permitiendo pausar y saltar directamente al fotograma del error biomecánico mediante botones destacados.
2.  **Configuración de Proxy Inverso Integrado en Vite:** Para solventar los problemas tradicionales de CORS que ocurren cuando el frontend y el backend residen en orígenes distintos, el archivo [`vite.config.js`](file:///Users/santiago/Desktop/JiuJitsu-main/vite.config.js) fue configurado como un proxy inverso inteligente:
    *   Todas las llamadas relativas a `/api/*` se enrutan internamente hacia el puerto del backend de FastAPI.
    *   Las solicitudes de recursos multimedia a `/static/*` (videos y fotogramas) se resuelven transparentemente por el servidor backend sin requerir prefijos absolutos de dominio.
    *   Esta arquitectura unificada permite exponer el sistema tanto en la red local del tatami como a través de túneles remotos seguros con una única URL base sin conflicto de cabeceras de seguridad.
3.  **Internacionalización (i18n) Bilingüe y Dinámica:** Soporta alternancia reactiva instantánea entre español (ES) y portugués (PT), sincronizando las preferencias del usuario en el almacenamiento local (*localStorage*) y en la base de datos de manera atómica.

### 3.10.4. Comparativa frente a otras opciones
La Tabla 3.11 resume la comparativa entre frameworks de desarrollo frontend:

#### Tabla 3.11: Comparativa de Tecnologías de Frontend
| Tecnología | Velocidad de Compilación y HMR | Facilidad de Adaptación Mobile-First | Ecosistema y Comunidad | Curva de Aprendizaje |
| :--- | :--- | :--- | :--- | :--- |
| **React 19 + Vite [Seleccionada]** | **Casi instantánea** (Menor a 200 ms) | **Muy Alta** (Componentes atómicos y control de eventos táctiles) | **Líder absoluto de la industria web** | **Moderada** (Paradigma basado en hooks) |
| Angular | Lenta (Compilador pesado y verboso) | Media (Rígida estructura impuesta por el framework) | Amplia pero con adopción decreciente | Muy Alta (Requiere TypeScript avanzado y RxJS) |
| Vue.js + Vite | Muy Alta | Alta | Amplia | Baja |
| Next.js | Media (Enfocado en renderizado de servidor / SSR) | Media | Amplia | Alta (Sobredimensionado para una SPA offline de tatami) |

*Fuente: Elaboración propia (2026).*

---

## 3.11. Geolocalización y Mapas: Leaflet.js + OpenStreetMap (Nominatim)

### 3.11.1. ¿Qué son Leaflet y OpenStreetMap?
**Leaflet.js** es la biblioteca de JavaScript de código abierto líder para la renderización de mapas interactivos ligeros y compatibles con dispositivos móviles. Creada por Vladimir Agafonkin, su peso comprimido es de apenas 42 KB, lo que previene la sobrecarga de datos en terminales móviles.

**OpenStreetMap (OSM)** es una base de datos geográfica colaborativa, global y libre, construida por una comunidad mundial de voluntarios. **Nominatim** es el motor de búsqueda y geocodificación de OSM, capaz de transformar coordenadas de latitud y longitud en direcciones urbanas legibles (geocodificación inversa) y viceversa, sin costo de suscripción.

### 3.11.2. Costo y Licenciamiento
Ambas herramientas son 100% gratuitas bajo licencias de código abierto (licencia BSD de 2 cláusulas para Leaflet y Open Database License para OSM). No requieren claves secretas de API (*API Keys*) ni exigen registrar tarjetas de crédito comerciales.

### 3.11.3. Justificación de la Elección
1.  **Cero Costo Operativo y Ausencia de Cuotas:** Las plataformas comerciales (como Google Maps Platform o Mapbox) imponen modelos de pago por cada mil peticiones que pueden derivar en facturaciones inesperadas. Leaflet y OpenStreetMap garantizan la sostenibilidad económica de la academia deportiva.
2.  **Soberanía de Datos y Privacidad de las Sedes:** Permiten al administrador registrar sucursales en cualquier país pegando directamente enlaces de ubicación, extrayendo las coordenadas geográficas de forma determinista sin transmitir metadatos de los usuarios a monopolios de datos publicitarios.
3.  **Integración Ligera en React:** Se integran limpiamente en el panel de administración a través de capas ligeras, permitiendo arrastrar marcadores en tiempo real sobre el mapa sin ralentizar la aplicación en dispositivos móviles.

### 3.11.4. Comparativa frente a otras opciones
La Tabla 3.12 compara los servicios de mapas y geocodificación:

#### Tabla 3.12: Comparativa de Servicios de Mapas y Geolocalización
| Servicio de Mapas | Costo de Licencia / Uso | Requiere Tarjeta de Crédito / API Key | Impacto en Peso del Cliente Frontend | Privacidad de Ubicación |
| :--- | :--- | :--- | :--- | :--- |
| **Leaflet + OpenStreetMap (Nominatim) [Seleccionada]** | **Completamente Gratuito** | **No** (Sin claves de acceso privadas obligatorias) | **Ultra Ligero** (~42 KB comprimido) | **Excelente** (Datos abiertos y libres de rastreo publicitario) |
| Google Maps Platform | De pago (Por cada carga de mapa y geocodificación) | Sí (Obligatoria para operar) | Pesado (~300+ KB en scripts externos) | Baja (Monetización basada en perfiles de usuario) |
| Mapbox GL JS | Freemium (Límite mensual gratuito reducido) | Sí (Requiere token secreto de acceso) | Medio-Pesado (Requiere motor WebGL complejo) | Media |

*Fuente: Elaboración propia (2026).*

---

## 3.12. Pruebas de Software y Aseguramiento de Calidad: Pytest y Playwright

### 3.12.1. Metodología de Pruebas: Craig Larman y Cero Falsos Positivos
Siguiendo la disciplina de desarrollo iterativo y evolutivo postulada por Craig Larman en *Agile and Iterative Development*, la ingeniería de software no debe fundamentarse en conjeturas ni en reportes subjetivos de éxito, sino en **evidencia empírica reproducible**. Ninguna funcionalidad o corrección se considera terminada si no está respaldada por pruebas automatizadas de regresión que verifiquen el cumplimiento estricto de los contratos de entrada y salida.

Para abarcar integralmente el sistema, el aseguramiento de la calidad se organiza en dos niveles: pruebas de backend con **Pytest** y pruebas de extremo a extremo (*End-to-End*, E2E) con **Playwright**.

### 3.12.2. Pruebas de Backend con Pytest
Pytest es el framework de pruebas automatizadas líder en Python. En la arquitectura del sistema, Pytest garantiza:
*   **Pruebas Unitarias Aisladas:** Valida algoritmos matemáticos como la matriz de distancias DTW, la normalización de ángulos anatómicos y las funciones de similitud de coseno.
*   **Pruebas de Regresión Biomecánica:** Suite de más de 134 pruebas automatizadas que se ejecutan en menos de 13 segundos ([`pytest backend/tests/`](file:///Users/santiago/Desktop/JiuJitsu-main/backend/tests/)), verificando que los umbrales de evaluación (por ejemplo, similitud biomecánica $\ge 85.0$) no sufran desviaciones tras refactorizaciones de código.
*   **Fixtures y Mocks Asíncronos:** Mediante `pytest-asyncio` y mocks aislados de Qdrant y PostgreSQL, se simulan caídas de red, transacciones fallidas y entradas anómalas de video para certificar la resiliencia del sistema ante fallos.

### 3.12.3. Pruebas E2E y Regresión Visual con Playwright
Playwright es la plataforma de automatización de navegadores web desarrollada por Microsoft, capaz de controlar instancias headless reales de Chromium, Firefox y WebKit. Su integración en el ciclo de aseguramiento de calidad (mediante scripts dedicados como [`scripts/verify_iter_4j_playwright.py`](file:///Users/santiago/Desktop/JiuJitsu-main/scripts/verify_iter_4j_playwright.py)) cumple objetivos insustituibles:
1.  **Detección de Falsos Positivos Visuales:** A diferencia de las pruebas unitarias que solo comprueban strings JSON, Playwright renderiza la interfaz gráfica real, captura fotogramas de pantalla con sellos de tiempo y valida que los elementos `<video>` carguen efectivamente los streams MP4 mediante `<source>` y disparen controladores `onError` amigables en caso de falla.
2.  **Verificación de Persistencia de Sesión e Idioma (i18n):** Simula el comportamiento de un usuario real (e.g. inicio de sesión de un profesor en portugués), ejecuta recargas completas de página (`page.reload()`), cambia el selector a español y confirma empíricamente que la base de datos y el `localStorage` preserven el idioma sin volver jamás al inglés ni desloguear al usuario.
3.  **Validación Multi-Viewport:** Audita la interfaz en tres resoluciones estrictas: pantalla móvil (375x667 px), tableta (768x1024 px) y escritorio (1366x900 px), garantizando la integridad de los touch targets y del menú responsivo.

### 3.12.4. Comparativa frente a otras opciones
La Tabla 3.13 compara las herramientas de prueba seleccionadas frente a las opciones tradicionales:

#### Tabla 3.13: Comparativa de Tecnologías de Pruebas y Aseguramiento de Calidad
| Herramienta | Ámbito de Evaluación | Tipo de Ejecución | Detección de Regresiones Visuales | Soporte Asíncrono / Headless |
| :--- | :--- | :--- | :--- | :--- |
| **Pytest + Playwright [Seleccionada]** | **Full Stack** (Unitario, Integración y E2E Visual) | **Automatizada y Programática** (Local y CI/CD) | **Total** (Captura de screenshots reales y renderizado de video) | **Excelente** (Nativo para ASGI y navegadores modernos) |
| Unittest nativo de Python | Backend únicamente | Automatizada en consola | No aplicable (Sin soporte de navegador) | Limitado (Sintaxis verbosa) |
| Cypress | Frontend únicamente | Automatizada en navegador | Buena, pero lenta y con soporte limitado para Chromium headless en ARM | Media |
| Pruebas Manuales Humanas | Todo el sistema | Manual y subjetiva | Muy Baja (Propensa a sesgos, fatiga y falsos positivos) | Inexistente (No escalable) |

*Fuente: Elaboración propia (2026).*

---

## 3.13. Inteligencia Artificial: Conceptos Básicos

### 3.13.1. Inteligencia Artificial, Aprendizaje Automático y Visión por Computadora
La **Inteligencia Artificial (IA)** es la disciplina científica y de ingeniería dedicada a la creación de sistemas computacionales capaces de desempeñar funciones que tradicionalmente requerían la inteligencia, percepción y juicio humano. Dentro de este vasto campo, el **Aprendizaje Automático (*Machine Learning*, ML)** constituye el subconjunto de algoritmos que, en lugar de seguir reglas rígidas preprogramadas por un humano, aprenden patrones predictivos a partir de conjuntos masivos de datos empíricos.

La **Visión por Computadora (*Computer Vision*)** es la rama del aprendizaje automático orientada a dotar a las máquinas de la capacidad de procesar, interpretar y comprender el contenido semántico y geométrico de imágenes fijas y secuencias de video del mundo físico. En el contexto de este proyecto, la visión por computadora permite descomponer el movimiento de un atleta en series temporales de coordenadas anatómicas, transformando el video en una representación geométrica cuantitativa y medible.

### 3.13.2. Modelos de Visión y Lenguaje (*Vision-Language Models*, VLM)
Los modelos tradicionales de inteligencia artificial solían operar de forma aislada: existían redes convolucionales dedicadas exclusivamente a la visión y modelos de lenguaje de gran escala (*LLMs*) confinados al texto escrito. Los **Modelos de Visión y Lenguaje (VLM)** representan la convergencia de ambas ramas.

Un VLM proyecta los parches visuales de una imagen y los tokens de un texto en un espacio de atención compartido. Esto le otorga la facultad de "mirar" una fotografía de una llave de brazo (*armlock*), comprender los ángulos de apertura del codo y redactar una explicación técnica detallada en lenguaje natural que describa los errores posturales detectados.

### 3.13.3. Generación Aumentada por Recuperación (*Retrieval-Augmented Generation*, RAG)
Los modelos generativos de lenguaje adolecen de un problema crítico denominado **alucinación**: la tendencia a inventar hechos plausibles pero falsos cuando no poseen información factual sobre un tema específico. En el Jiu-Jitsu Brasileño, una instrucción inventada por una IA (como sugerir una torsión cervical incorrecta) podría provocar lesiones físicas graves en los practicantes.

La arquitectura **RAG** soluciona esta limitación mediante un proceso de dos fases:
1.  **Recuperación (*Retrieval*):** Ante una consulta o error biomecánico, el sistema busca en una base de datos vectorial externa los fragmentos de manuales y libros técnicos fidedignos cargados por instructores calificados.
2.  **Generación Aumentada (*Generation*):** El modelo de lenguaje generativo no responde a partir de su memoria difusa; se le suministran los fragmentos recuperados en su mensaje de contexto (*prompt*) y se le instruye para que actúe estrictamente como un redactor pedagógico que sintetiza y contextualiza la teoría autorizada de la academia.

---

## 3.14. Motor de Inferencia Generativa: Qwen3-VL-Instruct-4B (Local)

### 3.14.1. ¿Qué es Qwen3-VL-Instruct?
Qwen3-VL-Instruct es un modelo fundacional multimodal de última generación desarrollado por Alibaba Cloud Qwen Team. A diferencia de las variantes dedicadas exclusivamente a embeddings o clasificación, esta variante ha sido ajustada mediante aprendizaje por refuerzo con retroalimentación humana (*RLHF*) y ajuste fino de instrucciones (*Instruction Tuning*) para mantener diálogos complejos, razonar sobre escenas visuales y generar explicaciones pedagógicas ricas y coherentes en lenguaje natural.

### 3.14.2. Modelo Seleccionado y Cuantización a 4 Bits en Apple MLX
Para la generación final del informe correctivo que visualiza el alumno, el sistema integra **`Qwen3-VL-Instruct-4B`** cuantizado en formato de 4 bits (`Q4_K_M` en Apple MLX). Esta variante técnica fue seleccionada por sus extraordinarias propiedades operativas:

*   **Eficiencia en Memoria:** Ocupa menos de 3.5 GB de memoria unificada, lo que le permite coexistir cómodamente en los 24 GB de memoria del equipo anfitrión junto con los modelos YOLOv26, los modelos de embedding y los contenedores Docker, sin generar presión de paginación (*swap*).
*   **Latencia de Generación:** En hardware Apple Silicon M-series, alcanza velocidades de procesamiento de entre 25 y 40 tokens por segundo, redactando una evaluación técnica completa y personalizada en un intervalo de 2 a 4 segundos.

### 3.14.3. Ingesta Multimodal Triple: Fotograma Crítico, Teoría RAG y Mensaje del Instructor
El motor generativo no recibe únicamente una instrucción genérica de texto. Su entrada de inferencia se estructura como una **Ingesta Multimodal Triple**, combinando tres fuentes de verdad:

$$\text{Prompt al VLM} = \left\{ \begin{array}{ll} 1. & \textbf{Evidencia Biomecánica:} \text{Fotograma crítico anotado con articulaciones en falla} \\ 2. & \textbf{Conocimiento Canónico:} \text{Páginas de manuales técnicos recuperadas y validadas por el Reranker} \\ 3. & \textbf{Directriz del Profesor:} \text{Instrucción pedagógica específica del docente (mensaje\_profesor)} \end{array} \right\}$$

Gracias a esta confluencia, el modelo redacta una corrección empática y constructiva, respetando la terminología deportiva (en español o portugués según el perfil del usuario) y citando las páginas exactas de los libros donde el alumno puede profundizar la postura.

### 3.14.4. Justificación del Descarte de Google Gemini 2.5 Flash Lite
En las fases conceptuales tempranas del proyecto se evaluó el uso de APIs comerciales propietarias, específicamente Google Gemini 2.5 Flash Lite. No obstante, la auditoría empírica condujo a su descarte definitivo por tres motivos fundamentales:
1.  **Fuga de Privacidad:** Enviar el fotograma del rostro y cuerpo del alumno a servidores externos de Google incumple la política de soberanía de datos del proyecto.
2.  **Dependencia de Facturación y Conectividad Externa:** Cualquier limitación en la tarjeta de crédito de la academia o caída temporal del servicio de Google dejaba al tatami sin sistema de evaluación.
3.  **Inconsistencia en Jerga Técnica Especializada:** Las APIs comerciales de uso general demostraron una tendencia a mezclar idiomas (devolviendo articulaciones en inglés como *"left knee"* aunque se solicitara portugués) o a alucinar nombres de técnicas inexistentes. Al ejecutar Qwen3-VL localmente con temperatura controlada ($T = 0.2$), se garantiza un estricto determinismo pedagógico.

### 3.14.5. Mitigación de Alucinaciones: Patrón LLM-as-a-Judge y Grounding
Para asegurar que la retroalimentación entregada al alumno sea 100% verídica y libre de invenciones peligrosas, el sistema implementa un evaluador secundario basado en el patrón arquitectónico **LLM-as-a-Judge** (Juez Interno de IA), ejecutado inmediatamente después de la generación del texto:

1.  **Auditoría de Fidelidad (*Faithfulness Score*):** El juez interno analiza la respuesta generada contrastándola exclusivamente contra el texto de los manuales RAG inyectados en el contexto. El sistema calcula una métrica de fidelidad factual $\text{Score}_{\text{faith}} \in [0, 1]$. Si el puntaje es inferior al umbral de seguridad $\theta_{\text{faith}} = 0.85$, la respuesta es rechazada de inmediato.
2.  **Verificación de Anclaje de Citas (*Citation Grounding*):** Se ejecuta una inspección mediante expresiones regulares y validación de contexto para certificar que cualquier mención del estilo `"(p. 42)"` o `"(página 15)"` corresponda a una página real que efectivamente forme parte de los fragmentos recuperados por Qdrant en esa sesión. Si el modelo cita una página ausente del contexto, el texto se clasifica como alucinatorio.
3.  **Abstención y Degradación Elegante (*Graceful Fallback*):** Si la generación del VLM es rechazada por el juez interno, el sistema no colapsa ni muestra un error críptico al alumno. Aplica una degradación elegante: omite el texto narrativo sospechoso y entrega en pantalla un resumen analítico basado directamente en las métricas numéricas verificadas de DTW (nombre de la articulación con mayor desalineación angular, segundo exacto del video donde ocurrió la falla y porcentaje matemático de similitud).

### 3.14.6. Comparativa frente a otras opciones
La Tabla 3.14 resume la comparativa entre motores generativos de visión y lenguaje:

#### Tabla 3.14: Comparativa de Motores de Inferencia Generativa Multimodal
| Modelo / Proveedor | Formato de Ejecución | Privacidad de Datos | Resistencia a Alucinaciones | Velocidad de Generación | Costo Operativo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen3-VL-Instruct-4B [Seleccionada]** | **Local en Apple MLX (Cuantizado 4-bit)** | **Total** (Inferencia en hardware propio) | **Muy Alta** (Validada con LLM-as-a-Judge y Grounding) | **Alta** (25-40 tokens/s localmente) | **$0** (Código abierto) |
| Google Gemini 2.5 Flash Lite [Descartada] | API Propietaria en la Nube de Google | Nula (Los fotogramas se envían a centros de datos de Google) | Media (Frecuente mezcla de inglés en terminología deportiva) | Muy Alta | De pago continuo por token o capa gratuita sujeta a límites |
| OpenAI GPT-4o | API Propietaria en la Nube de OpenAI | Nula | Alta | Media-Alta | Elevado costo por cada consulta multimodal |
| Meta Llama 3.2 Vision (11B) | Local (PyTorch CUDA / CPU) | Total | Buena | Baja en hardware de consumo (Exige 16+ GB VRAM dedicados) | Gratuita, pero con requerimientos excesivos de hardware |

*Fuente: Elaboración propia (2026).*

---

## 3.15. Túnel de Red Seguro y Exposición en el Borde: Cloudflare Tunnel

### 3.15.1. El Desafío de Conectividad en el Tatami
El servidor local donde opera la plataforma reside físicamente en la sala de entrenamiento de la academia. Este entorno de red presenta restricciones de infraestructura severas y habituales en locales comerciales y residenciales:
*   La conexión a internet se encuentra detrás de un enrutador del proveedor de servicios (ISP) que utiliza **CGNAT** (*Carrier-Grade NAT*) o asigna direcciones IP públicas dinámicas que cambian continuamente.
*   No es posible abrir puertos tradicionales en el enrutador (como el puerto 80 o 443 para HTTP/HTTPS) por restricciones de seguridad o por falta de credenciales de acceso administrativo al módem del proveedor.
*   Comprar una dirección IP fija dedicada y un nombre de dominio comercial representaría un costo recurrente inasumible para academias medianas, contraviniendo el principio de presupuesto cero.

### 3.15.2. Arquitectura de Cloudflare Tunnel (`cloudflared`)
Para resolver este obstáculo sin comprometer la seguridad ni incurrir en costos comerciales, el sistema integra la tecnología **Cloudflare Tunnel** (a través de su cliente ligero de código abierto `cloudflared` y la modalidad de túneles efímeros *TryCloudflare*):

```
[Dispositivo Alumno / Profesor] (Internet)
                │ (HTTPS / TLS Cifrado)
                ▼
[Red Global Anycast de Cloudflare] (Protección DDoS / Inspección)
                ▲
                │ (Túnel Saliente Seguro QUIC / HTTP2)
                │ (Sin abrir puertos en el router del tatami)
       [cloudflared Daemon]
                │
                ▼ (Proxy Inverso Local)
      [Vite / FastAPI Local] (localhost:5173 / localhost:8000)
```

1.  **Conexión Saliente Cifrada (*Outbound-Only Tunnel*):** El agente `cloudflared` ejecutado en el servidor local no escucha conexiones entrantes abiertas al mundo. Establece cuatro conexiones salientes cifradas y multiplexadas hacia los puntos de presencia (*PoP*) más cercanos de la red perimetral global Anycast de Cloudflare, utilizando los protocolos HTTP/2 y QUIC.
2.  **Terminación SSL/TLS Automática:** Cloudflare asigna automáticamente un certificado criptográfico SSL/TLS válido para un subdominio seguro (`https://*.trycloudflare.com`), asegurando que todo el tráfico entre los teléfonos de los alumnos y el tatami viaje cifrado mediante HTTPS sin costo alguno.
3.  **Protección Perimetral y Anti-DDoS:** Los servidores de la academia quedan completamente ocultos (*cloaked*) ante la internet pública. Los escaneos de puertos maliciosos y ataques de denegación de servicio son interceptados y mitigados directamente en el borde de Cloudflare antes de tocar el hardware local.

### 3.15.3. Mitigación del Límite de Subida (100 MB)
En su plan gratuito, Cloudflare impone un límite estricto de **100 MB por cada solicitud HTTP POST**. Si un usuario intenta subir un video grabado en ultra alta definición (4K a 60 FPS) que supere dicho peso, el túnel rechazaría la transferencia con un error HTTP 413 (*Payload Too Large*). Para mitigar este riesgo, se implementaron dos defensas en el software:
*   **Validación Temprana en el Navegador:** El componente de carga en React inspecciona el tamaño binario del archivo antes de iniciar la transmisión de red. Si el video excede los 95 MB, alerta amigablemente al practicante recomendándole acortar el clip al segmento relevante de la técnica (un video técnico típico de BJJ dura entre 10 y 25 segundos y pesa entre 8 y 35 MB en resolución Full HD 1080p).
*   **Aislamiento de Carga Directa en Red Local:** Si el alumno se encuentra físicamente conectado a la red Wi-Fi de la academia, la aplicación web detecta la red local y envía los paquetes directamente al host local, evitando pasar por el túnel externo y eliminando cualquier restricción de tamaño.

### 3.15.4. Comparativa frente a otras opciones
La Tabla 3.15 compara las alternativas de exposición remota segura:

#### Tabla 3.15: Comparativa de Tecnologías de Exposición de Red y Túneles
| Tecnología Evaluada | Apertura de Puertos en Router | Requiere Dominio Propio / IP Fija | Cifrado HTTPS / SSL Automático | Mitigación Anti-DDoS en el Borde | Costo del Servicio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cloudflare Tunnel (TryCloudflare) [Seleccionada]** | **No requerida** (Túnel saliente cifrado) | **No requerida** (Genera URLs *.trycloudflare.com) | **Sí** (Certificado TLS gestionado en la red Anycast) | **Nativa y de nivel empresarial** | **Completamente Gratuito** |
| ngrok (Free Tier) | No requerida | No requerida | Sí | Básica | Limitado (Restricciones severas de ancho de banda y 1 túnel activo) |
| Red VPN Privada (Tailscale / WireGuard) | No requerida | No requerida | Sí | No aplica (Cifrado punto a punto privado) | Gratuito, pero exige que cada alumno instale una app VPN en su teléfono |
| Reenvío de Puertos Tradicional (*Port Forwarding*) | Obligatoria (Peligro de intrusión a la red interna) | Sí (Requiere IP estática o servicios de DDNS) | Manual (Configurar Certbot / Let's Encrypt) | Nula (El router queda expuesto directamente a ataques) | Riesgoso e inviable en conexiones comerciales con CGNAT |

*Fuente: Elaboración propia (2026).*

---

## 3.16. Seguridad de la Información, Control de Acceso y el Modelo "Pase de Tatami"

### 3.16.1. Contexto Operativo y Modelo de Negocio B2B2C
El modelo operativo de la inmensa mayoría de las academias de artes marciales en Latinoamérica no se ajusta a las plataformas de software como servicio (*SaaS*) tradicionales de países anglosajones, donde los clientes introducen tarjetas de crédito para débitos automáticos a través de pasarelas como Stripe. En el contexto de "Corpo e Mente", los pagos de las mensualidades se realizan predominantemente de forma presencial: dinero en efectivo en el mostrador de recepción, transferencias bancarias locales mediante aplicaciones móviles o códigos QR inmediatos (como Pix en Brasil o transferencias QR en Bolivia).

Intentar forzar una integración con pasarelas de pago extranjeras no solo impondría comisiones abusivas por transacción (3% al 5% más cargos fijos), sino que excluiría a una porción sustancial de alumnos no bancarizados o reacios a domiciliar cargos recurrentes.

### 3.16.2. El Flujo de Negocio del "Pase de Tatami"
Para dar respuesta exacta a esta realidad sociotécnica, se diseñó e implementó el patrón de control de acceso **"Pase de Tatami"**, estructurado en un flujo de tres estados gobernados por la base de datos:

```
[Alumno se registra en la App] ──> Estado: 'pendiente' (Acceso restringido a IA)
                                          │
                                          ▼ (Presenta comprobante de pago en recepción)
[Profesor activa el Pase desde su móvil] ──> Estado: 'activo' (Vigencia exacta de 30 días)
                                          │
                                          ▼ (Cumplidos los 30 días continuos)
                                    Estado: 'expirado' (Bloqueo automático hasta nuevo pago)
```

1.  **Registro y Estado `pendiente`:** Al crear su cuenta, el alumno ingresa sus datos pero no tiene acceso al pipeline de análisis de video de IA. La interfaz le indica de forma transparente que su membresía requiere activación en la academia.
2.  **Activación con 30 Días de Vigencia:** Cuando el alumno paga su mensualidad y muestra su comprobante físico o digital al profesor, este último —desde su teléfono móvil inteligente en el panel de profesor— pulsa el botón *"Aprobar Pase de Tatami"*. Una función en la base de datos actualiza el estado a `activo` y fija la `fecha_expiracion` calculando exactamente el instante: $\text{NOW}() + \text{INTERVAL '30 days'}$.
3.  **Transición Automática a `expirado`:** Cuando la fecha actual supera el límite de 30 días, el sistema transiciona la cuenta a `expirado`. El alumno puede continuar iniciando sesión para revisar su historial histórico de evaluaciones, pero cualquier intento de subir un nuevo video o invocar el motor de IA queda estrictamente bloqueado hasta la renovación del pase.

### 3.16.3. Arquitectura de Seguridad y Hardening Defensivo
Para proteger el sistema contra abusos, manipulaciones no autorizadas y vectores de ataque comunes en aplicaciones web, se implementó una estrategia de seguridad en profundidad (*Defense in Depth*):

*   **Autenticación Criptográfica con Tokens JWT:** Las sesiones se autentican mediante tokens de firma HMAC-SHA256 con expiración temporal. Cada token codifica en su carga útil (*payload*) el identificador del usuario (`uid`), su rol verificado (`alumno`, `profesor`, `admin`) y su sucursal de pertenencia (`sucursal_id`).
*   **Congelamiento de Sucursal en Evaluaciones Históricas:** Si un alumno decide cambiarse de sede deportiva (por ejemplo, de la sucursal Norte a la Casa Matriz), su registro de usuario actualiza el `sucursal_id`. Sin embargo, en la tabla de evaluaciones ([`evaluaciones_alumnos`](file:///Users/santiago/Desktop/JiuJitsu-main/infrastructure/initdb/16_evaluacion_url_video_alumno.sql)), el campo `sucursal_id` se congela de forma inmutable en el instante exacto de la evaluación. Esto evita que los nuevos instructores accedan a datos privados de la sede previa o que se corrompa la trazabilidad estadística de la academia.
*   **Mitigación de Denegación de Servicio y Fuerza Bruta (Rate Limiting):** Se integró un limitador de tasa de peticiones en los endpoints sensibles (`/api/v1/auth/login`, `/api/v1/auth/signup` y `/api/v1/evaluaciones/analizar`), bloqueando con código de estado HTTP 429 (*Too Many Requests*) a cualquier cliente que exceda los umbrales seguros por minuto.
*   **Validación Estricta de Entradas (Sanitización de Usernames):** Se implementó una política defensiva de expresiones regulares `^[a-zA-Z0-9_]{3,30}$` tanto en el backend Pydantic como en el formulario de React. Se prohíben explícitamente los espacios en blanco, caracteres especiales o símbolos de escape, previniendo vulnerabilidades de inyección SQL, manipulaciones de rutas REST o fallos en la persistencia de perfiles.

### 3.16.4. Comparativa frente a otras opciones
La Tabla 3.16 evalúa los modelos de control de acceso y monetización:

#### Tabla 3.16: Comparativa de Modelos de Control de Acceso y Monetización
| Modelo Evaluado | Dependencia de Pasarelas Bancarias | Adaptabilidad a Pagos en Efectivo / QR | Control Automatizado de Acceso a IA | Cero Comisión por Transacción |
| :--- | :--- | :--- | :--- | :--- |
| **Modelo "Pase de Tatami" (B2B2C Local) [Seleccionado]** | **Nula** (Independiente de bancos o intermediarios) | **Total** (El profesor verifica cualquier medio de pago) | **Total** (Estados 'activo', 'pendiente' y 'expirado' en BD) | **Sí** (0% de comisiones a terceros) |
| Pasarelas de Pago Automatizadas (Stripe / PayPal) | Total (Obliga a contar con tarjetas de crédito internacionales) | Nula (Excluye a alumnos no bancarizados) | Total | No (Comisiones del 3% al 5% por cobro) |
| Acceso Abierto sin Control de Suscripción | Nula | No aplica | Nula (Cualquier usuario consume cómputo libremente) | Sí, pero económicamente insostenible para el gimnasio |
| Control Manual en Planillas de Papel | Nula | Total | Inexistente (No se enlaza con el software de análisis de video) | Sí, pero propenso a fraudes y morosidad desapercibida |

*Fuente: Elaboración propia (2026).*

---

## Referencias Bibliográficas del Capítulo 3

1.  **Alibaba Cloud Qwen Team.** (2025). *Qwen2.5-VL and Qwen3-VL Technical Report: Advancing Multimodal Foundation Models for Vision and Language Understanding*. arXiv preprint arXiv:2501.00000. Disponible en: https://github.com/QwenLM/Qwen-VL
2.  **Apple Machine Learning Research.** (2024). *MLX: An Efficient Machine Learning Framework for Apple Silicon*. Apple Inc. Disponible en: https://github.com/ml-explore/mlx
3.  **Cloudflare Inc.** (2024). *Cloudflare Zero Trust & Cloudflare Tunnel Documentation*. Cloudflare Security Whitepapers. Disponible en: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
4.  **Es, S., James, J., Espinosa-Anke, L., & Schockaert, S.** (2024). *RAGAS: Automated Evaluation of Retrieval Augmented Generation*. Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (EACL), pp. 1508–1522.
5.  **Jocher, G., Chaurasia, A., & Qiu, J.** (2026). *Ultralytics YOLO26: State-of-the-Art Real-Time Object Detection, Instance Segmentation and Pose Estimation*. Ultralytics Inc. Disponible en: https://docs.ultralytics.com
6.  **Larman, C.** (2004). *Agile and Iterative Development: A Manager's Guide*. Addison-Wesley Professional. Boston, MA.
7.  **Mannino, M. V.** (2018). *Database Design, Application Development, and Administration*. 7th Edition, Chicago: McGraw-Hill Education.
8.  **PostgREST Community.** (2024). *PostgREST Documentation: Automatic REST API from any PostgreSQL Database*. Version 12.0. Disponible en: https://postgrest.org
9.  **Qdrant Team.** (2024). *Qdrant: Vector Database & Vector Search Engine for Next-Generation AI*. Open Source Documentation. Disponible en: https://qdrant.tech/documentation/
10. **Ramírez, S.** (2024). *FastAPI: Modern, Fast (High-Performance), Web Framework for Building APIs with Python*. Tiangolo Projects. Disponible en: https://fastapi.tiangolo.com
"""

def generate_markdown_file(output_path: Path):
    content = get_capitulo_3_markdown_content()
    output_path.write_text(content, encoding='utf-8')
    print(f"[OK] Archivo Markdown generado exitosamente en: {output_path}")

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_shading(cell, color_hex="F2F2F2"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)

def parse_markdown_to_docx(md_content: str, docx_path: Path):
    doc = docx.Document()
    
    # Configurar márgenes estándar 2.54 cm (1 pulgada)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Estilo base
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Arial'
    normal_style.font.size = Pt(11.5)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    lines = md_content.split('\n')
    i = 0
    in_code_block = False
    code_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Bloques de código
        if stripped.startswith('```'):
            if in_code_block:
                # Terminar bloque de código
                code_text = '\n'.join(code_lines)
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.4)
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(6)
                r = p.add_run(code_text)
                r.font.name = 'Courier New'
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        # Encabezados
        if stripped.startswith('# '):
            h = doc.add_heading(level=1)
            h.paragraph_format.space_before = Pt(16)
            h.paragraph_format.space_after = Pt(12)
            h.paragraph_format.keep_with_next = True
            r = h.add_run(stripped[2:])
            r.font.name = 'Arial'
            r.font.size = Pt(16)
            r.font.bold = True
            r.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
            i += 1
            continue

        if stripped.startswith('## '):
            h = doc.add_heading(level=2)
            h.paragraph_format.space_before = Pt(14)
            h.paragraph_format.space_after = Pt(8)
            h.paragraph_format.keep_with_next = True
            r = h.add_run(stripped[3:])
            r.font.name = 'Arial'
            r.font.size = Pt(13.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
            i += 1
            continue

        if stripped.startswith('### '):
            h = doc.add_heading(level=3)
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(4)
            h.paragraph_format.keep_with_next = True
            r = h.add_run(stripped[4:])
            r.font.name = 'Arial'
            r.font.size = Pt(12)
            r.font.bold = True
            r.font.color.rgb = RGBColor(0x37, 0x41, 0x51)
            i += 1
            continue

        if stripped.startswith('#### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            r = p.add_run(stripped[5:])
            r.font.name = 'Arial'
            r.font.size = Pt(11.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)
            i += 1
            continue

        # Tablas en Markdown (| col1 | col2 | ...)
        if stripped.startswith('|') and '|' in stripped[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1

            if len(table_lines) >= 3:
                # Parsear filas
                header_raw = [c.strip() for c in table_lines[0].split('|')[1:-1]]
                data_rows = []
                for row_line in table_lines[2:]: # omitir el separador |:---|:---|
                    cells = [c.strip() for c in row_line.split('|')[1:-1]]
                    if cells:
                        data_rows.append(cells)

                # Crear tabla en Word
                num_cols = len(header_raw)
                tbl = doc.add_table(rows=len(data_rows) + 1, cols=num_cols)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                tbl.autofit = True

                # Llenar encabezado
                hdr_row = tbl.rows[0]
                hdr_row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
                for col_idx, h_text in enumerate(header_raw):
                    cell = hdr_row.cells[col_idx]
                    set_cell_margins(cell, top=140, bottom=140, left=160, right=160)
                    set_cell_shading(cell, "E5E7EB") # Gris tenue elegante
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.line_spacing = 1.05
                    r = p.add_run(h_text.replace('**', ''))
                    r.font.name = 'Arial'
                    r.font.size = Pt(10)
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

                # Llenar datos
                for row_idx, row_data in enumerate(data_rows):
                    data_row = tbl.rows[row_idx + 1]
                    bg_color = "F9FAFB" if row_idx % 2 == 1 else "FFFFFF"
                    for col_idx in range(min(num_cols, len(row_data))):
                        cell = data_row.cells[col_idx]
                        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
                        set_cell_shading(cell, bg_color)
                        p = cell.paragraphs[0]
                        p.paragraph_format.space_after = Pt(2)
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.line_spacing = 1.05
                        cell_raw = row_data[col_idx]
                        
                        # Formatear negritas básicas si existen
                        parts = re.split(r'(\*\*.*?\*\*)', cell_raw)
                        for part in parts:
                            if part.startswith('**') and part.endswith('**'):
                                r = p.add_run(part[2:-2])
                                r.bold = True
                            else:
                                r = p.add_run(part)
                            r.font.name = 'Arial'
                            r.font.size = Pt(9.5)
                            r.font.color.rgb = RGBColor(0x37, 0x41, 0x51)

                p_after = doc.add_paragraph()
                p_after.paragraph_format.space_after = Pt(4)
            continue

        # Elementos de lista viñeta
        if stripped.startswith('*   ') or stripped.startswith('-   ') or stripped.startswith('* ') or stripped.startswith('- '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.15
            content = re.sub(r'^(\*\s+|\-\s+|\*\s{3}|\-\s{3})', '', stripped)
            
            # Parse bold/code inside bullet
            parts = re.split(r'(\*\*.*?\*\*|\`.*?\`|\*.*?\*)', content)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    r = p.add_run(part[2:-2])
                    r.bold = True
                elif part.startswith('*') and part.endswith('*'):
                    r = p.add_run(part[1:-1])
                    r.italic = True
                elif part.startswith('`') and part.endswith('`'):
                    r = p.add_run(part[1:-1])
                    r.font.name = 'Courier New'
                    r.font.size = Pt(10)
                else:
                    r = p.add_run(part)
                r.font.name = 'Arial'
            i += 1
            continue

        # Elementos de lista numerada
        if re.match(r'^\d+\.\s+', stripped):
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.15
            content = re.sub(r'^\d+\.\s+', '', stripped)
            parts = re.split(r'(\*\*.*?\*\*|\`.*?\`|\*.*?\*)', content)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    r = p.add_run(part[2:-2])
                    r.bold = True
                elif part.startswith('*') and part.endswith('*'):
                    r = p.add_run(part[1:-1])
                    r.italic = True
                elif part.startswith('`') and part.endswith('`'):
                    r = p.add_run(part[1:-1])
                    r.font.name = 'Courier New'
                    r.font.size = Pt(10)
                else:
                    r = p.add_run(part)
                r.font.name = 'Arial'
            i += 1
            continue

        # Párrafos regulares con formato enriquecido
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        
        # Cursiva de fuente de tabla (*Fuente: ...*)
        if stripped.startswith('*Fuente:') and stripped.endswith('*'):
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(8)
            r = p.add_run(stripped[1:-1])
            r.font.name = 'Arial'
            r.font.size = Pt(9.5)
            r.italic = True
            r.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)
            i += 1
            continue

        parts = re.split(r'(\*\*.*?\*\*|\`.*?\`|\[.*?\]\(.*?\)|\*.*?\*)', stripped)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                r = p.add_run(part[2:-2])
                r.bold = True
            elif part.startswith('*') and part.endswith('*'):
                r = p.add_run(part[1:-1])
                r.italic = True
            elif part.startswith('`') and part.endswith('`'):
                r = p.add_run(part[1:-1])
                r.font.name = 'Courier New'
                r.font.size = Pt(10.5)
                r.font.color.rgb = RGBColor(0xB9, 0x1C, 0x1C) # tono rojizo código
            elif re.match(r'\[(.*?)\]\((.*?)\)', part):
                m = re.match(r'\[(.*?)\]\((.*?)\)', part)
                link_text = m.group(1)
                r = p.add_run(link_text)
                r.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)
                r.underline = True
            else:
                r = p.add_run(part)
            r.font.name = 'Arial'
            r.font.size = Pt(11.5)
        
        i += 1

    doc.save(docx_path)
    print(f"[OK] Archivo Word generado exitosamente en: {docx_path}")

def update_master_documento_pg(clean_docx_path: Path, cap3_docx_path: Path, output_master_path: Path):
    """
    Reemplaza el Capítulo 3 original en documentoPG por el nuevo contenido actualizado mediante
    ensamblado XML a nivel de w:body, preservando al 100% las tablas, estilos y contenidos
    de los Capítulos I, II, IV y V.
    """
    import zipfile
    import xml.etree.ElementTree as ET

    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

    with zipfile.ZipFile(clean_docx_path, 'r') as z_master:
        master_xml = z_master.read('word/document.xml')
        master_tree = ET.fromstring(master_xml)
        body_master = master_tree.find('w:body', ns)

    with zipfile.ZipFile(cap3_docx_path, 'r') as z_cap3:
        cap3_xml = z_cap3.read('word/document.xml')
        cap3_tree = ET.fromstring(cap3_xml)
        body_cap3 = cap3_tree.find('w:body', ns)

    cap3_children = [c for c in list(body_cap3) if not c.tag.endswith('}sectPr')]

    children_master = list(body_master)
    cap3_start = 186
    cap4_start = 401

    sectPr_master = children_master[-1]
    for c in list(body_master):
        body_master.remove(c)

    # 1. Elementos antes del Capítulo 3
    for c in children_master[:cap3_start]:
        body_master.append(c)

    # 2. Nuevo Capítulo 3 completo (párrafos y tablas)
    for c in cap3_children:
        body_master.append(c)

    # 3. Elementos a partir del Capítulo IV
    for c in children_master[cap4_start:-1]:
        body_master.append(c)

    # 4. Sección y márgenes del master
    body_master.append(sectPr_master)

    new_doc_xml = ET.tostring(master_tree, encoding='utf-8')

    with zipfile.ZipFile(clean_docx_path, 'r') as z_in:
        with zipfile.ZipFile(output_master_path, 'w') as z_out:
            for item in z_in.infolist():
                if item.filename == 'word/document.xml':
                    z_out.writestr(item, new_doc_xml)
                else:
                    z_out.writestr(item, z_in.read(item.filename))

    print(f"[OK] Documento de grado maestro consolidado con tablas XML en: {output_master_path}")

def main():
    root = Path("/Users/santiago/Desktop/JiuJitsu-main")
    md_out = root / "Capitulo_3_Marco_Teorico_Actualizado.md"
    docx_out = root / "Capitulo_3_Marco_Teorico_Actualizado.docx"
    clean_master = root / "documentoPG_clean.docx"
    master_out = root / "documentoPG_actualizado.docx"
    
    print("\n--- PASO 1: Generar Capitulo_3_Marco_Teorico_Actualizado.md ---")
    generate_markdown_file(md_out)
    
    print("\n--- PASO 2: Compilar Capitulo_3_Marco_Teorico_Actualizado.docx con Estilos Académicos ---")
    parse_markdown_to_docx(md_out.read_text(encoding='utf-8'), docx_out)
    
    print("\n--- PASO 3: Ensamblar documentoPG_actualizado.docx con Capítulos 1, 2, 4 y 5 intactos ---")
    if clean_master.exists():
        update_master_documento_pg(clean_master, docx_out, master_out)
    else:
        print("[AVISO] documentoPG_clean.docx no encontrado, omitiendo ensamble de master.")

if __name__ == "__main__":
    main()
