# src/application/factory.py
"""Fábrica de Inyección de Dependencias (Factory DI - Larman p. 279: Visibilidad Controlada).

Permite alternar entre repositorios en memoria para pruebas unitarias instantáneas (<100ms)
y repositorios PostgreSQL con pgvector y adaptadores reutilizados para producción.
"""

import os
from typing import Any, Optional

from src.application.profesor_controller import ProfesorController
from src.application.tecnica_controller import TecnicaController
from src.application.fuente_controller import FuenteController
from src.application.controllers import EvaluacionController
from src.services.sintesis_pedagogica_service import SintesisPedagogicaService

from src.infrastructure.mocks import (
    InMemoryProfesorRepository,
    InMemoryTecnicaRepository,
    InMemoryFuenteConocimientoRepository,
)
from src.infrastructure.persistence import (
    PostgresProfesorRepository,
    PostgresTecnicaRepository,
    PostgresFuenteConocimientoRepository,
)
from src.domain.models import ConfiguracionRAG
from src.infrastructure.adapters.yolo_adapter import AdaptadorYOLO
from src.infrastructure.adapters.gemini_service_adapter import AdaptadorGemini
from src.infrastructure.adapters.qwen_embedding_adapter import QwenEmbeddingAdapter
from src.infrastructure.adapters.qdrant_adapter import QdrantAdapter

# Almacenes compartidos en memoria para integración de casos de uso sin base de datos activa
_SHARED_MEM_TECNICA_REPO = InMemoryTecnicaRepository()
_SHARED_MEM_PROFESOR_REPO = InMemoryProfesorRepository(tecnica_repository=_SHARED_MEM_TECNICA_REPO)
_SHARED_MEM_FUENTE_REPO = InMemoryFuenteConocimientoRepository()


def reiniciar_repositorios_memoria() -> None:
    """Limpia los almacenes en memoria compartidos para aislamiento estricto entre pruebas."""
    _SHARED_MEM_TECNICA_REPO._storage.clear()
    _SHARED_MEM_PROFESOR_REPO._storage.clear()
    _SHARED_MEM_FUENTE_REPO._storage.clear()


def get_db_connection() -> str:
    """Retorna la cadena o URL de conexión configurada para PostgreSQL."""
    return os.getenv("DATABASE_URL", "postgresql://jiujitsu_user:jiujitsu_password@localhost:5432/jiujitsu_db")


def crear_profesor_controller(
    usar_db_real: bool = False,
    db_conn: Optional[Any] = None,
    nuevo_almacen: bool = False,
) -> ProfesorController:
    """Crea una instancia de ProfesorController inyectando el repositorio adecuado."""
    if usar_db_real:
        conn = db_conn if db_conn is not None else get_db_connection()
        repo = PostgresProfesorRepository(conn)
        return ProfesorController(repo)
    if nuevo_almacen:
        tec_repo = InMemoryTecnicaRepository()
        prof_repo = InMemoryProfesorRepository(tecnica_repository=tec_repo)
        return ProfesorController(prof_repo, tecnica_repository=tec_repo)
    return ProfesorController(_SHARED_MEM_PROFESOR_REPO, tecnica_repository=_SHARED_MEM_TECNICA_REPO)


def crear_tecnica_controller(
    usar_db_real: bool = False,
    db_conn: Optional[Any] = None,
    yolo_adapter: Optional[AdaptadorYOLO] = None,
    profesor_controller: Optional[ProfesorController] = None,
    nuevo_almacen: bool = False,
) -> TecnicaController:
    """Crea una instancia de TecnicaController inyectando repositorio y adaptador YOLO."""
    yolo = yolo_adapter if yolo_adapter is not None else AdaptadorYOLO()
    if usar_db_real:
        conn = db_conn if db_conn is not None else get_db_connection()
        repo = PostgresTecnicaRepository(conn, yolo_adapter=yolo)
        prof_repo = profesor_controller._repository if profesor_controller else None
        return TecnicaController(repository=repo, profesor_repository=prof_repo, yolo_adapter=yolo)

    if nuevo_almacen:
        repo = InMemoryTecnicaRepository()
        prof_repo = profesor_controller._repository if profesor_controller else None
    else:
        repo = _SHARED_MEM_TECNICA_REPO
        prof_repo = _SHARED_MEM_PROFESOR_REPO

    return TecnicaController(repository=repo, profesor_repository=prof_repo, yolo_adapter=yolo)


