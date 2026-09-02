"""
Capa de Dominio: Entidades puras, objetos de valor, interfaces y servicios de comparación (OOP).
"""

from .entities import ComparisonResult
from .geometry_utils import GeometryUtils
from .interfaces import (
    IInferenceEngine,
    IPoseEstimator,
    IStorageProvider,
    Keypoint,
    KeypointFrame,
)
from .comparator import BiomechanicsComparator, DEFAULT_ANATOMICAL_TRIPLETS

__all__ = [
    "ComparisonResult",
    "GeometryUtils",
    "BiomechanicsComparator",
    "DEFAULT_ANATOMICAL_TRIPLETS",
    "IStorageProvider",
    "IPoseEstimator",
    "IInferenceEngine",
    "Keypoint",
    "KeypointFrame",
]
