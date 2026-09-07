from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID


@dataclass(frozen=True)
class BoundingBox:
    """DTO para coordenadas del cuadro delimitador del sujeto detectado (RF-02b)."""
    x1: int
    y1: int
    x2: int
    y2: int
    track_id: int = 1
    confianza: float = 1.0


@dataclass(frozen=True)
class InferenceOutputDTO:
    """DTO estructurado de salida de inferencia del adaptador YOLO26-pose (DCD 5.3.1)."""
    keypoints: List[object]
    bounding_boxes: List[BoundingBox] = field(default_factory=list)
    confianzas: List[float] = field(default_factory=list)
    frames_procesados: int = 0


@dataclass(frozen=True)
class ErrorDTO:
    """DTO para transferencia de errores biomecánicos."""
    articulacion: str
    diferencia: float
    angulo_alumno: float
    angulo_maestro: float
    frame: int
    mensaje: str


@dataclass(frozen=True)
class AnalisisDTO:
    """DTO de diagnóstico final retornado por el controlador del caso de uso (CU-02)."""
    id: UUID
    video_id: UUID
    desviacion_angular_maxima: float
    articulacion_afectada: str
    estado_computo: str
    fotograma_url: Optional[str] = None
    total_errores: int = 0
    errores: List[ErrorDTO] = field(default_factory=list)
