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
        
        # 1. Priorizar búsqueda específica por tecnica_id
        resultados = []
        if tecnica_id:
            filtro_tecnica = Filter(must=[FieldCondition(key="tecnica_id", match=MatchValue(value=tecnica_id))])
            resultados = self.client.search(
                collection_name=self.collection_name,
                query_vector=("dense", query_embedding),
                query_filter=filtro_tecnica,
                limit=top_k
            )

        # 2. Fallback a alcance global si la técnica no tiene fragmentos asignados
        if not resultados:
            filtro_global = Filter(must=[FieldCondition(key="alcance", match=MatchValue(value="global"))])
            resultados = self.client.search(
                collection_name=self.collection_name,
                query_vector=("dense", query_embedding),
                query_filter=filtro_global,
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

    def eliminar_por_tecnica(self, tecnica_id: str) -> int:
        """Elimina de Qdrant todos los fragmentos RAG asociados a una técnica."""
        filtro = Filter(must=[
            FieldCondition(key="tecnica_id", match=MatchValue(value=str(tecnica_id))),
        ])
        try:
            count_res = self.client.count(
                collection_name=self.collection_name,
                count_filter=filtro,
                exact=True,
            )
            total = int(getattr(count_res, "count", 0) or 0)
            if total > 0:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=FilterSelector(filter=filtro),
                )
            return total
        except Exception as e:
            logger.warning("Error eliminando chunks RAG por tecnica_id=%s: %s", tecnica_id, e)
            return 0

    def eliminar_por_manual(self, filename: str) -> int:
        """
        Elimina de la colección RAG todos los puntos pertenecientes a un manual
        identificado por su filename en disco, fuente_nombre, fuente_url o media_path.
        """
        import os
        from urllib.parse import unquote

        target_raw = (filename or "").strip()
        target_name = os.path.basename(unquote(target_raw))
        if not target_name:
            return 0

        matched_ids = []
        next_offset = None
        try:
            while True:
                points, next_offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=256,
                    offset=next_offset,
                    with_payload=True,
                    with_vectors=False,
                )
                for p in points:
                    payload = p.payload or {}
                    fuente_nombre = str(payload.get("fuente_nombre") or "")
                    fuente_url = unquote(str(payload.get("fuente_url") or ""))
                    media_url = unquote(str(payload.get("media_url") or ""))
                    media_path = unquote(str(payload.get("media_path") or ""))

                    url_basename = os.path.basename(fuente_url.split("?")[0]) if fuente_url else ""
                    media_url_base = os.path.basename(media_url.split("?")[0]) if media_url else ""
                    media_path_base = os.path.basename(media_path) if media_path else ""

                    if (
                        fuente_nombre == target_name
                        or fuente_nombre == target_raw
                        or url_basename == target_name
                        or media_url_base == target_name
                        or media_path_base == target_name
                        or (f"/{target_name}" in fuente_url)
                        or (f"/{target_name}" in media_path)
                    ):
                        matched_ids.append(str(p.id))

                if next_offset is None:
                    break
        except Exception as e:
            logger.warning("Error escaneando Qdrant para eliminar manual '%s': %s", target_name, e)
            return 0

        if not matched_ids:
            return 0
        return self.eliminar_puntos(matched_ids)

    def buscar_biblioteca(self, query_embedding: list, limit: int = 10) -> list:
        """
        Búsqueda semántica en la colección RAG filtrando por cualquier fuente global (PDF, TXT, DOCX, imágenes).
        Retorna lista de diccionarios con contenido_texto, media_url, pagina, fuente_nombre, cita y score.
        """
        if len(query_embedding) != EXPECTED_RAG_DIM:
            raise ValueError(f"Embedding de consulta inválido: se esperaban {EXPECTED_RAG_DIM} dimensiones.")
        filtro = Filter(must=[
            FieldCondition(key="alcance", match=MatchValue(value="global")),
        ])
        resultados = self.client.search(
            collection_name=self.collection_name,
            query_vector=("dense", query_embedding),
            query_filter=filtro,
            limit=limit,
        )
        items = []
        for r in resultados:
            payload = r.payload or {}
            pagina = payload.get("pagina")
            fuente_nom = payload.get("fuente_nombre") or "Manual"
            cita = f"{fuente_nom}, p. {pagina}" if pagina else fuente_nom
            contenido = payload.get("contenido_texto", "")
            texto_asoc = payload.get("texto_asociado", "")
            if texto_asoc and texto_asoc not in contenido:
                contenido = f"{contenido}\n{texto_asoc}".strip() if contenido else texto_asoc

            items.append({
                "id": str(r.id),
                "score": float(r.score),
                "contenido_texto": contenido,
                "media_url": payload.get("media_url"),
                "media_path": payload.get("media_path"),
                "pagina": pagina,
                "fuente_nombre": fuente_nom,
                "fuente_referencia": payload.get("fuente_referencia"),
                "fuente_tipo": payload.get("fuente_tipo"),
                "fuente_url": payload.get("fuente_url"),
                "cita": cita,
            })
        return items

    def buscar_biblioteca_multimodal(
        self,
        text_vector: list,
        image_vector: list,
        alpha: float = 0.5,
        limit: int = 10
    ) -> list:
        """
        Búsqueda multimodal en manuales combinando el vector semántico textual y el
        vector visual del fotograma de error del alumno.
        """
        if len(text_vector) != EXPECTED_RAG_DIM or len(image_vector) != EXPECTED_RAG_DIM:
            raise ValueError(f"Embeddings inválidos: se esperaban {EXPECTED_RAG_DIM} dimensiones.")

        # Fusión ponderada de vectores densos de Qwen3-VL
        v_fused = [
            alpha * tv + (1.0 - alpha) * iv
            for tv, iv in zip(text_vector, image_vector)
        ]
        norm = sum(x * x for x in v_fused) ** 0.5
        if norm > 1e-9:
            v_fused = [x / norm for x in v_fused]

        return self.buscar_biblioteca(v_fused, limit=limit)



