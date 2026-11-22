import re
import unicodedata
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from uuid import UUID


@dataclass(frozen=True)
class NombreTecnica:
    """
    Value Object de Dominio (Information Expert - Larman) para la identidad nominal de una técnica.
    Separa el nombre visible legible (preserva espacios para UI, BM25, glosario y VLM)
    de la clave canónica compacta sin espacios, tildes ni distinción de mayúsculas (para unicidad).
    """

    visible: str
    clave_canonica: str

    @staticmethod
    def normalizar_visible(raw: str) -> str:
        limpio = " ".join(str(raw or "").strip().split())
        if not limpio:
            raise ValueError("El nombre de la técnica no puede estar vacío.")
        return limpio

    @staticmethod
    def calcular_clave_canonica(raw: str) -> str:
        sin_tildes = "".join(
            ch for ch in unicodedata.normalize("NFD", str(raw or ""))
            if unicodedata.category(ch) != "Mn"
        )
        clave = re.sub(r"[^a-z0-9]+", "", sin_tildes.lower())
        if not clave:
            raise ValueError("El nombre de la técnica debe contener caracteres alfanuméricos válidos.")
        return clave

    @classmethod
    def crear(cls, raw: str) -> "NombreTecnica":
        visible = cls.normalizar_visible(raw)
        clave = cls.calcular_clave_canonica(visible)
        return cls(visible=visible, clave_canonica=clave)

class EsqueletoBiomecanico(BaseModel):
    frame_idx: int = 0
    keypoints133: List[float] = Field(..., min_length=133, max_length=133)
    angulos_articulares: Dict[str, float] = Field(default_factory=dict)
    
    def calcular_angulo_articular(self, articulacion_a: str, articulacion_b: str) -> float:
        pass
        
    def to_vector_array(self) -> List[float]:
        """
        Retorna el vector crudo de 133 dims para comparación por similitud coseno
        contra la colección Qdrant `vectores_poses_jiujitsu` (size=133).
        """
        return list(self.keypoints133)

class Evaluacion(BaseModel):
    id: UUID
    alumno_id: UUID
    tecnica_id: UUID
    porcentaje_similitud: Optional[float] = None
    feedback_gemini_es: Optional[str] = None
    feedback_gemini_pt: Optional[str] = None
    estado: str = "procesando"
    
    def actualizar_resultado(self, similitud: float, feedback_es: str, feedback_pt: str) -> None:
        pass
        
    def marcar_estado(self, nuevo_estado: str) -> None:
        pass

class AnalisisResultDTO(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    similitud: float
    feedback: str
    feedback_summary: Optional[str] = None
    feedback_correction: Optional[str] = None
    frame_critico_path: Optional[Any] = None
    frame_alumno_idx: Optional[int] = None
    discrepancias: Optional[List[str]] = Field(default_factory=list)
    articulaciones_criticas: Optional[List[int]] = Field(default_factory=list)
    nombres_articulaciones_criticas: Optional[List[str]] = Field(default_factory=list)
    dtw_distance: Optional[float] = None
    dtw_normalizado: Optional[float] = None
    timestamp_error_segundos: Optional[float] = None
