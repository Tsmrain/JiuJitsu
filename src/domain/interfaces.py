# src/domain/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models import MatrizEsqueletica, DesviacionArticular

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

class ITecnicaRepository(ABC):
    """Contrato para almacenamiento y recuperación de Técnicas Patrón."""
    @abstractmethod
    def obtener_patron(self, id_tecnica: str) -> Optional[MatrizEsqueletica]:
        pass
