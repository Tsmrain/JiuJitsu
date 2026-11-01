import logging
import math
from typing import Any, Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


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
) -> List[Dict[str, Any]]:
    """
    Reranker multilingüe para chunks de RAG multimodal.

    Utiliza el espacio de embedding de 2048 dimensiones de Qwen3-VL (alineado
    para más de 30 idiomas: español, portugués, inglés) para calcular la
    similitud semántica fina entre la consulta técnica y el contenido textual
    de cada evidencia recuperada desde Qdrant.

    Combina:
    - Similitud semántica coseno directa Query <-> Chunk (peso 0.65)
    - Puntuación previa de búsqueda vectorial en Qdrant (peso 0.35)
    - Bonus leve (+0.05) para evidencias con material visual verificado

    Retorna los `top_k` chunks más relevantes ordenados descendentemente.
    """
    if not evidencias:
        return []

    if len(evidencias) <= 1:
        return evidencias

    if not query_texto or not query_texto.strip() or qwen_adapter is None:
        # Fallback sin reranking semántico: ordenar por score inicial y recortar a top_k
        ordenadas = sorted(
            evidencias,
            key=lambda x: float(x.get("score") or 0.0),
            reverse=True,
        )
        return ordenadas[:top_k]

    # 1. Obtener embedding de la query si el adaptador está disponible
    query_vec: Optional[List[float]] = None
    try:
        if hasattr(qwen_adapter, "generar_embedding_texto"):
            query_vec = qwen_adapter.generar_embedding_texto(query_texto.strip())
    except Exception as exc:
        logger.warning("Fallo al generar embedding de query para reranking: %s", exc)

    if not query_vec:
        ordenadas = sorted(
            evidencias,
            key=lambda x: float(x.get("score") or 0.0),
            reverse=True,
        )
        return ordenadas[:top_k]

    evidencias_puntuadas = []

    for ev in evidencias:
        # Extraer texto del chunk
        contenido = (ev.get("contenido_texto") or "").strip()
        asociado = (ev.get("texto_asociado") or "").strip()
        fuente = (ev.get("fuente_nombre") or "").strip()
        ref = (ev.get("fuente_referencia") or "").strip()

        partes_texto = [p for p in (contenido, asociado) if p]
        if not partes_texto:
            partes_texto = [p for p in (fuente, ref) if p]

        texto_chunk = " ".join(partes_texto).strip()

        sim_coseno = 0.0
        if texto_chunk and hasattr(qwen_adapter, "generar_embedding_texto"):
            try:
                chunk_vec = qwen_adapter.generar_embedding_texto(texto_chunk[:1000])
                sim_coseno = max(0.0, _cos_sim(query_vec, chunk_vec))
            except Exception as err_chunk:
                logger.debug("Error vectorizando chunk para reranking: %s", err_chunk)

        # Normalizar score de Qdrant (típicamente entre 0.0 y 1.0 para similitud coseno)
        score_qdrant = float(ev.get("score") or 0.5)
        # Si el score de Qdrant viene en escala > 1.0 (ej. distancia L2 negativa), clamp
        if score_qdrant > 1.0:
            score_qdrant = 1.0
        elif score_qdrant < 0.0:
            score_qdrant = max(0.0, 1.0 + score_qdrant)

        # Si no hubo texto para vectorizar pero hay score qdrant, usar score qdrant como proxy
        if sim_coseno == 0.0 and score_qdrant > 0.0:
            sim_coseno = score_qdrant

        # Score ponderado: 65% afinidad semántica en lenguaje natural + 35% retrieval inicial
        score_final = (0.65 * sim_coseno) + (0.35 * score_qdrant)

        # Bonus para evidencia visual verificada
        if ev.get("media_path"):
            score_final += 0.05

        ev_copy = dict(ev)
        ev_copy["rerank_score"] = round(float(score_final), 4)
        ev_copy["similitud_semantica"] = round(float(sim_coseno), 4)
        evidencias_puntuadas.append(ev_copy)

    # Ordenar descendentemente por rerank_score
    evidencias_puntuadas.sort(
        key=lambda x: x.get("rerank_score", 0.0),
        reverse=True,
    )

    return evidencias_puntuadas[:top_k]
