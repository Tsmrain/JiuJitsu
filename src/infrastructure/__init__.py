"""
Capa de Infraestructura: Adaptadores para almacenamiento, cómputo cloud y visión artificial.
"""

from .storage.local_storage_adapter import LocalStorageAdapter
from .inference.hardware_detector import get_device
from .inference.rtmpose3d_adapter import RTMPose3DAdapter
from .vision.frame_annotator import FrameAnnotator

__all__ = [
    "LocalStorageAdapter",
    "get_device",
    "RTMPose3DAdapter",
    "FrameAnnotator",
]
