"""
Adaptador de almacenamiento local para Fase 1 (Validación Local / Google Colab).

Implementa la interfaz IStorageProvider utilizando el sistema de archivos local,
aislando el dominio del mecanismo de persistencia físico según el patrón
GRASP Protected Variations (Craig Larman).
"""

import os
import shutil
from pathlib import Path
from typing import Any, Optional

from src.domain.interfaces import IStorageProvider


class LocalStorageAdapter(IStorageProvider):
    """
    Adaptador de almacenamiento en disco local.
    Gestiona la subida, descarga y acceso a cuadros de videos en el sistema de archivos.
    """

    def __init__(self, base_directory: str = "storage_local"):
        """
        Inicializa el adaptador de almacenamiento local.

        Args:
            base_directory: Directorio raíz donde se almacenarán los archivos gestionados.
        """
        self.base_path = Path(base_directory).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_storage_path(self, storage_path: str) -> Path:
        """
        Resuelve una ruta de almacenamiento a una ruta absoluta válida dentro del directorio base.
        """
        candidate = Path(storage_path)
        if candidate.is_absolute() and candidate.exists():
            return candidate
        
        # Intentar ruta relativa a base_path
        relative_candidate = self.base_path / storage_path
        if relative_candidate.exists():
            return relative_candidate
            
        # Si no existe, retornar la ruta esperada dentro del base_path
        return relative_candidate

    def upload_video(self, source_path: str, destination_name: str) -> str:
        """
        Almacena una copia del video en el directorio de almacenamiento local.

        Args:
            source_path: Ruta local del video original.
            destination_name: Nombre relativo o identificador de destino.

        Returns:
            Ruta absoluta normalizada del video almacenado.

        Raises:
            FileNotFoundError: Si el archivo origen no existe en el sistema.
        """
        src = Path(source_path).resolve()
        if not src.is_file():
            raise FileNotFoundError(f"El archivo origen no existe: {source_path}")

        dest = self.base_path / destination_name
        dest.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, dest)
        return str(dest)

    def download_video(self, storage_path: str, target_local_path: str) -> str:
        """
        Recupera un video desde el almacenamiento local hacia una ruta de destino.

        Args:
            storage_path: Ruta del archivo en el almacenamiento.
            target_local_path: Ruta de destino donde se copiará el archivo.

        Returns:
            Ruta absoluta normalizada del archivo descargado.

        Raises:
            FileNotFoundError: Si el archivo no existe en el almacenamiento.
        """
        resolved_src = self._resolve_storage_path(storage_path)
        if not resolved_src.is_file():
            raise FileNotFoundError(f"El archivo en almacenamiento no fue encontrado: {storage_path}")

        target = Path(target_local_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(resolved_src, target)
        return str(target)

    def get_frame(self, video_path: str, frame_idx: int) -> Any:
        """
        Extrae un fotograma específico del video.

        Args:
            video_path: Ruta del video a examinar.
            frame_idx: Índice del fotograma (0-indexed).

        Returns:
            Matriz de imagen del fotograma o contenido binario.

        Raises:
            FileNotFoundError: Si el video no existe.
            IndexError: Si el índice del fotograma no es válido o no se puede leer.
        """
        resolved_path = self._resolve_storage_path(video_path)
        if not resolved_path.is_file():
            raise FileNotFoundError(f"El archivo de video no existe: {video_path}")

        try:
            import cv2
            cap = cv2.VideoCapture(str(resolved_path))
            if not cap.isOpened():
                raise ValueError(f"No se pudo abrir el archivo de video con OpenCV: {resolved_path}")

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                raise IndexError(f"No se pudo leer el frame en el índice {frame_idx} del video {resolved_path}")

            return frame
        except ImportError:
            # Fallback en entornos ligeros sin OpenCV instalado: lectura binaria
            with open(resolved_path, "rb") as f:
                data = f.read()
            return data
