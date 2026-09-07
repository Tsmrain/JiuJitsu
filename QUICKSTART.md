# JiuJitsu Tesis - Sistema Híbrido de Análisis Biomecánico BJJ (Edge-Colab)

Sistema para comparar movimientos de Jiu-Jitsu Brasileño entre maestro y alumno usando Visión por Computadora (YOLO26-pose, normalización cinemática y DTW con restricción de Sakoe-Chiba) bajo una arquitectura híbrida **Edge-Colab** con persistencia relacional en **SQLite3** (Mannino).

Implementado bajo la **Arquitectura en Capas de Craig Larman** y patrones de asignación de responsabilidades **GRASP / GoF**.

---

## 🏛️ Arquitectura en Capas y Estructura del Repositorio

```
JiuJitsu/
├── README.md               # Documento Formal de Tesis (Capítulos I a X, Arquitectura Edge-Colab)
├── QUICKSTART.md           # Guía rápida de ejecución y despliegue
├── requirements.txt        # Dependencias oficiales del sistema (Edge-Colab)
├── setup_local.sh          # Script de instalación automatizada local (.venv + SQLite)
├── pytest.ini              # Configuración de pruebas automatizadas y markers
├── main.py                 # Punto de entrada principal CLI (Inyección de Dependencias)
├── src/                    # Código fuente modular en capas (Larman OOAD)
│   ├── config.py           # Configuración de rutas locales, umbrales y topología COCO
│   ├── utils.py            # Funciones auxiliares y reportes estadísticos
│   ├── domain/             # CAPA DE DOMINIO (Entidades, Objetos de Valor e Interfaces)
│   │   ├── entities.py     # TecnicaMaestra, AnalisisBiomecanico, ReglaBiomecanica
│   │   ├── value_objects.py# Keypoint, Frame, AnguloArticular, ErrorBiomecanico
│   │   ├── interfaces.py   # Contratos abstractos (IPoseExtractor, IStorageProvider...)
│   │   ├── repositories.py # Interfaces de repositorios (Mannino)
│   │   └── services/       # SERVICIOS DE DOMINIO (Information Expert / Pure Fabrication)
│   │       ├── angle_calculator.py # Cálculo cinemático de ángulos articulares
│   │       ├── dtw_comparator.py   # DTW con ventana Sakoe-Chiba O(N)
│   │       └── rule_engine.py      # Motor de evaluación determinista de reglas (RF-10)
│   ├── application/        # CAPA DE APLICACIÓN (Controladores de Casos de Uso)
│   │   ├── pipeline.py     # BiomechanicsPipeline (Larman Controller / Low Coupling)
│   │   ├── dto.py          # Data Transfer Objects (AnalisisDTO, ErrorDTO...)
│   │   └── services.py     # Coordinador de casos de uso de alto nivel
│   ├── infrastructure/     # CAPA DE INFRAESTRUCTURA (Adaptadores y Persistencia)
│   │   ├── adapters/       # YOLOPoseExtractor (Protected Variations / YOLO26-pose)
│   │   ├── storage.py      # LocalStorageAdapter (uploads/ & resultados/)
│   │   ├── repositories.py # SQLiteDB, TecnicaMaestraRepository, AnalisisRepository (Mannino)
│   │   ├── frame_annotator.py # Anotador gráfico de fotogramas con OpenCV
│   │   └── csv_exporter.py    # Exportador de series cinemáticas a CSV
│   └── ui/                 # CAPA DE PRESENTACIÓN (Streamlit)
│       └── streamlit_app.py# Interfaz web interactiva (Modos: Local, Colab JSON, SQLite)
├── tests/                  # Suite de pruebas automatizadas bajo disciplina TDD
│   ├── unit/               # Pruebas unitarias de dominio, cinemática y repositorios SQLite
│   ├── integration/        # Pruebas de integración del controlador (con Mocks)
│   └── real/               # Pruebas con modelo real en Colab GPU (@pytest.mark.real_model)
├── notebooks/
│   └── jiujiutsu_ai_engine.ipynb # Cuaderno oficial de Google Colab (GPU A100 / T4)
├── uploads/                # Directorio de videos MP4 cargados localmente
├── data/
│   └── bjj_analysis.db     # Base de datos relacional SQLite (Mannino)
├── resultados/             # Entregables visuales y datos tabulares
│   ├── fotogramas/         # Fotogramas clave anotados con OpenCV
│   ├── graficas/           # Curvas temporales de evolución cinemática
│   └── csv/                # Tablas de discrepancias articulares
└── Videos/                 # Videos de referencia canónica (Ground Truth)
    ├── Maestro.mp4         (1.96 MB, 783 frames)
    └── Alumno.mp4          (0.72 MB, 276 frames)
```

---

## 🚀 Opciones de Ejecución

### 1. Inicialización y Despliegue Local Automatizado

```bash
# Ejecutar script de aprovisionamiento
bash setup_local.sh
pip install -r requirements.txt

# Activar entorno virtual
source .venv/bin/activate

# Iniciar servidor interactivo de Streamlit
streamlit run src/ui/streamlit_app.py
```
La aplicación web estará disponible en `http://localhost:8501`.

### 2. Flujo Híbrido con Google Colab (Cerebro IA)

1. Abrir `notebooks/jiujiutsu_ai_engine.ipynb` en [Google Colab](https://colab.research.google.com/).
2. Activar entorno de ejecución con acelerador GPU (NVIDIA A100 o T4).
3. Cargar los videos `Maestro.mp4` y `Alumno.mp4` y ejecutar las celdas de inferencia.
4. Descargar el archivo `colab_analysis_results.json` generado.
5. En la interfaz local de Streamlit, seleccionar la pestaña **"Importar Resultados de Google Colab"** y cargar el JSON para visualizar fotogramas anotados y persistir en SQLite.

### 3. Línea de Comandos (CLI Local)

```bash
# Ejecutar con videos por defecto (Videos/Maestro.mp4 y Videos/Alumno.mp4)
python3 main.py

# O especificando rutas personalizadas:
python3 main.py --maestro Videos/Maestro.mp4 --alumno Videos/Alumno.mp4 --output resultados/
```

---

## 🧪 Validación de la Suite de Pruebas (TDD)

```bash
# Ejecutar pruebas unitarias y de integración locales
.venv/bin/pytest tests/ -v -m "not real_model"

# Ejecutar pruebas sobre modelo real (requiere GPU y pesos de YOLO)
.venv/bin/pytest -m real_model -v
```

---

## 📝 Documento de Tesis

Para consultar el marco teórico, fundamentación matemática, diagramas de ingeniería (UML, DCD, DDL, SSD) y la memoria académica completa, consulta el archivo [README.md](README.md).
