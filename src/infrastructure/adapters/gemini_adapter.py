# src/infrastructure/adapters/gemini_adapter.py
import os
import json
from typing import List, Optional, Dict, Any, Union
try:
    from google import genai
except ImportError:
    genai = None

from src.domain.interfaces import IGenerationService, IEmbeddingService
from src.domain.models import DesviacionArticular

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
    ) -> Union[Dict[str, Any], str]:
        if not desviaciones:
            return {
                "analisis_postural": f"Ejecución impecable de {tecnica}.",
                "riesgo_lesion": "Bajo o nulo. La postura preserva la integridad articular.",
                "paso_a_paso": "Continúa entrenando la técnica manteniendo la postura biomecánica de referencia.",
                "resumen_ejecutivo": f"¡Excelente ejecución de {tecnica}! Mantienes la postura del patrón."
            }

        falla = desviaciones[0]
        prompt = (
            f"Eres un instructor y analista biomecánico experto en Jiu-Jitsu Brasileño (BJJ). "
            f"Técnica evaluada: {tecnica}.\n"
            f"Desviaciones biomecánicas detectadas en el alumno:\n"
            f"- Articulación: {falla.nombre_articulacion} (Ángulo Esperado: {falla.angulo_esperado:.1f}°, Ángulo Real: {falla.angulo_real:.1f}°, Desviación: {falla.desviacion_grados:.1f}°).\n"
            f"Contexto técnico y pedagógico del manual de referencia (Jiu Jitsu University):\n"
            f"{contexto_manual or 'Mantén la postura base, base cerrada y control del eje articular'}.\n\n"
            f"INSTRUCCIONES DE RESPUESTA:\n"
            f"Debes responder ESTRICTAMENTE en formato JSON válido (sin texto adicional fuera del JSON), "
            f"con las siguientes 4 claves exactas:\n"
            f"1. \"analisis_postural\": Explicación biomecánica detallada de la posición y el desajuste angular detectado.\n"
            f"2. \"riesgo_lesion\": Evaluación del riesgo de lesión o ineficiencia mecánica producida por la desviación.\n"
            f"3. \"paso_a_paso\": Guía correctiva accionable en pasos secuenciales para corregir el ángulo.\n"
            f"4. \"resumen_ejecutivo\": Síntesis concisa y motivadora para el alumno.\n"
        )
        
        fallback_dict = {
            "analisis_postural": f"En {tecnica}, se detectó un desajuste en {falla.nombre_articulacion} de {falla.desviacion_grados:.1f}° (Esperado: {falla.angulo_esperado:.1f}°, Real: {falla.angulo_real:.1f}°).",
            "riesgo_lesion": "Riesgo de sobrecarga articular o pérdida de apalancamiento mecánico durante la ejecución.",
            "paso_a_paso": f"1. Reajusta la posición de {falla.nombre_articulacion}.\n2. Corrige el ángulo hacia {falla.angulo_esperado:.1f}° antes de aplicar presión.",
            "resumen_ejecutivo": f"En {tecnica}, se detectó un desajuste en {falla.nombre_articulacion} de {falla.desviacion_grados:.1f}°. Recuerda ajustar el ángulo."
        }

        if not self._client:
            return fallback_dict

        try:
            response = self._client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            raw_text = (response.text or "").strip()
            
            # Limpiar posibles bloques de markdown ```json ... ```
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()
            
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict) and all(k in parsed for k in ["analisis_postural", "riesgo_lesion", "paso_a_paso", "resumen_ejecutivo"]):
                return parsed
            elif isinstance(parsed, dict):
                # Completar claves faltantes con fallback_dict
                for k in ["analisis_postural", "riesgo_lesion", "paso_a_paso", "resumen_ejecutivo"]:
                    if k not in parsed:
                        parsed[k] = fallback_dict[k]
                return parsed
            return fallback_dict
        except Exception:
            return fallback_dict

    def generate_embedding(self, text: str) -> List[float]:
        if not self._client:
            return [0.05] * 768
        try:
            from google.genai import types
            model = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
            response = self._client.models.embed_content(
                model=model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"[ERROR GEMINI EMBEDDING] {e}")
            return [0.05] * 768

    def generar_embedding(self, texto: str) -> List[float]:
        return self.generate_embedding(texto)

