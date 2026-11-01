import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from rank_bm25 import BM25Okapi

from corpocmente.domain.glossary.glossary_service import expandir_query_con_glosario

logger = logging.getLogger(__name__)

_bm25_instance: Optional["QdrantBM25Corpus"] = None
_bm25_lock = threading.Lock()


class QdrantBM25Corpus:
    """
    Índice BM25 en memoria para los fragmentos de conocimiento técnico en Qdrant.
    Permite búsqueda léxica ultra rápida (< 5ms) con soporte para expansión de sinónimos.
    """

    def __init__(self, qdrant_adapter: Any):
        self.qdrant = qdrant_adapter
        self.doc_records: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.indexed_at: float = 0.0
        self._reindex()

    def _reindex(self) -> None:
        try:
            col_name = getattr(self.qdrant, "rag_collection_name", "rag_knowledge")
            client = getattr(self.qdrant, "client", None)
            if client is None or not hasattr(client, "scroll"):
                logger.warning("Qdrant adapter sin client disponible para indexar BM25.")
                return

            scroll_res = client.scroll(
                collection_name=col_name,
                limit=1500,
                with_payload=True,
                with_vectors=False,
            )
            if not isinstance(scroll_res, tuple) or len(scroll_res) < 2:
                return
            points, _ = scroll_res
            if not isinstance(points, (list, tuple)):
                return

            tokenized_corpus = []
            records = []
            for p in points:
                payload = getattr(p, "payload", None) or {}
                contenido = (payload.get("contenido_texto") or "").strip()
                asociado = (payload.get("texto_asociado") or "").strip()
                referencia = (payload.get("fuente_referencia") or "").strip()
                nombre_f = (payload.get("fuente_nombre") or "").strip()

                partes = [part for part in (contenido, asociado, referencia, nombre_f) if part]
                texto_total = " ".join(partes).strip()

                # Filtrar placeholders visuales sin contenido textual sustancial
                if len(texto_total) < 25 or texto_total.startswith("[Imagen:"):
                    continue

                tokens = [w for w in re.findall(r'\w+', texto_total.lower()) if len(w) > 2]
                if not tokens:
                    continue

                records.append({
                    "id": str(getattr(p, "id", "")),
                    "score": 0.0,
                    "contenido_texto": contenido,
                    "texto_asociado": asociado,
                    "fuente_referencia": referencia,
                    "fuente_nombre": nombre_f,
                    "media_path": payload.get("media_path"),
                    "media_url": payload.get("media_url"),
                    "video_path": payload.get("video_path"),
                    "tecnica_id": payload.get("tecnica_id"),
                    "alcance": payload.get("alcance", "global"),
                    "modalidad": payload.get("modalidad", "texto"),
                    "pagina": payload.get("pagina"),
                    "timestamp_seconds": payload.get("timestamp_seconds"),
                    "frame_idx": payload.get("frame_idx"),
                })
                tokenized_corpus.append(tokens)

            if tokenized_corpus:
                self.bm25 = BM25Okapi(tokenized_corpus)
                self.doc_records = records
                self.indexed_at = time.time()
                logger.info("BM25 indexado exitosamente con %d documentos técnicos.", len(records))
            else:
                logger.warning("No se encontraron documentos técnicos en Qdrant para BM25.")
        except Exception as exc:
            logger.error("Error indexando corpus BM25 desde Qdrant: %s", exc)

    def search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.doc_records or not query:
            return []

        tokens = [w for w in re.findall(r'\w+', query.lower()) if len(w) > 2]
        if not tokens:
            return []

        try:
            scores = self.bm25.get_scores(tokens)
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            resultados = []
            for idx in top_indices:
                score = float(scores[idx])
                if score > 0.0:
                    item = dict(self.doc_records[idx])
                    item["bm25_score"] = round(score, 4)
                    resultados.append(item)
            return resultados
        except Exception as exc:
            logger.warning("Fallo en búsqueda BM25: %s", exc)
            return []


def get_bm25_corpus(qdrant_adapter: Any) -> QdrantBM25Corpus:
    global _bm25_instance
    if _bm25_instance is None:
        with _bm25_lock:
            if _bm25_instance is None:
                _bm25_instance = QdrantBM25Corpus(qdrant_adapter)
    return _bm25_instance


