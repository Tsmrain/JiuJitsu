"""
Capa de Infraestructura y Persistencia (Craig Larman / Adaptadores de Proveedor).
Aísla la interacción con el motor de almacenamiento de objetos (Huawei Cloud OBS) y bases de datos relacionales.
"""

from src.infrastructure.storage.obs_adapter import (
    HuaweiOBSStorageAdapter,
    StorageOperationError,
)

__all__ = [
    "HuaweiOBSStorageAdapter",
    "StorageOperationError",
]
