import os
import pandas as pd
from .config import CSV_DIR


class CSVExporter:
    """
    Exportación de resultados biomecánicos a archivos estructurados CSV (RF-14)
    para análisis estadístico y trazabilidad de progresión.
    """

    @staticmethod
    def exportar_angulos(angulos, nombre):
        """
        Exporta la serie temporal de ángulos articulares a CSV.
        """
        os.makedirs(CSV_DIR, exist_ok=True)
        df = pd.DataFrame(angulos)
        ruta = os.path.join(CSV_DIR, nombre)
        df.to_csv(ruta, index=False)
        return ruta

    @staticmethod
    def exportar_similitud(similitud, nombre):
        """
        Exporta la curva de similitud angular por frame a CSV.
        """
        os.makedirs(CSV_DIR, exist_ok=True)
        df = pd.DataFrame({
            'frame': range(len(similitud)),
            'similitud_angular': similitud
        })
        ruta = os.path.join(CSV_DIR, nombre)
        df.to_csv(ruta, index=False)
        return ruta
