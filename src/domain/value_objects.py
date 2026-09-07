from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass(frozen=True)
class Keypoint:
    """Punto clave con coordenadas (x, y, confianza)."""
    x: float
    y: float
    confianza: float = 1.0

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y], dtype=np.float64)


@dataclass(frozen=True)
class Frame:
    """Fotograma con su colección inmutable de keypoints."""
    index: int
    keypoints: List[Keypoint]
    image: Optional[np.ndarray] = field(default=None, compare=False, hash=False)

    def get_keypoint_by_index(self, idx: int) -> Optional[Keypoint]:
        if 0 <= idx < len(self.keypoints):
            return self.keypoints[idx]
        return None


@dataclass(frozen=True)
class AnguloArticular:
    """Ángulo articular relativo en grados."""
    articulacion: str
    valor: float
    frame: int

    def es_valido(self, min_val: float = 0.0, max_val: float = 180.0) -> bool:
        return min_val <= self.valor <= max_val

    def diferencia(self, otro: 'AnguloArticular') -> float:
        return abs(self.valor - otro.valor)


@dataclass(frozen=True)
class ErrorBiomecanico:
    """Error biomecánico detectado entre la ejecución del alumno y el patrón del maestro."""
    articulacion: str
    angulo_alumno: float
    angulo_maestro: float
    diferencia: float
    frame: int
    mensaje: str = ""

    def es_critico(self, umbral: float = 15.0) -> bool:
        return self.diferencia > umbral