class HybridRetriever:
    """
    Recuperador Híbrido (Dense Vector + BM25 Léxico con Glosario) + Reciprocal Rank Fusion (RRF).
    
    Arquitectura:
    1. Stream Denso: Búsqueda vectorial en Qdrant (embeddings Qwen 2048 dims).
    2. Stream Léxico: BM25 Okapi con consulta expandida mediante Glosario Multilingüe.
    3. Fusión RRF: Combina ambos rankings con la constante k=60.
    4. Top-K Recall: Retorna los 20 mejores candidatos para el Cross-Encoder.
    """

    DEFAULT_K_RRF = 60

    @classmethod
    def fusionar_rrf(
        cls,
        candidatos_densos: List[Dict[str, Any]],
        candidatos_bm25: List[Dict[str, Any]],
        top_k: int = 20,
        k_rrf: int = 60,
        weight_bm25: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        Aplica Reciprocal Rank Fusion (RRF) sobre los resultados densos y léxicos:
        RRF(d) = 1.0 / (k + rank_dense(d)) + weight_bm25 / (k + rank_bm25(d))
        """
        rrf_scores: Dict[str, float] = {}
        candidatos_map: Dict[str, Dict[str, Any]] = {}

        # 1. Puntuar Stream Denso
        for rank, cand in enumerate(candidatos_densos):
            cid = str(cand.get("id"))
            if not cid:
                continue
            candidatos_map[cid] = cand
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k_rrf + (rank + 1)))

        # 2. Puntuar Stream BM25 (ponderado para balance óptimo semántico-léxico)
        for rank, cand in enumerate(candidatos_bm25):
            cid = str(cand.get("id"))
            if not cid:
                continue
            if cid not in candidatos_map:
                candidatos_map[cid] = cand
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (weight_bm25 / (k_rrf + (rank + 1)))

        # 3. Aplicar bonus para evidencia visual verificada antes de ordenar
        for cid, cand in candidatos_map.items():
            if cand.get("media_path"):
                rrf_scores[cid] = rrf_scores[cid] + 0.005

        # 4. Ordenar por RRF score descendente
        ordenados_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        resultados = []
        for cid in ordenados_ids[:top_k]:
            item = dict(candidatos_map[cid])
            score_rrf = rrf_scores[cid]
            item["rrf_score"] = round(score_rrf, 6)
            item["score"] = item.get("score") or round(score_rrf * 50.0, 4)
            resultados.append(item)

        return resultados

    @classmethod
    def recuperar(
        cls,
        query_texto: str,
        qdrant_adapter: Any,
        qwen_adapter: Optional[Any] = None,
        tecnica_id: Optional[UUID] = None,
        limit: int = 20,
        modo: str = "hybrid",
        k_rrf: int = 60,
        vectores_consulta: Optional[List[List[float]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta la recuperación según el modo especificado:
        - 'dense': Únicamente búsqueda vectorial en Qdrant.
        - 'bm25': Únicamente búsqueda léxica BM25 con glosario.
        - 'hybrid': Búsqueda combinada Densa + BM25 fusionada con RRF.
        """
        if modo == "bm25":
            corpus = get_bm25_corpus(qdrant_adapter)
            q_expandida = expandir_query_con_glosario(query_texto)
            return corpus.search(q_expandida, top_k=limit)

        # 1. Recuperación Densa (Qdrant)
        densos: List[Dict[str, Any]] = []
        if qdrant_adapter:
            try:
                vecs = vectores_consulta
                if not vecs and qwen_adapter and query_texto:
                    emb = qwen_adapter.generar_embedding_texto(query_texto.strip())
                    vecs = [emb]
                if vecs:
                    densos = qdrant_adapter.recuperar_evidencias_rag_multimodal(
                        vectores_consulta=vecs,
                        tecnica_id=tecnica_id,
                        limit=limit * 2 if modo == "hybrid" else limit,
                    )
            except Exception as exc:
                logger.warning("Fallo en recuperación densa: %s", exc)

        if modo == "dense":
            return densos[:limit]

        # 2. Recuperación BM25 con Expansión de Glosario
        bm25_results: List[Dict[str, Any]] = []
        try:
            corpus = get_bm25_corpus(qdrant_adapter)
            q_expandida = expandir_query_con_glosario(query_texto)
            bm25_results = corpus.search(q_expandida, top_k=limit * 2)
        except Exception as exc_bm25:
            logger.warning("Fallo en recuperación BM25: %s", exc_bm25)

        # 3. Fusión RRF (Hybrid)
        if not bm25_results:
            return densos[:limit]
        if not densos:
            return bm25_results[:limit]

        return cls.fusionar_rrf(
            candidatos_densos=densos,
            candidatos_bm25=bm25_results,
            top_k=limit,
            k_rrf=k_rrf,
        )
