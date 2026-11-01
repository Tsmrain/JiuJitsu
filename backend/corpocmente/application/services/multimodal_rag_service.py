import logging
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


def construir_query_texta_rag(
    tecnica_nombre: str,
    discrepancias: List[str],
) -> str:
    disp = ", ".join([str(x) for x in discrepancias if x]) or "desviaciones biomecánicas detectadas"

    return (
        f"Técnica: {tecnica_nombre}. "
        f"Errores biomecánicos detectados: {disp}. "
        "Recupera referencia visual del profesor y explicación correctiva precisa."
    )


# Alias
construir_query_textual_rag = construir_query_texta_rag


def obtener_evidencias_rag_multimodal(
    qwen_adapter,
    qdrant_adapter,
    tecnica_id: Optional[UUID],
    tecnica_nombre: str,
    discrepancias: List[str],
    frame_critico_path: Optional[str] = None,
    video_referencia_path: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Combina:
    - embedding de imagen del frame crítico del alumno
    - embedding textual de técnica + errores

    y devuelve evidencias priorizadas desde Qdrant.
    """
    vectores_consulta = []

    if frame_critico_path and os.path.isfile(frame_critico_path):
        try:
            vector_imagen = qwen_adapter.generar_embedding(
                image_path=frame_critico_path,
                prompt=(
                    f"Frame crítico del alumno ejecutando {tecnica_nombre}. "
                    "Buscar referencias visuales del profesor con postura similar o corregida."
                ),
            )
            vectores_consulta.append(vector_imagen)
        except Exception as exc:
            logger.warning("No se pudo vectorizar frame crítico para RAG visual: %s", exc)

    query_textual = construir_query_texta_rag(tecnica_nombre, discrepancias)

    try:
        vector_texto = qwen_adapter.generar_embedding_texto(query_textual)
        vectores_consulta.append(vector_texto)
    except Exception as exc:
        logger.warning("No se pudo generar embedding textual para RAG: %s", exc)

    if not vectores_consulta:
        logger.warning("No hay vectores de consulta para recuperar evidencia RAG.")
        return []

    retrieval_mode = os.getenv("RETRIEVAL_MODE", "hybrid").lower()
    if retrieval_mode in ("hybrid", "bm25"):
        try:
            from corpocmente.domain.services.hybrid_retriever import HybridRetriever
            return HybridRetriever.recuperar(
                query_texto=query_textual,
                qdrant_adapter=qdrant_adapter,
                qwen_adapter=qwen_adapter,
                tecnica_id=tecnica_id,
                limit=limit,
                modo=retrieval_mode,
                vectores_consulta=vectores_consulta,
            )
        except Exception as exc_h:
            logger.warning("Fallo en recuperación híbrida (%s), fallback a denso: %s", retrieval_mode, exc_h)

    if hasattr(qdrant_adapter, "recuperar_evidencias_rag_multimodal"):
        return qdrant_adapter.recuperar_evidencias_rag_multimodal(
            vectores_consulta=vectores_consulta,
            tecnica_id=tecnica_id,
            limit=limit,
            video_referencia_path=video_referencia_path,
        )
    elif hasattr(qdrant_adapter, "recuperar_evidencias_rag"):
        return qdrant_adapter.recuperar_evidencias_rag(
            vectores_consulta=vectores_consulta,
            tecnica_id=tecnica_id,
            limit=limit,
            video_referencia_path=video_referencia_path,
        )
    elif hasattr(qdrant_adapter, "recuperar_contexto_rag"):
        texto = qdrant_adapter.recuperar_contexto_rag(vectores_consulta[-1], tecnica_id)
        if texto:
            return [{"contenido_texto": texto, "modalidad": "texto"}]
        return []

    return []


def formatear_evidencias_texto(evidencias: List[Dict[str, Any]]) -> str:
    """
    Convierte evidencias RAG a texto para incluir en el prompt del VLM.
    Las imágenes se pasan aparte como parts multimodales.
    """
    if not evidencias:
        return ""

    lineas = []

    for i, ev in enumerate(evidencias, start=1):
        fuente = ev.get("fuente_nombre") or ev.get("fuente_tipo") or "Fuente desconocida"
        ref = ev.get("fuente_referencia") or ""
        timestamp = ev.get("timestamp_seconds")
        frame_idx = ev.get("frame_idx")
        contenido = ev.get("contenido_texto") or ""
        texto_asociado = ev.get("texto_asociado") or ""

        metadatos = []
        if timestamp is not None:
            metadatos.append(f"minuto {float(timestamp) / 60:.2f}")
        if frame_idx is not None:
            metadatos.append(f"frame {frame_idx}")
        if ev.get("media_path"):
            metadatos.append("evidencia visual disponible")

        meta = " | ".join(metadatos)
        bloque = f"[Evidencia {i}] Fuente: {fuente}"
        if ref:
            bloque += f" — {ref}"
        if meta:
            bloque += f" ({meta})"

        cuerpo = contenido
        if texto_asociado:
            cuerpo = f"{cuerpo}\n{texto_asociado}".strip()

        if cuerpo:
            bloque += f"\n{cuerpo}"

        lineas.append(bloque)

    return "\n\n---\n\n".join(lineas)
