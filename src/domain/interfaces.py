"""
Interfaces y contratos base del dominio biomecánico.

Aplica el patrón GRASP Protected Variations (Craig Larman) para desacoplar
las entidades del dominio y los casos de uso de la infraestructura externa
(sistemas de archivos locales, almacenamiento en la nube Huawei OBS y
motores de inferencia RTMPose3D / ONNX / PyTorch).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Any, Optional


@dataclass
class Keypoint:
    """Representación canónica de un punto anatómico o landmark en el espacio."""
    x: float
    y: float
    z: float = 0.0
    score: float = 1.0
    name: str = ""


@dataclass
class KeypointFrame:
    """Estructura de landmarks detectados en un fotograma temporal individual."""
    frame_idx: int
    timestamp_ms: float = 0.0
    keypoints: List[Keypoint] = field(default_factory=list)

    @property
    def keypoints_3d(self) -> Any:
        """Matriz o lista de coordenadas [num_keypoints, 3]."""
        coords = [[kp.x, kp.y, kp.z] for kp in self.keypoints]
        try:
            import numpy as np
            return np.array(coords, dtype=float)
        except ImportError:
            return coords

    @property
    def keypoints_2d(self) -> Any:
        """Matriz o lista de coordenadas [num_keypoints, 2]."""
        coords = [[kp.x, kp.y] for kp in self.keypoints]
        try:
            import numpy as np
            return np.array(coords, dtype=float)
        except ImportError:
            return coords

    @property
    def scores(self) -> Any:
        """Vector o lista de confidencias de detección [num_keypoints]."""
        vals = [kp.score for kp in self.keypoints]
        try:
            import numpy as np
            return np.array(vals, dtype=float)
        except ImportError:
            return vals


class IStorageProvider(ABC):
    """
    Interfaz de abstracción de almacenamiento de archivos y videos.
    Permite alternar entre LocalStorageProvider (Fase 1: Local/Colab)
    y HuaweiOBSProvider (Fase 2: Despliegue en Nube) sin modificar el dominio.
    """

    @abstractmethod
    def upload_video(self, source_path: str, destination_name: str) -> str:
        """
        Guarda o sube un archivo de video al proveedor de almacenamiento.

        Args:
            source_path: Ruta local del archivo de video original.
            destination_name: Nombre o clave de destino en el almacenamiento.

        Returns:
            Ruta persistida, identificador o URI accesible del video en el almacenamiento.
        """
        pass

    @abstractmethod
    def download_video(self, storage_path: str, target_local_path: str) -> str:
        """
        Descarga o recupera un archivo de video desde el almacenamiento.

        Args:
            storage_path: Ruta o identificador del archivo en el almacenamiento.
            target_local_path: Ruta local donde se guardará el archivo descargado.

        Returns:
            Ruta absoluta del archivo recuperado localmente.
        """
        pass

    @abstractmethod
    def get_frame(self, video_path: str, frame_idx: int) -> Any:
        """
        Extrae un fotograma específico de un video por su índice.

        Args:
            video_path: Ruta del video (local o en almacenamiento).
            frame_idx: Índice del fotograma a extraer (0-indexed).

        Returns:
            Matriz de imagen / datos del fotograma.
        """
        pass


class IPoseEstimator(ABC):
    """
    Interfaz de abstracción para motores de estimación de poses articulares 2D/3D (RTMPose3D).
    """

    @abstractmethod
    def extract_keypoints(self, video_path: str) -> List[KeypointFrame]:
        """
        Extrae la secuencia temporal de coordenadas articulares a partir de un video.

        Args:
            video_path: Ruta del video a procesar.

        Returns:
            Lista ordenada de fotogramas con sus respectivos landmarks anatómicos.
        """
        pass


class IInferenceEngine(IPoseEstimator, ABC):
    """
    Alias / Especialización de interfaz para motores de inferencia biomecánica,
    conforme a las directrices de Protected Variations (Larman).
    """
    pass
