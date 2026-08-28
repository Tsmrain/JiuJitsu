"""
Capa de Servicios del Dominio (Craig Larman / Motores Algorítmicos).
Expone los componentes de procesamiento cinemático y biomecánico.
"""

from src.services.dtw_comparator import DTWComparator
from src.services.kalman_filter import (
    KalmanFilterTracker,
    KalmanTracker,
    OclusionProlongadaError,
)

__all__ = [
    "KalmanTracker",
    "KalmanFilterTracker",
    "OclusionProlongadaError",
    "DTWComparator",
]
