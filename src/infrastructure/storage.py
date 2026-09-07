import os
import cv2
import pandas as pd
import numpy as np
from typing import Any

from ..domain.interfaces import IStorageProvider
from ..config import FOTOGRAMAS_DIR, CSV_DIR, GRAFICAS_DIR, VIDEOS_DIR, PROJECT_ROOT


class LocalStorageProvider(IStorageProvider):
    """
    Proveedor de almacenamiento local en disco (Protected Variations).
    """

    def guardar_imagen(self, imagen: Any, nombre: str) -> str:
        # Si es un gráfico de matplotlib
        if hasattr(imagen, 'savefig'):
            os.makedirs(GRAFICAS_DIR, exist_ok=True)
            ruta = os.path.join(GRAFICAS_DIR, nombre)
            imagen.savefig(ruta, dpi=150, bbox_inches='tight')
            return ruta

        # Si es una matriz de imagen OpenCV
        os.makedirs(FOTOGRAMAS_DIR, exist_ok=True)
        ruta = os.path.join(FOTOGRAMAS_DIR, nombre)
        cv2.imwrite(ruta, imagen, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return ruta

    def guardar_csv(self, data: Any, nombre: str) -> str:
        os.makedirs(CSV_DIR, exist_ok=True)
        ruta = os.path.join(CSV_DIR, nombre)
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            df = pd.DataFrame(data)
        df.to_csv(ruta, index=False)
        return ruta

    def cargar_video(self, nombre: str) -> str:
        # Búsqueda en VIDEOS_DIR o nombre absoluto
        if os.path.isabs(nombre) and os.path.exists(nombre):
            return nombre

        ruta = os.path.join(VIDEOS_DIR, nombre)
        if os.path.exists(ruta):
            return ruta

        # Fallback a búsqueda insensible a mayúsculas
        if os.path.exists(VIDEOS_DIR):
            for f in os.listdir(VIDEOS_DIR):
                if f.lower() == nombre.lower():
                    return os.path.join(VIDEOS_DIR, f)

        raise FileNotFoundError(f"Video no encontrado: {nombre} en {VIDEOS_DIR}")


class DriveStorageProvider(IStorageProvider):
    """
    Proveedor de almacenamiento integrado con Google Drive (Protected Variations).
    """

    def __init__(self, drive_root: str = "/content/drive/MyDrive"):
        self.drive_root = drive_root
        self.project_root = os.path.join(drive_root, "JiuJitsu_Tesis")
        self.fotogramas_dir = os.path.join(self.project_root, "resultados", "fotogramas")
        self.csv_dir = os.path.join(self.project_root, "resultados", "csv")
        self.graficas_dir = os.path.join(self.project_root, "resultados", "graficas")
        self.videos_dir = os.path.join(self.project_root, "videos")
        self._crear_estructura()

    def _crear_estructura(self):
        for d in [self.project_root, self.fotogramas_dir, self.csv_dir, self.graficas_dir, self.videos_dir]:
            os.makedirs(d, exist_ok=True)

    def guardar_imagen(self, imagen: Any, nombre: str) -> str:
        if hasattr(imagen, 'savefig'):
            ruta = os.path.join(self.graficas_dir, nombre)
            imagen.savefig(ruta, dpi=150, bbox_inches='tight')
            return ruta

        ruta = os.path.join(self.fotogramas_dir, nombre)
        cv2.imwrite(ruta, imagen, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return ruta

    def guardar_csv(self, data: Any, nombre: str) -> str:
        ruta = os.path.join(self.csv_dir, nombre)
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        df.to_csv(ruta, index=False)
        return ruta

    def cargar_video(self, nombre: str) -> str:
        ruta = os.path.join(self.videos_dir, nombre)
        if not os.path.exists(ruta):
            # Fallback a VIDEOS_DIR local si existe
            local_fallback = os.path.join(VIDEOS_DIR, nombre)
            if os.path.exists(local_fallback):
                return local_fallback
            raise FileNotFoundError(f"Video no encontrado en Drive: {ruta}")
        return ruta
