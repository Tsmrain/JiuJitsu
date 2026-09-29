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
    def __init__(self, colab_url: str = None):
        self.colab_url = colab_url if colab_url is not None else os.getenv("COLAB_TUNNEL_URL", "").strip()

    def extraer_keypoints(self, video_path: str) -> List[EsqueletoBiomecanico]:
        """Extrae el esqueleto biomecánico de los frames del video usando YOLO (Colab remoto)."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")
            
        if not self.colab_url or self.colab_url.startswith("https://placeholder"):
            logger.info("YOLOv26 (Colab) no configurado. Usando fallback local determinista.")
            return [EsqueletoBiomecanico(keypoints133=[0.5]*133, angulos_articulares={})]
            
        import requests
        try:
            endpoint = f"{self.colab_url.rstrip('/')}/extraer_poses"
            with open(video_path, 'rb') as f:
                resp = requests.post(endpoint, files={"video": f}, timeout=120)
            resp.raise_for_status()
            
            data = resp.json()
            esqueletos_dict = data.get("esqueletos", [])
            
            esqueletos = []
            for item in esqueletos_dict:
                esqueletos.append(EsqueletoBiomecanico(**item))
                
            return esqueletos
        except Exception as e:
            logger.error(f"Error llamando a YOLOv26 en Colab: {e}")
            return [EsqueletoBiomecanico(keypoints133=[0.5]*133, angulos_articulares={})]

    def dibujar_error_en_frame(self, frame_path: str, discrepancias: List[str]) -> str:
        """
        Utiliza YOLOv26 en Colab para dibujar la discrepancia sobre la imagen.
        Retorna la ruta temporal de la imagen modificada.
        """
        if not os.path.exists(frame_path):
            return frame_path
            
        if not self.colab_url or self.colab_url.startswith("https://placeholder"):
            return frame_path
            
        import requests
        import uuid
        try:
            endpoint = f"{self.colab_url.rstrip('/')}/dibujar_error"
            with open(frame_path, 'rb') as f:
                resp = requests.post(endpoint, files={"imagen": f}, data={"discrepancias": str(discrepancias)}, timeout=60)
            resp.raise_for_status()
            
            resaltado_path = f"/tmp/resaltado_{uuid.uuid4().hex[:8]}.jpg"
            with open(resaltado_path, "wb") as f:
                f.write(resp.content)
            return resaltado_path
        except Exception as e:
            logger.error(f"Error pidiendo a YOLOv26 dibujar el error: {e}")
            return frame_path

from corpocmente.config import settings

class GeminiApiAdapter:
    """
    Adaptador (GoF Adapter) para encapsular las llamadas a la API de Google Gemini
    utilizando el SDK oficial google-genai.
    
    Aísla al dominio de los detalles de red, autenticación y manejo de tokens.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash-lite"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
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
            video_file = self.client.files.upload(path=video_path)
            
            # Si el video está en estado PROCESSING, esperar a que pase a ACTIVE
            import time
            while video_file.state == "PROCESSING":
                time.sleep(1)
                video_file = self.client.files.get(name=video_file.name)

            if video_file.state == "FAILED":
                logger.error("El archivo de video falló en el procesamiento de Gemini.")
                return False

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[video_file, prompt_validacion]
            )
            
            # Limpieza del archivo temporal en la nube de Google
            try:
                self.client.files.delete(name=video_file.name)
            except Exception as del_err:
                logger.warning(f"No se pudo eliminar el archivo temporal de Gemini: {del_err}")
            
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
            image_file = self.client.files.upload(path=frame_image_path)

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


