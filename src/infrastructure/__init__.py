"""
Capa de Infraestructura (Infrastructure Layer - Craig Larman OOAD)
Implementa adaptadores para visión artificial, persistencia y almacenamiento.
"""

from .adapters.yolo_adapter import YOLOPoseExtractor
from .storage import LocalStorageProvider, DriveStorageProvider
from .frame_annotator import FrameAnnotatorImpl
from .csv_exporter import CSVExporter
from .repositories import TecnicaMaestraRepository, AnalisisRepository

__all__ = [
    'YOLOPoseExtractor',
    'LocalStorageProvider', 'DriveStorageProvider',
    'FrameAnnotatorImpl',
    'CSVExporter',
    'TecnicaMaestraRepository', 'AnalisisRepository'
]
