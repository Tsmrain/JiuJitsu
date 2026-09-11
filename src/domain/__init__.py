"""Capa de Dominio Puro (Domain Layer).

Implementa entidades de dominio y objetos de valor desacoplados de infraestructura,
siguiendo los patrones GRASP de Craig Larman y las pautas de modelado de datos de Mannino.
"""

from src.domain.models import (
    Punto3D,
    MatrizEsqueletica,
    DesviacionArticular,
    CalculadoraBiomecanica,
)
from src.domain.interfaces import (
    IInferenceEngine,
    IGenerationService,
    IEmbeddingService,
    ITecnicaRepository,
)

__all__ = [
    "Punto3D",
    "MatrizEsqueletica",
    "DesviacionArticular",
    "CalculadoraBiomecanica",
    "IInferenceEngine",
    "IGenerationService",
    "IEmbeddingService",
    "ITecnicaRepository",
]

