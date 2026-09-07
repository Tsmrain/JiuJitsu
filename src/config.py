import os

# =============================================
# CONFIGURACIÓN DE RUTAS
# =============================================

# Detectar si estamos en Google Colab
IS_COLAB = 'COLAB_GPU' in os.environ or 'COLAB_TPU_ADDR' in os.environ or os.path.exists('/content')

if IS_COLAB:
    # En Colab, preferir Drive si existe, o el directorio clonado en /content
    DRIVE_ROOT = "/content/drive/MyDrive"
    DRIVE_PROJECT = os.path.join(DRIVE_ROOT, "JiuJitsu_Tesis")
    if os.path.exists(DRIVE_PROJECT):
        PROJECT_ROOT = DRIVE_PROJECT
    elif os.path.exists("/content/JiuJitsu"):
        PROJECT_ROOT = "/content/JiuJitsu"
    else:
        PROJECT_ROOT = os.getcwd()
else:
    # En local, usar directorio raíz del proyecto
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Subdirectorios
if os.path.exists(os.path.join(PROJECT_ROOT, "Videos")):
    VIDEOS_DIR = os.path.join(PROJECT_ROOT, "Videos")
else:
    VIDEOS_DIR = os.path.join(PROJECT_ROOT, "videos")

RESULTADOS_DIR = os.path.join(PROJECT_ROOT, "resultados")
FOTOGRAMAS_DIR = os.path.join(RESULTADOS_DIR, "fotogramas")
CSV_DIR = os.path.join(RESULTADOS_DIR, "csv")
GRAFICAS_DIR = os.path.join(RESULTADOS_DIR, "graficas")
MODELOS_DIR = os.path.join(PROJECT_ROOT, "modelos")

# Crear directorios si no existen
for d in [VIDEOS_DIR, RESULTADOS_DIR, FOTOGRAMAS_DIR, CSV_DIR, GRAFICAS_DIR, MODELOS_DIR]:
    os.makedirs(d, exist_ok=True)

# =============================================
# CONFIGURACIÓN DE MODELO
# =============================================

MODELO_YOLO = "yolo26n-pose.pt"  # Puede actualizarse a "yolo26x-pose.pt" en GPUs de alta gama
UMBRAL_ERROR = 15.0              # Grados de tolerancia angular (RF-01)
VENTANA_DTW = 0.15               # 15% de la longitud de la serie (Sakoe-Chiba, RF-03)

# =============================================
# ARTICULACIONES Y MAPEO COCO (17 Keypoints)
# =============================================

ARTICULACIONES = ['codo_izq', 'codo_der', 'rodilla_izq', 'rodilla_der', 'cadera', 'hombro']

# Mapeo de articulación a índice COCO representativo (0-16)
INDICES_COCO = {
    'codo_izq': 7,
    'codo_der': 8,
    'rodilla_izq': 13,
    'rodilla_der': 14,
    'cadera': 12,
    'hombro': 5
}
