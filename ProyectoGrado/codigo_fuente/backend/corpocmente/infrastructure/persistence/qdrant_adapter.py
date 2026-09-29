import logging
import numpy as np
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
        self.rag_collection = "rag_knowledge"
        self._client = client

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(host=self.host, port=self.port)
        return self._client

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

    def buscar_maxima_diferencia(
        self,
        esqueletos_alumno: List['EsqueletoBiomecanico'],
        tecnica_id: UUID
    ) -> VectorSearchResultDTO:
        """
        Descarga UNA VEZ todos los vectores de referencia de la técnica desde Qdrant
        y compara cada frame del alumno contra ellos mediante similitud coseno local
        con numpy. Devuelve el par (frame alumno ↔ frame referencia) con MENOR
        similitud (peor ejecución) y su payload.
        """
        if not esqueletos_alumno:
            raise ValueError("La lista de esqueletos del alumno está vacía.")

        # 1. Descargar TODAS las referencias con scroll (no search)
        filtro = Filter(must=[
            FieldCondition(key="tecnica_id", match=MatchValue(value=str(tecnica_id)))
        ])
        referencias, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filtro,
            limit=10000,
            with_vectors=True,
            with_payload=True,
        )
        if not referencias:
            raise ValueError(
                f"No hay vectores de referencia en Qdrant para la técnica {tecnica_id}. "
                f"Ejecutar scripts/ingest_reference_video.py primero."
            )

        ref_vectors = np.array([p.vector for p in referencias], dtype=np.float32)
        ref_norms = np.linalg.norm(ref_vectors, axis=1, keepdims=True) + 1e-9
        ref_normed = ref_vectors / ref_norms

        # 2. Iterar frames del alumno localmente
        peor_similitud = 1.0
        peor_payload = None
        peor_frame_alumno = None

        for idx, esqueleto in enumerate(esqueletos_alumno):
            vec = np.array(esqueleto.to_vector_array(), dtype=np.float32)
            vec_n = vec / (np.linalg.norm(vec) + 1e-9)
            sims = ref_normed @ vec_n                 # coseno contra todas las refs
            j = int(np.argmin(sims))
            if float(sims[j]) < peor_similitud:
                peor_similitud = float(sims[j])
                peor_frame_alumno = idx
                peor_payload = referencias[j].payload or {}

        logger.info(
            f"Peor frame alumno: #{peor_frame_alumno} (similitud coseno = {peor_similitud:.4f})"
        )

        return VectorSearchResultDTO(
            score=round(peor_similitud * 100, 2),      # escala 0–100
            frame_path=peor_payload.get("frame_path", ""),
            discrepancias=peor_payload.get("discrepancias", []),
        )

    def recuperar_contexto_rag(self, vector_multimodal: List[float], tecnica_id: UUID) -> str:
        """
        Busca en la colección RAG (vectores de 2048 dims generados por Qwen) la teoría
        de libros o manuales más relevante para la query textual del análisis.

        Retorna los top-3 chunks concatenados con separador '---' para dar contexto
        enriquecido a Gemini. Retorna cadena vacía si no hay resultados o si falla.
        """
        filtro = Filter(
            must=[
                FieldCondition(
                    key="tecnica_id",
                    match=MatchValue(value=str(tecnica_id))
                )
            ]
        )
        try:
            resultados = self.client.search(
                collection_name=self.rag_collection,
                query_vector=("dense", vector_multimodal),
                query_filter=filtro,
                limit=3
            )
            if not resultados:
                return ""
            
            chunks = []
            for r in resultados:
                if r.payload and r.payload.get("contenido_texto"):
                    chunks.append(r.payload["contenido_texto"])
            
            return "\n\n---\n\n".join(chunks)
        except Exception as e:
            logger.warning(f"No se pudo recuperar contexto RAG de Qdrant: {e}")
            return ""
