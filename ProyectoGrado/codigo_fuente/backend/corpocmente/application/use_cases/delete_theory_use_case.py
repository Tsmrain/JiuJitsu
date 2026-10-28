import logging
from typing import Dict
from fastapi import HTTPException
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter

logger = logging.getLogger(__name__)


class DeleteTheoryUseCase:
    """
    Caso de Uso: Eliminar toda la teoría que un profesor subió para una técnica.

    Orquesta:
    1. Obtener los qdrant_point_ids asociados (vía RPC que hace SELECT + DELETE en Postgres).
    2. Borrar los puntos correspondientes en Qdrant.
    """

    def __init__(self):
        self.db = PostgrestClient()
        self.qdrant_rag = QdrantRAGAdapter()

    def execute(self, tecnica_id: str, profesor_id: str) -> Dict:
        logger.info(f"Eliminando teoría de técnica {tecnica_id} para profesor {profesor_id}")

        try:
            result = self.db.rpc("admin_delete_teoria_by_tecnica_profesor", {
                "p_tecnica_id": tecnica_id,
                "p_profesor_id": profesor_id,
            })
        except Exception as e:
            logger.error(f"Error eliminando metadata en Postgres: {e}")
            raise HTTPException(status_code=500, detail=f"Error eliminando teoría en Postgres: {str(e)}")

        # PostgREST devuelve [{"deleted_qdrant_ids": [...]}] o similar
        deleted_ids = []
        if result:
            if isinstance(result, list) and result:
                deleted_ids = result[0].get("deleted_qdrant_ids") or []
            elif isinstance(result, dict):
                deleted_ids = result.get("deleted_qdrant_ids") or []

        # Borrar en Qdrant (best-effort: si falla, loggeamos pero no rompemos la respuesta)
        qdrant_deleted = 0
        if deleted_ids:
            try:
                qdrant_deleted = self.qdrant_rag.eliminar_puntos(deleted_ids)
            except Exception as e:
                logger.error(f"Postgres OK pero falló borrado en Qdrant: {e}")

        return {
            "chunks_eliminados_postgres": len(deleted_ids),
            "chunks_eliminados_qdrant": qdrant_deleted,
        }
