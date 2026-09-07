# JiuJitsu Tesis - Análisis Biomecánico con YOLO26-pose

Sistema para comparar movimientos de Jiu-Jitsu Brasileño entre maestro y alumno usando Visión por Computadora (YOLO26-pose, normalización cinemática y DTW con restricción de Sakoe-Chiba).

Implementado bajo la **Arquitectura en Capas de Craig Larman** y patrones de asignación de responsabilidades **GRASP / GoF**.

---

## 🏛️ Arquitectura en Capas y Estructura del Repositorio

```
JiuJitsu/
├── .gitignore
├── README.md               # Documento Formal Completo de Tesis de Grado (Capítulos I a X)
├── QUICKSTART.md           # Guía rápida de ejecución y despliegue
├── requirements.txt        # Dependencias oficiales del pipeline
├── setup_colab.sh          # Script de instalación para Google Colab
├── setup_local.sh          # Script de instalación para entorno local (.venv)
├── setup_windows_gpu.bat   # Script de instalación para Windows con NVIDIA GPU
├── main.py                 # Punto de entrada principal CLI (Inyección de Dependencias)
├── src/                    # Código fuente modular en capas (Larman OOAD)
│   ├── __init__.py
│   ├── config.py           # Configuración de rutas, umbrales y topología COCO
│   ├── domain/             # CAPA DE DOMINIO (Entidades, Objetos de Valor e Interfaces)
│   │   ├── entities.py     # TecnicaMaestra, AnalisisBiomecanico, ReglaBiomecanica
│   │   ├── value_objects.py# Keypoint, Frame, AnguloArticular, ErrorBiomecanico
│   │   ├── interfaces.py   # Contratos abstractos (IPoseExtractor, IStorageProvider...)
│   │   └── services.py     # Servicios de dominio (AngleCalculatorImpl, DTWComparatorImpl...)
│   ├── application/        # CAPA DE APLICACIÓN (Controladores de Casos de Uso)
│   │   ├── pipeline.py     # BiomechanicsPipeline (Larman Controller / Low Coupling)
│   │   └── services.py     # AnalysisAppService (Coordinador de casos de uso y repositorios)
│   ├── infrastructure/     # CAPA DE INFRAESTRUCTURA (Adaptadores y Persistencia)
│   │   ├── adapters/       # YOLOPoseExtractor (Protected Variations / YOLO26-pose)
│   │   ├── storage.py      # LocalStorageProvider, DriveStorageProvider
│   │   └── repositories.py # TecnicaMaestraRepository, AnalisisRepository (Mannino)
│   ├── ui/                 # CAPA DE PRESENTACIÓN (Streamlit)
│   │   └── streamlit_app.py# Interfaz web interactiva con carga de videos y métricas
│   └── utils.py            # Funciones auxiliares y reportes estadísticos
├── tests/                  # Suite de pruebas unitarias (TDD)
│   ├── __init__.py
│   ├── test_domain_entities.py      # Pruebas de objetos de valor y entidades
│   ├── test_repositories.py         # Pruebas de persistencia en repositorios
│   ├── test_application_pipeline.py # Pruebas del controlador con Inyección de Dependencias
│   ├── test_angle_calculator.py     # Pruebas de cálculo cinemático
│   ├── test_dtw_comparator.py       # Pruebas de alineación DTW Sakoe-Chiba
│   └── test_pipeline.py             # Pruebas end-to-end con mocks
├── notebooks/
│   └── colab_demo.ipynb    # Notebook interactivo para Google Colab
├── Videos/                 # Videos Ground Truth de benchmark
│   ├── Maestro.mp4         (1.96 MB, 783 frames)
│   └── Alumno.mp4          (0.72 MB, 276 frames)
└── assets/                 # Logotipos institucionales (UPSA, Corpo & Mente)
```

---

## 🚀 Opciones de Ejecución

### 1. Interfaz Web Reactiva (Streamlit)

```bash
# Activar entorno virtual
source .venv/bin/activate

# Lanzar aplicación web
streamlit run src/ui/streamlit_app.py
```

### 2. Línea de Comandos (CLI)

```bash
# Ejecutar con videos por defecto (Videos/Maestro.mp4 y Videos/Alumno.mp4)
python3 main.py

# O especificando rutas personalizadas:
python3 main.py --maestro Videos/Maestro.mp4 --alumno Videos/Alumno.mp4 --output resultados/
```

### 3. Google Colab (Acelerado con GPU A100 / T4)

1. Abrir [Google Colab](https://colab.research.google.com/).
2. Subir o abrir `notebooks/colab_demo.ipynb`.
3. Seleccionar acelerador por hardware GPU.
4. Ejecutar las celdas secuencialmente para clonar el repositorio, aprovisionar dependencias y ejecutar el análisis.

---

## 🧪 Ejecución de Pruebas Unitarias

```bash
.venv/bin/pytest tests/ -v
```
*(Total: 25 pruebas unitarias automatizadas con 100% de éxito).*

---

## 📝 Documento de Tesis

Para consultar el marco teórico, fundamentación matemática, diagramas de ingeniería (UML, DCD, DDL, SSD) y la memoria académica completa, consulta el archivo [README.md](README.md).
