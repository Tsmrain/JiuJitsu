import os
import sys
import numpy as np

from .config import VIDEOS_DIR
from .pipeline import BiomechanicsPipeline
from .utils import verificar_videos, formatear_resumen


def main():
    """
    Punto de entrada principal para ejecución local o en Google Colab.
    """
    ruta_maestro, ruta_alumno = verificar_videos(VIDEOS_DIR)

    if not os.path.exists(ruta_maestro):
        print(f"❌ Error: No se encontró el video del maestro en: {ruta_maestro}")
        print(f"   Asegúrate de colocar 'Maestro.mp4' en el directorio '{VIDEOS_DIR}'.")
        sys.exit(1)

    if not os.path.exists(ruta_alumno):
        print(f"❌ Error: No se encontró el video del alumno en: {ruta_alumno}")
        print(f"   Asegúrate de colocar 'Alumno.mp4' en el directorio '{VIDEOS_DIR}'.")
        sys.exit(1)

    print("🚀 Iniciando Pipeline Biomecánico...")
    print(f"   Video Maestro: {ruta_maestro}")
    print(f"   Video Alumno:  {ruta_alumno}")

    pipeline = BiomechanicsPipeline()
    resultados = pipeline.ejecutar(ruta_maestro, ruta_alumno)

    print("\n" + formatear_resumen(resultados))
    return resultados


if __name__ == "__main__":
    main()
