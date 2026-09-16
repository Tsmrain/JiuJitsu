# src/infrastructure/adapters/gemini_service_adapter.py
"""Adaptador de orquestación para Gemini AI (Generación).

Consolida la lógica de AdaptadorGemini (antes en src/services/adapters.py):
- Generación de texto pedagógico (IGenerationService)

Aplica Variaciones Protegidas (Larman): la capa de aplicación nunca depende
directamente del SDK de Google Genai.
"""

import os
from typing import List, Optional, Dict, Any, Union

from src.domain.interfaces import IGenerationService
from src.domain.models import DesviacionArticular


class AdaptadorGemini(IGenerationService):
    """Adaptador de orquestación para IA Generativa Gemini.

    Responsabilidad única: Generación de contenido pedagógico.
    """

    def __init__(self, api_key: Optional[str] = None):
        from src.infrastructure.adapters.gemini_adapter import GeminiServiceAdapter
        key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._inner = GeminiServiceAdapter(api_key=key)


    def generar_consejo(
        self,
        tecnica: str,
        desviaciones: List[DesviacionArticular],
        contexto_manual: Optional[str] = None,
    ) -> Union[Dict[str, Any], str]:
        """Implementación del contrato IGenerationService con soporte estructurado JSON."""
        return self._inner.generar_consejo(tecnica, desviaciones, contexto_manual)
