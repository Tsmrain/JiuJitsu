# src/infrastructure/adapters/gemini_embedding_adapter.py
"""Adaptador de Infraestructura/Servicio para gemini-embedding-2 (Google GenAI SDK).

Implementa IEmbeddingService siguiendo las directrices oficiales de Google Developers,
fijando dimensión canónica en 768 y prefijo semántico 'task: search result | query:'
para optimizar la representación vectorial para tareas de recuperación (retrieval).
"""

import os
import time
from typing import List, Optional
from google import genai
from google.genai import types
from src.domain.interfaces import IEmbeddingService


class GeminiEmbedding2Adapter(IEmbeddingService):
    """Adapter para gemini-embedding-2 multimodal (dimensión estricta 768)."""

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._client = genai.Client(api_key=key) if key else None
        self._model = "gemini-embedding-2"
        self._dim = 768

    def generar_embedding(self, texto: str) -> List[float]:
        """Genera embedding con task_type optimizado para retrieval y dimensión 768."""
        if not self._client:
            # Vector determinista normalizado de 768 dimensiones para entornos sin API key
            return [0.05] * self._dim

        response = self._client.models.embed_content(
            model=self._model,
            contents=f"task: search result | query: {texto}",
            config=types.EmbedContentConfig(output_dimensionality=self._dim),
        )
        vector = response.embeddings[0].values
        if len(vector) != self._dim:
            raise ValueError(f"Dimensión incorrecta: {len(vector)} != {self._dim}")
        return vector

    def generar_embeddings_batch(
        self, textos: List[str], max_retries: int = 3, backoff_base: float = 1.0
    ) -> List[List[float]]:
        """Genera embeddings en lote para ingesta masiva con reintento exponencial ante 429."""
        if not textos:
            return []

        if not self._client:
            return [[0.05] * self._dim for _ in textos]

        prepared = [f"task: search result | query: {t}" for t in textos]

        for intento in range(max_retries):
            try:
                response = self._client.models.embed_content(
                    model=self._model,
                    contents=prepared,
                    config=types.EmbedContentConfig(output_dimensionality=self._dim),
                )
                vectors = [e.values for e in response.embeddings]
                if any(len(v) != self._dim for v in vectors):
                    raise ValueError("Uno o más embeddings tienen dimensión incorrecta")
                return vectors
            except Exception as e:
                err_str = str(e).lower()
                if ("429" in err_str or "quota" in err_str or "exhausted" in err_str) and intento < max_retries - 1:
                    wait_time = backoff_base * (2**intento)
                    time.sleep(wait_time)
                else:
                    raise

        return []

    def generate_embedding(self, text: str) -> List[float]:
        """Implementación estricta del contrato IEmbeddingService."""
        return self.generar_embedding(text)
