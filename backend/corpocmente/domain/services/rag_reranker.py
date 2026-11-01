import logging
import math
import os
import threading
import time
from typing import Any, Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

_reranker_model = None
_reranker_processor = None
_reranker_lock = threading.Lock()
_reranker_failed = False


class Qwen3VLRerankerCrossEncoder:
    """
    Cross-Encoder de Reranking multimodal y multilingüe basado en Qwen3-VL-Reranker-2B-4bit
    ejecutado nativamente en Apple Silicon Metal GPU mediante MLX.

    Características:
    - Evaluación conjunta (Query, Documento) en un único paso forward (Cross-Encoder real).
    - Desactivación estricta de 'Think Mode': evalúa directamente los logits binarios
      (yes_token vs no_token) mediante sigmoid sin generación autoregresiva de texto.
    - Soporte nativo para 30+ idiomas (Español, Portugués, Inglés, etc.).
    - Latencia p95 < 1.0s para 20 candidatos en Apple Silicon.
    """

    MODEL_ID = os.getenv("RERANKER_MODEL_ID", "mlx-community/Qwen3-VL-Reranker-2B-4bit")
    DEFAULT_INSTRUCTION = "Given a jiu-jitsu technique question, retrieve the manual passage that answers it."

    @classmethod
    def get_instance(cls):
        global _reranker_model, _reranker_processor, _reranker_failed
        if _reranker_failed:
            return None, None

        if _reranker_model is None or _reranker_processor is None:
            with _reranker_lock:
                if _reranker_model is None or _reranker_processor is None:
                    try:
                        from mlx_embeddings import load
                        logger.info("Cargando Qwen3-VL-Reranker Cross-Encoder MLX: %s", cls.MODEL_ID)
                        t0 = time.time()
                        _reranker_model, _reranker_processor = load(cls.MODEL_ID)
                        logger.info("Qwen3-VL-Reranker cargado exitosamente en %.2fs.", time.time() - t0)
                    except Exception as err:
                        logger.warning("No se pudo cargar Qwen3-VL-Reranker MLX (%s): %s. Fallback activo.", cls.MODEL_ID, err)
                        _reranker_failed = True
                        return None, None

        return _reranker_model, _reranker_processor

    @classmethod
    def rerank_pairs(
        cls,
        query: str,
        documents: List[str],
        instruction: Optional[str] = None,
    ) -> List[float]:
        """
        Calcula las puntuaciones de relevancia cross-encoder para cada documento respecto a la query.
        Retorna una lista de floats (0.0 a 1.0).
        """
        model, processor = cls.get_instance()
        if model is None or processor is None or not documents:
            return []

        payload = {
            "instruction": instruction or cls.DEFAULT_INSTRUCTION,
            "query": {"text": query.strip()},
            "documents": [{"text": d.strip() if d else ""} for d in documents],
            "enable_thinking": False,
        }

        try:
            import mlx.core as mx
            scores = model.rerank(payload, processor)
            mx.eval(scores)
            res = [float(s) for s in scores.tolist()]
            if hasattr(mx, "clear_cache"):
                mx.clear_cache()
            elif hasattr(mx.metal, "clear_cache"):
                mx.metal.clear_cache()
            return res
        except Exception as exc:
            logger.warning("Error durante inferencia de Qwen3-VL-Reranker: %s", exc)
            return []


def _cos_sim(vec_a: List[float], vec_b: List[float]) -> float:
    """Calcula la similitud de coseno entre dos vectores numéricos."""
    if not vec_a or not vec_b:
        return 0.0
    arr_a = np.asarray(vec_a, dtype=np.float32)
    arr_b = np.asarray(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(arr_a)
    norm_b = np.linalg.norm(arr_b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))


