"""Adaptadores de Infraestructura (Infrastructure Adapters).

Implementaciones concretas de los contratos de dominio:
  - IInferenceEngine  → ColabYOLOAdapter, AdaptadorYOLO
  - IGenerationService → GeminiServiceAdapter, AdaptadorGemini
  - IEmbeddingService  → QwenEmbeddingAdapter
  - IVectorStore       → QdrantAdapter

Aplican el patrón Variaciones Protegidas (Larman, Cap. 17): el núcleo de dominio
y la capa de aplicación son completamente agnósticos al hardware (GPU Colab)
y al proveedor de persistencia vectorial (Qdrant).
"""

from src.infrastructure.adapters.colab_adapter import ColabYOLOAdapter
from src.infrastructure.adapters.gemini_adapter import GeminiServiceAdapter
from src.infrastructure.adapters.yolo_adapter import AdaptadorYOLO
from src.infrastructure.adapters.gemini_service_adapter import AdaptadorGemini
from src.infrastructure.adapters.qwen_embedding_adapter import QwenEmbeddingAdapter
from src.infrastructure.adapters.qdrant_adapter import QdrantAdapter

__all__ = [
    "ColabYOLOAdapter",
    "GeminiServiceAdapter",
    "AdaptadorYOLO",
    "AdaptadorGemini",
    "QwenEmbeddingAdapter",
    "QdrantAdapter",
]

