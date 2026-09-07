"""
Capa de Aplicación (Application Layer - Craig Larman OOAD)
Contiene controladores de caso de uso (Controllers) y Data Transfer Objects (DTOs).
"""

from .pipeline import BiomechanicsPipeline
from .dto import AnalisisDTO, ErrorDTO, InferenceOutputDTO, BoundingBox

__all__ = [
    'BiomechanicsPipeline',
    'AnalisisDTO',
    'ErrorDTO',
    'InferenceOutputDTO',
    'BoundingBox'
]
