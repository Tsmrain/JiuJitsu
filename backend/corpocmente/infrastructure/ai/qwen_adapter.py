import json
import logging
import os
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

NGROK_HEADERS = {
    "ngrok-skip-browser-warning": "1",
    "User-Agent": "CorpocmenteBackend/1.0",
}


class QwenEmbeddingAdapter:
    """
    Adaptador para Qwen3-VL-Embedding-2B (Google Colab Remoto / Fallback Local).

    Soporta:
    - generar_embedding_texto()
    - generar_embedding_imagen() para imágenes usando el endpoint /embed_images.
    - generar_embedding() como alias directo hacia generar_embedding_imagen().
    """

    def __init__(self, colab_url: str = None):
        self._dim = 2048
        self.colab_url = (
            colab_url
            if colab_url is not None
            else os.getenv("COLAB_TUNNEL_URL", "")
        ).strip()

    def _base_url(self) -> str:
        if (
            not self.colab_url
            or "placeholder" in self.colab_url
            or self.colab_url.startswith("https://placeholder")
        ):
            raise RuntimeError(
                "COLAB_TUNNEL_URL no está configurada correctamente. "
                "Levanta el worker de Colab y copia la URL de ngrok en .env."
            )
        return self.colab_url.rstrip("/")

    def _validar_vector(self, vector: List[float]) -> List[float]:
        if not isinstance(vector, list):
            raise ValueError("El embedding devuelto no es una lista.")
        if len(vector) != self._dim:
            raise ValueError(
                f"Dimensión inesperada de embedding: {len(vector)}. "
                f"Se esperaban {self._dim} para la colección rag_knowledge."
            )
        return [float(x) for x in vector]

    def generar_embedding_texto(self, texto: str) -> List[float]:
        """Genera un embedding de texto de 2048 dimensiones para la teoría (RAG)."""
        # Prioridad 1: Google Drive Data Lake si token.json existe
        try:
            from corpocmente.infrastructure.storage.google_drive_client import GoogleDriveDataLakeClient
            client = GoogleDriveDataLakeClient()
            if client.token_file.exists():
                import uuid
                job_id = f"query_{uuid.uuid4().hex[:8]}"
                res = client.vectorizar_texto_qwen(texto, job_id=job_id, timeout=60)
                embs = res.get("embeddings") or []
                if embs:
                    return self._validar_vector(embs[0])
        except Exception as e_drive:
            logger.warning("Fallo vectorizando texto vía Drive (%s), intentando fallback HTTP...", e_drive)

        endpoint = f"{self._base_url()}/embed_text"

        response = requests.post(
            endpoint,
            data={"texto": texto},
            headers=NGROK_HEADERS,
            timeout=120,
        )
        response.raise_for_status()

        data = response.json()
        embeddings = data.get("embeddings") or []

        if not embeddings:
            raise ValueError("El worker no devolvió embeddings de texto.")

        return self._validar_vector(embeddings[0])

    def generar_embedding_imagen(self, image_path: str, prompt: str = "consulta_visual") -> List[float]:
        """
        Vectoriza una imagen real usando el Worker de Colab (Google Drive Data Lake o /embed_images).
        No usa fallback de vector inventado para evitar ensuciar Qdrant.
        """
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"No existe la imagen para vectorizar: {image_path}")

        # Prioridad 1: Google Drive Data Lake si token.json existe
        try:
            from corpocmente.infrastructure.storage.google_drive_client import GoogleDriveDataLakeClient
            client = GoogleDriveDataLakeClient()
            if client.token_file.exists():
                import uuid
                import base64
                job_id = f"img_{uuid.uuid4().hex[:8]}"
                with open(image_path, "rb") as f:
                    b64_str = base64.b64encode(f.read()).decode("utf-8")
                lote = [{"label": prompt or "consulta_visual", "b64": b64_str}]
                res = client.vectorizar_imagenes_qwen(lote, job_id=job_id, timeout=60)
                embs = res.get("embeddings") or []
                if embs:
                    return self._validar_vector(embs[0])
        except Exception as e_drive:
            logger.warning("Fallo vectorizando imagen vía Drive (%s), intentando fallback HTTP...", e_drive)

        if not self.colab_url or "placeholder" in self.colab_url:
            raise RuntimeError(
                "COLAB_TUNNEL_URL no está configurada para generar embeddings visuales y no hay token.json."
            )

        endpoint = f"{self._base_url()}/embed_images"
        filename = os.path.basename(image_path)
        ext = filename.lower()

        if ext.endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
        elif ext.endswith(".png"):
            mime_type = "image/png"
        elif ext.endswith(".webp"):
            mime_type = "image/webp"
        elif ext.endswith((".tif", ".tiff")):
            mime_type = "image/tiff"
        elif ext.endswith(".bmp"):
            mime_type = "image/bmp"
        else:
            mime_type = "image/jpeg"

        label = prompt or "consulta_visual"

        with open(image_path, "rb") as f:
            response = requests.post(
                endpoint,
                data={
                    "labels": label,
                    "texts_json": json.dumps([label], ensure_ascii=False),
                },
                files={
                    "files": (
                        filename,
                        f,
                        mime_type,
                    )
                },
                headers=NGROK_HEADERS,
                timeout=180,
            )

        if response.status_code == 404:
            raise RuntimeError(
                "El worker de Colab no expone /embed_images. "
                "Actualiza el notebook del worker multimodal."
            )

        response.raise_for_status()
        data = response.json()

        embeddings = data.get("embeddings") or []
        if not embeddings:
            raise ValueError("El worker no devolvió embeddings de imagen.")

        return self._validar_vector(embeddings[0])

    def generar_embedding(self, image_path: str, prompt: str = "consulta_visual") -> List[float]:
        """Delegación segura a generar_embedding_imagen para compatibilidad de firma."""
        return self.generar_embedding_imagen(image_path, prompt=prompt)
