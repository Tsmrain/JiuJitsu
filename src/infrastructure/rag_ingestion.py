# src/infrastructure/rag_ingestion.py
import psycopg2
from typing import List, Optional
from src.infrastructure.gemini_adapter import GeminiServiceAdapter

class IngestorRAG:
    """Servicio para fragmentar e indexar manuales de Jiu-Jitsu en pgvector."""
    
    def __init__(self, db_url: str, gemini_adapter: GeminiServiceAdapter):
        self._db_url = db_url
        self._gemini = gemini_adapter

    def indexar_documento(self, titulo: str, texto_completo: str, tamano_chunk: int = 500) -> int:
        """Fragmenta un texto completo, genera sus embeddings e inserta en recursos_didacticos."""
        # 1. Fragmentación simple
        chunks = [texto_completo[i:i+tamano_chunk] for i in range(0, len(texto_completo), tamano_chunk)]
        
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
                        (titulo, chunk, vector)
                    )
                    insertados += 1
            conn.commit()
        return insertados
