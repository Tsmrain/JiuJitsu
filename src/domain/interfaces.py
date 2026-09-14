# src/domain/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models import (
    Profesor,
    TecnicaPatron,
    FuenteConocimiento,
    MatrizEsqueletica,
    DesviacionArticular,
)

class IInferenceEngine(ABC):
    """Contrato para motores de visión artificial (YOLO26x Pose + Depth)."""
    @abstractmethod
    def inferir_esqueleto_3d(self, video_path: str) -> MatrizEsqueletica:
        pass

class IGenerationService(ABC):
    """Contrato para servicios de LLM/RAG (Gemini 3.8 Flash)."""
    @abstractmethod
    def generar_consejo(
        self, 
        tecnica: str, 
        desviaciones: List[DesviacionArticular], 
        contexto_manual: Optional[str] = None
    ) -> str:
        pass

class IEmbeddingService(ABC):
    """Contrato para servicios de generación de embeddings vectoriales."""
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        pass

class IProfesorRepository(ABC):
    """Contrato para persistencia y consulta de profesores/instructores."""
    @abstractmethod
    def guardar(self, profesor: Profesor) -> None:
        pass

    @abstractmethod
    def obtener_por_id(self, id_profesor: str) -> Optional[Profesor]:
        pass

    @abstractmethod
    def listar_todos(self) -> List[Profesor]:
        pass

    @abstractmethod
    def eliminar(self, id_profesor: str) -> bool:
        pass

    @abstractmethod
    def actualizar(self, id_profesor: str, nombre: str, email: str) -> bool:
        """Actualiza los datos de un profesor existente. Lanza ValueError si el email ya existe en otro registro."""
        pass

class ITecnicaRepository(ABC):
    """Contrato para almacenamiento y recuperación de Técnicas Patrón."""
    @abstractmethod
    def registrar_patron(self, tecnica: TecnicaPatron) -> bool:
        pass

    @abstractmethod
    def obtener_patron(self, id_tecnica: str) -> Optional[TecnicaPatron]:
        pass

    @abstractmethod
    def listar_por_instructor(self, id_profesor: str) -> List[TecnicaPatron]:
        pass

class IFuenteConocimientoRepository(ABC):
    """Contrato para acervo de literatura técnica indexada para RAG."""
    @abstractmethod
    def indexar_documento(self, fuente: FuenteConocimiento) -> str:
        pass

    @abstractmethod
    def buscar_contexto(self, consulta_embedding: List[float], limite: int = 3) -> List[FuenteConocimiento]:
        pass

    @abstractmethod
    def listar_fuentes(self, id_tecnica: Optional[str] = None) -> List[FuenteConocimiento]:
        pass

