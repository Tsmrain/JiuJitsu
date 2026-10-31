from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID

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

from typing import List, Dict, Optional, Any

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
