"""
Capa de Infraestructura (Infrastructure Layer) - JiuJitsu Biomechanics
Implementa adaptadores de hardware/IA, proveedores de almacenamiento y repositorios.
"""

from .storage import LocalStorageProvider, DriveStorageProvider
from .repositories import TecnicaMaestraRepository, AnalisisRepository
from .adapters.yolo_adapter import YOLOPoseExtractor

__all__ = [
    'LocalStorageProvider', 'DriveStorageProvider',
    'TecnicaMaestraRepository', 'AnalisisRepository',
    'YOLOPoseExtractor'
]
