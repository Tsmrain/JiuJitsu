import time
import uuid
from typing import Any, List, Optional, Union
import psycopg2

from src.services.chunker_semantico import ChunkerSemanticoBJJ
from src.infrastructure.adapters.qwen_embedding_adapter import QwenEmbeddingAdapter
from src.infrastructure.adapters.qdrant_adapter import QdrantAdapter

# Constantes formales de configuración RAG
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200
EMBEDDING_MODEL: str = "Qwen3-VL-Embedding-2B"
EMBEDDING_DIM: int = 2048


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



class PipelineIngestaRAG:
    """Pipeline orquestador para ingesta, fragmentación semántica y persistencia en Qdrant + PostgreSQL.

    Integra ChunkerSemanticoBJJ con QwenEmbeddingAdapter (2048d) y QdrantAdapter para almacenamiento
    vectorial y búsqueda semántica, manteniendo metadatos en PostgreSQL bajo Mannino BCNF.
    """

    def __init__(
        self,
        db_connection: Union[Any, str],
        embedding_service: Optional[Any] = None,
        chunker: Optional[ChunkerSemanticoBJJ] = None,
        qdrant_adapter: Optional[Any] = None,
    ):
        self._db = db_connection
        self._embedding = embedding_service if embedding_service is not None else QwenEmbeddingAdapter()
        self._chunker = chunker if chunker is not None else ChunkerSemanticoBJJ(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        if qdrant_adapter is not None:
            self._qdrant = qdrant_adapter
        else:
            try:
                self._qdrant = QdrantAdapter()
            except Exception:
                self._qdrant = None

    def indexar_manual(
        self,
        id_tecnica: Optional[str] = None,
        titulo: str = "",
        texto_completo: str = "",
        tipo_recurso: str = "Manual",
        max_retries: int = 3,
        id_instructor: Optional[str] = None,
    ) -> List[str]:
        """Fragmenta texto con ChunkerSemanticoBJJ y persiste chunks con embedding de 2048d en Qdrant y metadatos en PostgreSQL."""
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
        id_documento = f"doc_{uuid.uuid4().hex[:12]}"
        prefix = id_tecnica if id_tecnica else "fuente"
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                for idx, (chunk, vector) in enumerate(zip(chunks, vectores)):
                    if len(vector) != EMBEDDING_DIM:
                        raise ValueError(f"Dimensión incorrecta del embedding: {len(vector)} != {EMBEDDING_DIM}")

                    id_fuente = f"{prefix}_chk_{uuid.uuid4().hex[:8]}"
                    titulo_chunk = f"{titulo} [Parte {idx + 1}]"

                    if id_instructor:
                        cur.execute(
                            """
                            INSERT INTO instructores (id_instructor, nombre_completo)
                            VALUES (%s, %s)
                            ON CONFLICT (id_instructor) DO NOTHING;
                            """,
                            (id_instructor, id_instructor)
                        )

                    cur.execute(
                        """
                        INSERT INTO fuentes_conocimiento (id_fuente, id_documento, id_tecnica, id_instructor, titulo, tipo_recurso, chunk_texto)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id_fuente) DO UPDATE
                        SET id_documento = EXCLUDED.id_documento,
                            id_tecnica = EXCLUDED.id_tecnica,
                            id_instructor = EXCLUDED.id_instructor,
                            titulo = EXCLUDED.titulo,
                            tipo_recurso = EXCLUDED.tipo_recurso,
                            chunk_texto = EXCLUDED.chunk_texto;
                        """,
                        (id_fuente, id_documento, id_tecnica, id_instructor, titulo_chunk, tipo_recurso, chunk),
                    )

                    if self._qdrant is not None:
                        self._qdrant.upsert(
                            id_fuente=id_fuente,
                            vector=vector,
                            payload={
                                "id_fuente": id_fuente,
                                "id_documento": id_documento,
                                "id_tecnica": id_tecnica or "",
                                "id_instructor": id_instructor or "",
                                "titulo": titulo_chunk,
                                "documento_titulo": titulo,
                                "tipo_recurso": tipo_recurso,
                                "chunk_texto": chunk,
                            },
                        )

                    ids_generados.append(id_fuente)
            conn.commit()

        return ids_generados

