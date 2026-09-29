import logging
import requests
from fastapi import HTTPException
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.application.dtos.knowledge_dtos import IngestionResponse
from corpocmente.config import settings

logger = logging.getLogger(__name__)


class IngestKnowledgeUseCase:
    """
    Caso de Uso: Ingestión de material teórico (libros/manuales) al sistema RAG.

    Orquesta:
    1. Delegar la vectorización al Worker de Colab (Qwen3-VL-Embedding-2B).
    2. Persistir los chunks en Qdrant (búsqueda vectorial).
    3. Persistir la metadata de cada chunk en PostgreSQL (trazabilidad + CRUD).
    """

    def __init__(self, qdrant_rag_adapter: QdrantRAGAdapter = None):
        self.qdrant_rag = qdrant_rag_adapter or QdrantRAGAdapter()
        self.worker_url = settings.COLAB_TUNNEL_URL
        self.db = PostgrestClient()

    def execute(
        self,
        tecnica_id: str,
        contenido_texto: str,
        profesor_id: str = None,
        sucursal_id: str = None,
    ) -> IngestionResponse:
        logger.info(f"Iniciando ingestión RAG para técnica {tecnica_id}")

        if not self.worker_url or "placeholder" in self.worker_url:
            raise HTTPException(status_code=503, detail="COLAB_TUNNEL_URL no configurada.")

        try:
            response = requests.post(
                f"{self.worker_url.rstrip('/')}/embed_text",
                data={"texto": contenido_texto},
                timeout=120
            )
            response.raise_for_status()
            embed_data = response.json()

            # 1. Persistir en Qdrant
            qdrant_result = self.qdrant_rag.ingestar_desde_respuesta(embed_data, tecnica_id)
            point_ids = qdrant_result["point_ids"]
            chunks = qdrant_result["chunks"]

            # 2. Persistir metadata en PostgreSQL (si tenemos profesor/sucursal)
            if profesor_id and sucursal_id:
                for i, (chunk, pid) in enumerate(zip(chunks, point_ids)):
                    try:
                        self.db.rpc("admin_save_teoria_chunk", {
                            "p_tecnica_id": tecnica_id,
                            "p_profesor_id": profesor_id,
                            "p_sucursal_id": sucursal_id,
                            "p_chunk_index": i,
                            "p_contenido_texto": chunk,
                            "p_qdrant_point_id": pid,
                        })
                    except Exception as e:
                        logger.warning(f"No se pudo registrar chunk {i} en Postgres: {e}")

            return IngestionResponse(
                status="success",
                chunks_procesados=len(chunks)
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error comunicando con Colab: {e}")
            raise HTTPException(status_code=503, detail=f"Worker de Colab no disponible: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en ingestión RAG: {e}")
            raise HTTPException(status_code=500, detail=f"Error interno en ingestión: {str(e)}")
