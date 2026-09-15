# src/infrastructure/adapters/qwen_embedding_adapter.py
"""Adaptador de infraestructura para Qwen3-VL-Embedding-2B (Google Colab Remoto / Fallback Local).

Implementa IEmbeddingService para vectorización multimodal y textual de 2048 dimensiones.
Aplica Variaciones Protegidas (Larman):
Prioridad 1: Endpoint HTTP remoto en Google Colab con aceleración GPU T4 (/embed).
Prioridad 2: Modelo local con PyTorch/SentenceTransformer (si GPU local o configurada).
Prioridad 3: Fallback determinista seguro para tests y CI sin hardware activo.
"""

import os
from typing import List, Optional
import requests

from src.domain.interfaces import IEmbeddingService


class QwenEmbeddingAdapter(IEmbeddingService):
    """Adaptador de infraestructura para Qwen3-VL-Embedding-2B en GPU Colab remota o local."""

    def __init__(self, api_key: Optional[str] = None):
        self._dim = 2048
        self._client = None
        # Prioridad: Colab Remoto > GPU Local > CPU Fallback
        self.colab_url = os.getenv("COLAB_TUNNEL_URL", "").strip()

        if not self.colab_url or self.colab_url.startswith("https://placeholder"):
            try:
                from sentence_transformers import SentenceTransformer
                import torch
                self.device = "cuda" if os.getenv("USE_GPU", "true").lower() == "true" else "cpu"
                
                # Optimizado con bfloat16 (Flash Attention removido para compatibilidad)
                model_kwargs = {"torch_dtype": torch.bfloat16}
                
                self._client = SentenceTransformer(
                    "Qwen/Qwen3-VL-Embedding-2B", 
                    device=self.device, 
                    trust_remote_code=True,
                    model_kwargs=model_kwargs
                )
            except Exception:
                self._client = None

    def generar_embedding(self, texto: str) -> List[float]:
        """Genera embedding de 2048 dimensiones para un texto individual."""
        if self.colab_url and not self.colab_url.startswith("https://placeholder"):
            resultado = self._llamar_colab_remoto([texto])
            if resultado and len(resultado) > 0:
                return resultado[0]

        if not self._client:
            return [0.05] * self._dim

        return self._client.encode(texto, normalize_embeddings=True).tolist()

    def generate_embedding(self, text: str) -> List[float]:
        """Implementación estricta del contrato IEmbeddingService."""
        return self.generar_embedding(text)

    def generar_embeddings_batch(
        self, textos: List[str], max_retries: int = 3, backoff_base: float = 1.0
    ) -> List[List[float]]:
        """Genera lote de embeddings de 2048 dimensiones."""
        if not textos:
            return []

        if self.colab_url and not self.colab_url.startswith("https://placeholder"):
            return self._llamar_colab_remoto(textos)

        if not self._client:
            return [[0.05] * self._dim for _ in textos]

        return self._client.encode(textos, normalize_embeddings=True).tolist()

    def _llamar_colab_remoto(self, textos: List[str]) -> List[List[float]]:
        """Invoca el endpoint /embed de Colab usando micro-batching para evitar OOM."""
        endpoint = f"{self.colab_url.rstrip('/')}/embed"
        resultados = []
        
        # Tamaño de micro-lote seguro para GPU L4 (24GB) o T4
        MICRO_BATCH_SIZE = 32

        try:
            for i in range(0, len(textos), MICRO_BATCH_SIZE):
                micro_lote = textos[i : i + MICRO_BATCH_SIZE]
                resp = requests.post(endpoint, json={"textos": micro_lote}, timeout=180)
                resp.raise_for_status()
                data = resp.json()
                vectores = data.get("embeddings", [])
                
                if vectores and all(len(v) == self._dim for v in vectores):
                    resultados.extend(vectores)
                else:
                    print(f"[WARN COLAB EMBEDDINGS] Dimensiones no esperadas en micro-lote {i//MICRO_BATCH_SIZE}")
                    resultados.extend([[0.05] * self._dim for _ in micro_lote])
            return resultados
        except Exception as e:
            print(f"[ERROR COLAB EMBEDDINGS] {e}")
            faltantes = len(textos) - len(resultados)
            if faltantes > 0:
                resultados.extend([[0.05] * self._dim for _ in range(faltantes)])
            return resultados
