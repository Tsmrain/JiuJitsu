from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID

class EsqueletoBiomecanico(BaseModel):
    keypoints133: List[float] = Field(..., min_length=133, max_length=133)
    angulos_articulares: Dict[str, float] = Field(default_factory=dict)
    
    def calcular_angulo_articular(self, articulacion_a: str, articulacion_b: str) -> float:
        pass
        
    def to_vector_array(self) -> List[float]:
        pass

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
    similitud: float
    feedback: str
