from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Any, Dict
import numpy as np


class IPoseExtractor(ABC):
    """Interfaz para extractores de pose (Protected Variations / GoF Adapter)."""

    @abstractmethod
    def extraer_keypoints(self, video_path: str) -> Tuple[np.ndarray, List[np.ndarray]]:
        """Extrae keypoints [N, 17, 2] y fotogramas leídos de un video."""
        pass

    @abstractmethod
    def get_dispositivo(self) -> str:
        """Retorna el dispositivo de hardware asignado para inferencia (CPU / GPU)."""
        pass


class IAngleCalculator(ABC):
    """Interfaz para calculadores de ángulos cinemáticos (Information Expert)."""

    @abstractmethod
    def calcular_angulo(self, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        """Calcula el ángulo en grados entre tres puntos coordenados."""
        pass

    @abstractmethod
    def extraer_angulos(self, keypoints: np.ndarray) -> Dict[str, float]:
        """Extrae los ángulos cinemáticos de un fotograma individual."""
        pass


class IDTWComparator(ABC):
    """Interfaz para comparadores de series temporales (Pure Fabrication)."""

    @abstractmethod
    def comparar(self, serie_a: List[float], serie_b: List[float]) -> Tuple[float, List[Tuple[int, int]]]:
        """Compara dos series temporales retornando distancia DTW y camino de alineación."""
        pass

    @abstractmethod
    def comparar_articulacion(
        self, angulos_maestro: List[dict], angulos_alumno: List[dict], articulacion: str
    ) -> Tuple[Optional[float], Optional[List[Tuple[int, int]]], List[float], List[float]]:
        """Extrae y compara las series de una articulación específica."""
        pass


class IFrameAnnotator(ABC):
    """Interfaz para anotadores de fotogramas (Pure Fabrication)."""

    @abstractmethod
    def anotar_error(
        self, frame: np.ndarray, keypoints: np.ndarray,
        articulacion: str, error: float, frame_idx: int
    ) -> np.ndarray:
        """Anota un fotograma inyectando indicadores gráficos de error."""
        pass


class IStorageProvider(ABC):
    """Interfaz para proveedores de almacenamiento (Protected Variations)."""

    @abstractmethod
    def guardar_imagen(self, imagen: Any, nombre: str) -> str:
        """Persiste una imagen o figura y retorna su ruta o URL."""
        pass

    @abstractmethod
    def guardar_csv(self, data: Any, nombre: str) -> str:
        """Persiste datos estructurados en formato CSV y retorna la ruta."""
        pass

    @abstractmethod
    def cargar_video(self, nombre: str) -> str:
        """Localiza y retorna la ruta absoluta de un archivo de video."""
        pass
