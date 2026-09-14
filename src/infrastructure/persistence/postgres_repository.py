# src/infrastructure/persistence/postgres_repository.py
"""Adaptadores de Persistencia Relacional en PostgreSQL y pgvector.

Diseñado bajo la Forma Normal de Boyce-Codd (BCNF) según Mannino (7th Ed., Cap. 6-8).
Aplica el principio de Variaciones Protegidas de Craig Larman mediante reutilización
obligatoria de AdaptadorYOLO y AdaptadorGemini.
"""

from typing import Any, Dict, List, Optional, Union
import psycopg2

from src.domain.interfaces import (
    IProfesorRepository,
    ITecnicaRepository,
    IFuenteConocimientoRepository,
)
from src.domain.models import (
    Profesor,
    TecnicaPatron,
    FuenteConocimiento,
    MatrizEsqueletica,
    ConfiguracionRAG,
)
from src.infrastructure.adapters.yolo_adapter import AdaptadorYOLO
from src.infrastructure.adapters.gemini_service_adapter import AdaptadorGemini


class _DBContext:
    """Administrador de contexto para conexiones a PostgreSQL (permite instancia de conexión o URL)."""

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


class PostgresProfesorRepository(IProfesorRepository):
    """Implementación de persistencia para instructores bajo BCNF."""

    def __init__(self, db_connection: Union[Any, str]):
        self._db = db_connection

    def guardar(self, profesor: Profesor) -> None:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO profesores (id_profesor, nombre, email, fecha_registro)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id_profesor) DO UPDATE
                    SET nombre = EXCLUDED.nombre,
                        email = EXCLUDED.email;
                    """,
                    (profesor.id_profesor, profesor.nombre, profesor.email, profesor.fecha_registro),
                )

    def obtener_por_id(self, id_profesor: str) -> Optional[Profesor]:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_profesor, nombre, email, fecha_registro FROM profesores WHERE id_profesor = %s;",
                    (id_profesor,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return Profesor(
                    id_profesor=row[0],
                    nombre=row[1],
                    email=row[2],
                    fecha_registro=row[3],
                )

    def listar_todos(self) -> List[Profesor]:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_profesor, nombre, email, fecha_registro FROM profesores ORDER BY nombre;"
                )
                rows = cur.fetchall()
                return [
                    Profesor(id_profesor=r[0], nombre=r[1], email=r[2], fecha_registro=r[3])
                    for r in rows
                ]

    def eliminar(self, id_profesor: str) -> bool:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM profesores WHERE id_profesor = %s;", (id_profesor,))
                return getattr(cur, "rowcount", 1) > 0

    def actualizar(self, id_profesor: str, nombre: str, email: str) -> bool:
        clean_email = email.strip()
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_profesor FROM profesores WHERE LOWER(email) = LOWER(%s) AND id_profesor != %s;",
                    (clean_email, id_profesor),
                )
                if cur.fetchone():
                    raise ValueError(f"El email '{email}' ya se encuentra registrado.")
                cur.execute(
                    "UPDATE profesores SET nombre = %s, email = %s WHERE id_profesor = %s;",
                    (nombre, clean_email, id_profesor),
                )
                return getattr(cur, "rowcount", 0) > 0


class PostgresTecnicaRepository(ITecnicaRepository):
    """Implementación de persistencia para técnicas patrón con serialización validada en YOLO."""

    def __init__(self, db_connection: Union[Any, str], yolo_adapter: Optional[AdaptadorYOLO] = None):
        self._db = db_connection
        self._yolo = yolo_adapter if yolo_adapter is not None else AdaptadorYOLO()

    def registrar_patron(self, tecnica: TecnicaPatron) -> bool:
        # VALIDAR matriz usando AdaptadorYOLO EXISTENTE antes de persistir
        if not self._yolo.validar_matriz_esqueletica(tecnica.matriz_esqueletica):
            raise ValueError("Matriz esquelética inválida según contrato YOLO26x")

        # Serializar solo después de validar
        matriz_json = self._yolo.serializar_para_db(tecnica.matriz_esqueletica)

        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tecnicas_patron (id_tecnica, id_profesor, nombre, categoria, matriz_esqueletica, video_url, descripcion)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
                    ON CONFLICT (id_tecnica) DO UPDATE
                    SET id_profesor = EXCLUDED.id_profesor,
                        nombre = EXCLUDED.nombre,
                        categoria = EXCLUDED.categoria,
                        matriz_esqueletica = EXCLUDED.matriz_esqueletica,
                        video_url = EXCLUDED.video_url,
                        descripcion = EXCLUDED.descripcion;
                    """,
                    (
                        tecnica.id_tecnica,
                        tecnica.id_profesor,
                        tecnica.nombre,
                        tecnica.categoria,
                        matriz_json,
                        tecnica.video_url,
                        tecnica.descripcion,
                    ),
                )
        return True

    def obtener_patron(self, id_tecnica: str) -> Optional[TecnicaPatron]:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id_tecnica, id_profesor, nombre, categoria, matriz_esqueletica, video_url, descripcion
                    FROM tecnicas_patron WHERE id_tecnica = %s;
                    """,
                    (id_tecnica,),
                )
                row = cur.fetchone()
                if not row or not row[4]:
                    return None

                matriz = self._yolo.deserializar_desde_db(row[4])
                return TecnicaPatron(
                    id_tecnica=row[0],
                    id_profesor=row[1] or "inst_default",
                    nombre=row[2],
                    categoria=row[3] or "General",
                    matriz_esqueletica=matriz,
                    video_url=row[5],
                    descripcion=row[6],
                )

    def listar_por_instructor(self, id_profesor: str) -> List[TecnicaPatron]:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id_tecnica, id_profesor, nombre, categoria, matriz_esqueletica, video_url, descripcion
                    FROM tecnicas_patron WHERE id_profesor = %s ORDER BY nombre;
                    """,
                    (id_profesor,),
                )
                rows = cur.fetchall()
                resultado = []
                for r in rows:
                    matriz = self._yolo.deserializar_desde_db(r[4])
                    resultado.append(
                        TecnicaPatron(
                            id_tecnica=r[0],
                            id_profesor=r[1],
                            nombre=r[2],
                            categoria=r[3] or "General",
                            matriz_esqueletica=matriz,
                            video_url=r[5],
                            descripcion=r[6],
                        )
                    )
                return resultado


