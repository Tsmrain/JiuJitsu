"""Módulo de infraestructura del sistema."""

from src.infrastructure.interfaces import (
    IAnalisisBiomecanicoRepository,
    IHuaweiOBSStorageAdapter,
    ITecnicaMaestraRepository,
    IVideoEjecucionRepository,
)
from src.infrastructure.storage.obs_adapter import (
    HuaweiOBSStorageAdapter,
    StorageOperationError,
)

__all__ = [
    "IAnalisisBiomecanicoRepository",
    "IHuaweiOBSStorageAdapter",
    "ITecnicaMaestraRepository",
    "IVideoEjecucionRepository",
    "HuaweiOBSStorageAdapter",
    "StorageOperationError",
]
