from typing import List, Optional
import os
import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError

from corpocmente.domain.entities.models import EsqueletoBiomecanico

logger = logging.getLogger(__name__)

class GeminiRateLimitError(Exception):
    """Excepción lanzada cuando se supera el límite de cuota (Rate Limit 429) de Gemini API."""
    pass
class YOLOPoseAdapter:
    def extraer_keypoints(self, video_path: str) -> List[EsqueletoBiomecanico]:
        """Extrae el esqueleto biomecánico del video usando YOLO v11/26."""
        pass

class GeminiApiAdapter:
    """
    Adaptador (GoF Adapter) para encapsular las llamadas a la API de Google Gemini
    utilizando el SDK oficial google-genai.
    
    Aísla al dominio de los detalles de red, autenticación y manejo de tokens.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash-lite"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Se requiere una API Key válida para instanciar GeminiApiAdapter.")
        
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def validar_es_jiujitsu(self, video_path: str) -> bool:
        """
        Valida mediante visión multimodal de Gemini si el video corresponde a una técnica de Jiu-Jitsu.
        Resuelve el paso 2 del Flujo Principal y el Flujo Alternativo 2a (Prevención de SPAM).
        """
        if not os.path.exists(video_path):
            logger.error(f"El archivo de video no existe en la ruta: {video_path}")
            return False

        prompt_validacion = (
            "Analiza brevemente este video. ¿El contenido muestra a personas practicando o ejecutando "
            "una técnica, movimiento o lucha de Jiu-Jitsu Brasileño (BJJ) o Artes Marciales Grappling? "
            "Responde estrictamente con la palabra 'SI' o 'NO'."
        )

        try:
            # Cargar el archivo utilizando la Files API de Gemini para procesamiento multimodal
            video_file = self.client.files.upload(file=video_path)
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[video_file, prompt_validacion]
            )
            
            # Limpieza del archivo temporal en la nube de Google
            self.client.files.delete(name=video_file.name)
            
            resultado = response.text.strip().upper() if response.text else "NO"
            return "SI" in resultado or "SÍ" in resultado

        except APIError as e:
            if getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("Límite de cuota superado en la API de Gemini durante la validación.")
                raise GeminiRateLimitError("Cuota de Gemini API agotada (429).") from e
            logger.error(f"Error de API al validar video con Gemini: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en validar_es_jiujitsu: {e}")
            return False

    def generar_texto_feedback(self, prompt: str, frame_image_path: str) -> str:
        """
        Genera la evaluación cualitativa estructurada en el idioma seleccionado (ES/PT)
        enviando el prompt de la estrategia y la imagen del fotograma con la discrepancia clave.
        """
        if not os.path.exists(frame_image_path):
            raise FileNotFoundError(f"Fotograma de análisis no encontrado en: {frame_image_path}")

        try:
            # Cargar el fotograma estático (JPG/PNG) para la inspección visual de Gemini
            image_file = self.client.files.upload(file=frame_image_path)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[image_file, prompt],
                config=types.GenerateContentConfig(
                    temperature=0.2, # Baja temperatura para respuestas consistentes y técnicas
                    max_output_tokens=800
                )
            )

            # Limpiar la imagen subida
            self.client.files.delete(name=image_file.name)

            if response.text:
                return response.text.strip()
            else:
                raise ValueError("Gemini API retornó una respuesta vacía.")

        except APIError as e:
            if getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("Límite de cuota (429) alcanzado al generar feedback.")
                raise GeminiRateLimitError("Límite de velocidad/cuota excedido en Gemini API.") from e
            logger.error(f"Error en llamada a Gemini API: {e}")
            raise e

class QwenRerankerAdapter:
    def rerank_frames(self, candidato_frames: List[str], video_alumno: str) -> str:
        """Utiliza Qwen3-VL-Reranker para seleccionar el frame exacto del error."""
        pass
