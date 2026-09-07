"""
Capa de Dominio (Domain Layer - Craig Larman OOAD)
Contiene entidades, objetos de valor, interfaces y servicios de dominio.
"""

from .entities import TecnicaMaestra, AnalisisBiomecanico, ReglaBiomecanica, FotogramaAnotado
from .value_objects import Keypoint, Frame, AnguloArticular, ErrorBiomecanico
from .interfaces import (
    IPoseExtractor, IAngleCalculator, IDTWComparator,
    IFrameAnnotator, IStorageProvider
)
from .repositories import TecnicaMaestraRepository, AnalisisRepository
from .services import AngleCalculatorImpl, DTWComparatorImpl, RuleEngine

__all__ = [
    'TecnicaMaestra', 'AnalisisBiomecanico', 'ReglaBiomecanica', 'FotogramaAnotado',
    'Keypoint', 'Frame', 'AnguloArticular', 'ErrorBiomecanico',
    'IPoseExtractor', 'IAngleCalculator', 'IDTWComparator', 'IFrameAnnotator', 'IStorageProvider',
    'TecnicaMaestraRepository', 'AnalisisRepository',
    'AngleCalculatorImpl', 'DTWComparatorImpl', 'RuleEngine'
]
