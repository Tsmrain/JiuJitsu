"""
backend/corpocmente/infrastructure/ai/qwen_adapter.py
Adaptador de embeddings para Qwen3-VL.
Soporta inferencia local nativa con Apple Silicon MLX (USE_LOCAL_QWEN=true)
o túnel HTTP remoto hacia Google Colab (fallback).
"""
import json
import logging
import os
import threading
from typing import List, Optional, Union
from PIL import Image

import requests

logger = logging.getLogger(__name__)

NGROK_HEADERS = {
    "ngrok-skip-browser-warning": "1",
    "User-Agent": "CorpocmenteBackend/1.0",
}

# Cache global del modelo y processor para evitar recargas en memoria
_local_model = None
_local_processor = None
_local_lock = threading.Lock()


class QwenEmbeddingAdapter:
    """
    Adaptador para Qwen3-VL-Embedding-2B.

    Genera representaciones vectoriales densas de exactamente 2048 dimensiones,
    compatibles con la colección rag_knowledge de Qdrant.

    Soporta:
    - generar_embedding_texto()
    - generar_embedding_imagen()
    - generar_embedding() como alias directo hacia generar_embedding_imagen().
    - generar_embeddings_texto_lote()
    """

    def __init__(
        self,
        colab_url: Optional[str] = None,
        use_local: Optional[bool] = None,
        local_model_id: Optional[str] = None,
    ):
        self._dim = 2048

        if use_local is not None:
            self.use_local = use_local
        else:
            self.use_local = os.getenv("USE_LOCAL_QWEN", "true").lower() in ("true", "1", "yes")

        self.local_model_id = (
            local_model_id
            or os.getenv("LOCAL_QWEN_MODEL", "mlx-community/Qwen3-VL-Embedding-2B-8bit")
        ).strip()

        self.colab_url = (
            colab_url
            if colab_url is not None
            else os.getenv("COLAB_TUNNEL_URL", "")
        ).strip()

    @classmethod
    def _get_local_model_and_processor(cls, model_id: str):
        global _local_model, _local_processor
        if _local_model is None or _local_processor is None:
            with _local_lock:
                if _local_model is None or _local_processor is None:
                    try:
                        from mlx_embeddings import load
                    except ImportError as err:
                        raise ImportError(
                            "mlx_embeddings no está disponible en este entorno. "
                            "Instala la librería ejecutando: pip install mlx-embeddings mlx-lm"
                        ) from err
                    logger.info("Cargando modelo local Qwen MLX: %s", model_id)
                    _local_model, _local_processor = load(model_id)
                    logger.info("Modelo local Qwen MLX cargado exitosamente.")
        return _local_model, _local_processor

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

    # --- INFERENCIA LOCAL MLX ---

    def _generar_embedding_texto_local(self, texto: str) -> List[float]:
        model, processor = self._get_local_model_and_processor(self.local_model_id)
        import mlx.core as mx

        if hasattr(model, "language_model"):
            model.language_model._position_ids = None
            model.language_model._rope_deltas = None

        inputs = processor.prepare_embedding_inputs([{"text": texto}])
        outputs = model(**inputs)
        mx.eval(outputs.text_embeds)
        vector = outputs.text_embeds[0].tolist()
        return self._validar_vector(vector)

    def _generar_embedding_imagen_local(
        self,
        image_input: Union[str, Image.Image],
        prompt: str = "consulta_visual",
    ) -> List[float]:
        if isinstance(image_input, str):
            if not os.path.isfile(image_input):
                raise FileNotFoundError(f"No existe la imagen para vectorizar: {image_input}")
            img_target = image_input
        elif isinstance(image_input, Image.Image):
            img_target = image_input
        else:
            raise ValueError(f"Tipo de imagen no soportado: {type(image_input)}")

        model, processor = self._get_local_model_and_processor(self.local_model_id)
        import mlx.core as mx

        if hasattr(model, "language_model"):
            model.language_model._position_ids = None
            model.language_model._rope_deltas = None

        inputs = processor.prepare_embedding_inputs([
            {"image": img_target, "text": prompt or "consulta_visual"}
        ])
        outputs = model(**inputs)
        mx.eval(outputs.text_embeds)
        vector = outputs.text_embeds[0].tolist()
        return self._validar_vector(vector)

    def _generar_embeddings_texto_lote_local(self, textos: List[str]) -> List[List[float]]:
        if not textos:
            return []
        model, processor = self._get_local_model_and_processor(self.local_model_id)
        import mlx.core as mx

        resultados = []
        lote_tamano = 8
        for i in range(0, len(textos), lote_tamano):
            batch = textos[i : i + lote_tamano]
            items = [{"text": t} for t in batch]
            inputs = processor.prepare_embedding_inputs(items)
            outputs = model(**inputs)
            mx.eval(outputs.text_embeds)
            for v in outputs.text_embeds:
                resultados.append(self._validar_vector(v.tolist()))
        return resultados

    # --- API PÚBLICA ---

    def generar_embedding_texto(self, texto: str) -> List[float]:
        """Genera un embedding de texto de 2048 dimensiones para la teoría (RAG)."""
        if self.use_local:
            try:
                return self._generar_embedding_texto_local(texto)
            except Exception as e:
                logger.error("Error en inferencia local MLX para texto: %s", e)
                if not self.colab_url or "placeholder" in self.colab_url:
                    raise
                logger.warning("Intentando fallback a worker HTTP remoto tras fallo local...")

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

    def generar_embedding_imagen(
        self,
        image_path: Union[str, Image.Image],
        prompt: str = "consulta_visual",
    ) -> List[float]:
        """
        Vectoriza una imagen real usando inferencia local MLX o HTTP Colab.
        Retorna vector de 2048 dimensiones.
        """
        if self.use_local:
            try:
                return self._generar_embedding_imagen_local(image_path, prompt=prompt)
            except Exception as e:
                logger.error("Error en inferencia local MLX para imagen: %s", e)
                if not self.colab_url or "placeholder" in self.colab_url:
                    raise
                logger.warning("Intentando fallback a worker HTTP remoto tras fallo local...")

        # Validar worker remoto antes de procesar archivos
        self._base_url()

        if isinstance(image_path, Image.Image):
            import io
            buf = io.BytesIO()
            image_path.save(buf, format="JPEG")
            img_bytes = buf.getvalue()
            filename = "image.jpg"
            mime_type = "image/jpeg"
        else:
            if not os.path.isfile(image_path):
                raise FileNotFoundError(f"No existe la imagen para vectorizar: {image_path}")
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
            with open(image_path, "rb") as f:
                img_bytes = f.read()

        endpoint = f"{self._base_url()}/embed_images"
        label = prompt or "consulta_visual"

        response = requests.post(
            endpoint,
            data={
                "labels": label,
                "texts_json": json.dumps([label], ensure_ascii=False),
            },
            files={
                "files": (
                    filename,
                    img_bytes,
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

    def generar_embedding(
        self,
        image_path: Union[str, Image.Image],
        prompt: str = "consulta_visual",
    ) -> List[float]:
        """Delegación segura a generar_embedding_imagen para compatibilidad de firma."""
        return self.generar_embedding_imagen(image_path, prompt=prompt)

    def generar_embeddings_texto_lote(self, textos: List[str]) -> List[List[float]]:
        """Vectoriza una lista de fragmentos de texto."""
        if self.use_local:
            return self._generar_embeddings_texto_lote_local(textos)
        return [self.generar_embedding_texto(t) for t in textos]