class PostgresFuenteConocimientoRepository(IFuenteConocimientoRepository):
    """Implementación de persistencia para fuentes RAG indexadas en pgvector.

    Aplica el principio de Experto en Información (Larman p. 235) inyectando
    ConfiguracionRAG para gobernar umbrales de similitud y límites de recuperación.
    """

    def __init__(
        self,
        db_connection: Union[Any, str],
        config_rag: Optional[ConfiguracionRAG] = None,
        gemini_adapter: Optional[AdaptadorGemini] = None,
    ):
        self._db = db_connection
        if isinstance(config_rag, ConfiguracionRAG):
            self._config = config_rag
            self._gemini = gemini_adapter if gemini_adapter is not None else AdaptadorGemini()
        elif config_rag is not None and not isinstance(config_rag, ConfiguracionRAG) and gemini_adapter is None:
            # Compatibilidad si se inyecta adaptador en el segundo parámetro posicional
            self._config = ConfiguracionRAG()
            self._gemini = config_rag
        else:
            self._config = config_rag if config_rag is not None else ConfiguracionRAG()
            self._gemini = gemini_adapter if gemini_adapter is not None else AdaptadorGemini()

    def indexar_documento(self, fuente: FuenteConocimiento) -> str:
        # GENERAR embedding usando AdaptadorGemini EXISTENTE si no viene provisto
        if fuente.embedding_vector is None:
            vector = self._gemini.generar_embedding(fuente.chunk_texto)
        else:
            vector = fuente.embedding_vector

        if len(vector) != 768:
            raise ValueError(f"Embedding dimensión incorrecta: {len(vector)} != 768")

        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO fuentes_conocimiento (id_fuente, id_tecnica, titulo, tipo_recurso, embedding_vector, chunk_texto, fecha_carga)
                    VALUES (%s, %s, %s, %s, %s::vector, %s, %s)
                    ON CONFLICT (id_fuente) DO UPDATE
                    SET id_tecnica = EXCLUDED.id_tecnica,
                        titulo = EXCLUDED.titulo,
                        tipo_recurso = EXCLUDED.tipo_recurso,
                        embedding_vector = EXCLUDED.embedding_vector,
                        chunk_texto = EXCLUDED.chunk_texto;
                    """,
                    (
                        fuente.id_fuente,
                        fuente.id_tecnica,
                        fuente.titulo,
                        fuente.tipo_recurso,
                        vector,
                        fuente.chunk_texto,
                        fuente.fecha_carga,
                    ),
                )
        return fuente.id_fuente

    def buscar_contexto(
        self,
        consulta_embedding: List[float],
        limite: Optional[int] = None,
        id_tecnica: Optional[str] = None,
    ) -> List[FuenteConocimiento]:
        if len(consulta_embedding) != 768:
            raise ValueError(f"Dimensión de embedding de búsqueda incorrecta: {len(consulta_embedding)} != 768")

        if isinstance(limite, str) and id_tecnica is None:
            id_tecnica = limite
            limite = None

        k = limite if (isinstance(limite, int) and limite > 0) else self._config.top_k_resultados
        umbral = self._config.umbral_similitud_minima

        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                if id_tecnica:
                    cur.execute(
                        """
                        SELECT id_fuente, id_tecnica, titulo, tipo_recurso, chunk_texto, fecha_carga
                        FROM fuentes_conocimiento
                        WHERE id_tecnica = %s AND (1 - (embedding_vector <=> %s::vector)) >= %s
                        ORDER BY embedding_vector <=> %s::vector ASC
                        LIMIT %s;
                        """,
                        (id_tecnica, consulta_embedding, umbral, consulta_embedding, k),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id_fuente, id_tecnica, titulo, tipo_recurso, chunk_texto, fecha_carga
                        FROM fuentes_conocimiento
                        WHERE (1 - (embedding_vector <=> %s::vector)) >= %s
                        ORDER BY embedding_vector <=> %s::vector ASC
                        LIMIT %s;
                        """,
                        (consulta_embedding, umbral, consulta_embedding, k),
                    )
                rows = cur.fetchall()
                return [
                    FuenteConocimiento(
                        id_fuente=str(r[0]),
                        id_tecnica=r[1] or "",
                        titulo=r[2],
                        tipo_recurso=r[3],
                        chunk_texto=r[4],
                        embedding_vector=None,
                        fecha_carga=r[5],
                    )
                    for r in rows
                ]

    def listar_fuentes(self, id_tecnica: Optional[str] = None) -> List[FuenteConocimiento]:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                if id_tecnica:
                    cur.execute(
                        """
                        SELECT id_fuente, id_tecnica, titulo, tipo_recurso, chunk_texto, fecha_carga
                        FROM fuentes_conocimiento WHERE id_tecnica = %s ORDER BY fecha_carga DESC;
                        """,
                        (id_tecnica,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id_fuente, id_tecnica, titulo, tipo_recurso, chunk_texto, fecha_carga
                        FROM fuentes_conocimiento ORDER BY fecha_carga DESC;
                        """
                    )
                rows = cur.fetchall()
                return [
                    FuenteConocimiento(
                        id_fuente=str(r[0]),
                        id_tecnica=r[1] or "",
                        titulo=r[2],
                        tipo_recurso=r[3],
                        chunk_texto=r[4],
                        embedding_vector=None,
                        fecha_carga=r[5],
                    )
                    for r in rows
                ]