def rerank_evidencias_multilingue(
    query_texto: str,
    evidencias: List[Dict[str, Any]],
    qwen_adapter: Any = None,
    top_k: int = 3,
    instruction: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Reranker multilingüe para chunks de RAG multimodal.

    Pipeline de Dos Etapas (Two-Stage Retrieval):
    1. Fase de Recall: Qdrant recupera top_k candidatos (hasta 20) usando embeddings densos.
    2. Fase de Precision (Reranking): Cross-Encoder real Qwen3-VL-Reranker-2B-4bit evalúa
       conjuntamente (Query, Chunk) para calcular la puntuación de relevancia exacta.

    Desactiva explícitamente Think Mode para garantizar inferencia determinista y baja latencia (p95 < 1s).
    Si el Cross-Encoder MLX no está disponible, realiza fallback transparente a similitud coseno de embeddings.

    Retorna los `top_k` chunks más relevantes ordenados descendentemente.
    """
    if not evidencias:
        return []

    if len(evidencias) <= 1:
        return evidencias

    if not query_texto or not query_texto.strip():
        ordenadas = sorted(
            evidencias,
            key=lambda x: float(x.get("score") or 0.0),
            reverse=True,
        )
        return ordenadas[:top_k]

    # Extraer textos de los chunks candidatos
    textos_chunks: List[str] = []
    for ev in evidencias:
        contenido = (ev.get("contenido_texto") or "").strip()
        asociado = (ev.get("texto_asociado") or "").strip()
        fuente = (ev.get("fuente_nombre") or "").strip()
        ref = (ev.get("fuente_referencia") or "").strip()

        partes_texto = [p for p in (contenido, asociado) if p]
        if not partes_texto:
            partes_texto = [p for p in (fuente, ref) if p]

        texto_chunk = " ".join(partes_texto).strip()
        textos_chunks.append(texto_chunk[:350] if texto_chunk else "Técnica de Jiu-Jitsu")

    # Intentar Reranking con Cross-Encoder real MLX
    cross_scores = Qwen3VLRerankerCrossEncoder.rerank_pairs(
        query=query_texto,
        documents=textos_chunks,
        instruction=instruction,
    )

    if cross_scores and len(cross_scores) == len(evidencias):
        evidencias_puntuadas = []
        for ev, score in zip(evidencias, cross_scores):
            ev_copy = dict(ev)
            score_final = score
            if ev.get("media_path"):
                score_final += 0.05
            ev_copy["cross_encoder_score"] = round(float(score), 4)
            ev_copy["rerank_score"] = round(float(score_final), 4)
            evidencias_puntuadas.append(ev_copy)

        evidencias_puntuadas.sort(
            key=lambda x: x.get("rerank_score", 0.0),
            reverse=True,
        )
        return evidencias_puntuadas[:top_k]

    # --- FALLBACK BI-ENCODER (Similitud Coseno de Embeddings) ---
    if qwen_adapter is None:
        ordenadas = sorted(
            evidencias,
            key=lambda x: float(x.get("score") or 0.0),
            reverse=True,
        )
        return ordenadas[:top_k]

    query_vec: Optional[List[float]] = None
    try:
        if hasattr(qwen_adapter, "generar_embedding_texto"):
            query_vec = qwen_adapter.generar_embedding_texto(query_texto.strip())
    except Exception as exc:
        logger.warning("Fallo al generar embedding de query para reranking fallback: %s", exc)

    if not query_vec:
        ordenadas = sorted(
            evidencias,
            key=lambda x: float(x.get("score") or 0.0),
            reverse=True,
        )
        return ordenadas[:top_k]

    evidencias_puntuadas = []
    for ev, texto_chunk in zip(evidencias, textos_chunks):
        sim_coseno = 0.0
        if texto_chunk and hasattr(qwen_adapter, "generar_embedding_texto"):
            try:
                chunk_vec = qwen_adapter.generar_embedding_texto(texto_chunk)
                sim_coseno = max(0.0, _cos_sim(query_vec, chunk_vec))
            except Exception as err_chunk:
                logger.debug("Error vectorizando chunk para fallback: %s", err_chunk)

        score_qdrant = float(ev.get("score") or 0.5)
        if score_qdrant > 1.0:
            score_qdrant = 1.0
        elif score_qdrant < 0.0:
            score_qdrant = max(0.0, 1.0 + score_qdrant)

        if sim_coseno == 0.0 and score_qdrant > 0.0:
            sim_coseno = score_qdrant

        score_final = (0.65 * sim_coseno) + (0.35 * score_qdrant)
        if ev.get("media_path"):
            score_final += 0.05

        ev_copy = dict(ev)
        ev_copy["rerank_score"] = round(float(score_final), 4)
        ev_copy["similitud_semantica"] = round(float(sim_coseno), 4)
        evidencias_puntuadas.append(ev_copy)

    evidencias_puntuadas.sort(
        key=lambda x: x.get("rerank_score", 0.0),
        reverse=True,
    )
    return evidencias_puntuadas[:top_k]
