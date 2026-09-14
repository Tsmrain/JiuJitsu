# src/infrastructure/adapters/gemini_adapter.py
import os
from typing import List, Optional
try:
    from google import genai
except ImportError:
    genai = None

from src.domain.interfaces import IGenerationService, IEmbeddingService
from src.domain.models import DesviacionArticular

class GeminiServiceAdapter(IGenerationService, IEmbeddingService):
    """Adaptador de infraestructura para la API oficial de Google Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if genai and self._api_key:
            self._client = genai.Client(api_key=self._api_key)
        else:
            self._client = None

    def generar_consejo(
        self, 
        tecnica: str, 
        desviaciones: List[DesviacionArticular], 
        contexto_manual: Optional[str] = None
    ) -> str:
        if not desviaciones:
            return f"¡Ejecución impecable de {tecnica}! Mantienes la postura del patrón."

        detalles = "\n".join([
            f"- {d.nombre_articulacion}: Desviación de {d.desviacion_grados:.1f}° "
            f"(Esperado: {d.angulo_esperado:.1f}°, Real: {d.angulo_real:.1f}°)" 
            for d in desviaciones
        ])
        prompt = (
            f"Eres un instructor experto en BJJ. Técnica: {tecnica}. "
            f"Errores:\n{detalles}\n"
            f"Contexto: {contexto_manual or 'Ajusta la postura básica.'}. Da una retroalimentación concisa."
        )
        
        if not self._client:
            falla = desviaciones[0]
            return f"En {tecnica}, se detectó un desajuste en {falla.nombre_articulacion} de {falla.desviacion_grados:.1f}°. Recuerda ajustar el ángulo."

        try:
            response = self._client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
            return response.text
        except Exception:
            response = self._client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            return response.text

    def generate_embedding(self, text: str) -> List[float]:
        if not self._client:
            return [0.0] * 768
        try:
            from google.genai import types
            response = self._client.models.embed_content(
                model="gemini-embedding-2",
                contents=f"task: search result | query: {text}",
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            return response.embeddings[0].values
        except Exception:
            return [0.0] * 768

