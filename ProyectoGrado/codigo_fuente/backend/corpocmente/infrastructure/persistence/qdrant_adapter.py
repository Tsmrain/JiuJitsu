import logging
from typing import List, Dict, Optional
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from corpocmente.config import settings

logger = logging.getLogger(__name__)

class VectorSearchResultDTO:
    def __init__(self, score: float, frame_path: str, discrepancias: List[str]):
        self.score = score
        self.frame_path = frame_path
        self.discrepancias = discrepancias

class QdrantVectorAdapter:
    """
    Adaptador (GoF Adapter) para encapsular las búsquedas por similitud vectorial (HNSW + Coseno)
    en Qdrant DB, aislando el dominio del cliente nativo de Qdrant.
    """

    def __init__(self, 
                 host: Optional[str] = None, 
                 port: Optional[int] = None, 
                 collection_name: Optional[str] = None,
                 client: Optional[QdrantClient] = None):
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        
        # Inyección de cliente o instanciación por defecto
        self.client = client or QdrantClient(host=self.host, port=self.port)

    def asegurar_coleccion(self, vector_size: int = 133) -> None:
        """Crea la colección en Qdrant con métrica de Coseno si no existe previamente."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            logger.info(f"Colección Qdrant '{self.collection_name}' creada con dimensión {vector_size}.")

    def insertar_vector(self, vector_id: UUID, vector: List[float], payload: Dict) -> None:
        """Inserta o actualiza un vector biomecánico con sus metadatos (payload)."""
        point = PointStruct(
            id=str(vector_id),
            vector=vector,
            payload=payload
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    def buscar_similitud_pose(self, vector_alumno: List[float], tecnica_id: UUID) -> VectorSearchResultDTO:
        """
        Busca el fotograma de referencia más similar en Qdrant filtrando por la técnica.
        Retorna el score de similitud, la ruta de la imagen patrón y sus discrepancias técnicas.
        """
        filtro_tecnica = Filter(
            must=[
                FieldCondition(
                    key="tecnica_id",
                    match=MatchValue(value=str(tecnica_id))
                )
            ]
        )

        resultados = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector_alumno,
            query_filter=filtro_tecnica,
            limit=1
        )

        if not resultados:
            raise ValueError(f"No se encontraron vectores de referencia para la técnica ID {tecnica_id}")

        mejor_coincidencia = resultados[0]
        payload = mejor_coincidencia.payload or {}

        # Mapeo a DTO desacoplado
        return VectorSearchResultDTO(
            score=round(float(mejor_coincidencia.score) * 100, 2),  # Porcentaje de similitud
            frame_path=payload.get("frame_path", ""),
            discrepancias=payload.get("discrepancias", [])
        )
