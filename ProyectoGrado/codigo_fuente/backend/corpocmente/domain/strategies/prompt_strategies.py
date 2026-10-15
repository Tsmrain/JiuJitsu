from abc import ABC, abstractmethod
from typing import List

class IPromptStrategy(ABC):
    @abstractmethod
    def construir_prompt_evaluacion(self, tecnica_nombre: str, discrepancias: List[str]) -> str:
        """Construye el prompt en el idioma correspondiente."""
        pass

class SpanishPromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(self, tecnica_nombre: str, discrepancias: List[str]) -> str:
        prompt = (
            f"Eres un maestro cinturón negro de Jiu-Jitsu Brasileño. "
            f"La técnica evaluada es: {tecnica_nombre}. "
            f"La imagen adjunta es EL FOTOGRAMA CRÍTICO donde el alumno cometió el mayor error biomecánico. "
            f"Los errores detectados por análisis de pose son:\n"
        )
        for d in discrepancias:
            prompt += f"- {d}\n"
        prompt += (
            "Responde en español con máximo 2 frases y 45 palabras. Indica el principal error "
            "visible y una corrección concreta. Usa lenguaje simple, respetuoso y directo. "
            "No uses Markdown, títulos, listas, saludos ni explicaciones largas. No menciones "
            "herramientas, modelos, algoritmos, tecnologías ni cómo se hizo el análisis. "
            "Si la imagen no permite confirmar un detalle, no lo inventes."
        )
        return prompt
