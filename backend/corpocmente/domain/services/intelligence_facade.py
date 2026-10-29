import os
import logging
from typing import Optional
from uuid import UUID, uuid4

from corpocmente.domain.entities.models import AnalisisResultDTO
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
from corpocmente.domain.strategies.prompt_strategies import EnglishPromptStrategy
from corpocmente.application.services.multimodal_rag_service import (
    formatear_evidencias_texto,
    obtener_evidencias_rag_multimodal,
)

logger = logging.getLogger(__name__)

class IntelligenceAnalysisFacade:
    def __init__(self, 
                 yolo_adapter: YOLOPoseAdapter, 
                 qdrant_adapter: QdrantVectorAdapter, 
                 gemini_adapter: GeminiApiAdapter,
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
        persona_idx: Optional[int] = None
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
                evaluacion_id=str(evaluacion_id) if evaluacion_id else None
            )
            if isinstance(ext_res, dict):
                secuencia_alumno = ext_res.get("secuencia_kpts", [])
                cobertura = ext_res.get("cobertura", 0.0)
                total_frames = ext_res.get("total_frames", 0)
                if isinstance(total_frames, (int, float)) and isinstance(cobertura, (int, float)):
                    if total_frames == 0 or cobertura < 0.70:
                        raise ValueError(f"Tracking insuficiente en el video del alumno: cobertura {cobertura*100:.1f}% < 70%.")

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
            from corpocmente.infrastructure.ai.adapters import COCO_JOINT_NAMES_EN
            discrepancias_detectadas = [
                f"Biomechanical deviation at {COCO_JOINT_NAMES_EN[idx] if idx < len(COCO_JOINT_NAMES_EN) else f'Joint #{idx}'}: misalignment vs. the instructor's pattern."
                for idx in arts_criticas
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
            feedback_summary = "Good technique"
            feedback_correction = "Technique executed correctly. Excellent work!"
            feedback_texto = feedback_correction
        else:
            contexto_profundo = ""
            evidencias_rag = []
            if self.qwen:
                try:
                    evidencias_rag = obtener_evidencias_rag_multimodal(
                        qwen_adapter=self.qwen,
                        qdrant_adapter=self.qdrant,
                        tecnica_id=tecnica_id,
                        tecnica_nombre=tecnica_nombre,
                        discrepancias=discrepancias_detectadas,
                        frame_critico_path=frame_para_embedding,
                        video_referencia_path=video_referencia_path,
                        limit=5,
                    )
                    contexto_profundo = formatear_evidencias_texto(evidencias_rag)
                    if contexto_profundo:
                        contexto_profundo = (
                            "\n\n[Evidence retrieved from manuals and instructor reference videos]:\n"
                            + contexto_profundo
                        )
                except Exception as e_rag:
                    logger.warning("Fallo en recuperación RAG multimodal (no bloqueante): %s", e_rag)

            strategy = EnglishPromptStrategy()
            prompt = strategy.construir_prompt_evaluacion(tecnica_nombre, discrepancias_detectadas)
            if contexto_profundo:
                prompt += contexto_profundo

            res_gemini = self.gemini.generar_texto_feedback(
                prompt,
                frame_resaltado,
                evidencias_visuales=evidencias_rag,
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

        return AnalisisResultDTO(
            similitud=similitud,
            feedback=feedback_texto,
            feedback_summary=feedback_summary,
            feedback_correction=feedback_correction,
            frame_critico_path=frame_resaltado,
            frame_alumno_idx=frame_alumno_critico,
            discrepancias=discrepancias_detectadas,
            articulaciones_criticas=arts_criticas,
            dtw_distance=dtw_distance,
            dtw_normalizado=dtw_normalizado
        )
