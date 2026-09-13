# src/application/fuente_controller.py
"""Controlador de Aplicación / Fachada de Sesión para Fuentes de Conocimiento (RAG).

Orquesta la fragmentación, vectorización con AdaptadorGemini y almacenamiento
en el acervo documental del sistema pedagógico.
"""

from typing import Any, Dict, List, Optional
from src.domain.interfaces import IFuenteConocimientoRepository
from src.domain.models import FuenteConocimiento
from src.services.adapters import AdaptadorGemini


class FuenteController:
    """Session Facade para la indexación y búsqueda de literatura didáctica de BJJ."""

    def __init__(
        self,
        repository: IFuenteConocimientoRepository,
        gemini_adapter: Optional[AdaptadorGemini] = None,
    ):
        self._repository = repository
        self._gemini = gemini_adapter if gemini_adapter is not None else AdaptadorGemini()

    def indexar_fuente(
        self,
        id_fuente: str,
        id_tecnica: str,
        titulo: str,
        tipo_recurso: str,
        chunk_texto: str,
        embedding_vector: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Genera embedding mediante AdaptadorGemini si no se provee y persiste."""
        vector = embedding_vector
        if vector is None:
            vector = self._gemini.generar_embedding(chunk_texto)

        fuente = FuenteConocimiento(
            id_fuente=id_fuente,
            id_tecnica=id_tecnica,
            titulo=titulo,
            tipo_recurso=tipo_recurso,
            chunk_texto=chunk_texto,
            embedding_vector=vector,
        )

        id_generado = self._repository.indexar_documento(fuente)
        return {
            "id_fuente": id_generado,
            "id_tecnica": fuente.id_tecnica,
            "titulo": fuente.titulo,
            "tipo_recurso": fuente.tipo_recurso,
            "dimension_embedding": len(vector),
            "longitud_chunk": len(fuente.chunk_texto),
        }

    def buscar_contexto(self, consulta_embedding: List[float], limite: int = 3) -> List[Dict[str, Any]]:
        """Recupera los fragmentos de conocimiento con mayor similitud semántica."""
        fuentes = self._repository.buscar_contexto(consulta_embedding, limite=limite)
        return [
            {
                "id_fuente": f.id_fuente,
                "id_tecnica": f.id_tecnica,
                "titulo": f.titulo,
                "tipo_recurso": f.tipo_recurso,
                "chunk_texto": f.chunk_texto,
            }
            for f in fuentes
        ]

    def listar_fuentes(self, id_tecnica: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista las fuentes indexadas, opcionalmente filtradas por técnica."""
        fuentes = self._repository.listar_fuentes(id_tecnica)
        return [
            {
                "id_fuente": f.id_fuente,
                "id_tecnica": f.id_tecnica,
                "titulo": f.titulo,
                "tipo_recurso": f.tipo_recurso,
                "chunk_texto": f.chunk_texto,
            }
            for f in fuentes
        ]
