import os
import logging
from typing import Optional
from uuid import UUID, uuid4

from corpocmente.domain.entities.models import AnalisisResultDTO
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
from corpocmente.domain.strategies.prompt_strategies import EnglishPromptStrategy
from corpocmente.domain.services.rag_reranker import rerank_evidencias_multilingue
from corpocmente.application.services.multimodal_rag_service import (
    formatear_evidencias_texto,
    incluir_mensaje_profesor,
    obtener_evidencias_rag_multimodal,
)

logger = logging.getLogger(__name__)

UMBRAL_RELEVANCIA_RAG = 0.65


def _sanitizar_respuesta_coach(texto: str, idioma: str = "es") -> str:
    """
    Limpia citas rígidas de página '(p. X)' y reemplaza roles literales de manual ('Tori'/'Uke')
    si el modelo local los filtró desde el texto fuente.
    """
    import re
    if not texto or not isinstance(texto, str):
        return ""
    res = texto.strip()
    # Remover citas de página como '(p. 20)', '(pág. 20)', '(page 20)' sin romper la puntuación
    res = re.sub(r"\s*\(\s*(?:p(?:ág|ag)?\.?|page)\s*\d+[^)]*\)", "", res, flags=re.IGNORECASE)

    lang = (idioma or "es").lower().strip()
    if lang.startswith("pt"):
        res = re.sub(r"\bde\s+uke\b", "do seu parceiro", res, flags=re.IGNORECASE)
        res = re.sub(r"\bpara\s+uke\b", "para seu parceiro", res, flags=re.IGNORECASE)
        res = re.sub(r"\buke\b", "seu parceiro", res, flags=re.IGNORECASE)
        res = re.sub(r"\btori\s+deve\b", "Você deve", res, flags=re.IGNORECASE)
        res = re.sub(r"\btori\b", "você", res, flags=re.IGNORECASE)
    elif lang.startswith("en"):
        res = re.sub(r"\buke's\b", "your partner's", res, flags=re.IGNORECASE)
        res = re.sub(r"\buke\b", "your partner", res, flags=re.IGNORECASE)
        res = re.sub(r"\btori\s+must\b", "You must", res, flags=re.IGNORECASE)
        res = re.sub(r"\btori\s+should\b", "You should", res, flags=re.IGNORECASE)
        res = re.sub(r"\btori\b", "you", res, flags=re.IGNORECASE)
    else:
        res = re.sub(r"\b(?:de|del)\s+uke\b", "de tu compañero", res, flags=re.IGNORECASE)
        res = re.sub(r"\b(?:a|al|para)\s+uke\b", "a tu compañero", res, flags=re.IGNORECASE)
        res = re.sub(r"\buke\b", "tu compañero", res, flags=re.IGNORECASE)
        res = re.sub(r"\btori\s+debe\b", "Debes", res, flags=re.IGNORECASE)
        res = re.sub(r"\btori\b", "tú", res, flags=re.IGNORECASE)

    # Limpiar espacios dobles antes de signos de puntuación
    res = re.sub(r"\s+([.,;:])", r"\1", res)
    res = re.sub(r" {2,}", " ", res).strip()
    return res

