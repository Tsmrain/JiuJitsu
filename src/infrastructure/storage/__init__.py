"""Módulo de almacenamiento de infraestructura (Huawei OBS)."""

from src.infrastructure.storage.obs_adapter import (
    HuaweiOBSStorageAdapter,
    StorageOperationError,
)

__all__ = [
    "HuaweiOBSStorageAdapter",
    "StorageOperationError",
]
