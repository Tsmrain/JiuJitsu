from dataclasses import dataclass, field
from typing import List
from uuid import UUID

@dataclass
class ReglaBiomecanica:
    """Entidad que modela el catálogo de errores deterministas (RF-10)."""
    id: UUID
    articulacion_clave: str
    umbral_angular_tolerado: float
    descripcion_error: str

@dataclass
class TecnicaMaestra:
    """Entidad que representa el video patrón y su catálogo de reglas (RF-01)."""
    id: UUID
    nombre: str
    categoria_tecnica: str
    posicion_origen: str
    ventana_sakoe_chiba: float
    video_url: str
    reglas: List[ReglaBiomecanica] = field(default_factory=list)
