# src/infrastructure/rag_ingestion.py
"""Módulo de Ingesta y Fragmentación Semántica para Sistema RAG.

Diseñado bajo el Proceso Unificado (Larman). Define las especificaciones formales
de chunking (1000 caracteres, 200 de solapamiento) y dimensionamiento vectorial
(768 floats para gemini-embedding-2).
"""

from typing import List, Optional
import psycopg2
from src.infrastructure.gemini_adapter import GeminiServiceAdapter

# Constantes formales de configuración RAG
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200
EMBEDDING_MODEL: str = "gemini-embedding-2"
EMBEDDING_DIM: str = 768


class IngestorRAGStub:
    """Stub tipado preparatorio para el subsistema RAG de la fase de Construcción.

    Define el contrato de fragmentación con ventana deslizante y solapamiento
    para preservar la coherencia contextual biomecánica en documentos extensos.
    """

    def __init__(self, tamano_chunk: int = CHUNK_SIZE, solapamiento: int = CHUNK_OVERLAP):
        self.tamano_chunk = tamano_chunk
        self.solapamiento = solapamiento

    def fragmentar_texto(
        self,
        texto: str,
        tamano_chunk: int = 1000,
        solapamiento: int = 200,
    ) -> List[str]:
        """Divide un texto continuo en fragmentos discretos con solapamiento controlado.

        Args:
            texto: Cadena de texto bruto correspondiente a manuales técnicos de BJJ.
            tamano_chunk: Longitud máxima en caracteres de cada fragmento (por defecto 1000).
            solapamiento: Cantidad de caracteres compartidos entre fragmentos adyacentes (por defecto 200).

        Returns:
            Lista de fragmentos de texto válidos y no vacíos.
        """
        if not texto or not texto.strip():
            return []

        paso = max(1, tamano_chunk - solapamiento)
        chunks: List[str] = []
        i = 0
        while i < len(texto):
            chunk = texto[i : i + tamano_chunk].strip()
            if chunk:
                chunks.append(chunk)
            i += paso

        return chunks


class IngestorRAG:
    """Servicio legacy para fragmentar e indexar manuales de Jiu-Jitsu en pgvector."""

    def __init__(self, db_url: str, gemini_adapter: GeminiServiceAdapter):
        self._db_url = db_url
        self._gemini = gemini_adapter

    def indexar_documento(self, titulo: str, texto_completo: str, tamano_chunk: int = 500) -> int:
        """Fragmenta un texto completo, genera sus embeddings e inserta en recursos_didacticos."""
        # 1. Fragmentación simple
        chunks = [texto_completo[i : i + tamano_chunk] for i in range(0, len(texto_completo), tamano_chunk)]

        insertados = 0
        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                for chunk in chunks:
                    if not chunk.strip():
                        continue
                    # 2. Generar vector denso
                    vector = self._gemini.generate_embedding(chunk)

                    # 3. Insertar en pgvector
                    cur.execute(
                        """
                        INSERT INTO recursos_didacticos (titulo, contenido_texto, embedding)
                        VALUES (%s, %s, %s::vector);
                        """,
                        (titulo, chunk, vector),
                    )
                    insertados += 1
            conn.commit()
        return insertados
