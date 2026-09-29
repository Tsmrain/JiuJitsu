import logging
from typing import List, Dict
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient

logger = logging.getLogger(__name__)


class ListTheoryUseCase:
    """
    Caso de Uso: Listar chunks de teoría de una técnica.

    El profesor usa esto para ver qué subió. Devuelve metadata + preview del texto.
    """

    def __init__(self):
        self.db = PostgrestClient()

    def execute(self, tecnica_id: str, profesor_id: str = None) -> List[Dict]:
        """
        Lista chunks de teoría de una técnica.
        Si profesor_id viene, filtra solo los del profesor (vista "mis aportes").
        Si no, devuelve todos los aportes de la técnica (vista "material de la técnica").
        """
        logger.info(f"Listando teoría para técnica {tecnica_id} (filtro profesor: {profesor_id})")

        try:
            chunks = self.db.rpc("admin_list_teoria_by_tecnica", {
                "p_tecnica_id": tecnica_id
            })
        except Exception as e:
            logger.error(f"Error consultando teoría en Postgres: {e}")
            return []

        if not chunks:
            return []

        if profesor_id:
            chunks = [c for c in chunks if str(c.get("profesor_id")) == str(profesor_id)]

        return chunks