def crear_fuente_controller(
    usar_db_real: bool = False,
    db_conn: Optional[Any] = None,
    config_rag: Optional[ConfiguracionRAG] = None,
    nuevo_almacen: bool = False,
    qdrant_adapter: Optional[Any] = None,
) -> FuenteController:
    """Crea una instancia de FuenteController inyectando el adaptador multimodal de Qwen y Qdrant."""
    adaptador_qwen = QwenEmbeddingAdapter()
    cfg = config_rag if config_rag is not None else ConfiguracionRAG()
    if usar_db_real:
        conn = db_conn if db_conn is not None else get_db_connection()
        qdrant = qdrant_adapter if qdrant_adapter is not None else QdrantAdapter()
        repo = PostgresFuenteConocimientoRepository(
            conn, config_rag=cfg, embedding_service=adaptador_qwen, qdrant_adapter=qdrant
        )
        from src.infrastructure.persistence.rag_ingestion import PipelineIngestaRAG
        pipeline = PipelineIngestaRAG(
            db_connection=conn,
            embedding_service=adaptador_qwen,
            qdrant_adapter=qdrant,
        )
        return FuenteController(
            repository=repo,
            embedding_service=adaptador_qwen,
            qdrant_adapter=qdrant,
            pipeline_ingesta=pipeline,
        )
    else:
        repo = InMemoryFuenteConocimientoRepository(config_rag=cfg) if nuevo_almacen else _SHARED_MEM_FUENTE_REPO
        return FuenteController(repository=repo, embedding_service=adaptador_qwen)


def crear_sintesis_pedagogica_service(
    usar_db_real: bool = False,
    db_conn: Optional[Any] = None,
    config_rag: Optional[ConfiguracionRAG] = None,
    nuevo_almacen: bool = False,
    qdrant_adapter: Optional[Any] = None,
) -> SintesisPedagogicaService:
    """Crea una instancia de SintesisPedagogicaService con repositorio y configuración inyectada."""
    cfg = config_rag if config_rag is not None else ConfiguracionRAG()
    if usar_db_real:
        conn = db_conn if db_conn is not None else get_db_connection()
        qdrant = qdrant_adapter if qdrant_adapter is not None else QdrantAdapter()
        repo = PostgresFuenteConocimientoRepository(conn, config_rag=cfg, qdrant_adapter=qdrant)
    else:
        repo = InMemoryFuenteConocimientoRepository(config_rag=cfg) if nuevo_almacen else _SHARED_MEM_FUENTE_REPO
    return SintesisPedagogicaService(repo=repo, config=cfg)


def crear_evaluacion_controller(
    inference_engine: Optional[Any] = None,
    generation_service: Optional[Any] = None,
    tecnica_repository: Optional[Any] = None,
    usar_db_real: bool = False,
    db_conn: Optional[Any] = None,
    config_rag: Optional[ConfiguracionRAG] = None,
    qdrant_adapter: Optional[Any] = None,
) -> EvaluacionController:
    """Crea una instancia de EvaluacionController con el servicio de síntesis pedagógica inyectado."""
    from src.infrastructure.mocks import MockYOLOEngine, MockGeminiService
    inf = inference_engine if inference_engine is not None else MockYOLOEngine()
    gen = generation_service if generation_service is not None else MockGeminiService()
    tec = tecnica_repository if tecnica_repository is not None else _SHARED_MEM_TECNICA_REPO
    sintesis = crear_sintesis_pedagogica_service(
        usar_db_real=usar_db_real, db_conn=db_conn, config_rag=config_rag, qdrant_adapter=qdrant_adapter
    )
    return EvaluacionController(
        inference_engine=inf,
        generation_service=gen,
        tecnica_repository=tec,
        sintesis_service=sintesis,
    )

def crear_auth_controller(
    usar_db_real: bool = False,
    db_conn: Optional[Any] = None,
    nuevo_almacen: bool = False,
):
    from src.application.auth_controller import AuthController
    from src.infrastructure.persistence.postgres_repository import PostgresUsuarioRepository
    from src.infrastructure.mocks import InMemoryUsuarioRepository

    if usar_db_real:
        conn = db_conn if db_conn is not None else get_db_connection()
        repo = PostgresUsuarioRepository(conn)
    else:
        repo = InMemoryUsuarioRepository()
    return AuthController(usuario_repo=repo)

