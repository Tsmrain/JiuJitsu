import os
import cv2
import pandas as pd
from pathlib import Path
from typing import Any

from ..domain.interfaces import IStorageProvider
from ..config import UPLOAD_FOLDER, RESULTS_DIR, VIDEOS_DIR, FOTOGRAMAS_DIR, CSV_DIR, GRAFICAS_DIR


class LocalStorageAdapter(IStorageProvider):
    """Adaptador GoF para almacenamiento local (Edge)."""

    def __init__(self):
        self.upload_dir = Path(UPLOAD_FOLDER)
        self.results_dir = Path(RESULTS_DIR)

    def guardar_video_subido(self, file_name: str, file_bytes: bytes) -> str:
        """Guarda un video cargado por el usuario en uploads/."""
        file_path = self.upload_dir / file_name
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        return str(file_path)

    def guardar_fotograma(self, file_name: str, file_bytes: bytes) -> str:
        """Guarda un fotograma binario en resultados/fotogramas/."""
        dest_dir = self.results_dir / 'fotogramas'
        dest_dir.mkdir(parents=True, exist_ok=True)
        file_path = dest_dir / file_name
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        return str(file_path)

    def obtener_ruta_video(self, file_name: str) -> str:
        """Retorna la ruta absoluta de un video en uploads/."""
        return str(self.upload_dir / file_name)

    def eliminar_archivo(self, file_path: str):
        """Elimina un archivo del sistema de archivos local."""
        path = Path(file_path)
        if path.exists():
            path.unlink()

    # -------------------------------------------------------------------------
    # Implementación de IStorageProvider para Pipeline y OpenCV / Matplotlib
    # -------------------------------------------------------------------------
    def guardar_imagen(self, imagen: Any, nombre: str) -> str:
        """Persiste una imagen anotada (OpenCV) o gráfico (Matplotlib)."""
        if hasattr(imagen, 'savefig'):
            dest_dir = self.results_dir / 'graficas'
            dest_dir.mkdir(parents=True, exist_ok=True)
            ruta = dest_dir / nombre
            imagen.savefig(str(ruta), dpi=150, bbox_inches='tight')
            return str(ruta)

        dest_dir = self.results_dir / 'fotogramas'
        dest_dir.mkdir(parents=True, exist_ok=True)
        ruta = dest_dir / nombre
        cv2.imwrite(str(ruta), imagen, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return str(ruta)

    def guardar_csv(self, data: Any, nombre: str) -> str:
        """Persiste datos cinemáticos tabulares en resultados/csv/."""
        dest_dir = self.results_dir / 'csv'
        dest_dir.mkdir(parents=True, exist_ok=True)
        ruta = dest_dir / nombre
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        df.to_csv(str(ruta), index=False)
        return str(ruta)

    def cargar_video(self, nombre: str) -> str:
        """Busca y retorna la ruta del video en uploads, Videos o ruta absoluta."""
        p = Path(nombre)
        if p.is_absolute() and p.exists():
            return str(p)

        # 1. Buscar en UPLOAD_FOLDER
        cand_upload = self.upload_dir / nombre
        if cand_upload.exists():
            return str(cand_upload)

        # 2. Buscar en VIDEOS_DIR
        cand_videos = Path(VIDEOS_DIR) / nombre
        if cand_videos.exists():
            return str(cand_videos)

        # 3. Fallback insensible a mayúsculas
        for search_dir in [self.upload_dir, Path(VIDEOS_DIR)]:
            if search_dir.exists():
                for f in search_dir.iterdir():
                    if f.name.lower() == nombre.lower():
                        return str(f)

        raise FileNotFoundError(f"Video no encontrado: '{nombre}' en {self.upload_dir} ni {VIDEOS_DIR}")


# Alias de compatibilidad
LocalStorageProvider = LocalStorageAdapter


class DriveStorageProvider(IStorageProvider):
    """Proveedor de almacenamiento integrado con Google Drive (Protected Variations)."""

    def __init__(self, drive_root: str = "/content/drive/MyDrive"):
        self.drive_root = Path(drive_root)
        self.project_root = self.drive_root / "JiuJitsu_Tesis"
        self.fotogramas_dir = self.project_root / "resultados" / "fotogramas"
        self.csv_dir = self.project_root / "resultados" / "csv"
        self.graficas_dir = self.project_root / "resultados" / "graficas"
        self.videos_dir = self.project_root / "videos"
        self._crear_estructura()

    def _crear_estructura(self):
        for d in [self.project_root, self.fotogramas_dir, self.csv_dir, self.graficas_dir, self.videos_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def guardar_imagen(self, imagen: Any, nombre: str) -> str:
        if hasattr(imagen, 'savefig'):
            ruta = self.graficas_dir / nombre
            imagen.savefig(str(ruta), dpi=150, bbox_inches='tight')
            return str(ruta)

        ruta = self.fotogramas_dir / nombre
        cv2.imwrite(str(ruta), imagen, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return str(ruta)

    def guardar_csv(self, data: Any, nombre: str) -> str:
        ruta = self.csv_dir / nombre
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        df.to_csv(str(ruta), index=False)
        return str(ruta)

    def cargar_video(self, nombre: str) -> str:
        ruta = self.videos_dir / nombre
        if not ruta.exists():
            local_fallback = Path(VIDEOS_DIR) / nombre
            if local_fallback.exists():
                return str(local_fallback)
            raise FileNotFoundError(f"Video no encontrado en Drive: {ruta}")
        return str(ruta)
