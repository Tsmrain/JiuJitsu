import os
from pathlib import Path

# =============================================================================
# Raíz del proyecto y detección de Colab
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
IS_COLAB = 'COLAB_GPU' in os.environ or 'COLAB_TPU_ADDR' in os.environ or os.path.exists('/content')

UPLOAD_FOLDER = PROJECT_ROOT / 'uploads'
DATA_DIR = PROJECT_ROOT / 'data'
RESULTS_DIR = PROJECT_ROOT / 'resultados'
DB_PATH = DATA_DIR / 'bjj_analysis.db'

# Modelos y Videos
MODELS_DIR = PROJECT_ROOT / 'modelos'
MODELOS_DIR = MODELS_DIR
VIDEOS_DIR = PROJECT_ROOT / 'Videos'

# Compatibilidad con módulos existentes
RESULTADOS_DIR = RESULTS_DIR
FOTOGRAMAS_DIR = RESULTS_DIR / 'fotogramas'
CSV_DIR = RESULTS_DIR / 'csv'
GRAFICAS_DIR = RESULTS_DIR / 'graficas'

# =============================================================================
# INICIALIZACIÓN DE DIRECTORIOS (IDEMPOTENTE)
# =============================================================================
for directory in [UPLOAD_FOLDER, DATA_DIR, MODELS_DIR, VIDEOS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

for sub_dir in ['fotogramas', 'graficas', 'csv']:
    (RESULTS_DIR / sub_dir).mkdir(parents=True, exist_ok=True)

# =============================================================================
# PARÁMETROS CINEMÁTICOS Y MODELO DE IA
# =============================================================================
MODELO_YOLO = "yolo26n-pose.pt"  # O yolo26x-pose.pt en A100 Colab
UMBRAL_ERROR = 15.0              # Tolerancia angular en grados (RF-01)
VENTANA_DTW = 0.15               # 15% de la longitud de la serie (Sakoe-Chiba, RF-03)

# Articulaciones y Mapeo COCO estándar (17 keypoints)
ARTICULACIONES = ['codo_izq', 'codo_der', 'rodilla_izq', 'rodilla_der', 'cadera', 'hombro']

INDICES_COCO = {
    'codo_izq': 7,
    'codo_der': 8,
    'rodilla_izq': 13,
    'rodilla_der': 14,
    'cadera': 12,
    'hombro': 5
}
