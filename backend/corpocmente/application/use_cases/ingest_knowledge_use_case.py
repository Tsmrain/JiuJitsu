import logging
import requests
from typing import Optional, Callable
from fastapi import HTTPException
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.application.dtos.knowledge_dtos import IngestionResponse
from corpocmente.config import settings

logger = logging.getLogger(__name__)


NGROK_HEADERS = {
    "ngrok-skip-browser-warning": "1",
    "User-Agent": "CorpocmenteBackend/1.0",
}


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
        tecnica_id: Optional[str],
        contenido_texto: str,
        profesor_id: str = None,
        sucursal_id: str = None,
        fuente_tipo: str = "manual",
        fuente_nombre: str = None,
        fuente_referencia: str = None,
        fuente_url: str = None,
        alcance: str = "tecnica",
        embedding_data: Optional[dict] = None,
        metadata_por_chunk: Optional[list[dict]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> IngestionResponse:
        logger.info(f"Iniciando ingestión RAG para técnica {tecnica_id}")

        if embedding_data is None and (not self.worker_url or "placeholder" in self.worker_url):
            raise HTTPException(status_code=503, detail="COLAB_TUNNEL_URL no configurada.")

        try:
            if embedding_data is None:
                response = requests.post(
                    f"{self.worker_url.rstrip('/')}/embed_text",
                    data={"texto": contenido_texto},
                    headers=NGROK_HEADERS,
                    timeout=120
                )
                response.raise_for_status()
                embed_data = response.json()
            else:
                embed_data = embedding_data

            # 1. Persistir en Qdrant
            qdrant_result = self.qdrant_rag.ingestar_desde_respuesta(
                embed_data,
                tecnica_id,
                fuente_tipo=fuente_tipo,
                fuente_nombre=fuente_nombre,
                fuente_referencia=fuente_referencia,
                fuente_url=fuente_url,
                alcance=alcance,
                metadata_por_chunk=metadata_por_chunk,
            )
            point_ids = qdrant_result["point_ids"]
            chunks = qdrant_result["chunks"]

            # 2. Persistir metadata en PostgreSQL (si tenemos profesor/sucursal)
            if profesor_id and (sucursal_id or alcance == "global"):
                for i, (chunk, pid) in enumerate(zip(chunks, point_ids)):
                    try:
                        self.db.rpc("admin_save_teoria_chunk", {
                            "p_tecnica_id": tecnica_id,
                            "p_profesor_id": profesor_id,
                            "p_sucursal_id": sucursal_id,
                            "p_chunk_index": i,
                            "p_contenido_texto": chunk,
                            "p_qdrant_point_id": pid,
                            "p_fuente_tipo": fuente_tipo,
                            "p_fuente_nombre": fuente_nombre,
                            "p_fuente_referencia": fuente_referencia,
                            "p_fuente_url": fuente_url,
                            "p_alcance": alcance,
                        })
                    except Exception as e:
                        # Fallback resiliente ante bases de datos antiguas con restricción CHECK estrecha
                        if fuente_tipo not in ("manual", "video", "articulo"):
                            try:
                                self.db.rpc("admin_save_teoria_chunk", {
                                    "p_tecnica_id": tecnica_id,
                                    "p_profesor_id": profesor_id,
                                    "p_sucursal_id": sucursal_id,
                                    "p_chunk_index": i,
                                    "p_contenido_texto": chunk,
                                    "p_qdrant_point_id": pid,
                                    "p_fuente_tipo": "manual",
                                    "p_fuente_nombre": fuente_nombre,
                                    "p_fuente_referencia": fuente_referencia,
                                    "p_fuente_url": fuente_url,
                                    "p_alcance": alcance,
                                })
                                continue
                            except Exception:
                                pass
                        logger.warning(f"No se pudo registrar chunk {i} en Postgres: {e}")
                    finally:
                        if progress_callback:
                            progress_callback(i + 1, len(chunks))

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
