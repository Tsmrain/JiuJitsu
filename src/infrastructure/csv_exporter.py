import os
import pandas as pd
from typing import Any

from ..config import CSV_DIR


class CSVExporter:
    """
    Servicio de infraestructura para exportación tabular a archivos CSV (RF-14 - Pure Fabrication).
    """

    @staticmethod
    def exportar_angulos(angulos: Any, nombre: str) -> str:
        """Exporta serie temporal de ángulos articulares a CSV."""
        os.makedirs(CSV_DIR, exist_ok=True)
        df = angulos if isinstance(angulos, pd.DataFrame) else pd.DataFrame(angulos)
        ruta = os.path.join(CSV_DIR, nombre)
        df.to_csv(ruta, index=False)
        return ruta

    @staticmethod
    def exportar_similitud(similitud: Any, nombre: str) -> str:
        """Exporta serie de similitud por frame a CSV."""
        os.makedirs(CSV_DIR, exist_ok=True)
        df = pd.DataFrame({
            'frame': range(len(similitud)),
            'similitud_angular': similitud
        })
        ruta = os.path.join(CSV_DIR, nombre)
        df.to_csv(ruta, index=False)
        return ruta
