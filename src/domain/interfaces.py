# src/domain/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from src.domain.models import (
    Profesor,
    TecnicaPatron,
    FuenteConocimiento,
    MatrizEsqueletica,
    DesviacionArticular,
    Usuario,
)

class IUsuarioRepository(ABC):
    """Contrato para persistencia y consulta de cuentas de usuario."""

    @abstractmethod
    def guardar(self, usuario: Usuario) -> None:
        pass

    @abstractmethod
    def obtener_por_id(self, id_usuario: str) -> Optional[Usuario]:
        pass

    @abstractmethod
    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        pass

    @abstractmethod
    def listar_todos(self) -> List[Usuario]:
        pass

    @abstractmethod
    def eliminar(self, id_usuario: str) -> bool:
        pass

class IInferenceEngine(ABC):
    """Contrato para motores de visión artificial (YOLO26x Pose + Depth)."""
    @abstractmethod
    def inferir_esqueleto_3d(self, video_path: str) -> MatrizEsqueletica:
        pass

class IGenerationService(ABC):
    """Contrato para servicios de LLM/RAG (Gemini 2.5 Flash)."""
    @abstractmethod
    def generar_consejo(
        self, 
        tecnica: str, 
        desviaciones: List[DesviacionArticular], 
        contexto_manual: Optional[str] = None
    ) -> Union[Dict[str, Any], str]:
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

    def eliminar(self, id_fuente: str) -> bool:
        """Elimina una fuente por su identificador."""
        return False

    def actualizar(self, id_fuente: str, titulo: str, chunk_texto: Optional[str] = None) -> bool:
        """Actualiza metadatos de una fuente."""
        return False

class IVectorStore(ABC):
    """Contrato abstracto para almacenamiento y recuperación de vectores densos (Qdrant)."""

    @abstractmethod
    def upsert(
        self,
        id_fuente: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> None:
        """Inserta o actualiza un vector con su payload asociado."""
        pass

    @abstractmethod
    def buscar(
        self,
        consulta_embedding: List[float],
        limite: int = 3,
        umbral_similitud: Optional[float] = None,
        id_tecnica: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Realiza búsqueda semántica KNN por similitud de coseno."""
        pass

    def eliminar(self, id_fuente: str) -> bool:
        """Elimina un vector por su id de fuente."""
        return False

    def eliminar_por_documento(self, id_documento: str) -> bool:
        """Elimina todos los vectores asociados a un documento por su id_documento."""
        return False

class IHistorialRepository(ABC):
    """Contrato para persistencia y consulta del historial de progreso de evaluaciones."""

    @abstractmethod
    def guardar_evaluacion(self, id_alumno: str, id_tecnica: str, resultado: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def obtener_progreso(self, id_alumno: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def listar_todas(self, id_tecnica: Optional[str] = None) -> List[Dict[str, Any]]:
        pass
