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
from src.services.adapters import AdaptadorYOLO, AdaptadorGemini

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
    gemini_adapter: Optional[AdaptadorGemini] = None,
    nuevo_almacen: bool = False,
) -> FuenteController:
    """Crea una instancia de FuenteController inyectando repositorio y adaptador Gemini."""
    gemini = gemini_adapter if gemini_adapter is not None else AdaptadorGemini()
    if usar_db_real:
        conn = db_conn if db_conn is not None else get_db_connection()
        repo = PostgresFuenteConocimientoRepository(conn, gemini_adapter=gemini)
    else:
        repo = InMemoryFuenteConocimientoRepository() if nuevo_almacen else _SHARED_MEM_FUENTE_REPO
    return FuenteController(repository=repo, gemini_adapter=gemini)
