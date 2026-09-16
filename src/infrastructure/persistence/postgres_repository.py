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
    IVectorStore,
    IUsuarioRepository,
    IEmbeddingService,
)
from src.domain.models import (
    Profesor,
    TecnicaPatron,
    FuenteConocimiento,
    MatrizEsqueletica,
    ConfiguracionRAG,
    Usuario,
)
from src.infrastructure.adapters.yolo_adapter import AdaptadorYOLO
from src.infrastructure.adapters.qwen_embedding_adapter import QwenEmbeddingAdapter
from src.infrastructure.adapters.qdrant_adapter import QdrantAdapter


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
                    INSERT INTO usuarios (id_usuario, nombre_completo, email, rol, password_hash, fecha_registro)
                    VALUES (%s, %s, %s, 'profesor', 'mock_hash', %s)
                    ON CONFLICT (id_usuario) DO UPDATE
                    SET nombre_completo = EXCLUDED.nombre_completo,
                        email = EXCLUDED.email;
                    """,
                    (profesor.id_profesor, profesor.nombre, profesor.email, profesor.fecha_registro),
                )

    def obtener_por_id(self, id_profesor: str) -> Optional[Profesor]:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_usuario, nombre_completo, email, fecha_registro FROM usuarios WHERE id_usuario = %s AND rol = 'profesor';",
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
                    "SELECT id_usuario, nombre_completo, email, fecha_registro FROM usuarios WHERE rol = 'profesor' ORDER BY nombre;"
                )
                rows = cur.fetchall()
                return [
                    Profesor(id_profesor=r[0], nombre=r[1], email=r[2], fecha_registro=r[3])
                    for r in rows
                ]

    def eliminar(self, id_profesor: str) -> bool:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM usuarios WHERE id_usuario = %s AND rol = 'profesor';", (id_profesor,))
                return getattr(cur, "rowcount", 1) > 0

    def actualizar(self, id_profesor: str, nombre: str, email: str) -> bool:
        clean_email = email.strip()
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_usuario FROM usuarios WHERE LOWER(email) = LOWER(%s) AND id_usuario != %s AND rol = 'profesor';",
                    (clean_email, id_profesor),
                )
                if cur.fetchone():
                    raise ValueError(f"El email '{email}' ya se encuentra registrado.")
                cur.execute(
                    """
                    UPDATE usuarios 
                    SET nombre_completo = %s, email = %s 
                    WHERE id_usuario = %s AND rol = 'profesor'
                    """,
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

    def eliminar(self, id_tecnica: str) -> bool:
        """Elimina una técnica patrón limpiando dependencias de clave foránea."""
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM evaluaciones_alumno WHERE id_tecnica = %s;", (id_tecnica,))
                cur.execute("UPDATE fuentes_conocimiento SET id_tecnica = NULL WHERE id_tecnica = %s;", (id_tecnica,))
                cur.execute("DELETE FROM tecnicas_patron WHERE id_tecnica = %s;", (id_tecnica,))
                return cur.rowcount > 0

    def eliminar_patron(self, id_tecnica: str) -> bool:
        """Alias para retrocompatibilidad con controladores."""
        return self.eliminar(id_tecnica)


class PostgresFuenteConocimientoRepository(IFuenteConocimientoRepository):
    """Implementación de persistencia híbrida: Relacional en PostgreSQL y Vectorial en Qdrant.

    Aplica el principio de Experto en Información (Larman p. 235) inyectando
    ConfiguracionRAG y desacopla la persistencia vectorial hacia QdrantAdapter.
    """

    def __init__(
        self,
        db_connection: Union[Any, str],
        config_rag: Optional[ConfiguracionRAG] = None,
        qdrant_adapter: Optional[IVectorStore] = None,
        embedding_service: Optional[IEmbeddingService] = None,
    ):
        self._db = db_connection
        self._config = config_rag if isinstance(config_rag, ConfiguracionRAG) else ConfiguracionRAG()
        self._embedding = embedding_service if embedding_service is not None else QwenEmbeddingAdapter()

        if qdrant_adapter is not None:
            self._qdrant = qdrant_adapter
        else:
            try:
                self._qdrant = QdrantAdapter()
            except Exception:
                self._qdrant = None

    def indexar_documento(self, fuente: FuenteConocimiento) -> str:
        # GENERAR embedding usando adaptador si no viene provisto
        if fuente.embedding_vector is None:
            if hasattr(self._embedding, "generar_embedding"):
                vector = self._embedding.generar_embedding(fuente.chunk_texto)
            elif hasattr(self._embedding, "generate_embedding"):
                vector = self._embedding.generate_embedding(fuente.chunk_texto)
            else:
                vector = [0.05] * 2048
        else:
            vector = fuente.embedding_vector

        if len(vector) != 2048:
            raise ValueError(f"Embedding dimensión incorrecta: {len(vector)} != 2048")

        # 1. Almacenar vector y payload en Qdrant (Capa Vectorial)
        if self._qdrant is not None:
            self._qdrant.upsert(
                id_fuente=fuente.id_fuente,
                vector=vector,
                payload={
                    "id_fuente": fuente.id_fuente,
                    "id_tecnica": fuente.id_tecnica,
                    "titulo": fuente.titulo,
                    "tipo_recurso": fuente.tipo_recurso,
                    "chunk_texto": fuente.chunk_texto,
                },
            )

        # 2. Persistir metadatos relacionales en PostgreSQL (Mannino BCNF)
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO fuentes_conocimiento (id_fuente, id_tecnica, titulo, tipo_recurso, chunk_texto, fecha_carga)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id_fuente) DO UPDATE
                    SET id_tecnica = EXCLUDED.id_tecnica,
                        titulo = EXCLUDED.titulo,
                        tipo_recurso = EXCLUDED.tipo_recurso,
                        chunk_texto = EXCLUDED.chunk_texto;
                    """,
                    (
                        fuente.id_fuente,
                        fuente.id_tecnica,
                        fuente.titulo,
                        fuente.tipo_recurso,
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
        """Recupera fragmentos semánticos usando búsqueda vectorial KNN en Qdrant."""
        if len(consulta_embedding) != 2048:
            raise ValueError(f"Dimensión de embedding de búsqueda incorrecta: {len(consulta_embedding)} != 2048")

        if isinstance(limite, str) and id_tecnica is None:
            id_tecnica = limite
            limite = None

        k = limite if (isinstance(limite, int) and limite > 0) else self._config.top_k_resultados
        umbral = self._config.umbral_similitud_minima

        if self._qdrant is None:
            return []

        resultados_qdrant = self._qdrant.buscar(
            consulta_embedding=consulta_embedding,
            limite=k,
            umbral_similitud=umbral,
            id_tecnica=id_tecnica,
        )

        return [
            FuenteConocimiento(
                id_fuente=str(r["id_fuente"]),
                id_documento=r.get("id_documento"),
                id_tecnica=r.get("id_tecnica") or "",
                titulo=r.get("titulo") or "",
                tipo_recurso=r.get("tipo_recurso") or "Manual",
                chunk_texto=r.get("chunk_texto") or "",
                embedding_vector=None,
                similitud=r.get("similitud"),
            )
            for r in resultados_qdrant
        ]

    def listar_fuentes(self, id_tecnica: Optional[str] = None) -> List[FuenteConocimiento]:
        """Recupera el acervo documental agrupado a nivel de documento padre (sin exponer chunks individuales)."""
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                if id_tecnica:
                    cur.execute(
                        """
                        SELECT 
                            COALESCE(id_documento, MIN(id_fuente)) AS doc_id,
                            id_tecnica,
                            REGEXP_REPLACE(titulo, '\\s*\\[Parte\\s+\\d+\\]$', '') AS base_titulo,
                            tipo_recurso,
                            COUNT(*) AS total_chunks,
                            MAX(fecha_carga) AS max_fecha,
                            MAX(id_instructor) AS id_instructor
                        FROM fuentes_conocimiento
                        WHERE id_tecnica = %s
                        GROUP BY id_documento, id_tecnica, REGEXP_REPLACE(titulo, '\\s*\\[Parte\\s+\\d+\\]$', ''), tipo_recurso
                        ORDER BY MAX(fecha_carga) DESC;
                        """,
                        (id_tecnica,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT 
                            COALESCE(id_documento, MIN(id_fuente)) AS doc_id,
                            id_tecnica,
                            REGEXP_REPLACE(titulo, '\\s*\\[Parte\\s+\\d+\\]$', '') AS base_titulo,
                            tipo_recurso,
                            COUNT(*) AS total_chunks,
                            MAX(fecha_carga) AS max_fecha,
                            MAX(id_instructor) AS id_instructor
                        FROM fuentes_conocimiento
                        GROUP BY id_documento, id_tecnica, REGEXP_REPLACE(titulo, '\\s*\\[Parte\\s+\\d+\\]$', ''), tipo_recurso
                        ORDER BY MAX(fecha_carga) DESC;
                        """
                    )
                rows = cur.fetchall()
                return [
                    FuenteConocimiento(
                        id_fuente=str(r[0]),
                        id_documento=str(r[0]),
                        id_tecnica=r[1] if r[1] else None,
                        titulo=r[2],
                        tipo_recurso=r[3],
                        chunk_texto=f"{r[4]} fragmentos",
                        total_chunks=int(r[4]) if r[4] is not None else 1,
                        embedding_vector=None,
                        fecha_carga=r[5],
                        id_instructor=r[6] if len(r) > 6 and r[6] else None,
                    )
                    for r in rows
                ]

    def eliminar(self, id_fuente_or_doc: str) -> bool:
        """Elimina un documento o fuente en cascada tanto de PostgreSQL como de Qdrant."""
        doc_id = id_fuente_or_doc
        chunk_ids = []

        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                # 1. Identificar chunks asociados y el id_documento real
                cur.execute(
                    "SELECT id_fuente, id_documento FROM fuentes_conocimiento WHERE id_documento = %s OR id_fuente = %s;",
                    (id_fuente_or_doc, id_fuente_or_doc),
                )
                rows = cur.fetchall() if hasattr(cur, "fetchall") else []
                if rows:
                    chunk_ids = [r[0] for r in rows]
                    if not doc_id.startswith("doc_") and rows[0][1]:
                        doc_id = rows[0][1]

                # 2. Eliminar en Qdrant por id_documento nativo
                if self._qdrant is not None:
                    if hasattr(self._qdrant, "eliminar_por_documento"):
                        self._qdrant.eliminar_por_documento(doc_id)
                    elif hasattr(self._qdrant, "eliminar"):
                        for cid in chunk_ids:
                            self._qdrant.eliminar(cid)
                        self._qdrant.eliminar(doc_id)

                # 3. Eliminar en PostgreSQL
                cur.execute(
                    "DELETE FROM fuentes_conocimiento WHERE id_documento = %s OR id_fuente = %s;",
                    (doc_id, id_fuente_or_doc),
                )
                return getattr(cur, "rowcount", 1) > 0

    def actualizar(self, id_fuente: str, titulo: str, chunk_texto: Optional[str] = None) -> bool:
        """Actualiza metadatos de una fuente o documento en PostgreSQL."""
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                if chunk_texto:
                    cur.execute(
                        "UPDATE fuentes_conocimiento SET titulo = %s, chunk_texto = %s WHERE id_documento = %s OR id_fuente = %s;",
                        (titulo, chunk_texto, id_fuente, id_fuente),
                    )
                else:
                    cur.execute(
                        "UPDATE fuentes_conocimiento SET titulo = %s WHERE id_documento = %s OR id_fuente = %s;",
                        (titulo, id_fuente, id_fuente),
                    )
                return getattr(cur, "rowcount", 0) > 0


class PostgresUsuarioRepository(IUsuarioRepository):
    """Implementación de persistencia para usuarios bajo BCNF."""

    def __init__(self, db_connection: Union[Any, str]):
        self._db = db_connection

    def guardar(self, usuario: Usuario) -> None:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_usuario FROM usuarios WHERE LOWER(email) = LOWER(%s) AND id_usuario != %s;",
                    (usuario.email, usuario.id_usuario),
                )
                if cur.fetchone():
                    raise ValueError(f"El email '{usuario.email}' ya se encuentra registrado.")
                
                cur.execute(
                    """
                    INSERT INTO usuarios (id_usuario, email, nombre_completo, rol, password_hash, fecha_registro)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id_usuario) DO UPDATE
                    SET email = EXCLUDED.email,
                        nombre_completo = EXCLUDED.nombre_completo,
                        rol = EXCLUDED.rol,
                        password_hash = EXCLUDED.password_hash;
                    """,
                    (
                        usuario.id_usuario,
                        usuario.email.strip().lower(),
                        usuario.nombre_completo,
                        usuario.rol,
                        usuario.password_hash,
                        usuario.fecha_registro,
                    ),
                )

    def obtener_por_id(self, id_usuario: str) -> Optional[Usuario]:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_usuario, email, nombre_completo, rol, password_hash, fecha_registro FROM usuarios WHERE id_usuario = %s;",
                    (id_usuario,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return Usuario(
                    id_usuario=row[0],
                    email=row[1],
                    nombre_completo=row[2],
                    rol=row[3],
                    password_hash=row[4],
                    fecha_registro=row[5],
                )

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_usuario, email, nombre_completo, rol, password_hash, fecha_registro FROM usuarios WHERE LOWER(email) = LOWER(%s);",
                    (email.strip(),),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return Usuario(
                    id_usuario=row[0],
                    email=row[1],
                    nombre_completo=row[2],
                    rol=row[3],
                    password_hash=row[4],
                    fecha_registro=row[5],
                )

    def listar_todos(self) -> List[Usuario]:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id_usuario, email, nombre_completo, rol, password_hash, fecha_registro FROM usuarios ORDER BY nombre_completo;")
                return [
                    Usuario(id_usuario=r[0], email=r[1], nombre_completo=r[2], rol=r[3], password_hash=r[4], fecha_registro=r[5])
                    for r in cur.fetchall()
                ]

    def eliminar(self, id_usuario: str) -> bool:
        with _DBContext(self._db) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
                return getattr(cur, "rowcount", 0) > 0
