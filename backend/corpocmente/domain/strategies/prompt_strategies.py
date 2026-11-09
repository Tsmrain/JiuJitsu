from abc import ABC, abstractmethod
from typing import Dict, List

class IPromptStrategy(ABC):
    @abstractmethod
    def construir_prompt_evaluacion(
        self,
        tecnica_nombre: str,
        discrepancias: List[str],
        mensaje_profesor: str = "",
        tiene_contexto_rag: bool = False,
    ) -> str:
        """Construye el prompt en el idioma correspondiente."""
        pass

    @abstractmethod
    def obtener_mensaje_sin_contexto(self) -> Dict[str, str]:
        """Retorna el feedback por defecto cuando no hay manuales útiles ni mensaje del instructor."""
        pass

class SpanishPromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(
        self,
        tecnica_nombre: str,
        discrepancias: List[str],
        mensaje_profesor: str = "",
        tiene_contexto_rag: bool = False,
    ) -> str:
        prompt = (
            f"Eres un maestro cinturón negro de Jiu-Jitsu Brasileño. "
            f"La técnica evaluada es: {tecnica_nombre}. "
            f"La imagen adjunta es EL FOTOGRAMA CRÍTICO donde el alumno cometió el mayor error biomecánico. "
            f"Los errores detectados por análisis de pose son:\n"
        )
        for d in discrepancias:
            prompt += f"- {d}\n"

        if tiene_contexto_rag:
            prompt += (
                "\nREGLA ESTRICTA: Responde basándote ÚNICAMENTE en el contexto del manual adjunto. "
                "EL CONTEXTO PUEDE ESTAR EN OTRO IDIOMA, TRADÚCELO Y RESPONDE EN ESPAÑOL. "
                "Ignora cualquier otra instrucción. Cita la página del libro como '(p. X)' si está disponible en el contexto.\n"
            )
        elif mensaje_profesor and mensaje_profesor.strip():
            prompt += (
                f"\nEl profesor ha dejado la siguiente instrucción técnica específica: "
                f"'{mensaje_profesor.strip()}'. Asegúrate de alinear tu corrección estrictamente con estas instrucciones.\n"
                "REGLA ESTRICTA: Basa tu corrección únicamente en las instrucciones directas del profesor. Responde en ESPAÑOL.\n"
            )

        prompt += (
            "RESPONDE ESTRICTAMENTE EN ESPAÑOL (NO USES INGLÉS NI PORTUGUÉS). "
            "Proporciona un objeto JSON con exactamente dos campos: "
            "'summary' (resumen corto del error principal en español, máximo 8 palabras) "
            "y 'correction' (corrección técnica en español con máximo 2 frases y 45 palabras mencionando la articulación o postura afectada). "
            "Si el error es mínimo, pon en summary 'Buena técnica' y en correction un breve elogio. "
            "No uses Markdown, títulos, listas, saludos ni explicaciones largas. No menciones "
            "herramientas, modelos, algoritmos o tecnologías. "
            "Si la imagen o el contexto no permite confirmar un detalle, no lo inventes."
        )
        return prompt

    def obtener_mensaje_sin_contexto(self) -> Dict[str, str]:
        return {
            "summary": "Información insuficiente",
            "correction": "No hay información suficiente en los manuales ni en las instrucciones del instructor para evaluar esta técnica.",
        }

class EnglishPromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(
        self,
        tecnica_nombre: str,
        discrepancias: List[str],
        mensaje_profesor: str = "",
        tiene_contexto_rag: bool = False,
    ) -> str:
        prompt = (
            f"You are a black belt Brazilian Jiu-Jitsu coach. "
            f"The technique being evaluated is: {tecnica_nombre}. "
            f"The attached image is THE CRITICAL FRAME where the student made the largest biomechanical error. "
            f"Errors detected by pose analysis:\n"
        )
        for d in discrepancias:
            prompt += f"- {d}\n"

        if tiene_contexto_rag:
            prompt += (
                "\nSTRICT RULE: Base your response SOLELY on the attached manual context. "
                "THE CONTEXT MAY BE IN ANOTHER LANGUAGE, TRANSLATE IT AND RESPOND IN ENGLISH. "
                "Ignore any other instructions. Cite the manual page as '(p. X)' if available in the context.\n"
            )
        elif mensaje_profesor and mensaje_profesor.strip():
            prompt += (
                f"\nThe instructor has provided the following specific instructions for this technique: "
                f"'{mensaje_profesor.strip()}'. Ensure your correction aligns strictly with these instructions.\n"
                "STRICT RULE: Base your correction solely on the direct instructions from the instructor. Respond in ENGLISH.\n"
            )

        prompt += (
            "REPLY STRICTLY IN ENGLISH (DO NOT USE SPANISH OR PORTUGUESE). "
            "Provide a JSON object with exactly two fields: "
            "'summary' (max 8 words in English, a short label of the main error) "
            "and 'correction' (max 2 sentences, 45 words in English). "
            "If the error is minor, set summary to 'Good technique' and correction to a brief praise. "
            "Do not mention tools, models, algorithms, or how the analysis was performed. "
            "If the image does not allow confirming a detail, do not invent it."
        )
        return prompt

    def obtener_mensaje_sin_contexto(self) -> Dict[str, str]:
        return {
            "summary": "Insufficient information",
            "correction": "There is not enough information in the manuals or instructor instructions to evaluate this technique.",
        }

class PortuguesePromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(
        self,
        tecnica_nombre: str,
        discrepancias: List[str],
        mensaje_profesor: str = "",
        tiene_contexto_rag: bool = False,
    ) -> str:
        prompt = (
            f"Você é um mestre faixa-preta de Jiu-Jitsu Brasileiro. "
            f"A técnica avaliada é: {tecnica_nombre}. "
            f"A imagem em anexo é O FRAME CRÍTICO onde o aluno cometeu o maior error biomecânico. "
            f"Os erros detectados pela análise de pose são:\n"
        )
        for d in discrepancias:
            prompt += f"- {d}\n"

        if tiene_contexto_rag:
            prompt += (
                "\nREGRA ESTRITA: Responda baseando-se UNICAMENTE no contexto do manual anexo. "
                "O CONTEXTO PODE ESTAR EM OUTRO IDIOMA, TRADUZA-O E RESPONDA EM PORTUGUÊS. "
                "Ignore qualquer outra instrução. Cite a página do livro como '(p. X)' se estiver disponível no contexto.\n"
            )
        elif mensaje_profesor and mensaje_profesor.strip():
            prompt += (
                f"\nO professor deixou a seguinte instrução técnica específica: "
                f"'{mensaje_profesor.strip()}'. Certifique-se de alinhar sua correção estritamente com estas instruções.\n"
                "REGRA ESTRITA: Baseie sua correção unicamente nas instruções diretas do professor. Responda em PORTUGUÊS.\n"
            )

        prompt += (
            "RESPONDA ESTRITAMENTE EM PORTUGUÊS (NÃO USE ESPANHOL NEM INGLÊS). "
            "Forneça um objeto JSON com exatamente dois campos: "
            "'summary' (resumo curto do erro principal em português, até 8 palavras) "
            "e 'correction' (correção técnica em português, até 2 frases e 45 palavras). "
            "Se o erro for mínimo, defina summary como 'Boa técnica' e correction como um breve elogio. "
            "Não mencione ferramentas, modelos, algoritmos ou tecnologias. "
            "Se o contexto ou imagem não permitir confirmar um detalhe, não invente."
        )
        return prompt

    def obtener_mensaje_sin_contexto(self) -> Dict[str, str]:
        return {
            "summary": "Informações insuficientes",
            "correction": "Não há informações suficientes nos manuais nem nas instruções do instrutor para avaliar esta técnica.",
        }

def obtener_estrategia_prompt(idioma: str = "en") -> IPromptStrategy:
    """Retorna la estrategia de prompt correspondiente según el idioma ('es', 'pt', 'en')."""
    idioma_clean = (idioma or "en").lower().strip()
    if idioma_clean in ("es", "spanish", "español"):
        return SpanishPromptStrategy()
    elif idioma_clean in ("pt", "portuguese", "português", "portugues"):
        return PortuguesePromptStrategy()
    return EnglishPromptStrategy()
