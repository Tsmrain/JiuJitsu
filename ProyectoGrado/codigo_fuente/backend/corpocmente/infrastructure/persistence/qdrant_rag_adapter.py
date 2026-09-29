from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any
import uuid
import json

class QdrantRAGAdapter:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "rag_knowledge"
        self._asegurar_coleccion()

    def _asegurar_coleccion(self):
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={"dense": VectorParams(size=2048, distance=Distance.COSINE)}
            )

    def ingestar_desde_respuesta(self, data: dict, tecnica_id: str) -> dict:
        """
        Ingesta chunks + embeddings en Qdrant.
        Retorna dict con chunks_count y lista de point_ids generados.
        """
        chunks = data["chunks"]
        embeddings = data["embeddings"]
        puntos = []
        point_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            pid = str(uuid.uuid4())
            point_ids.append(pid)
            puntos.append(PointStruct(
                id=pid,
                vector={"dense": embedding},
                payload={"tecnica_id": tecnica_id, "contenido_texto": chunk, "chunk_index": i}
            ))
        self.client.upsert(collection_name=self.collection_name, points=puntos)
        return {"chunks_count": len(puntos), "point_ids": point_ids, "chunks": chunks}

    def ingestar_desde_json(self, json_path: str, tecnica_id: str) -> int:
        """Compatibilidad para ingesta desde archivos JSON guardados localmente."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self.ingestar_desde_respuesta(data, tecnica_id)

    def recuperar_contexto(self, query_embedding: list, tecnica_id: str, top_k: int = 3) -> list:
        filtro = Filter(must=[FieldCondition(key="tecnica_id", match=MatchValue(value=tecnica_id))])
        resultados = self.client.search(
            collection_name=self.collection_name,
            query_vector=("dense", query_embedding),
            query_filter=filtro,
            limit=top_k
        )
        return [r.payload["contenido_texto"] for r in resultados]

    def eliminar_puntos(self, point_ids: list) -> int:
        """
        Elimina puntos de la colección RAG por sus IDs.
        Retorna la cantidad de IDs solicitados para eliminar.
        """
        if not point_ids:
            return 0
        from qdrant_client.models import PointIdsList
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=point_ids)
        )
        return len(point_ids)

