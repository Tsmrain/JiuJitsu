"""
Módulo de inferencia y visión artificial.
Contiene la detección de hardware y adaptadores de modelos de estimación de pose 3D.
"""

from .hardware_detector import get_device
from .rtmpose3d_adapter import RTMPose3DAdapter

__all__ = [
    "get_device",
    "RTMPose3DAdapter",
]
