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

        tiene_msg = bool(mensaje_profesor and mensaje_profesor.strip())
        if tiene_contexto_rag and tiene_msg:
            prompt += (
                f"\nEl profesor ha dejado la siguiente instrucción técnica específica: "
                f"'{mensaje_profesor.strip()}'.\n"
                "Usa el contexto de los manuales adjuntos junto con las indicaciones del profesor como base y límite técnico de tu conocimiento, "
                "pero razona con libertad en un lenguaje humano, cercano y práctico de entrenador en el tatami (sin copiar frases rígidas del libro).\n"
            )
        elif tiene_contexto_rag:
            prompt += (
                "\nUsa los manuales adjuntos y lo observable en el fotograma como base y límite técnico de tu conocimiento, "
                "pero razona contextualmente y explícalo con naturalidad humana como un entrenador en el tatami (sin copiar frases literales del libro).\n"
            )
        elif tiene_msg:
            prompt += (
                f"\nEl profesor ha dejado la siguiente instrucción técnica específica: "
                f"'{mensaje_profesor.strip()}'.\n"
                "Usa esa secuencia técnica del profesor como base principal y conecta las articulaciones detectadas con lo que ves en el fotograma, "
                "explicando la corrección de forma humana, natural y directa (sin cambiar el mecanismo ni invertir los pasos que indicó el profesor).\n"
            )
        else:
            prompt += (
                "\nNo hay manuales ni instrucciones escritas del profesor cargadas para esta técnica. "
                "Analiza directamente el fotograma clave limpio del alumno junto con el nombre de la técnica "
                "y los errores biomecánicos detectados para brindar una corrección práctica y humana basada en lo observable.\n"
            )

        prompt += (
            "ESTILO Y REGLAS OBLIGATORIAS:\n"
            "1. Respeta el objetivo real de la técnica evaluada: si es un escape, salida o pase de guardia, la prioridad es romper el control o abrir las piernas de tu compañero para liberarte; si es una sumisión o control, la prioridad es asegurar y finalizar.\n"
            "2. Traduce TODOS los términos al español correcto (ej. 'cotovelo'->'codo', 'joelho'->'rodilla', 'quadril'->'cadera'), sin dejar palabras en portugués ni inglés.\n"
            "3. NUNCA menciones nombres propios de personas (alumnos, profesores o autores) ni los términos 'Tori' o 'Uke'. "
            "Háblale directamente al practicante en segunda persona ('mantén...', 'presiona...', 'abre...') y, como máximo, refiérete a 'tu compañero' si hablas de la otra persona.\n"
            "4. NO cites páginas como '(p. X)' ni nombres de libros, ni menciones 'patrón'.\n"
            "5. Observa con precisión el fotograma limpio para respetar si la persona está de pie, arrodillada o acostada, y explica qué ajuste físico concreto en las articulaciones afectadas mejora la ejecución de esta técnica.\n"
            "6. RESPONDE ESTRICTAMENTE EN ESPAÑOL. Proporciona un objeto JSON con exactamente dos campos: "
            "'summary' (título breve y accionable del ajuste principal en español, máximo 8 palabras) "
            "y 'correction' (corrección humana, clara y contextual de coach en español, máximo 2 frases y 50 palabras mencionando la articulación o postura afectada). "
            "Si el error es mínimo, pon en summary 'Buena técnica' y en correction un breve elogio. "
            "No uses Markdown, títulos, listas, saludos ni menciones herramientas, modelos o algoritmos."
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

        tiene_msg = bool(mensaje_profesor and mensaje_profesor.strip())
        if tiene_contexto_rag and tiene_msg:
            prompt += (
                f"\nThe instructor has provided the following specific instructions for this technique: "
                f"'{mensaje_profesor.strip()}'.\n"
                "Use both the instructor's instructions and the attached manual context as your knowledge boundary, "
                "synthesizing them naturally like a real mats-side coach rather than copying textbook phrases.\n"
            )
        elif tiene_contexto_rag:
            prompt += (
                "\nUse the attached manual context and the visible keyframe as your knowledge boundary, "
                "explaining the adjustment naturally like a real coach on the mat rather than copying literal textbook phrasing.\n"
            )
        elif tiene_msg:
            prompt += (
                f"\nThe instructor has provided the following specific instructions for this technique: "
                f"'{mensaje_profesor.strip()}'. Ensure your correction aligns strictly with these instructions. "
                "Keep a natural, practical mats-side coaching tone.\n"
            )
        else:
            prompt += (
                "\nNo reference manuals or instructor notes are loaded for this technique. "
                "Analyze the clean student keyframe directly together with the technique name "
                "and detected biomechanical deviations, giving a practical coaching correction grounded in what is visible.\n"
            )

        prompt += (
            "MANDATORY RULES:\n"
            "1. Respect the true goal of the evaluated technique: if it is an escape, guard break, or pass, focus on freeing yourself or opening the guard (never say to hold the partner's guard); if it is a submission or pin, focus on control and finishing.\n"
            "2. NEVER use proper names of people or the terms 'Tori' or 'Uke'. Address the practitioner directly in second person ('you should...', 'keep...') and refer at most to 'your partner'.\n"
            "3. Do NOT cite page numbers '(p. X)', book titles, or robotic phrases like 'aligned with the pattern'.\n"
            "4. Look at the clean frame and connect the affected joints directly to the concrete body adjustment and what it achieves in this technique.\n"
            "5. REPLY STRICTLY IN ENGLISH (DO NOT USE SPANISH OR PORTUGUESE). Provide a JSON object with exactly two fields: "
            "'summary' (max 8 words in English, actionable label of the main fix) "
            "and 'correction' (max 2 sentences, 50 words in English in a natural coaching tone). "
            "If the error is minor, set summary to 'Good technique' and correction to brief praise. "
            "Do not use markdown or mention tools, models, or algorithms."
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

        tiene_msg = bool(mensaje_profesor and mensaje_profesor.strip())
        if tiene_contexto_rag and tiene_msg:
            prompt += (
                f"\nO professor deixou a seguinte instrução técnica específica: "
                f"'{mensaje_profesor.strip()}'.\n"
                "Use tanto as instruções do professor quanto o contexto do manual anexo como base e limite técnico, "
                "explicando de forma humana, natural e prática como um treinador no tatame (sem copiar frases rígidas do livro).\n"
            )
        elif tiene_contexto_rag:
            prompt += (
                "\nUse o contexto do manual anexo e o frame visível como base e limite técnico, "
                "raciocinando de forma humana, natural e prática como um treinador no tatame.\n"
            )
        elif tiene_msg:
            prompt += (
                f"\nO professor deixou a seguinte instrução técnica específica: "
                f"'{mensaje_profesor.strip()}'. Use-a como base técnica junto com as articulações detectadas, "
                "com linguagem natural e prática de treinador no tatame.\n"
            )
        else:
            prompt += (
                "\nNão há manuais nem instruções do instrutor carregadas para esta técnica. "
                "Analise diretamente o frame limpo do aluno junto com o nome da técnica "
                "e os desvios biomecânicos detectados para fornecer uma correção prática e humana baseada no que é visível.\n"
            )

        prompt += (
            "REGRAS OBRIGATÓRIAS:\n"
            "1. Respeite o objetivo real da técnica avaliada: se for uma saída, fuga ou abertura/passagem de guarda, foque em abrir ou sair do controle do parceiro; se for finalização ou imobilização, foque em controlar e finalizar.\n"
            "2. NUNCA mencione nomes próprios de pessoas nem os termos 'Tori' ou 'Uke'. Fale diretamente na segunda pessoa ('você deve...', 'mantenha...') e refira-se no máximo a 'seu parceiro'.\n"
            "3. NÃO cite números de página '(p. X)', nomes de livros nem expressões robóticas como 'alinhado com o padrão'.\n"
            "4. Observe o frame limpo e conecte as articulações afetadas ao ajuste corporal concreto e ao seu efeito nesta técnica.\n"
            "5. RESPONDA ESTRITAMENTE EM PORTUGUÊS. Forneça um objeto JSON com exatamente dois campos: "
            "'summary' (título curto e acionável em português, até 8 palavras) "
            "e 'correction' (correção humana e clara de treinador em português, até 2 frases e 50 palavras). "
            "Se o erro for mínimo, defina summary como 'Boa técnica' e correction como um breve elogio. "
            "Não use markdown nem mencione ferramentas, modelos ou algoritmos."
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
