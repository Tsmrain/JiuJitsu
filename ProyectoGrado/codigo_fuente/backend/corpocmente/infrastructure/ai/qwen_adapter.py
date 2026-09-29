import os
import requests
from typing import List
import logging

logger = logging.getLogger(__name__)

class QwenEmbeddingAdapter:
    """Adaptador para Qwen3-VL-Embedding-2B (Google Colab Remoto / Fallback Local)."""

    def __init__(self, colab_url: str = None):
        self._dim = 2048
        self.colab_url = colab_url if colab_url is not None else os.getenv("COLAB_TUNNEL_URL", "").strip()

    def generar_embedding(self, image_path: str) -> List[float]:
        """
        DEPRECATED (C11.4): Este método apunta al endpoint `/embed` que no existe
        en el Worker de Colab actual (solo existe `/embed_text`).
        
        El pipeline RAG actual usa `generar_embedding_texto` con una query textual
        construida a partir del nombre de la técnica + discrepancias detectadas.
        
        Se mantiene por compatibilidad con tests existentes. NO USAR en código nuevo.
        """
        logger.warning(
            "QwenEmbeddingAdapter.generar_embedding (imagen) está DEPRECATED. "
            "Usar generar_embedding_texto en su lugar."
        )
        if not self.colab_url or self.colab_url.startswith("https://placeholder"):
            logger.info("Usando fallback de Qwen: vector determinista 2048-dim.")
            return [0.05] * self._dim

        # Invocación remota al Worker de Colab
        try:
            endpoint = f"{self.colab_url.rstrip('/')}/embed"
            
            # Asumiendo que enviamos la imagen en base64 o como multipart
            # Por simplicidad en la arquitectura actual del worker, enviaremos la ruta local
            # o se simula si es un POST a /embed
            # (en un entorno distribuido real subiríamos el bytearray)
            resp = requests.post(endpoint, json={"image_path": image_path}, timeout=60)
            resp.raise_for_status()
            
            data = resp.json()
            vectores = data.get("embeddings", [])
            
            if vectores and len(vectores[0]) == self._dim:
                return vectores[0]
            else:
                logger.warning("Colab Qwen retornó dimensiones inesperadas.")
                return [0.05] * self._dim
                
        except Exception as e:
            logger.error(f"Error llamando a Qwen en Colab: {e}")
            return [0.05] * self._dim

    def generar_embedding_texto(self, texto: str) -> List[float]:
        """Genera un embedding de texto de 2048 dimensiones para la teoría (RAG)."""
        if not self.colab_url or self.colab_url.startswith("https://placeholder"):
            logger.info("Usando fallback de Qwen texto: vector determinista 2048-dim.")
            return [0.07] * self._dim

        try:
            endpoint = f"{self.colab_url.rstrip('/')}/embed_text"
            resp = requests.post(endpoint, data={"texto": texto}, timeout=60)
            resp.raise_for_status()
            
            data = resp.json()
            vectores = data.get("embeddings", [])
            
            if vectores and len(vectores[0]) == self._dim:
                return vectores[0]
            else:
                logger.warning("Colab Qwen retornó dimensiones inesperadas para texto.")
                return [0.07] * self._dim
                
        except Exception as e:
            logger.error(f"Error llamando a Qwen texto en Colab: {e}")
            return [0.07] * self._dim
