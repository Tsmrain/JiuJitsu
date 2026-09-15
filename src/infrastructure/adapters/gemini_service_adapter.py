# src/infrastructure/adapters/gemini_service_adapter.py
"""Adaptador de orquestación para Gemini AI (Generación + Embeddings).

Consolida la lógica de AdaptadorGemini (antes en src/services/adapters.py):
- Generación de texto pedagógico (IGenerationService)
- Generación de embeddings 768-dim con fallback garantizado (IEmbeddingService)

Aplica Variaciones Protegidas (Larman): la capa de aplicación nunca depende
directamente del SDK de Google Genai.
"""

import os
from typing import List, Optional, Dict, Any, Union

from src.domain.interfaces import IGenerationService, IEmbeddingService
from src.domain.models import DesviacionArticular


class AdaptadorGemini(IGenerationService, IEmbeddingService):
    """Adaptador de orquestación para IA Generativa y Vectorización Gemini.

    Garantiza embeddings con dimensión estricta de 768 floats (gemini-embedding-2).
    """

    def __init__(self, api_key: Optional[str] = None):
        from src.infrastructure.adapters.gemini_adapter import GeminiServiceAdapter
        key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._inner = GeminiServiceAdapter(api_key=key)

    def generar_embedding(self, texto: str) -> List[float]:
        """Genera un vector embedding de 768 dimensiones para el texto dado."""
        vector = self._inner.generate_embedding(texto)
        if not vector or len(vector) != 768:
            return [0.05] * 768
        return vector

    def generate_embedding(self, text: str) -> List[float]:
        """Implementación del contrato IEmbeddingService."""
        return self.generar_embedding(text)

    def generar_consejo(
        self,
        tecnica: str,
        desviaciones: List[DesviacionArticular],
        contexto_manual: Optional[str] = None,
    ) -> Union[Dict[str, Any], str]:
        """Implementación del contrato IGenerationService con soporte estructurado JSON."""
        return self._inner.generar_consejo(tecnica, desviaciones, contexto_manual)
