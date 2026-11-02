import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LocalVLMAdapter:
    """
    Adaptador local de VLM usando Qwen3-VL-Instruct vía mlx-vlm.
    Provee generar_texto_feedback().
    """

    def __init__(self, model_name: str = "mlx-community/Qwen3-VL-4B-Instruct-4bit"):
        from mlx_vlm import load
        logger.info("Cargando VLM local: %s", model_name)
        self.model_name = model_name
        self.model, self.processor = load(model_name)
        logger.info("VLM local listo.")

    def generar_texto_feedback(
        self,
        prompt: str,
        frame_image_path: str,
        evidencias_visuales: Optional[List[Dict]] = None,
    ) -> Dict[str, str]:
        from mlx_vlm import generate

        if not os.path.exists(frame_image_path):
            raise FileNotFoundError(frame_image_path)

        images = [frame_image_path]
        # top_k de recuperación es cinco: no descartamos páginas recuperadas antes
        # de que el VLM pueda contrastarlas con el fotograma del alumno.
        for ev in (evidencias_visuales or [])[:5]:
            payload = ev.get("payload", ev)
            media_path = payload.get("media_path")
            if media_path and os.path.exists(media_path):
                ext = os.path.splitext(media_path)[1].lower()
                if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
                    images.append(media_path)
                elif ext == ".pdf":
                    try:
                        import fitz
                        doc = fitz.open(media_path)
                        if doc.page_count > 0:
                            page_idx = min(max(0, int(payload.get("pagina") or 1) - 1), doc.page_count - 1)
                            page = doc.load_page(page_idx)
                            pix = page.get_pixmap(dpi=150)
                            tmp_img = f"/tmp/corpocmente_frames/pdf_p{page_idx}_{os.path.basename(media_path)}.png"
                            os.makedirs(os.path.dirname(tmp_img), exist_ok=True)
                            pix.save(tmp_img)
                            images.append(tmp_img)
                    except Exception as err:
                        logger.warning("No se pudo renderizar página del PDF %s: %s", media_path, err)

        full_prompt = (
            prompt
            + "\n\nLas imágenes adjuntas, después del fotograma del alumno, son páginas recuperadas del manual. "
              "Básate en el mensaje del profesor y en las imágenes de las páginas del manual adjuntas para dar la corrección. "
              "Menciona la indicación del profesor y cita la página del libro como '(p. X)' de donde sacaste la referencia o corrección visual. "
              "Si la información no está en el texto, en la imagen o en el mensaje del profesor, abstente de inventar."
            + "\n\nResponde EXCLUSIVAMENTE con un objeto JSON válido "
              "con las claves 'summary' y 'correction'. "
              "No agregues markdown, ni texto fuera del JSON."
        )

        if hasattr(self.processor, "apply_chat_template"):
            content = [{"type": "image"} for _ in images] + [{"type": "text", "text": full_prompt}]
            formatted_prompt = self.processor.apply_chat_template(
                [{"role": "user", "content": content}],
                add_generation_prompt=True,
            )
        else:
            formatted_prompt = full_prompt

        raw = generate(
            self.model,
            self.processor,
            formatted_prompt,
            images,
            max_tokens=400,
            temperature=0.2,
            verbose=False,
        )

        return self._parsear_json(raw)

    @staticmethod
    def _parsear_json(text) -> Dict[str, str]:
        if hasattr(text, "text"):
            text = text.text
        text = str(text).strip()
        # Nivel 1: JSON directo
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return {
                    "summary": str(parsed.get("summary", "Technique feedback")).strip(),
                    "correction": str(parsed.get("correction", "")).strip(),
                }
        except json.JSONDecodeError:
            pass

        # Nivel 2: bloque ```json ... ```
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(1))
                return {
                    "summary": str(parsed.get("summary", "Technique feedback")).strip(),
                    "correction": str(parsed.get("correction", "")).strip(),
                }
            except json.JSONDecodeError:
                pass

        # Nivel 3: fallback texto plano
        sentences = re.split(r"(?<=[.!?])\s+", text)
        summary = sentences[0][:80] if sentences else "Technique feedback"
        return {"summary": summary, "correction": text[:500]}

    def evaluar_fidelidad_grounding(
        self,
        respuesta: Dict[str, str],
        contexto: str,
        mensaje_profesor: str = "",
    ) -> Dict[str, Any]:
        """
        Ejecuta un 'LLM-as-a-Judge' utilizando el VLM local para verificar si la
        respuesta generada está 100% anclada al contexto recuperado de Qdrant y/o
        a las instrucciones del profesor.

        Devuelve:
        {
            "faithfulness_score": float (0.0 a 1.0),
            "unsupported_claims": List[str],
            "reasoning": str
        }
        """
        summary = str(respuesta.get("summary", "")).strip()
        correction = str(respuesta.get("correction", "")).strip()

        # Si es un halago o técnica correcta sin errores biomecánicos, fidelidad completa
        if summary.lower() in ("good technique", "buena técnica", "boa técnica"):
            return {
                "faithfulness_score": 1.0,
                "unsupported_claims": [],
                "reasoning": "Respuesta de técnica correcta sin afirmaciones de error que requieran anclaje.",
            }

        contexto_completo = ""
        if mensaje_profesor and mensaje_profesor.strip():
            contexto_completo += f"Instrucciones del profesor:\n{mensaje_profesor.strip()}\n\n"
        if contexto and contexto.strip():
            contexto_completo += f"Contexto de manuales y referencias:\n{contexto.strip()}"

        if not contexto_completo.strip():
            return {
                "faithfulness_score": 0.0,
                "unsupported_claims": ["No hay contexto de referencia disponible para validar la respuesta."],
                "reasoning": "Contexto ausente.",
            }

        from mlx_vlm import generate

        prompt_juez = (
            "Eres un evaluador de fidelidad (Faithfulness Judge) para sistemas de Jiu-Jitsu Brasileño.\n"
            "Tu tarea es verificar rigurosamente si la respuesta generada está fundamentada en el contexto provisto (manuales técnicos o indicaciones del profesor).\n\n"
            f"[CONTEXTO DE REFERENCIA]:\n{contexto_completo.strip()}\n\n"
            f"[RESPUESTA A EVALUAR]:\nSummary: {summary}\nCorrection: {correction}\n\n"
            "REGLAS ESTRICTAS DE EVALUACIÓN:\n"
            "1. El 'Summary' es el diagnóstico del error biomecánico observado. Es válido si se relaciona directamente con el problema técnico cubierto en el contexto.\n"
            "2. La 'Correction' debe basarse en los principios, articulaciones, agarres o posturas explicados en el contexto.\n"
            "3. Si la respuesta contiene afirmaciones técnicas ajenas, inventa nombres de llaves o movimientos ausentes en el contexto, agrégalas a 'unsupported_claims'.\n"
            "4. Si 'unsupported_claims' NO está vacío, 'faithfulness_score' DEBE ser menor a 0.70 (por ejemplo 0.0 a 0.50).\n"
            "5. Si todas las afirmaciones técnicas están respaldadas por el contexto, 'unsupported_claims' debe ser [] y 'faithfulness_score' entre 0.90 y 1.0.\n"
            "6. Responde EXCLUSIVAMENTE con un JSON con el siguiente formato:\n"
            "{\"faithfulness_score\": <float entre 0.0 y 1.0>, \"unsupported_claims\": [<lista de strings>], \"reasoning\": \"<breve explicación>\"}"
        )

        if hasattr(self.processor, "apply_chat_template"):
            content = [{"type": "text", "text": prompt_juez}]
            formatted_prompt = self.processor.apply_chat_template(
                [{"role": "user", "content": content}],
                add_generation_prompt=True,
            )
        else:
            formatted_prompt = prompt_juez

        raw = generate(
            self.model,
            self.processor,
            formatted_prompt,
            [],
            max_tokens=250,
            temperature=0.0,
            verbose=False,
        )

        return self._parsear_json_judge(raw)

    @staticmethod
    def _parsear_json_judge(text) -> Dict[str, Any]:
        if hasattr(text, "text"):
            text = text.text
        text = str(text).strip()

        parsed_data = None
        # Nivel 1: parseo directo
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                parsed_data = parsed
        except json.JSONDecodeError:
            pass

        # Nivel 2: regex json block
        if parsed_data is None:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(1))
                    if isinstance(parsed, dict):
                        parsed_data = parsed
                except json.JSONDecodeError:
                    pass

        # Nivel 3: búsqueda del primer '{' y último '}'
        if parsed_data is None:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(text[start : end + 1])
                    if isinstance(parsed, dict):
                        parsed_data = parsed
                except json.JSONDecodeError:
                    pass

        if parsed_data is not None:
            score = parsed_data.get("faithfulness_score")
            try:
                score = float(score)
            except (TypeError, ValueError):
                score = 0.5
            score = max(0.0, min(1.0, score))
            unsupported = parsed_data.get("unsupported_claims")
            if not isinstance(unsupported, list):
                unsupported = [str(unsupported)] if unsupported else []
            # Si hay unsupported claims, asegurar que score sea < 0.85
            if unsupported and score >= 0.85:
                score = 0.60
            return {
                "faithfulness_score": round(score, 2),
                "unsupported_claims": [str(c).strip() for c in unsupported if str(c).strip()],
                "reasoning": str(parsed_data.get("reasoning", "")).strip(),
            }

        # Fallback si no se pudo parsear
        return {
            "faithfulness_score": 0.50,
            "unsupported_claims": ["No se pudo parsear el veredicto del juez LLM."],
            "reasoning": text[:200],
        }


