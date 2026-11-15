import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LocalVLMAdapter:
    """
    Adaptador local de VLM usando Qwen3-VL-Instruct vía mlx-vlm.
    Provee generar_texto_feedback(), reescribir_query_cognitiva() y verificar_faithfulness().
    """

    _cached_models = {}

    def __init__(self, model_name: str = "mlx-community/Qwen3-VL-4B-Instruct-4bit"):
        self.model_name = model_name
        if model_name not in LocalVLMAdapter._cached_models:
            from mlx_vlm import load
            logger.info("Cargando VLM local: %s", model_name)
            m, p = load(model_name)
            LocalVLMAdapter._cached_models[model_name] = (m, p)
            logger.info("VLM local listo.")
        self.model, self.processor = LocalVLMAdapter._cached_models[model_name]

    def reescribir_query_cognitiva(self, query: str) -> str:
        """
        Reescribe y expande la consulta del usuario para optimizar la búsqueda semántica en Jiu-Jitsu.
        Diferencia explícitamente conceptos de defensa/escape vs ataque/sumisión.
        """
        if not query or not query.strip():
            return ""

        prompt = (
            "Eres un experto en Jiu-Jitsu. Reescribe la siguiente consulta del usuario para que sea óptima para una búsqueda semántica. "
            "Si el usuario busca 'defensa', expande la consulta incluyendo 'escape', 'survive', 'defend'. "
            "Si busca 'ataque', expande incluyendo 'submission', 'finish', 'attack'. "
            "Devuelve SOLO el texto reescrito, sin explicaciones ni comillas.\n\n"
            f"Consulta: {query.strip()}"
        )

        try:
            from mlx_vlm import generate
            if hasattr(self.processor, "apply_chat_template"):
                content = [{"type": "text", "text": prompt}]
                formatted_prompt = self.processor.apply_chat_template(
                    [{"role": "user", "content": content}],
                    add_generation_prompt=True,
                )
            else:
                formatted_prompt = prompt

            raw = generate(
                self.model,
                self.processor,
                formatted_prompt,
                [],
                max_tokens=60,
                temperature=0.0,
                verbose=False,
            )
            reescrita = str(raw.text if hasattr(raw, "text") else raw).strip()
            reescrita = re.sub(r'^(?:Consulta reescrita|Reescritura|Respuesta):\s*', '', reescrita, flags=re.IGNORECASE)
            reescrita = reescrita.strip('"\' ')
            if reescrita and len(reescrita) > 3:
                return reescrita
        except Exception as e:
            logger.warning("Fallo en reescritura con VLM: %s. Aplicando fallback determinista.", e)

        return self._reescribir_query_fallback(query)

    def generar_respuesta_rag_chat(
        self,
        query: str,
        chunks: List[Dict],
        idioma: str = "es",
    ) -> str:
        """
        Genera una respuesta conversacional como profesor de BJJ usando los top-3 recursos
        disponibles (manuales e instrucciones del profesor), con citas [1], [2], [3].
        """
        lang = (idioma or "es").lower().strip()
        top_chunks = list(chunks or [])[:3]
        if not top_chunks:
            if lang.startswith("pt"):
                return "Ainda não tenho essa informação nos nossos manuais nem nas anotações da academia. Sugiro perguntar diretamente ao seu instrutor no tatame!"
            if lang.startswith("en"):
                return "I don't have that information in our manuals or your coach's notes yet. I recommend asking your instructor directly on the mat!"
            return "Aún no tengo esa información en nuestros manuales ni en las notas de tu profesor. Te sugiero preguntárselo directamente a tu instructor en el tatami."

        context_lines = []
        for idx, ch in enumerate(top_chunks, start=1):
            cita = ch.get("cita") or ch.get("fuente_nombre") or f"Referencia {idx}"
            pagina = ch.get("pagina")
            fuente_label = f"{cita}" if pagina or cita else f"Referencia {idx}"
            texto = (ch.get("contenido_texto") or "").strip()[:900]
            context_lines.append(f"[{idx}] ({fuente_label}):\n{texto}")
        context_block = "\n\n".join(context_lines)

        if lang.startswith("pt"):
            system_persona = (
                "Você é um professor de Jiu-Jitsu Brasileiro experiente, gentil e paciente. "
                "Responda às dúvidas do aluno de forma conversacional, natural e em linguagem simples, como se estivesse no tatame. "
                "Seja direto e breve (máximo 2 parágrafos curtos, sem repetir frases). "
                "Se a informação não estiver nos manuais nem nas instruções do professor, diga gentilmente que não possui essa informação e sugira perguntar ao seu instrutor. "
                "Não use linguagem técnica de banco de dados, nem diga 'fragmentos' ou 'textos'. "
                "Cite suas fontes no final usando [1], [2]. Responda estritamente em português."
            )
        elif lang.startswith("en"):
            system_persona = (
                "You are an experienced, friendly, and patient Brazilian Jiu-Jitsu professor. "
                "Answer the student's question in a natural, conversational, easy-to-understand way, as if you were on the mat. "
                "Be concise and clear (at most 2 short paragraphs, without repeating sentences). "
                "If the information is not in the manuals or the instructor's notes, kindly say you don't have that information and suggest asking their coach. "
                "Do not use database technical jargon, and do not say 'fragments', 'chunks', or 'texts'. "
                "Cite your sources at the end using [1], [2]. Reply strictly in English."
            )
        else:
            system_persona = (
                "Eres un profesor de Jiu-Jitsu Brasileño experimentado, amable y paciente. "
                "Responde a las dudas del alumno de forma conversacional, natural y en lenguaje sencillo, como si estuvieras en el tatami. "
                "Sé claro y conciso (máximo 2 o 3 párrafos cortos, sin repetir ideas ni frases). "
                "Si la información no está en los manuales ni en las instrucciones del profesor, di amablemente que no tienes esa información y sugiérele preguntarle a su instructor. "
                "No uses lenguaje técnico de bases de datos, ni digas 'fragmentos' o 'textos'. "
                "Cita tus fuentes al final usando [1], [2]. Responde estrictamente en español."
            )

        prompt = (
            f"{system_persona}\n\n"
            f"Apuntes e información disponible:\n{context_block}\n\n"
            f"Duda del alumno: {query.strip()}\n\n"
            "Respuesta del profesor:"
        )

        try:
            from mlx_vlm import generate
            if hasattr(self.processor, "apply_chat_template"):
                content = [{"type": "text", "text": prompt}]
                formatted_prompt = self.processor.apply_chat_template(
                    [{"role": "user", "content": content}],
                    add_generation_prompt=True,
                )
            else:
                formatted_prompt = prompt

            raw = generate(
                self.model,
                self.processor,
                formatted_prompt,
                [],
                max_tokens=280,
                temperature=0.25,
                verbose=False,
            )
            answer = str(raw.text if hasattr(raw, "text") else raw).strip()
            if answer and len(answer) > 5:
                return answer
        except Exception as e:
            logger.warning("Fallo generando respuesta RAG con Qwen3-VL: %s. Aplicando resumen citado.", e)

        # Fallback determinista con citas inline reales
        bullets = []
        for idx, ch in enumerate(top_chunks, start=1):
            snippet = " ".join((ch.get("contenido_texto") or "").split())[:220]
            if snippet:
                bullets.append(f"- {snippet} [{idx}]")
        return "\n".join(bullets) if bullets else top_chunks[0].get("contenido_texto", "")

    @staticmethod
    def _reescribir_query_fallback(query: str) -> str:
        q_lower = query.lower()
        terminos = [query.strip()]
        if any(w in q_lower for w in ["defensa", "defesa", "defense", "escape", "defender", "zafar", "escapar"]):
            terminos.append("escape survive defend defense counter")
        elif any(w in q_lower for w in ["ataque", "attack", "sumision", "submissao", "submission", "finalizar", "finalizacao", "llave", "armbar"]):
            terminos.append("submission finish attack lock")
        return " ".join(terminos)

    def generar_texto_feedback(
        self,
        prompt: str,
        frame_image_path: str,
        evidencias_visuales: Optional[List[Dict]] = None,
        idioma: str = "es",
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

        lang = (idioma or "es").lower().strip()
        tiene_imagenes_manual = len(images) > 1
        if tiene_imagenes_manual:
            if lang in ("pt", "portuguese", "português", "portugues"):
                instruccion_rag = (
                    "\n\nAs imagens anexadas, após o fotograma do aluno, são páginas recuperadas do manual. "
                    "Baseie-se na mensagem do professor e nas imagens das páginas do manual anexadas para dar a correção. "
                    "Mencione a indicação do professor e cite a página do livro como '(p. X)' de onde tirou a referência visual. "
                    "Se a informação não estiver no texto, na imagem ou na mensagem do professor, abstenha-se de inventar. "
                    "RESPONDA ESTRITAMENTE EM PORTUGUÊS. "
                    "\n\nResponda EXCLUSIVAMENTE com um objeto JSON válido "
                    "com as chaves 'summary' e 'correction'. Não use markdown nem texto fora do JSON."
                )
            elif lang in ("en", "english"):
                instruccion_rag = (
                    "\n\nThe attached images, after the student's frame, are retrieved manual pages. "
                    "Base your correction on the instructor's message and the attached manual page images. "
                    "Mention the instructor's instructions and cite the manual page as '(p. X)' where you retrieved the visual reference or correction. "
                    "If the information is not in the text, the image, or the instructor's message, refrain from inventing details. "
                    "REPLY STRICTLY IN ENGLISH. "
                    "\n\nReply EXCLUSIVELY with a valid JSON object "
                    "containing keys 'summary' and 'correction'. Do not include markdown or text outside the JSON."
                )
            else:
                instruccion_rag = (
                    "\n\nLas imágenes adjuntas, después del fotograma del alumno, son páginas recuperadas del manual. "
                    "Básate en el mensaje del profesor y en las imágenes de las páginas del manual adjuntas para dar la corrección. "
                    "Menciona la indicación del profesor y cita la página del libro como '(p. X)' de donde sacaste la referencia o corrección visual. "
                    "Si la información no está en el texto, en la imagen o en el mensaje del profesor, abstente de inventar. "
                    "RESPONDE ESTRICTAMENTE EN ESPAÑOL. "
                    "\n\nResponde EXCLUSIVAMENTE con un objeto JSON válido "
                    "con las claves 'summary' y 'correction'. "
                    "No agregues markdown, ni texto fuera del JSON."
                )
        else:
            if lang in ("pt", "portuguese", "português", "portugues"):
                instruccion_rag = (
                    "\n\nAnalise o frame crítico do aluno seguindo rigorosamente as instruções do professor ou o contexto técnico fornecido no prompt. "
                    "Não cite números de página '(p. X)' se não houver páginas de manual anexadas. "
                    "RESPONDA ESTRITAMENTE EM PORTUGUÊS. "
                    "\n\nResponda EXCLUSIVAMENTE com um objeto JSON válido "
                    "com as chaves 'summary' e 'correction'. Não use markdown nem texto fora do JSON."
                )
            elif lang in ("en", "english"):
                instruccion_rag = (
                    "\n\nAnalyze the student's critical frame strictly following the instructor's instructions or technical context provided in the prompt. "
                    "Do not cite page numbers '(p. X)' unless manual text explicitly provides them. "
                    "REPLY STRICTLY IN ENGLISH. "
                    "\n\nReply EXCLUSIVELY with a valid JSON object "
                    "containing keys 'summary' and 'correction'. Do not include markdown or text outside the JSON."
                )
            else:
                instruccion_rag = (
                    "\n\nAnaliza el fotograma crítico del alumno siguiendo estrictamente las indicaciones del profesor o las referencias técnicas incluidas en el prompt. "
                    "No cites páginas '(p. X)' si no se incluyeron en el contexto. "
                    "RESPONDE ESTRICTAMENTE EN ESPAÑOL. "
                    "\n\nResponde EXCLUSIVAMENTE con un objeto JSON válido "
                    "con las claves 'summary' y 'correction'. "
                    "No agregues markdown, ni texto fuera del JSON."
                )

        full_prompt = prompt + instruccion_rag

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

        try:
            return self._parsear_json(raw, idioma=idioma)
        except ValueError as err_lang:
            logger.warning("VLM respondió en idioma incorrecto (%s). Reintentando con instrucción estricta...", err_lang)
            prompt_reintento = formatted_prompt + (
                f"\n\nATENCIÓN: Tu respuesta previa fue rechazada porque no estaba en el idioma '{idioma}'. "
                f"RESPONDE OBLIGATORIAMENTE Y ÚNICAMENTE EN EL IDIOMA '{idioma}'. No uses ningún otro idioma."
            )
            raw_retry = generate(
                self.model,
                self.processor,
                prompt_reintento,
                images,
                max_tokens=400,
                temperature=0.0,
                verbose=False,
            )
            return self._parsear_json(raw_retry, idioma=idioma)

    @staticmethod
    def _validar_idioma(texto: str, idioma: Optional[str]) -> None:
        """
        Valida que la respuesta del VLM respete el idioma solicitado ('es', 'pt', 'en').
        Si el VLM responde en otro idioma, lanza ValueError para que el parseador lo rechace.
        """
        if not idioma or not texto:
            return
        lang = idioma.lower().strip()
        if lang in ("portuguese", "português", "portugues"):
            lang = "pt"
        elif lang in ("spanish", "español"):
            lang = "es"
        elif lang in ("english",):
            lang = "en"

        if lang not in ("es", "pt", "en"):
            return

        tokens = re.findall(r"\b[a-záéíóúãõâêîôûàèìòùçñ]+\b", texto.lower())
        if not tokens:
            return
        tokens_set = set(tokens)

        pt_strict_markers = {"do", "da", "dos", "das", "no", "na", "nos", "nas", "não", "você", "quadril", "cotovelo", "mantenha"}
        es_strict_markers = {"del", "al", "cadera", "codo", "mantén", "mantener", "mantenga", "buena", "bueno"}
        en_strict_markers = {"the", "is", "are", "keep", "your", "tight", "with", "avoid", "good", "should", "close"}

        pt_hits = len(tokens_set.intersection(pt_strict_markers))
        es_hits = len(tokens_set.intersection(es_strict_markers))
        en_hits = len(tokens_set.intersection(en_strict_markers))

        if lang == "pt":
            if en_hits >= 2 and pt_hits == 0:
                raise ValueError(f"Respuesta del VLM rechazada: se esperaba idioma 'pt' pero respondió en inglés ({texto[:60]}...).")
            if es_hits >= 2 and pt_hits == 0:
                raise ValueError(f"Respuesta del VLM rechazada: se esperaba idioma 'pt' pero respondió en español ({texto[:60]}...).")
        elif lang == "es":
            if en_hits >= 2 and es_hits == 0:
                raise ValueError(f"Respuesta del VLM rechazada: se esperaba idioma 'es' pero respondió en inglés ({texto[:60]}...).")
            if pt_hits >= 2 and es_hits == 0:
                raise ValueError(f"Respuesta del VLM rechazada: se esperaba idioma 'es' pero respondió en portugués ({texto[:60]}...).")
        elif lang == "en":
            if es_hits >= 2 and en_hits == 0:
                raise ValueError(f"Respuesta del VLM rechazada: se esperaba idioma 'en' pero respondió en español ({texto[:60]}...).")
            if pt_hits >= 2 and en_hits == 0:
                raise ValueError(f"Respuesta del VLM rechazada: se esperaba idioma 'en' pero respondió en portugués ({texto[:60]}...).")

    @staticmethod
    def _parsear_json(text, idioma: Optional[str] = None) -> Dict[str, str]:
        if hasattr(text, "text"):
            text = text.text
        text = str(text).strip()
        parsed_result = None

        # Nivel 1: JSON directo
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                parsed_result = {
                    "summary": str(parsed.get("summary", "Technique feedback")).strip(),
                    "correction": str(parsed.get("correction", "")).strip(),
                }
        except json.JSONDecodeError:
            pass

        # Nivel 2: bloque ```json ... ```
        if not parsed_result:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(1))
                    parsed_result = {
                        "summary": str(parsed.get("summary", "Technique feedback")).strip(),
                        "correction": str(parsed.get("correction", "")).strip(),
                    }
                except json.JSONDecodeError:
                    pass

        # Nivel 3: fallback texto plano
        if not parsed_result:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            summary = sentences[0][:80] if sentences else "Technique feedback"
            parsed_result = {"summary": summary, "correction": text[:500]}

        if idioma:
            texto_completo = f"{parsed_result['summary']} {parsed_result['correction']}"
            LocalVLMAdapter._validar_idioma(texto_completo, idioma)

        return parsed_result

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
            "6. La respuesta puede estar redactada en un idioma diferente al del contexto (por ejemplo, respuesta en portugués o español con manuales en inglés). Evalúa la equivalencia semántica y biomecánica entre idiomas. NO consideres como no respaldada una afirmación por el solo hecho de ser una traducción o sinónimo en otro idioma.\n"
            "7. Responde EXCLUSIVAMENTE con un JSON con el siguiente formato:\n"
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


