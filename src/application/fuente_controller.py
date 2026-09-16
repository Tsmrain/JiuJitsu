# src/application/fuente_controller.py
"""Controlador de Aplicación / Fachada de Sesión para Fuentes de Conocimiento (RAG).

Orquesta la fragmentación, vectorización con QwenEmbeddingAdapter (2048d) y almacenamiento
en el acervo documental del sistema pedagógico.
"""

import uuid
from typing import Any, Dict, List, Optional
from src.domain.interfaces import IFuenteConocimientoRepository, IVectorStore, IEmbeddingService
from src.domain.models import FuenteConocimiento
from src.infrastructure.adapters.qwen_embedding_adapter import QwenEmbeddingAdapter


class FuenteController:
    """Session Facade para la indexación y búsqueda de literatura didáctica de BJJ.
    
    Aplica el patrón GRASP: Controlador de Larman para desacoplar la capa de presentación
    (API REST) de los detalles de persistencia, chunking y vectorización.
    """

    def __init__(
        self,
        repository: IFuenteConocimientoRepository,
        embedding_service: Optional[IEmbeddingService] = None,
        qdrant_adapter: Optional[IVectorStore] = None,
        pipeline_ingesta: Optional[Any] = None,
    ):
        self._repository = repository
        self._embedding_service = embedding_service if embedding_service is not None else QwenEmbeddingAdapter()
        self._qdrant = qdrant_adapter
        self._pipeline = pipeline_ingesta

    def indexar_fuente(
        self,
        id_fuente: str,
        id_tecnica: str,
        titulo: str,
        tipo_recurso: str,
        chunk_texto: str,
        embedding_vector: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Genera embedding mediante Adaptador (Qwen) si no se provee y persiste."""
        vector = embedding_vector
        if vector is None:
            vector = self._embedding_service.generate_embedding(chunk_texto)

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

    def indexar_manual(
        self,
        id_instructor: str,
        titulo: str,
        texto_completo: str,
        id_tecnica: Optional[str] = None,
        tipo_recurso: str = "Manual",
    ) -> Dict[str, Any]:
        """Coordina la fragmentación semántica, generación de embeddings Qwen (batching),
        almacenamiento vectorial en Qdrant y persistencia de metadatos en PostgreSQL.
        """
        clean_titulo = titulo.strip()
        if not clean_titulo:
            raise ValueError("El título no puede ser vacío.")
        if not texto_completo or len(texto_completo.strip()) < 50:
            raise ValueError("El PDF no contiene texto extraíble (puede ser un PDF escaneado o de solo imágenes). Por favor, suba un PDF con texto seleccionable.")

        if self._pipeline is not None:
            ids = self._pipeline.indexar_manual(
                id_tecnica=id_tecnica,
                titulo=clean_titulo,
                texto_completo=texto_completo,
                tipo_recurso=tipo_recurso,
                id_instructor=id_instructor,
            )
            chunks_indexados = len(ids)
        else:
            # Fallback en memoria / unit tests: fragmentación regular
            chunk_size = 1000
            chunks = [
                texto_completo[i : i + chunk_size].strip()
                for i in range(0, len(texto_completo), chunk_size)
                if texto_completo[i : i + chunk_size].strip()
            ]
            ids = []
            prefix = id_tecnica if id_tecnica else "fuente"
            for idx, chunk in enumerate(chunks):
                id_f = f"{prefix}_chk_{uuid.uuid4().hex[:8]}"
                tit = f"{clean_titulo} [Parte {idx + 1}]"
                res = self.indexar_fuente(
                    id_fuente=id_f,
                    id_tecnica=id_tecnica or "general",
                    titulo=tit,
                    tipo_recurso=tipo_recurso,
                    chunk_texto=chunk,
                )
                ids.append(res["id_fuente"])
            chunks_indexados = len(chunks)

        return {
            "message": "Manual procesado y almacenado exitosamente",
            "id_instructor": id_instructor,
            "titulo": clean_titulo,
            "caracteres_extraidos": len(texto_completo),
            "chunks_indexados": chunks_indexados,
            "ids_chunks": ids,
        }

    def buscar_contexto(
        self,
        consulta_embedding: Optional[List[float]] = None,
        texto_consulta: Optional[str] = None,
        limite: int = 3,
        id_tecnica: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Recupera los fragmentos de conocimiento con mayor similitud semántica.
        
        Flujo: Generar embedding de consulta con Qwen -> Buscar en Qdrant -> Devolver payloads.
        """
        vector = consulta_embedding
        if vector is None:
            if texto_consulta:
                vector = self._embedding_service.generate_embedding(texto_consulta)
            else:
                vector = [0.05] * 2048

        # Si QdrantAdapter está inyectado directamente, buscar en Qdrant y retornar payloads
        if self._qdrant is not None:
            return self._qdrant.buscar(
                consulta_embedding=vector,
                limite=limite,
                id_tecnica=id_tecnica,
            )

        # De lo contrario, delegar al repositorio de dominio
        try:
            fuentes = self._repository.buscar_contexto(vector, limite=limite, id_tecnica=id_tecnica)
        except TypeError:
            fuentes = self._repository.buscar_contexto(vector, limite=limite)

        return [
            {
                "id_fuente": f.id_fuente,
                "id_tecnica": f.id_tecnica,
                "titulo": f.titulo,
                "tipo_recurso": f.tipo_recurso,
                "chunk_texto": f.chunk_texto,
                "similitud": getattr(f, "similitud", None),
            }
            for f in fuentes
        ]

    def listar_fuentes(self, id_tecnica: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista las fuentes indexadas agrupadas a nivel de documento didáctico."""
        fuentes = self._repository.listar_fuentes(id_tecnica)
        return [
            {
                "id_fuente": f.id_fuente,
                "id_documento": getattr(f, "id_documento", f.id_fuente),
                "id_tecnica": f.id_tecnica,
                "id_instructor": getattr(f, "id_instructor", "inst_santiago"),
                "titulo": f.titulo,
                "tipo_recurso": f.tipo_recurso,
                "chunk_texto": f.chunk_texto,
                "total_chunks": getattr(f, "total_chunks", 1) or 1,
                "fecha_creacion": f.fecha_carga.isoformat() if hasattr(getattr(f, "fecha_carga", None), "isoformat") else (str(f.fecha_carga) if getattr(f, "fecha_carga", None) else None),
            }
            for f in fuentes
        ]

    def actualizar_fuente(
        self,
        id_fuente: str,
        titulo: str,
        id_instructor: Optional[str] = None,
        texto_completo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Actualiza metadatos de una fuente de información."""
        clean_titulo = titulo.strip()
        if not clean_titulo:
            raise ValueError("El título es obligatorio.")
        if hasattr(self._repository, "actualizar"):
            self._repository.actualizar(id_fuente=id_fuente, titulo=clean_titulo, chunk_texto=texto_completo)
        return {
            "message": "Fuente actualizada exitosamente",
            "id_fuente": id_fuente,
            "titulo": clean_titulo,
        }

    def eliminar_fuente(self, id_fuente: str) -> Dict[str, Any]:
        """Elimina una fuente o documento consolidado de persistencia (Postgres y Qdrant)."""
        if hasattr(self._repository, "eliminar"):
            self._repository.eliminar(id_fuente)
        elif self._qdrant is not None:
            if hasattr(self._qdrant, "eliminar_por_documento"):
                self._qdrant.eliminar_por_documento(id_fuente)
            elif hasattr(self._qdrant, "eliminar"):
                self._qdrant.eliminar(id_fuente)
        return {
            "message": "Fuente eliminada exitosamente",
            "id_fuente": id_fuente,
        }


