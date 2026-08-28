"""
Subpaquete de Almacenamiento de Objetos en Nube (Huawei Cloud OBS / Adapter Pattern).
"""

from src.infrastructure.storage.obs_adapter import (
    HuaweiOBSStorageAdapter,
    StorageOperationError,
)

__all__ = [
    "HuaweiOBSStorageAdapter",
    "StorageOperationError",
]
