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

        # 0. Recuperar patrón activo de referencia desde Qdrant
        secuencia_maestro = None
        if hasattr(self.qdrant, "obtener_secuencia_referencia"):
            try:
                res_q = self.qdrant.obtener_secuencia_referencia(tecnica_id=tecnica_id)
                if isinstance(res_q, list) and len(res_q) > 0:
                    secuencia_maestro = res_q
            except Exception as e_q:
                logger.warning(f"Error consultando obtener_secuencia_referencia: {e_q}")

        # Si no hay patrón en Qdrant pero se proveyó video de referencia, asegurar ingesta
        if not secuencia_maestro and video_referencia_path and hasattr(self.qdrant, "asegurar_poses_referencia"):
            try:
                self.qdrant.asegurar_poses_referencia(
                    tecnica_id=tecnica_id,
                    video_referencia_path=video_referencia_path,
                    yolo_adapter=self.yolo,
                    tecnica_nombre=tecnica_nombre
                )
                if hasattr(self.qdrant, "obtener_secuencia_referencia"):
                    res_q = self.qdrant.obtener_secuencia_referencia(tecnica_id=tecnica_id)
                    if isinstance(res_q, list) and len(res_q) > 0:
                        secuencia_maestro = res_q
            except Exception as e_ref:
                logger.warning(f"No se pudo auto-ingerir video de referencia del profesor: {e_ref}")

        secuencia_alumno = None
        if hasattr(self.yolo, "extraer_secuencia"):
            ext_res = self.yolo.extraer_secuencia(
                video_path,
                persona_idx_inicial=persona_idx,
                evaluacion_id=str(evaluacion_id) if evaluacion_id else None,
                tecnica_id=str(tecnica_id) if tecnica_id else None
            )
            if isinstance(ext_res, dict):
                secuencia_alumno = ext_res.get("secuencia_kpts", [])
                cobertura = ext_res.get("cobertura", 0.0)
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

        # 2. Comparación DTW o fallback a máxima diferencia
        if secuencia_maestro:
            from corpocmente.domain.biomechanics.dtw_comparator import comparar_secuencias_con_dtw
            dtw_res = comparar_secuencias_con_dtw(secuencia_maestro, secuencia_alumno)
            similitud = dtw_res["score_similitud"]
            frame_alumno_critico = dtw_res["frame_alumno_critico"]
            arts_criticas = dtw_res.get("articulaciones_criticas", [])
            from corpocmente.infrastructure.ai.adapters import obtener_nombres_articulaciones
            nombres_arts = obtener_nombres_articulaciones(arts_criticas, idioma=idioma)
            lang_clean = (idioma or "es").lower().strip()
            if lang_clean in ("pt", "portuguese", "português", "portugues"):
                discrepancias_detectadas = [
                    f"Desvio biomecânico em {art}: desalinhamento em relação ao padrão do instrutor."
                    for art in nombres_arts
                ]
            elif lang_clean in ("en", "english"):
                discrepancias_detectadas = [
                    f"Biomechanical deviation at {art}: misalignment vs. the instructor's pattern."
                    for art in nombres_arts
                ]
            else:
                discrepancias_detectadas = [
                    f"Desviación biomecánica en {art}: desalineación respecto al patrón del instructor."
                    for art in nombres_arts
                ]
            dtw_distance = dtw_res.get("dtw_distance")
            dtw_normalizado = dtw_res.get("dtw_normalizado")
            kpts_critico = secuencia_alumno[frame_alumno_critico] if frame_alumno_critico < len(secuencia_alumno) else None
        elif hasattr(self.qdrant, "buscar_maxima_diferencia"):
            if esqueletos_frames is not None:
                esqueletos_para_qdrant = esqueletos_frames
            else:
                esqueletos_para_qdrant = []
                for i, kp in enumerate(secuencia_alumno):
                    vec = list(kp)
                    if len(vec) < 133:
                        vec.extend([0.0] * (133 - len(vec)))
                    esqueletos_para_qdrant.append(EsqueletoBiomecanico(frame_idx=i, keypoints133=vec[:133], angulos_articulares={}))
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

        es_limpio_valido = isinstance(frame_limpio, (str, bytes, os.PathLike)) and os.path.isfile(frame_limpio)
        frame_para_embedding = frame_limpio if es_limpio_valido else frame_resaltado

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

                    if manuales_candidatos:
                        # Reranking multilingüe con Cross-Encoder real Qwen3-VL (Iteración 3R)
                        partes_q = [tecnica_nombre]
                        if discrepancias_detectadas:
                            partes_q.append(", ".join(discrepancias_detectadas))
                        query_rerank = ". ".join(partes_q).strip()
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
                                evidencias_rag = evidencias_reranked
                                contexto_profundo = formatear_evidencias_texto(evidencias_rag)
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

            from corpocmente.domain.strategies.prompt_strategies import obtener_estrategia_prompt
            strategy = obtener_estrategia_prompt(idioma)

            if tiene_contexto_rag:
                # Prioridad 1: Manual RAG de alta relevancia (ignora mensaje del profesor)
                prompt = strategy.construir_prompt_evaluacion(
                    tecnica_nombre,
                    discrepancias_detectadas,
                    mensaje_profesor="",
                    tiene_contexto_rag=True,
                )
                if contexto_profundo:
                    prompt += contexto_profundo

                res_gemini = self.gemini.generar_texto_feedback(
                    prompt,
                    frame_resaltado,
                    evidencias_visuales=evidencias_rag,
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

            elif mensaje_profesor and mensaje_profesor.strip():
                # Prioridad 2: No hay manual útil pero sí mensaje del profesor
                prompt = strategy.construir_prompt_evaluacion(
                    tecnica_nombre,
                    discrepancias_detectadas,
                    mensaje_profesor=mensaje_profesor.strip(),
                    tiene_contexto_rag=False,
                )

                res_gemini = self.gemini.generar_texto_feedback(
                    prompt,
                    frame_resaltado,
                    evidencias_visuales=[],
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

            else:
                # Prioridad 3: Fallback Seguro (ni manuales útiles ni mensaje del instructor)
                # NO invocamos al VLM para prevenir alucinaciones
                fallback_data = strategy.obtener_mensaje_sin_contexto()
                feedback_summary = fallback_data.get("summary", "Información insuficiente")
                feedback_correction = fallback_data.get(
                    "correction",
                    "No hay información suficiente en los manuales ni en las instrucciones del instructor para evaluar esta técnica.",
                )
                feedback_texto = feedback_correction
                logger.info(
                    "Prioridad 3 activa (Fallback seguro): Sin manuales ni mensaje del profesor para '%s'. VLM omitido.",
                    tecnica_nombre,
                )

            # Mecanismo de Grounding (Anti-Alucinaciones con LLM-as-a-Judge)
            # Solo aplica si se consultó al VLM (Prioridad 1 o 2)
            if (tiene_contexto_rag or (mensaje_profesor and mensaje_profesor.strip())) and hasattr(self.gemini, "evaluar_fidelidad_grounding"):
                try:
                    eval_grounding = self.gemini.evaluar_fidelidad_grounding(
                        respuesta={"summary": feedback_summary, "correction": feedback_correction},
                        contexto=contexto_profundo if tiene_contexto_rag else "",
                        mensaje_profesor="" if tiene_contexto_rag else mensaje_profesor,
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
                                "Alucinación detectada por LLM-Judge (score=%.2f, claims=%s). Aplicando fallback seguro.",
                                faith_score,
                                unsupported,
                            )
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
