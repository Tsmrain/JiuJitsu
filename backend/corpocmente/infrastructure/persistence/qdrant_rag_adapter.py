from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, FilterSelector
from typing import List, Dict, Any
import uuid
import json
import math
from qdrant_client import QdrantClient
from corpocmente.config import settings

EXPECTED_RAG_DIM = 2048

class QdrantRAGAdapter:
    def __init__(self, host=None, port=None, client=None, collection_name=None):
        self.client = client or QdrantClient(
            host=host or settings.QDRANT_HOST,
            port=port or settings.QDRANT_PORT,
        )
        self.collection_name = collection_name or settings.QDRANT_RAG_COLLECTION
        if self.collection_name == settings.QDRANT_COLLECTION:
            raise ValueError("La colección RAG no puede compartir espacio con los keypoints biomecánicos.")
        self._asegurar_coleccion()

    def _asegurar_coleccion(self):
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={"dense": VectorParams(size=2048, distance=Distance.COSINE)}
            )

    def ingestar_desde_respuesta(
        self,
        data: dict,
        tecnica_id: str,
        fuente_tipo: str = "manual",
        fuente_nombre: str = None,
        fuente_referencia: str = None,
        fuente_url: str = None,
        alcance: str = "tecnica",
        metadata_por_chunk: List[Dict[str, Any]] = None,
    ) -> dict:
        """
        Ingesta chunks + embeddings en Qdrant.
        Retorna dict con chunks_count y lista de point_ids generados.
        """
        chunks = data["chunks"]
        embeddings = data["embeddings"]
        if len(chunks) != len(embeddings):
            raise ValueError("El worker devolvió distinta cantidad de chunks y embeddings.")
        for index, embedding in enumerate(embeddings):
            if not isinstance(embedding, list) or len(embedding) != EXPECTED_RAG_DIM:
                raise ValueError(
                    f"Embedding RAG {index} inválido: se esperaban {EXPECTED_RAG_DIM} dimensiones."
                )
            if any(not math.isfinite(float(value)) for value in embedding):
                raise ValueError(f"Embedding RAG {index} contiene valores no finitos.")
        puntos = []
        point_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            pid = str(uuid.uuid4())
            point_ids.append(pid)
            payload = {
                "tecnica_id": tecnica_id,
                "alcance": alcance,
                "contenido_texto": chunk,
                "chunk_index": i,
                "fuente_tipo": fuente_tipo,
                "fuente_nombre": fuente_nombre,
                "fuente_referencia": fuente_referencia,
                "fuente_url": fuente_url,
                "modalidad": "texto",
            }
            if metadata_por_chunk and i < len(metadata_por_chunk):
                payload.update(metadata_por_chunk[i])
            puntos.append(PointStruct(
                id=pid,
                vector={"dense": embedding},
                payload=payload,
            ))
        self.client.upsert(collection_name=self.collection_name, points=puntos)
        return {"chunks_count": len(puntos), "point_ids": point_ids, "chunks": chunks}

    def ingestar_desde_json(self, json_path: str, tecnica_id: str) -> int:
        """Compatibilidad para ingesta desde archivos JSON guardados localmente."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self.ingestar_desde_respuesta(data, tecnica_id)

    def recuperar_contexto(self, query_embedding: list, tecnica_id: str, top_k: int = 3) -> list:
        if len(query_embedding) != EXPECTED_RAG_DIM:
            raise ValueError(f"Embedding de consulta inválido: se esperaban {EXPECTED_RAG_DIM} dimensiones.")
        filtro = Filter(should=[
            Filter(must=[FieldCondition(key="tecnica_id", match=MatchValue(value=tecnica_id))]),
            Filter(must=[FieldCondition(key="alcance", match=MatchValue(value="global"))]),
        ])
        resultados = self.client.search(
            collection_name=self.collection_name,
            query_vector=("dense", query_embedding),
            query_filter=filtro,
            limit=top_k
        )
        fragmentos = []
        for resultado in resultados:
            payload = resultado.payload or {}
            contenido = payload.get("contenido_texto")
            if not contenido:
                continue
            fuente = [
                valor for valor in (
                    payload.get("fuente_nombre") or payload.get("fuente_tipo"),
                    payload.get("fuente_referencia"),
                    payload.get("fuente_url"),
                ) if valor
            ]
            prefijo = f"Fuente: {' — '.join(fuente)}\n" if fuente else ""
            fragmentos.append(f"{prefijo}{contenido}")
        return fragmentos

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

    def eliminar_mensaje_profesor(self, tecnica_id: str) -> None:
        """El mensaje es un singleton por técnica; evita recuperar versiones obsoletas."""
        filtro = Filter(must=[
            FieldCondition(key="tecnica_id", match=MatchValue(value=str(tecnica_id))),
            FieldCondition(key="fuente_tipo", match=MatchValue(value="instructor_message")),
        ])
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(filter=filtro),
        )

