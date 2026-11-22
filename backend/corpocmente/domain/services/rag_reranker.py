import logging
import math
import os
import re
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
            scores = model.rerank(payload, processor)
            # Los doubles de prueba no son tensores MLX; no importamos MLX (que
            # inicializa Metal) únicamente para materializar un objeto simulado.
            if scores.__class__.__module__.startswith("mlx"):
                import mlx.core as mx
                mx.eval(scores)
            else:
                mx = None
            res = [float(s) for s in scores.tolist()]
            if mx is not None and hasattr(mx, "clear_cache"):
                mx.clear_cache()
            elif mx is not None and hasattr(mx.metal, "clear_cache"):
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


def _extraer_ventana_relevante_rerank(
    texto: str,
    query_texto: str,
    sinonimos_query: set,
    max_chars: int = 1200,
) -> str:
    """
    Para chunks extensos multi-página (ej. 8000 chars), selecciona la sección o ventana
    que mejor coincide con la consulta y sus sinónimos en lugar de truncar ciegamente a [:400].
    """
    clean_text = (texto or "").strip()
    if len(clean_text) <= max_chars:
        return clean_text

    secciones = re.split(r"(?=\[P[aá]gina\s+\d+\])", clean_text, flags=re.IGNORECASE)
    secciones = [s.strip() for s in secciones if s.strip()]
    if len(secciones) <= 1:
        # Dividir en ventanas deslizantes si el bloque no tiene marcadores [Página X]
        paso = 700
        secciones = [clean_text[i:i + max_chars] for i in range(0, len(clean_text), paso)]

    stopwords = {
        "como", "hace", "hacer", "para", "sobre", "desde", "esta", "este",
        "jiu", "jitsu", "bjj", "paso", "cual", "the", "how", "with", "tecnica", "técnica",
    }
    tokens = {
        tok for tok in re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑçÇãõÃÕ0-9\-]{3,}", query_texto.lower())
        if tok not in stopwords
    }
    for syn in sinonimos_query:
        for tok in re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑçÇãõÃÕ0-9\-]{3,}", str(syn).lower()):
            if tok not in stopwords:
                tokens.add(tok)

    if not tokens:
        return clean_text[:max_chars]

    scored = []
    for idx_sec, sec in enumerate(secciones):
        sec_lower = sec.lower()
        head_lower = sec_lower[:200]
        score = sum(3 for tok in tokens if tok in head_lower) + sum(1 for tok in tokens if tok in sec_lower)
        # Penalizar páginas/encabezados vacíos sin cuerpo descriptivo
        if len(sec.strip()) < 160 and "descri" not in sec_lower:
            score = max(0, score - 5)
        scored.append((score, idx_sec, sec))

    best_score = max(s[0] for s in scored)
    if best_score <= 0:
        return clean_text[:max_chars]

    scored.sort(key=lambda x: (-x[0], x[1]))
    mejor = scored[0][2]
    if len(mejor) <= max_chars:
        return mejor

    # Centrar ventana dentro de la mejor sección alrededor del primer hit de token
    mejor_lower = mejor.lower()
    hit_pos = -1
    for tok in sorted(tokens, key=len, reverse=True):
        pos = mejor_lower.find(tok)
        if pos != -1:
            hit_pos = pos
            break
    if hit_pos == -1:
        return mejor[:max_chars]
    start = max(0, hit_pos - max_chars // 3)
    return mejor[start:start + max_chars].strip()


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

    try:
        from corpocmente.domain.glossary.glossary_service import (
            cargar_glosario,
            expandir_query_con_glosario,
            obtener_sinonimos_multilingues,
        )
        sinonimos_query = obtener_sinonimos_multilingues(query_texto)
        query_expandida_ce = expandir_query_con_glosario(query_texto, max_sinonimos=12) or query_texto
        glosario_items = cargar_glosario().get("sinonimos", [])
    except Exception:
        sinonimos_query = set()
        query_expandida_ce = query_texto
        glosario_items = []

    # Identificar grupos conceptuales del glosario presentes en la query (ej: {"armbar", "mount"})
    q_lower = query_texto.lower()
    grupos_query: List[tuple] = []
    for entry in glosario_items:
        variantes = set()
        for lang_key in ("es", "pt", "en"):
            for v in entry.get(lang_key, []):
                if v:
                    variantes.add(v.lower().strip())
        canon = (entry.get("canonical") or "").lower().strip()
        if canon:
            variantes.add(canon)
        if any(re.search(r"\b" + re.escape(v) + r"\b", q_lower) for v in variantes):
            grupos_query.append((canon or next(iter(variantes), ""), variantes))

    # Extraer textos sustanciales de los chunks candidatos (ventanas centradas en la consulta)
    textos_chunks: List[str] = []
    placeholders_vacios: List[bool] = []
    for ev in evidencias:
        contenido = (ev.get("contenido_texto") or "").strip()
        asociado = (ev.get("texto_asociado") or "").strip()
        fuente = (ev.get("fuente_nombre") or "").strip()
        ref = (ev.get("fuente_referencia") or "").strip()

        partes_texto = [p for p in (contenido, asociado) if p]
        if not partes_texto:
            partes_texto = [p for p in (fuente, ref) if p]

        texto_chunk = " ".join(partes_texto).strip()
        texto_sin_placeholder = re.sub(
            r"^\[Imagen:\s*Página\s+\d+\s+del\s+manual\s+PDF\]\s*",
            "",
            texto_chunk,
            flags=re.IGNORECASE,
        ).strip()
        es_vacio = len(texto_sin_placeholder) < 25 and bool(ev.get("media_path"))
        placeholders_vacios.append(es_vacio)
        if texto_sin_placeholder:
            fragmento = _extraer_ventana_relevante_rerank(
                texto_sin_placeholder,
                query_texto=query_texto,
                sinonimos_query=sinonimos_query,
                max_chars=1200,
            )
            textos_chunks.append(fragmento)
        else:
            textos_chunks.append("Página visual del manual sin texto")

    def _bonus_glosario(texto_doc: str, base_score: float, qdrant_score: float, es_vacio: bool) -> float:
        if es_vacio or not texto_doc:
            return 0.0
        doc_lower = texto_doc.lower()
        if grupos_query:
            grupos_hit = sum(
                1 for _, vars_set in grupos_query
                if any(v in doc_lower for v in vars_set)
            )
            if grupos_hit >= 2 and (base_score >= 0.15 or qdrant_score >= 0.40):
                return 0.50
            if grupos_hit == 1 and base_score >= 0.25:
                return 0.22
            return 0.0
        if not sinonimos_query or base_score < 0.25:
            return 0.0
        hits = sum(1 for s in sinonimos_query if s and s in doc_lower)
        if hits >= 2:
            return 0.35
        if hits == 1:
            return 0.22
        return 0.0

    # Intentar Reranking con Cross-Encoder real MLX
    cross_scores = Qwen3VLRerankerCrossEncoder.rerank_pairs(
        query=query_expandida_ce,
        documents=textos_chunks,
        instruction=instruction,
    )

    if cross_scores and len(cross_scores) == len(evidencias):
        evidencias_puntuadas = []
        for ev, score, texto_doc, es_vacio in zip(evidencias, cross_scores, textos_chunks, placeholders_vacios):
            ev_copy = dict(ev)
            q_score = float(ev.get("score") or 0.0)
            score_final = float(score) * (0.5 if es_vacio else 1.0)
            if ev.get("media_path") and not es_vacio:
                score_final += 0.05
            score_final = min(1.0, score_final + _bonus_glosario(texto_doc, float(score), q_score, es_vacio))
            ev_copy["cross_encoder_score"] = round(float(score), 4)
            ev_copy["rerank_score"] = round(float(score_final), 4)
            ev_copy["_matched_snippet"] = texto_doc
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
