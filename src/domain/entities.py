from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4

from .value_objects import ErrorBiomecanico


@dataclass
class ReglaBiomecanica:
    """Regla de tolerancia y evaluación pedagógica de error biomecánico (RF-10)."""
    articulacion_clave: str
    umbral_angular_tolerado: float = 15.0
    descripcion_error: str = ""

    def evaluar(self, angulo_desviacion: float) -> bool:
        """Determina si la desviación supera el umbral permitido."""
        return angulo_desviacion > self.umbral_angular_tolerado


@dataclass
class TecnicaMaestra:
    """Entidad de técnica maestra de Jiu-Jitsu Brasileño (RF-01)."""
    id: UUID = field(default_factory=uuid4)
    nombre: str = ""
    categoria: str = ""
    posicion_origen: str = ""
    video_url: str = ""
    ventana_sakoe_chiba: float = 0.15
    fecha_carga: datetime = field(default_factory=datetime.now)
    reglas: List[ReglaBiomecanica] = field(default_factory=list)


@dataclass
class FotogramaAnotado:
    """Entregable visual anotado con OpenCV (RF-05, RF-06)."""
    imagen_url: str
    coordenada_error_x: int
    coordenada_error_y: int
    explicacion_causa: str


@dataclass
class AnalisisBiomecanico:
    """Entidad que consolida el resultado del análisis biomecánico (1:1 con el video)."""
    id: UUID = field(default_factory=uuid4)
    video_id: UUID = field(default_factory=uuid4)
    fecha_procesamiento: datetime = field(default_factory=datetime.now)
    desviacion_angular_maxima: float = 0.0
    articulacion_afectada: str = ""
    puntuacion_global: float = 100.0
    estado_computo: str = "completado"
    fotograma_anotado: Optional[FotogramaAnotado] = None
    errores: List[ErrorBiomecanico] = field(default_factory=list)


@dataclass
class RolUsuario:
    """Rol de usuario en el sistema de auditoría biomecánica (profesor o alumno)."""
    id_rol: str  # 'profesor' | 'alumno'
    descripcion: str = ""


@dataclass
class CodigoActivacion:
    """Token de acceso y autorización para procesamiento en la plataforma."""
    id_codigo: UUID = field(default_factory=uuid4)
    hash_codigo: str = ""
    estudiante_id: Optional[str] = None
    fecha_expiracion: datetime = field(default_factory=datetime.now)
    activo: bool = True


@dataclass
class HeadCoach:
    """Entidad que representa al profesor / instructor de la academia (CU-01)."""
    id: UUID = field(default_factory=uuid4)
    nombre: str = ""
    correo: str = ""
    rol: str = "profesor"
    tecnicas_homologadas: List[UUID] = field(default_factory=list)


@dataclass
class Estudiante:
    """Entidad que representa al practicante en el tatami (CU-02)."""
    id: UUID = field(default_factory=uuid4)
    nombre: str = ""
    correo: str = ""
    grado_cinturon: str = "Blanco"
    peso_kg: float = 70.0
    rol: str = "alumno"
    token_api_colab: Optional[str] = None
    estado_membresia: str = "activa"
