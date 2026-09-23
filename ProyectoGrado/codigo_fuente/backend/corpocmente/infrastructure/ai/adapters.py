from typing import List, Optional
import os
import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError

from corpocmente.domain.entities.models import EsqueletoBiomecanico

logger = logging.getLogger(__name__)

import cv2
from ultralytics import YOLO

class GeminiRateLimitError(Exception):
    """Excepción lanzada cuando se supera el límite de cuota (Rate Limit 429) de Gemini API."""
    pass

class YOLOPoseAdapter:
    def __init__(self, model_path: str = "yolo11n-pose.pt"):
        # Se guarda el path para lazy-loading del modelo (.pt)
        self.model_path = model_path
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = YOLO(self.model_path)
        return self._model

    def extraer_keypoints(self, video_path: str) -> List[EsqueletoBiomecanico]:
        """Extrae el esqueleto biomecánico de los frames del video usando YOLO."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")
            
        resultados_yolo = self.model.predict(source=video_path, stream=True, verbose=False)
        esqueletos = []
        
        for resultado in resultados_yolo:
            if resultado.keypoints and len(resultado.keypoints.data) > 0:
                # resultado.keypoints.data tiene forma (num_personas, num_keypoints, 3)
                # Tomamos la primera persona detectada
                keypoints_tensor = resultado.keypoints.data[0]
                
                # Aplanar el tensor a una lista de floats
                # YOLOv8-pose por defecto da 17 keypoints (x, y, conf) = 51 valores.
                # Si el modelo específico retorna más (WholeBody), los aplanamos todos.
                kpts_flat = keypoints_tensor.flatten().tolist()
                
                # Asegurar longitud 133 (Rellenar con ceros o truncar según modelo de dominio)
                if len(kpts_flat) < 133:
                    kpts_flat.extend([0.0] * (133 - len(kpts_flat)))
                elif len(kpts_flat) > 133:
                    kpts_flat = kpts_flat[:133]
                    
                esqueletos.append(
                    EsqueletoBiomecanico(
                        keypoints133=kpts_flat,
                        angulos_articulares={}
                    )
                )
        
        if not esqueletos:
            logger.warning(f"No se detectaron poses en el video: {video_path}")
            
        return esqueletos

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

class QwenRerankerAdapter:
    def rerank_frames(self, candidato_frames: List[str], video_alumno: str) -> str:
        """Utiliza Qwen3-VL-Reranker para seleccionar el frame exacto del error."""
        pass