class IntelligenceAnalysisFacade:
    def __init__(self, 
                 yolo_adapter: YOLOPoseAdapter, 
                 qdrant_adapter: QdrantVectorAdapter, 
                 gemini_adapter: LocalVLMAdapter,
                 qwen_adapter: QwenEmbeddingAdapter = None):
        self.yolo = yolo_adapter
        self.qdrant = qdrant_adapter
        self.gemini = gemini_adapter
        self.qwen = qwen_adapter

    def ejecutar_analisis_completo(
        self,
        video_path: str,
        tecnica_id: UUID,
        tecnica_nombre: str,
        video_referencia_path: Optional[str] = None,
        evaluacion_id: Optional[str] = None,
        persona_idx: Optional[int] = None,
        mensaje_profesor: str = "",
        idioma: str = "es"
    ) -> AnalisisResultDTO:
        from corpocmente.domain.entities.models import EsqueletoBiomecanico

        # 0. Recuperar patrones activos de referencia desde Qdrant (Soporte 1:N)
        secuencias_referencia = []
        if hasattr(self.qdrant, "obtener_todas_secuencias_referencia"):
            try:
                res_all = self.qdrant.obtener_todas_secuencias_referencia(tecnica_id=tecnica_id)
                if isinstance(res_all, list) and len(res_all) > 0 and isinstance(res_all[0], list):
                    secuencias_referencia = res_all
            except Exception as e_q:
                logger.warning(f"Error consultando obtener_todas_secuencias_referencia: {e_q}")

        if not secuencias_referencia and hasattr(self.qdrant, "obtener_secuencia_referencia"):
            try:
                res_q = self.qdrant.obtener_secuencia_referencia(tecnica_id=tecnica_id)
                if isinstance(res_q, list) and len(res_q) > 0 and isinstance(res_q[0], list):
                    if len(res_q[0]) > 0 and isinstance(res_q[0][0], list):
                        secuencias_referencia = res_q
                    else:
                        secuencias_referencia = [res_q]
            except Exception as e_q:
                logger.warning(f"Error consultando obtener_secuencia_referencia: {e_q}")

        # Si no hay patrón en Qdrant pero se proveyó video de referencia, asegurar ingesta
        if not secuencias_referencia and video_referencia_path and hasattr(self.qdrant, "asegurar_poses_referencia"):
            try:
                self.qdrant.asegurar_poses_referencia(
                    tecnica_id=tecnica_id,
                    video_referencia_path=video_referencia_path,
                    yolo_adapter=self.yolo,
                    tecnica_nombre=tecnica_nombre
                )
                if hasattr(self.qdrant, "obtener_todas_secuencias_referencia"):
                    res_all = self.qdrant.obtener_todas_secuencias_referencia(tecnica_id=tecnica_id)
                    if isinstance(res_all, list) and len(res_all) > 0 and isinstance(res_all[0], list):
                        secuencias_referencia = res_all
                elif hasattr(self.qdrant, "obtener_secuencia_referencia"):
                    res_q = self.qdrant.obtener_secuencia_referencia(tecnica_id=tecnica_id)
                    if isinstance(res_q, list) and len(res_q) > 0 and isinstance(res_q[0], list):
                        if len(res_q[0]) > 0 and isinstance(res_q[0][0], list):
                            secuencias_referencia = res_q
                        else:
                            secuencias_referencia = [res_q]
            except Exception as e_ref:
                logger.warning(f"No se pudo auto-ingerir video de referencia del profesor: {e_ref}")

        secuencia_alumno = None
        frame_idxs_alumno = None
        if hasattr(self.yolo, "extraer_secuencia"):
            try:
                from corpocmente.config import settings
                frame_stride = max(1, int(getattr(settings, "FRAME_STRIDE", 1)))
            except Exception:
                frame_stride = 1
            logger.info(
                "[INTEGRACION] Facade -> extraer_secuencia video=%s persona_idx=%s patrones_ref=%d frame_stride=%d",
                video_path,
                persona_idx,
                len(secuencias_referencia),
                frame_stride,
            )
            ext_res = self.yolo.extraer_secuencia(
                video_path,
                persona_idx_inicial=persona_idx,
                evaluacion_id=str(evaluacion_id) if evaluacion_id else None,
                tecnica_id=str(tecnica_id) if tecnica_id else None,
                frame_stride=frame_stride,
            )
            if isinstance(ext_res, dict):
                secuencia_alumno = ext_res.get("secuencia_kpts", [])
                frame_idxs_alumno = ext_res.get("frame_idxs")
                if frame_idxs_alumno is not None and len(frame_idxs_alumno) != len(secuencia_alumno):
                    frame_idxs_alumno = None
                tracking_stats = ext_res.get("tracking_stats")
                if tracking_stats and tracking_stats.get("perdido_definitivamente_en_frame") is not None:
                    raise ValueError(
                        f"El track del alumno (ID={tracking_stats.get('id_principal')}) se perdió en el frame "
                        f"{tracking_stats.get('perdido_definitivamente_en_frame')}. Ajusta la configuración del tracker o recorta el video."
                    )
                cobertura = (
                    float(tracking_stats.get("cobertura_principal", ext_res.get("cobertura", 0.0)))
                    if tracking_stats
                    else ext_res.get("cobertura", 0.0)
                )
                total_frames = ext_res.get("total_frames", 0)
                if isinstance(total_frames, (int, float)) and isinstance(cobertura, (int, float)):
                    if total_frames == 0 or cobertura < 0.40:
                        raise ValueError(f"Tracking insuficiente en el video del alumno: cobertura {cobertura*100:.1f}% < 40%.")

        esqueletos_frames = None
        if secuencia_alumno is None:
            esqueletos_frames = self.yolo.extraer_keypoints(video_path)
            secuencia_alumno = [e.to_vector_array() if hasattr(e, "to_vector_array") else e for e in esqueletos_frames]

        if not secuencia_alumno:
            raise ValueError("No se pudo detectar el esqueleto biomecánico en el video del alumno.")

        # 2. Comparación DTW multi-referencia (1:N) o fallback a máxima diferencia
        mejor_dtw_res = None
        if secuencias_referencia:
            from corpocmente.domain.biomechanics.dtw_comparator import comparar_secuencias_con_dtw
            logger.info("Comparando video del alumno contra %d patrón(es) de referencia activo(s) para técnica %s", len(secuencias_referencia), tecnica_id)
            for idx_ref, sec_ref in enumerate(secuencias_referencia):
                try:
                    dtw_cand = comparar_secuencias_con_dtw(
                        sec_ref,
                        secuencia_alumno,
                        frame_idxs_alumno=frame_idxs_alumno,
                    )
                    score_cand = dtw_cand.get("score_similitud", 0.0)
                    logger.debug("Patrón ref #%d: score_similitud = %.2f%%", idx_ref + 1, score_cand)
                    if mejor_dtw_res is None or score_cand > mejor_dtw_res.get("score_similitud", -1.0):
                        mejor_dtw_res = dtw_cand
                except Exception as e_dtw:
                    logger.warning("Error comparando con patrón #%d: %s", idx_ref + 1, e_dtw)

        if mejor_dtw_res:
            similitud = mejor_dtw_res["score_similitud"]
            frame_alumno_critico = mejor_dtw_res["frame_alumno_critico"]
            seq_alumno_critico = mejor_dtw_res.get("seq_alumno_critico", frame_alumno_critico)
            arts_criticas = mejor_dtw_res.get("articulaciones_criticas", [])
            from corpocmente.infrastructure.ai.adapters import obtener_nombres_articulaciones
            nombres_arts = obtener_nombres_articulaciones(arts_criticas, idioma=idioma)
            lang_clean = (idioma or "es").lower().strip()
            if lang_clean in ("pt", "portuguese", "português", "portugues"):
                discrepancias_detectadas = [
                    f"Ajuste necessário em {art} durante {tecnica_nombre}."
                    for art in nombres_arts
                ]
            elif lang_clean in ("en", "english"):
                discrepancias_detectadas = [
                    f"Adjustment needed at {art} during {tecnica_nombre}."
                    for art in nombres_arts
                ]
            else:
                discrepancias_detectadas = [
                    f"Ajuste necesario en {art} durante {tecnica_nombre}."
                    for art in nombres_arts
                ]
            dtw_distance = mejor_dtw_res.get("dtw_distance")
            dtw_normalizado = mejor_dtw_res.get("dtw_normalizado")
            crit_pos = (
                frame_idxs_alumno.index(frame_alumno_critico)
                if frame_idxs_alumno and frame_alumno_critico in frame_idxs_alumno
                else seq_alumno_critico
            )
            kpts_critico = secuencia_alumno[crit_pos] if 0 <= crit_pos < len(secuencia_alumno) else None
        elif hasattr(self.qdrant, "buscar_maxima_diferencia"):
            if esqueletos_frames is not None:
                esqueletos_para_qdrant = esqueletos_frames
            else:
                esqueletos_para_qdrant = []
                for i, kp in enumerate(secuencia_alumno):
                    vec = list(kp)
                    if len(vec) < 133:
                        vec.extend([0.0] * (133 - len(vec)))
                    real_idx = (
                        frame_idxs_alumno[i]
                        if frame_idxs_alumno and i < len(frame_idxs_alumno)
                        else i
                    )
                    esqueletos_para_qdrant.append(EsqueletoBiomecanico(frame_idx=real_idx, keypoints133=vec[:133], angulos_articulares={}))
            resultado_comparacion = self.qdrant.buscar_maxima_diferencia(esqueletos_para_qdrant, tecnica_id)
            similitud = resultado_comparacion.score
            frame_alumno_critico = getattr(resultado_comparacion, "frame_alumno_idx", 0) or 0
            arts_criticas = getattr(resultado_comparacion, "articulaciones_criticas", [])
            discrepancias_detectadas = resultado_comparacion.discrepancias
            kpts_critico = getattr(resultado_comparacion, "keypoints_alumno", None)
            dtw_distance = None
            dtw_normalizado = None
        else:
            raise ValueError(f"No existe un patrón biomecánico activo registrado para la técnica {tecnica_id}")

        # 3. Extraer y resaltar el error en el fotograma crítico del alumno
        eval_suffix = evaluacion_id or uuid4().hex[:8]
        out_frame_path = f"/tmp/corpocmente_frames/critico_{eval_suffix}.jpg"
        out_clean_path = f"/tmp/corpocmente_frames/clean_{eval_suffix}.jpg"
        frame_limpio = None

        if os.path.exists(video_path) and hasattr(self.yolo, "extraer_frame_y_dibujar_error"):
            try:
                frame_resaltado = self.yolo.extraer_frame_y_dibujar_error(
                    video_path=video_path,
                    frame_idx=frame_alumno_critico,
                    keypoints133=kpts_critico,
                    articulaciones_criticas=arts_criticas,
                    output_path=out_frame_path,
                    clean_output_path=out_clean_path,
                    tecnica_nombre=tecnica_nombre,
                    persona_idx=persona_idx,
                    idioma=idioma,
                )
                if os.path.isfile(out_clean_path):
                    frame_limpio = out_clean_path
            except TypeError:
                try:
                    frame_resaltado = self.yolo.extraer_frame_y_dibujar_error(
                        video_path=video_path,
                        frame_idx=frame_alumno_critico,
                        keypoints133=kpts_critico,
                        articulaciones_criticas=arts_criticas,
                        output_path=out_frame_path,
                        clean_output_path=out_clean_path,
                        tecnica_nombre=tecnica_nombre,
                    )
                    if os.path.isfile(out_clean_path):
                        frame_limpio = out_clean_path
                except TypeError:
                    frame_resaltado = self.yolo.extraer_frame_y_dibujar_error(
                        video_path=video_path,
                        frame_idx=frame_alumno_critico,
                        keypoints133=kpts_critico,
                        articulaciones_criticas=arts_criticas,
                        output_path=out_frame_path,
                        tecnica_nombre=tecnica_nombre,
                    )
        elif hasattr(self.yolo, "dibujar_error_en_frame"):
            frame_resaltado = self.yolo.dibujar_error_en_frame(
                out_frame_path,
                discrepancias_detectadas
            )
        else:
            frame_resaltado = out_frame_path

        if not frame_limpio and os.path.exists(video_path) and hasattr(self.yolo, "extraer_frame_limpio"):
            frame_limpio = self.yolo.extraer_frame_limpio(
                video_path=video_path,
                frame_idx=frame_alumno_critico,
                output_path=out_clean_path,
            )

        from pathlib import Path
        es_limpio_valido = isinstance(frame_limpio, (str, bytes, Path)) and os.path.isfile(frame_limpio)
        frame_para_embedding = frame_limpio if es_limpio_valido else frame_resaltado
        # Para que Qwen3-VL observe agarres, solapas y postura real sin oclusión gráfica de líneas/puntos,
        # enviamos el fotograma limpio (fallback al anotado si no existe archivo limpio en disco).
        frame_para_vlm = frame_para_embedding

        # 4. Evaluación y feedback condicional (IA sólo si hay errores)
        UMBRAL_ACEPTABLE = 85.0
        if similitud >= UMBRAL_ACEPTABLE:
            lang_clean = (idioma or "es").lower().strip()
            if lang_clean in ("pt", "portuguese", "português", "portugues"):
                feedback_summary = "Boa técnica"
                feedback_correction = "Técnica executada corretamente. Excelente trabalho!"
            elif lang_clean in ("es", "spanish", "español"):
                feedback_summary = "Buena técnica"
                feedback_correction = "¡Técnica ejecutada correctamente. Excelente trabajo!"
            else:
                feedback_summary = "Good technique"
                feedback_correction = "Technique executed correctly. Excellent work!"
            feedback_texto = feedback_correction
        else:
            contexto_profundo = ""
            evidencias_rag = []
            tiene_contexto_rag = False

            if self.qwen:
                try:
                    evidencias_candidatas = obtener_evidencias_rag_multimodal(
                        qwen_adapter=self.qwen,
                        qdrant_adapter=self.qdrant,
                        tecnica_id=tecnica_id,
                        tecnica_nombre=tecnica_nombre,
                        discrepancias=discrepancias_detectadas,
                        frame_critico_path=frame_para_embedding,
                        video_referencia_path=video_referencia_path,
                        limit=5,
                    )
                    # Filtrar únicamente evidencias de manuales (no mensajes de profesor) para evaluar la relevancia RAG
                    manuales_candidatos = [
                        e for e in evidencias_candidatas
                        if e.get("fuente_tipo") != "instructor_message" and e.get("tipo") != "instructor_message"
                    ]

                    # Fallback global: si la técnica no tiene manuales propios (o solo tiene frames de video),
                    # consultar la biblioteca global (tecnica_id=None) antes de rendirse.
                    tiene_manual_especifico = any(
                        e.get("fuente_tipo") not in ("video_referencia", "video_frame")
                        for e in manuales_candidatos
                    )
                    if not manuales_candidatos or not tiene_manual_especifico:
                        evidencias_globales = obtener_evidencias_rag_multimodal(
                            qwen_adapter=self.qwen,
                            qdrant_adapter=self.qdrant,
                            tecnica_id=None,
                            tecnica_nombre=tecnica_nombre,
                            discrepancias=discrepancias_detectadas,
                            frame_critico_path=frame_para_embedding,
                            video_referencia_path=video_referencia_path,
                            limit=5,
                        )
                        ids_existentes = {e.get("id") for e in manuales_candidatos if e.get("id")}
                        for ev_g in evidencias_globales:
                            if ev_g.get("fuente_tipo") == "instructor_message" or ev_g.get("tipo") == "instructor_message":
                                continue
                            if ev_g.get("id") and ev_g.get("id") in ids_existentes:
                                continue
                            manuales_candidatos.append(ev_g)
                            if ev_g.get("id"):
                                ids_existentes.add(ev_g.get("id"))

                    if manuales_candidatos:
                        # Reranking multilingüe con Cross-Encoder real Qwen3-VL (Iteración 3R)
                        # Usar el nombre de la técnica limpio para no diluir la consulta cross-lingual con plantillas de discrepancias.
                        query_rerank = (tecnica_nombre or "").strip() or ", ".join(discrepancias_detectadas)
                        evidencias_reranked = rerank_evidencias_multilingue(
                            query_texto=query_rerank,
                            evidencias=manuales_candidatos,
                            qwen_adapter=self.qwen,
                            top_k=5,
                            instruction="Given a jiu-jitsu technique question, retrieve the manual passage that answers it.",
                        )
                        if evidencias_reranked:
                            mejor_manual = evidencias_reranked[0]
                            score_relevancia = float(
                                mejor_manual.get("rerank_score")
                                if mejor_manual.get("rerank_score") is not None
                                else mejor_manual.get("score", 0.0)
                            )
                            if score_relevancia >= UMBRAL_RELEVANCIA_RAG:
                                tiene_contexto_rag = True
                                evidencias_rag = [
                                    e for e in evidencias_reranked
                                    if float(
                                        e.get("rerank_score")
                                        if e.get("rerank_score") is not None
                                        else e.get("score", 0.0)
                                    ) >= UMBRAL_RELEVANCIA_RAG
                                ][:3] or [mejor_manual]
                                evidencias_para_prompt = []
                                for ev_sel in evidencias_rag:
                                    ev_p = dict(ev_sel)
                                    snippet = ev_p.get("_matched_snippet")
                                    texto_orig = str(ev_p.get("contenido_texto") or "")
                                    if snippet and len(texto_orig) > 1600:
                                        import re as _re
                                        if ev_p.get("pagina") is None:
                                            m_pag = _re.search(r"\[P[aá]gina\s+(\d+)\]", snippet, flags=_re.IGNORECASE)
                                            if m_pag:
                                                ev_p["pagina"] = int(m_pag.group(1))
                                        # Si el snippet termina cortado antes del final del bloque largo, unir la continuación
                                        # del bloque siguiente del mismo manual para no cortar una técnica a mitad de frase.
                                        if snippet and snippet.rstrip()[-1:] not in (".", "!", "?"):
                                            fuente_sel = ev_p.get("fuente_nombre")
                                            cont_added = False
                                            for cand in manuales_candidatos:
                                                if cand.get("id") == ev_p.get("id"):
                                                    continue
                                                if fuente_sel and cand.get("fuente_nombre") != fuente_sel:
                                                    continue
                                                cand_txt = (cand.get("contenido_texto") or "").strip()
                                                if len(cand_txt) > 500 and not cand_txt.lstrip().startswith("[Página"):
                                                    tail = _re.split(r"\[P[aá]gina\s+\d+\]", cand_txt, maxsplit=1, flags=_re.IGNORECASE)[0].strip()
                                                    if tail and not tail[:20].isdigit():
                                                        snippet = (snippet.rstrip() + tail[:900]).strip()
                                                        cont_added = True
                                                        break
                                            if not cont_added:
                                                pos_snip = texto_orig.find(snippet[-80:])
                                                if pos_snip != -1:
                                                    extra = texto_orig[pos_snip + 80:pos_snip + 980]
                                                    extra = _re.split(r"\[P[aá]gina\s+\d+\]", extra, maxsplit=1, flags=_re.IGNORECASE)[0]
                                                    if extra:
                                                        snippet = (snippet + extra).strip()
                                        ev_p["contenido_texto"] = snippet
                                    evidencias_para_prompt.append(ev_p)
                                contexto_profundo = formatear_evidencias_texto(evidencias_para_prompt)
                                if contexto_profundo:
                                    contexto_profundo = (
                                        "\n\n[Evidence retrieved from manuals and instructor reference videos]:\n"
                                        + contexto_profundo
                                    )
                                logger.info(
                                    "Prioridad 1 activa: RAG manual válido para '%s' (score=%.4f >= %.2f)",
                                    tecnica_nombre,
                                    score_relevancia,
                                    UMBRAL_RELEVANCIA_RAG,
                                )
                            else:
                                logger.info(
                                    "RAG manual por debajo del umbral para '%s' (score=%.4f < %.2f). RAG descartado.",
                                    tecnica_nombre,
                                    score_relevancia,
                                    UMBRAL_RELEVANCIA_RAG,
                                )
                except Exception as e_rag:
                    logger.warning("Fallo en recuperación RAG multimodal o reranking (no bloqueante): %s", e_rag)
            elif hasattr(self.qdrant, "recuperar_contexto_rag"):
                try:
                    ctx_directo = self.qdrant.recuperar_contexto_rag(tecnica_id, discrepancias_detectadas)
                    if not ctx_directo:
                        ctx_directo = self.qdrant.recuperar_contexto_rag(None, discrepancias_detectadas)
                    if ctx_directo:
                        tiene_contexto_rag = True
                        contexto_profundo = f"\n\n[Contexto RAG]:\n{ctx_directo}"
                        logger.info("Prioridad 1 activa: RAG de texto directo obtenido desde qdrant para '%s'", tecnica_nombre)
                except Exception as e_ctx:
                    logger.warning("Fallo en recuperación RAG directa desde qdrant: %s", e_ctx)

            if not (mensaje_profesor and str(mensaje_profesor).strip()) and hasattr(self.qdrant, "obtener_mensaje_profesor_rag"):
                try:
                    msgs_qdrant = self.qdrant.obtener_mensaje_profesor_rag(tecnica_id)
                    if isinstance(msgs_qdrant, list) and len(msgs_qdrant) > 0 and isinstance(msgs_qdrant[0], dict):
                        txt_q = (msgs_qdrant[0].get("contenido_texto") or "").strip()
                        if txt_q:
                            mensaje_profesor = txt_q
                except Exception as e_qm:
                    logger.debug("Fallo consultando mensaje_profesor en Qdrant fallback: %s", e_qm)

            from corpocmente.domain.strategies.prompt_strategies import obtener_estrategia_prompt
            strategy = obtener_estrategia_prompt(idioma)

            msg_prof_limpio = mensaje_profesor.strip() if mensaje_profesor and str(mensaje_profesor).strip() else ""
            tiene_mensaje_profesor = bool(msg_prof_limpio)

            # Cubre los 4 escenarios:
            # 1) Ambos (manual + mensaje del profesor)
            # 2) Solo manual de biblioteca
            # 3) Solo instrucciones escritas del profesor
            # 4) Ninguno (análisis visual directo con nombre de técnica + fotograma limpio sin esqueleto)
            prompt = strategy.construir_prompt_evaluacion(
                tecnica_nombre,
                discrepancias_detectadas,
                mensaje_profesor=msg_prof_limpio,
                tiene_contexto_rag=tiene_contexto_rag,
            )
            if tiene_contexto_rag and contexto_profundo:
                prompt += contexto_profundo

            # Liberar caché MPS de PyTorch antes de ejecutar MLX VLM para evitar contención Metal GPU
            try:
                import gc
                import torch
                gc.collect()
                if hasattr(torch, "mps") and torch.backends.mps.is_available():
                    torch.mps.synchronize()
                    torch.mps.empty_cache()
            except Exception:
                pass

            evidencias_vlm = evidencias_rag if tiene_contexto_rag else []
            vlm_ok = False
            try:
                res_gemini = self.gemini.generar_texto_feedback(
                    prompt,
                    frame_para_vlm,
                    evidencias_visuales=evidencias_vlm,
                    idioma=idioma,
                )

                if isinstance(res_gemini, dict):
                    feedback_summary = res_gemini.get("summary", "Technique error")
                    feedback_correction = res_gemini.get("correction", "")
                    feedback_texto = feedback_correction
                else:
                    feedback_texto = str(res_gemini)
                    partes = feedback_texto.split(".")
                    feedback_summary = partes[0].strip() if partes else "Technique error"
                    feedback_correction = feedback_texto
                vlm_ok = True
            except Exception as e_vlm:
                logger.warning("Fallo invocando VLM para '%s': %s. Aplicando fallback.", tecnica_nombre, e_vlm)
                lang_fb = (idioma or "es").lower().strip()
                if tiene_mensaje_profesor:
                    if lang_fb.startswith("pt"):
                        feedback_summary = f"Ajuste técnico em {tecnica_nombre}"
                    elif lang_fb.startswith("en"):
                        feedback_summary = f"Coach cue for {tecnica_nombre}"
                    else:
                        feedback_summary = f"Indicaciones del profesor: {tecnica_nombre}"
                    feedback_correction = msg_prof_limpio
                    feedback_texto = feedback_correction
                elif tiene_contexto_rag:
                    from corpocmente.infrastructure.ai.adapters import obtener_nombres_articulaciones
                    arts_lbl = ", ".join(obtener_nombres_articulaciones(arts_criticas or [], idioma=idioma))
                    if lang_fb.startswith("pt"):
                        feedback_summary = f"Ajuste em {tecnica_nombre}"
                        feedback_correction = f"Revise o posicionamento em {arts_lbl or 'suas articulações'} para executar {tecnica_nombre} com controle."
                    elif lang_fb.startswith("en"):
                        feedback_summary = f"Adjustment for {tecnica_nombre}"
                        feedback_correction = f"Focus on {arts_lbl or 'your posture and grips'} to execute {tecnica_nombre} cleanly."
                    else:
                        feedback_summary = f"Ajuste técnico en {tecnica_nombre}"
                        feedback_correction = f"Ajusta {arts_lbl or 'tu postura y agarres'} en el punto clave para completar {tecnica_nombre}."
                    feedback_texto = feedback_correction
                else:
                    fallback_data = strategy.obtener_mensaje_sin_contexto()
                    feedback_summary = fallback_data.get("summary", "Información insuficiente")
                    feedback_correction = fallback_data.get(
                        "correction",
                        "No hay información suficiente en los manuales ni en las instrucciones del instructor para evaluar esta técnica.",
                    )
                    feedback_texto = feedback_correction

            # Mecanismo de Grounding (Anti-Alucinaciones con LLM-as-a-Judge)
            # Aplica únicamente cuando el VLM respondió y hay fuentes de referencia
            if vlm_ok and (tiene_contexto_rag or tiene_mensaje_profesor) and hasattr(self.gemini, "evaluar_fidelidad_grounding"):
                try:
                    partes_juez = [f"Técnica evaluada: {tecnica_nombre}"]
                    if discrepancias_detectadas:
                        partes_juez.append(
                            "Observaciones biomecánicas del frame:\n"
                            + "\n".join(f"- {d}" for d in discrepancias_detectadas)
                        )
                    if tiene_contexto_rag and contexto_profundo:
                        partes_juez.append(contexto_profundo)
                    contexto_juez = "\n\n".join(partes_juez)
                    eval_grounding = self.gemini.evaluar_fidelidad_grounding(
                        respuesta={"summary": feedback_summary, "correction": feedback_correction},
                        contexto=contexto_juez,
                        mensaje_profesor=msg_prof_limpio,
                    )
                    if (
                        isinstance(eval_grounding, dict)
                        and "faithfulness_score" in eval_grounding
                        and isinstance(eval_grounding["faithfulness_score"], (int, float))
                    ):
                        faith_score = float(eval_grounding["faithfulness_score"])
                        unsupported = eval_grounding.get("unsupported_claims") or []
                        if faith_score < 0.85 or (isinstance(unsupported, list) and len(unsupported) > 0):
                            logger.warning(
                                "Alucinación detectada por LLM-Judge (score=%.2f, claims=%s). Reintentando ajuste estricto.",
                                faith_score,
                                unsupported,
                            )
                            reintento_ok = False
                            if tiene_contexto_rag:
                                try:
                                    prompt_estricto = (
                                        prompt
                                        + "\n\nCORRECCIÓN OBLIGATORIA: Elimina detalles no respaldados ("
                                        + ", ".join(str(c) for c in unsupported[:3])
                                        + ") y redacta de forma humana respetando fielmente las instrucciones del profesor/manual y la postura real de la imagen."
                                    )
                                    res_re = self.gemini.generar_texto_feedback(
                                        prompt_estricto,
                                        frame_para_vlm,
                                        evidencias_visuales=evidencias_vlm,
                                        idioma=idioma,
                                    )
                                    if isinstance(res_re, dict) and (res_re.get("correction") or "").strip():
                                        feedback_summary = res_re.get("summary", feedback_summary)
                                        feedback_correction = res_re.get("correction", feedback_correction)
                                        feedback_texto = feedback_correction
                                        reintento_ok = True
                                except Exception as e_retry:
                                    logger.debug("Reintento tras LLM-Judge falló: %s", e_retry)

                            if not reintento_ok:
                                if tiene_mensaje_profesor:
                                    lang_fb = (idioma or "es").lower().strip()
                                    if lang_fb.startswith("pt"):
                                        feedback_summary = f"Ajuste técnico em {tecnica_nombre}"
                                    elif lang_fb.startswith("en"):
                                        feedback_summary = f"Coach cue for {tecnica_nombre}"
                                    else:
                                        feedback_summary = f"Indicaciones del profesor: {tecnica_nombre}"
                                    feedback_correction = msg_prof_limpio
                                    feedback_texto = feedback_correction
                                elif tiene_contexto_rag:
                                    # Si el manual fue recuperado con alta relevancia, nunca sobrescribir con
                                    # "Información insuficiente" por discrepancia del juez.
                                    logger.info("Conservando respuesta generada respaldada por manual RAG para '%s'.", tecnica_nombre)
                                else:
                                    fallback_data = strategy.obtener_mensaje_sin_contexto()
                                    feedback_summary = fallback_data.get("summary", "Información insuficiente")
                                    feedback_correction = fallback_data.get(
                                        "correction",
                                        "No hay información suficiente en los manuales ni en las instrucciones del instructor para evaluar esta técnica.",
                                    )
                                    feedback_texto = feedback_correction
                except Exception as e_judge:
                    logger.warning("Fallo en evaluación de fidelidad grounding (no bloqueante): %s", e_judge)

        timestamp_error_segundos = None
        if os.path.exists(video_path) and frame_alumno_critico is not None:
            try:
                import cv2
                cap = cv2.VideoCapture(video_path)
                fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
                cap.release()
                if fps > 0:
                    timestamp_error_segundos = round(frame_alumno_critico / fps, 2)
            except Exception as e_fps:
                logger.warning("No se pudo calcular FPS para timestamp_error_segundos: %s", e_fps)

        from corpocmente.infrastructure.ai.adapters import obtener_nombres_articulaciones
        nombres_articulaciones_criticas = obtener_nombres_articulaciones(arts_criticas or [], idioma=idioma)

        feedback_summary = _sanitizar_respuesta_coach(feedback_summary, idioma=idioma) or feedback_summary
        feedback_correction = _sanitizar_respuesta_coach(feedback_correction, idioma=idioma) or feedback_correction
        feedback_texto = _sanitizar_respuesta_coach(feedback_texto, idioma=idioma) or feedback_texto

        return AnalisisResultDTO(
            similitud=similitud,
            feedback=feedback_texto,
            feedback_summary=feedback_summary,
            feedback_correction=feedback_correction,
            frame_critico_path=frame_resaltado,
            frame_alumno_idx=frame_alumno_critico,
            timestamp_error_segundos=timestamp_error_segundos,
            discrepancias=discrepancias_detectadas,
            articulaciones_criticas=arts_criticas,
            nombres_articulaciones_criticas=nombres_articulaciones_criticas,
            dtw_distance=dtw_distance,
            dtw_normalizado=dtw_normalizado
        )
