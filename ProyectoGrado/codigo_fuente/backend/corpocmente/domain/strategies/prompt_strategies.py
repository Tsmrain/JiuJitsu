from abc import ABC, abstractmethod
from typing import List

class IPromptStrategy(ABC):
    @abstractmethod
    def construir_prompt_evaluacion(self, discrepancias: List[str]) -> str:
        """Construye el prompt en el idioma correspondiente."""
        pass

class PortuguesePromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(self, discrepancias: List[str]) -> str:
        prompt = "Você é um mestre faixa preta de Jiu-Jitsu Brasileiro. "
        prompt += "Analise os seguintes erros biomecânicos detectados na técnica:\n"
        for d in discrepancias:
            prompt += f"- {d}\n"
        prompt += "Forneça instruções claras e corretivas em português."
        return prompt

class SpanishPromptStrategy(IPromptStrategy):
    def construir_prompt_evaluacion(self, discrepancias: List[str]) -> str:
        prompt = "Eres un maestro cinturón negro de Jiu-Jitsu Brasileño. "
        prompt += "Analiza los siguientes errores biomecánicos detectados en la técnica:\n"
        for d in discrepancias:
            prompt += f"- {d}\n"
        prompt += "Proporciona instrucciones claras y correctivas en español."
        return prompt
