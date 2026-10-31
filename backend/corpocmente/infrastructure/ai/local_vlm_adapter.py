import json
import logging
import os
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LocalVLMAdapter:
    """
    Reemplazo local de GeminiApiAdapter usando Qwen3-VL-Instruct vía mlx-vlm.
    Misma firma que GeminiApiAdapter.generar_texto_feedback().
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
        for ev in (evidencias_visuales or [])[:3]:
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

