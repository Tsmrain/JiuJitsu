"""
Capa de Dominio (Domain Layer) - JiuJitsu Biomechanics
Contiene objetos de valor, entidades del negocio y contratos (interfaces).
"""

from .value_objects import Keypoint, Frame, AnguloArticular, ErrorBiomecanico
from .entities import TecnicaMaestra, ReglaBiomecanica, AnalisisBiomecanico, FotogramaAnotado
from .interfaces import (
    IPoseExtractor, IAngleCalculator, IDTWComparator,
    IFrameAnnotator, IStorageProvider
)

__all__ = [
    'Keypoint', 'Frame', 'AnguloArticular', 'ErrorBiomecanico',
    'TecnicaMaestra', 'ReglaBiomecanica', 'AnalisisBiomecanico', 'FotogramaAnotado',
    'IPoseExtractor', 'IAngleCalculator', 'IDTWComparator',
    'IFrameAnnotator', 'IStorageProvider'
]
