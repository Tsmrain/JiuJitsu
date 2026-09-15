# src/infrastructure/adapters/qdrant_adapter.py
"""Adaptador de Infraestructura para Qdrant Vector Store (Variaciones Protegidas - Larman).

Permite almacenar e indexar vectores densos de 2048 dimensiones (Qwen3-VL-Embedding-2B)
usando métrica de similitud Cosine en un clúster local de Qdrant.
"""

import os
import uuid
from typing import Any, Dict, List, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
    )
except ImportError:
    QdrantClient = None
    Distance = None
    VectorParams = None
    PointStruct = None
    Filter = None
    FieldCondition = None
    MatchValue = None

from src.domain.interfaces import IVectorStore


class QdrantAdapter(IVectorStore):
    """Adaptador concreto para Qdrant implementando el contrato IVectorStore."""

    COLECCION_DEFECTO: str = "bjj_knowledge"
    DIMENSION_DEFECTO: int = 2048

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        client: Optional[Any] = None,
    ):
        self.url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY", None)
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION", self.COLECCION_DEFECTO)
        self.dimension = self.DIMENSION_DEFECTO

        if client is not None:
            self._client = client
        elif QdrantClient is not None:
            self._client = QdrantClient(url=self.url, api_key=self.api_key)
        else:
            self._client = None

        self._coleccion_inicializada = False

    def asegurar_coleccion(self) -> None:
        """Verifica la existencia de la colección 'bjj_knowledge' y la crea con métrica Cosine si no existe."""
        if not self._client:
            return

        try:
            if not self._client.collection_exists(self.collection_name):
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
                )
            self._coleccion_inicializada = True
        except Exception as e:
            print(f"[QdrantAdapter] Advertencia al verificar/crear colección: {e}")

    def _convertir_a_point_id(self, id_fuente: str) -> str:
        """Convierte cualquier ID de texto arbitrario en un UUID determinista v5 compatible con Qdrant."""
        try:
            return str(uuid.UUID(id_fuente))
        except (ValueError, AttributeError):
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(id_fuente)))

    def upsert(
        self,
        id_fuente: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> None:
        """Inserta o actualiza un vector de 2048 dimensiones con su payload en Qdrant."""
        if len(vector) != self.dimension:
            raise ValueError(f"Dimensión incorrecta del vector para Qdrant: {len(vector)} != {self.dimension}")

        if not self._client:
            return

        self.asegurar_coleccion()
        point_id = self._convertir_a_point_id(id_fuente)

        # Garantizar claves mínimas requeridas en el payload
        datos_payload = {
            "id_fuente": payload.get("id_fuente", id_fuente),
            "titulo": payload.get("titulo", ""),
            "chunk_texto": payload.get("chunk_texto", ""),
            "id_tecnica": payload.get("id_tecnica", ""),
        }
        # Agregar cualquier metadato adicional provisto
        for k, v in payload.items():
            if k not in datos_payload:
                datos_payload[k] = v

        punto = PointStruct(
            id=point_id,
            vector=vector,
            payload=datos_payload,
        )

        self._client.upsert(
            collection_name=self.collection_name,
            points=[punto],
        )

    def buscar(
        self,
        consulta_embedding: List[float],
        limite: int = 3,
        umbral_similitud: Optional[float] = None,
        id_tecnica: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Busca los fragmentos más cercanos por similitud coseno con filtro opcional por técnica."""
        if len(consulta_embedding) != self.dimension:
            raise ValueError(
                f"Dimensión incorrecta del vector de consulta: {len(consulta_embedding)} != {self.dimension}"
            )

        if not self._client:
            return []

        self.asegurar_coleccion()

        # Configurar filtro nativo si se solicita id_tecnica
        query_filter = None
        if id_tecnica:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="id_tecnica",
                        match=MatchValue(value=id_tecnica),
                    )
                ]
            )

        hits = []
        try:
            if hasattr(self._client, "query_points"):
                res = self._client.query_points(
                    collection_name=self.collection_name,
                    query=consulta_embedding,
                    limit=limite,
                    score_threshold=umbral_similitud,
                    query_filter=query_filter,
                )
                hits = res.points
            elif hasattr(self._client, "search"):
                hits = self._client.search(
                    collection_name=self.collection_name,
                    query_vector=consulta_embedding,
                    limit=limite,
                    score_threshold=umbral_similitud,
                    query_filter=query_filter,
                )
        except Exception as e:
            print(f"[QdrantAdapter] Error en búsqueda vectorial: {e}")
            return []

        resultados: List[Dict[str, Any]] = []
        for hit in hits:
            p = getattr(hit, "payload", {}) or {}
            score = getattr(hit, "score", 0.0)
            resultados.append({
                "id_fuente": p.get("id_fuente", str(getattr(hit, "id", ""))),
                "id_documento": p.get("id_documento"),
                "titulo": p.get("titulo", ""),
                "chunk_texto": p.get("chunk_texto", ""),
                "id_tecnica": p.get("id_tecnica", ""),
                "similitud": float(score),
                "payload": p,
            })

        return resultados

    def eliminar(self, id_fuente: str) -> bool:
        """Elimina un vector/punto de la colección de Qdrant por su ID de fuente."""
        if not self._client:
            return False
        try:
            point_id = self._convertir_a_point_id(id_fuente)
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id],
            )
            return True
        except Exception as e:
            print(f"[QdrantAdapter] Advertencia al eliminar punto {id_fuente}: {e}")
            return False

    def eliminar_por_documento(self, id_documento: str) -> bool:
        """Elimina eficientemente todos los vectores asociados a un documento usando filtros nativos de Qdrant."""
        if not self._client or not id_documento:
            return False
        try:
            self.asegurar_coleccion()
            filtro = Filter(
                must=[
                    FieldCondition(
                        key="id_documento",
                        match=MatchValue(value=id_documento),
                    )
                ]
            )
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=filtro,
            )
            return True
        except Exception as e:
            print(f"[QdrantAdapter] Advertencia al eliminar por documento {id_documento}: {e}")
            return False

