import time
import uuid
from typing import Any, List, Optional, Union
import psycopg2

from src.services.chunker_semantico import ChunkerSemanticoBJJ
from src.infrastructure.adapters.gemini_embedding_adapter import GeminiEmbedding2Adapter

# Constantes formales de configuración RAG
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200
EMBEDDING_MODEL: str = "gemini-embedding-2"
EMBEDDING_DIM: int = 768


class _DBContext:
    """Administrador de contexto para conexiones a PostgreSQL (acepta conexión, cursor mock o URL)."""

    def __init__(self, db: Union[Any, str]):
        self.db = db
        self._owned = False
        self.conn = None

    def __enter__(self):
        if isinstance(self.db, str):
            self.conn = psycopg2.connect(self.db)
            self._owned = True
            if hasattr(self.conn, "__enter__"):
                return self.conn.__enter__()
            return self.conn
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._owned and self.conn:
            if hasattr(self.conn, "__exit__"):
                self.conn.__exit__(exc_type, exc_val, exc_tb)
            else:
                if exc_type is None and hasattr(self.conn, "commit"):
                    self.conn.commit()
                if hasattr(self.conn, "close"):
                    self.conn.close()


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
    """Servicio de ingesta compatible y adaptado para fragmentar e indexar manuales de Jiu-Jitsu en pgvector."""

    def __init__(self, db_url: Union[str, Any], gemini_adapter: Optional[Any] = None):
        self._db_url = db_url
        self._gemini = gemini_adapter if gemini_adapter is not None else GeminiEmbedding2Adapter()
        self._chunker = ChunkerSemanticoBJJ(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    def indexar_documento(self, titulo: str, texto_completo: str, tamano_chunk: int = 500) -> int:
        """Fragmenta un texto completo, genera sus embeddings e inserta en recursos_didacticos (legacy)."""
        chunks = [texto_completo[i : i + tamano_chunk] for i in range(0, len(texto_completo), tamano_chunk)]

        insertados = 0
        with _DBContext(self._db_url) as conn:
            with conn.cursor() as cur:
                for chunk in chunks:
                    if not chunk.strip():
                        continue
                    # Generar vector denso (soporta generate_embedding o generar_embedding)
                    if hasattr(self._gemini, "generate_embedding"):
                        vector = self._gemini.generate_embedding(chunk)
                    else:
                        vector = self._gemini.generar_embedding(chunk)

                    cur.execute(
                        """
                        INSERT INTO recursos_didacticos (titulo, contenido_texto, embedding)
                        VALUES (%s, %s, %s::vector);
                        """,
                        (titulo, chunk, vector),
                    )
                    insertados += 1
        return insertados


class PipelineIngestaRAG:
    """Pipeline orquestador para ingesta, fragmentación semántica y persistencia en pgvector.

    Integra ChunkerSemanticoBJJ (RecursiveCharacterTextSplitter) con GeminiEmbedding2Adapter
    manejando reintentos exponenciales ante saturación de cuota HTTP 429.
    """

    def __init__(
        self,
        db_connection: Union[Any, str],
        embedding_service: Optional[Any] = None,
        chunker: Optional[ChunkerSemanticoBJJ] = None,
    ):
        self._db = db_connection
        self._embedding = embedding_service if embedding_service is not None else GeminiEmbedding2Adapter()
        self._chunker = chunker if chunker is not None else ChunkerSemanticoBJJ(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    def indexar_manual(
        self,
        id_tecnica: str,
        titulo: str,
        texto_completo: str,
        tipo_recurso: str = "Manual",
        max_retries: int = 3,
    ) -> List[str]:
        """Fragmenta texto con ChunkerSemanticoBJJ y persiste chunks con embedding_vector de 768d."""
        chunks = self._chunker.fragmentar(texto_completo)
        if not chunks:
            return []

        # Generar embeddings usando batch con retry si el adaptador lo expone
        if hasattr(self._embedding, "generar_embeddings_batch"):
            vectores = self._embedding.generar_embeddings_batch(chunks, max_retries=max_retries)
        else:
            vectores = []
            for chunk in chunks:
                for intento in range(max_retries):
                    try:
                        if hasattr(self._embedding, "generar_embedding"):
                            vec = self._embedding.generar_embedding(chunk)
                        else:
                            vec = self._embedding.generate_embedding(chunk)
                        vectores.append(vec)
                        break
                    except Exception as e:
                        if "429" in str(e) and intento < max_retries - 1:
                            time.sleep(1.0 * (2**intento))
                        else:
                            raise

        ids_generados: List[str] = []
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                for idx, (chunk, vector) in enumerate(zip(chunks, vectores)):
                    if len(vector) != EMBEDDING_DIM:
                        raise ValueError(f"Dimensión incorrecta del embedding: {len(vector)} != {EMBEDDING_DIM}")

                    id_fuente = f"{id_tecnica}_chk_{uuid.uuid4().hex[:8]}"
                    cur.execute(
                        """
                        INSERT INTO fuentes_conocimiento (id_fuente, id_tecnica, titulo, tipo_recurso, embedding_vector, chunk_texto)
                        VALUES (%s, %s, %s, %s, %s::vector, %s)
                        ON CONFLICT (id_fuente) DO UPDATE
                        SET chunk_texto = EXCLUDED.chunk_texto,
                            embedding_vector = EXCLUDED.embedding_vector;
                        """,
                        (id_fuente, id_tecnica, f"{titulo} [Parte {idx + 1}]", tipo_recurso, vector, chunk),
                    )
                    ids_generados.append(id_fuente)

        return ids_generados
