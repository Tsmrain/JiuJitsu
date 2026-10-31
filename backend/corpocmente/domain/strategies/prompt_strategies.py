from abc import ABC, abstractmethod
from typing import List

class IPromptStrategy(ABC):
    @abstractmethod
    def construir_prompt_evaluacion(self, tecnica_nombre: str, discrepancias: List[str], mensaje_profesor: str = "") -> str:
        """Construye el prompt en el idioma correspondiente."""
        pass

class SpanishPromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(self, tecnica_nombre: str, discrepancias: List[str], mensaje_profesor: str = "") -> str:
        prompt = (
            f"Eres un maestro cinturón negro de Jiu-Jitsu Brasileño. "
            f"La técnica evaluada es: {tecnica_nombre}. "
            f"La imagen adjunta es EL FOTOGRAMA CRÍTICO donde el alumno cometió el mayor error biomecánico. "
            f"Los errores detectados por análisis de pose son:\n"
        )
        for d in discrepancias:
            prompt += f"- {d}\n"
        if mensaje_profesor and mensaje_profesor.strip():
            prompt += (
                f"\nEl profesor ha dejado la siguiente instrucción técnica específica: "
                f"'{mensaje_profesor.strip()}'. Asegúrate de alinear tu corrección estrictamente con estas instrucciones.\n"
            )
        prompt += (
            "Responde en español con máximo 2 frases y 45 palabras. Indica el principal error "
            "visible y una corrección concreta mencionando la articulación o postura afectada. Usa lenguaje simple, respetuoso y directo. "
            "No uses Markdown, títulos, listas, saludos ni explicaciones largas. No menciones "
            "herramientas, modelos, algoritmos, tecnologías ni cómo se hizo el análisis. "
            "Si la imagen no permite confirmar un detalle, no lo inventes."
        )
        return prompt

class EnglishPromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(self, tecnica_nombre: str, discrepancias: List[str], mensaje_profesor: str = "") -> str:
        prompt = (
            f"You are a black belt Brazilian Jiu-Jitsu coach. "
            f"The technique being evaluated is: {tecnica_nombre}. "
            f"The attached image is THE CRITICAL FRAME where the student made the largest biomechanical error. "
            f"Errors detected by pose analysis:\n"
        )
        for d in discrepancias:
            prompt += f"- {d}\n"
        if mensaje_profesor and mensaje_profesor.strip():
            prompt += (
                f"\nThe instructor has provided the following specific instructions for this technique: "
                f"'{mensaje_profesor.strip()}'. Ensure your correction aligns strictly with these instructions.\n"
            )
        prompt += (
            "Reply in English. Provide a JSON object with exactly two fields: "
            "'summary' (max 8 words, a short label of the main error, e.g. 'Elbow flaring, lose hip connection') "
            "and 'correction' (max 2 sentences, 45 words, Markdown format with one bold keyword and one bullet point if helpful). "
            "If the error is minor, set summary to 'Good technique' and correction to a brief praise. "
            "Cite the source if the context includes one: e.g. 'as taught in Jiu-Jitsu University (p. 116)'. "
            "Do not mention tools, models, algorithms, or how the analysis was performed. "
            "If the image does not allow confirming a detail, do not invent it."
        )
        return prompt
