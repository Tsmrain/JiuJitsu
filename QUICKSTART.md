# JiuJitsu Tesis - Análisis Biomecánico con YOLO26-pose

Sistema para comparar movimientos de Jiu-Jitsu Brasileño entre maestro y alumno usando Visión por Computadora (YOLO26-pose, normalización cinemática y DTW con restricción de Sakoe-Chiba).

## 📁 Estructura del Repositorio

```
JiuJitsu/
├── .gitignore
├── README.md               # Documento Formal Completo de Tesis de Grado (Capítulos I a X)
├── QUICKSTART.md           # Guía rápida de ejecución y despliegue
├── requirements.txt        # Dependencias oficiales del pipeline
├── setup_colab.sh          # Script de instalación para Google Colab
├── setup_local.sh          # Script de instalación para entorno local (.venv)
├── setup_windows_gpu.bat   # Script de instalación para Windows con NVIDIA GPU
├── src/                    # Código fuente modular del pipeline
│   ├── __init__.py
│   ├── config.py           # Configuración de rutas, umbrales y topología COCO
│   ├── pose_extractor.py   # Inferencia con YOLO26-pose
│   ├── angle_calculator.py # Mapeo antropomórfico y cálculo angular
│   ├── dtw_comparator.py   # Alineación temporal DTW con Sakoe-Chiba
│   ├── frame_annotator.py  # Anotación visual de error con OpenCV
│   ├── csv_exporter.py     # Exportación de datos estructurados a CSV
│   ├── pipeline.py         # Orquestador del pipeline biomecánico
│   ├── utils.py            # Funciones auxiliares y de reporte
│   └── main.py             # Punto de entrada CLI
├── tests/                  # Suite de pruebas unitarias
│   ├── __init__.py
│   ├── test_angle_calculator.py
│   ├── test_dtw_comparator.py
│   └── test_pipeline.py
├── notebooks/
│   └── colab_demo.ipynb    # Notebook de demostración para Google Colab
├── Videos/                 # Videos Ground Truth de benchmark
│   ├── Maestro.mp4
│   └── Alumno.mp4
└── assets/                 # Logotipos institucionales
```

## 🚀 Ejecución en Google Colab

1. Abrir [Google Colab](https://colab.research.google.com/).
2. Subir o abrir el notebook `notebooks/colab_demo.ipynb`.
3. Activar el entorno de ejecución con GPU (**Entorno de ejecución > Cambiar tipo de entorno de ejecución > GPU A100 / T4**).
4. Ejecutar las celdas en orden. El script clonará el repositorio, instalará las dependencias y ejecutará el análisis biomecánico completo mostrando el fotograma anotado y la gráfica resultante.

## 🛠️ Ejecución y Desarrollo Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/Tsmrain/JiuJitsu.git
cd JiuJitsu

# 2. Configurar entorno e instalar dependencias
bash setup_local.sh
source .venv/bin/activate

# 3. Ejecutar pipeline de análisis biomecánico
python3 -m src.main
```

## 🧪 Ejecución de Pruebas Unitarias

```bash
python3 -m unittest discover -s tests -v
```

## 📊 Entregables Generados

* **Fotograma Anotado:** Imagen JPG (~80 KB) con círculo rojo concéntrico y texto indicando el error angular crítico en `resultados/fotogramas/`.
* **Gráfica Temporal:** Curva de evolución de similitud angular por frame en `resultados/graficas/`.
* **Series CSV:** Archivos tabulares con series de ángulos articulares y porcentajes de similitud por frame en `resultados/csv/`.

## 📝 Documento de Tesis

Para consultar el marco teórico, fundamentación matemática, diagramas de ingeniería (UML, DCD, DDL, SSD) y la memoria académica completa, consulta el archivo [README.md](README.md).
