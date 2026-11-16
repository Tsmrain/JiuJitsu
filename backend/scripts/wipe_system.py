#!/usr/bin/env python3
"""
Limpieza total del sistema (FASE 1):
1. PostgreSQL: TRUNCATE ... CASCADE de teoria_referencia, patrones_referencia,
   videos_referencia, evaluaciones_alumnos y tecnicas (preserva usuarios/sucursales).
2. Qdrant: elimina y recrea las colecciones `vectores_poses_jiujitsu` (133 dims)
   y `rag_knowledge` (dense: 2048 dims).
3. Almacenamiento local: elimina todos los archivos dentro de CORPOCMENTE_DATA_DIR
   (y backend/storage/manuales/paginas residuales).
"""

import os
import shutil
import sys
from pathlib import Path

ROOT_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_BACKEND))

from dotenv import load_dotenv

load_dotenv(ROOT_BACKEND / ".env")

import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from corpocmente.config import settings, storage_root


TABLES_TO_TRUNCATE = [
    "teoria_referencia",
    "patrones_referencia",
    "videos_referencia",
    "evaluaciones_alumnos",
    "tecnicas",
]


def wipe_postgres() -> dict:
    db_url = os.getenv(
        "DATABASE_URL",
        "postgres://postgres:postgres@localhost:5432/corpocmente",
    )
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    counts = {}
    with conn.cursor() as cur:
        cur.execute(
            f"TRUNCATE TABLE {', '.join(TABLES_TO_TRUNCATE)} RESTART IDENTITY CASCADE;"
        )
        for tbl in TABLES_TO_TRUNCATE:
            cur.execute(f"SELECT COUNT(*) FROM {tbl};")
            counts[tbl] = int(cur.fetchone()[0])
    conn.close()
    return counts


def wipe_qdrant() -> dict:
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    existing = {c.name for c in client.get_collections().collections}

    if settings.QDRANT_COLLECTION in existing:
        client.delete_collection(settings.QDRANT_COLLECTION)
    client.create_collection(
        collection_name=settings.QDRANT_COLLECTION,
        vectors_config=VectorParams(size=133, distance=Distance.COSINE),
    )

    if settings.QDRANT_RAG_COLLECTION in existing:
        client.delete_collection(settings.QDRANT_RAG_COLLECTION)
    client.create_collection(
        collection_name=settings.QDRANT_RAG_COLLECTION,
        vectors_config={"dense": VectorParams(size=2048, distance=Distance.COSINE)},
    )

    return {
        settings.QDRANT_COLLECTION: client.get_collection(settings.QDRANT_COLLECTION).points_count,
        settings.QDRANT_RAG_COLLECTION: client.get_collection(settings.QDRANT_RAG_COLLECTION).points_count,
    }


def wipe_local_storage() -> dict:
    data_dir = storage_root()
    removed_files = 0
    if data_dir.exists():
        for entry in list(data_dir.iterdir()):
            if entry.is_dir():
                for p in entry.rglob("*"):
                    if p.is_file() or p.is_symlink():
                        removed_files += 1
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)
                removed_files += 1

    # Recrear subdirectorios vacíos esperados por start.sh y la API
    for sub in ("logs", "uploads", "frames", "manuales", "rag_frames", "comparaciones", "reference_videos"):
        (data_dir / sub).mkdir(parents=True, exist_ok=True)

    # Limpiar también páginas residuales en backend/storage/manuales/paginas
    legacy_pages = ROOT_BACKEND / "storage" / "manuales" / "paginas"
    if legacy_pages.exists():
        for entry in list(legacy_pages.iterdir()):
            if entry.is_dir():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)

    remaining = sum(1 for p in data_dir.rglob("*") if p.is_file() or p.is_symlink())
    return {
        "data_dir": str(data_dir),
        "removed_files": removed_files,
        "remaining_files": remaining,
    }


def main() -> None:
    pg_counts = wipe_postgres()
    qdrant_counts = wipe_qdrant()
    storage_info = wipe_local_storage()

    print("=== WIPE SYSTEM COMPLETADO ===")
    print("PostgreSQL (filas por tabla):")
    for tbl, cnt in pg_counts.items():
        print(f"  - {tbl}: {cnt}")
    print("Qdrant (puntos por colección):")
    for col, cnt in qdrant_counts.items():
        print(f"  - {col}: {cnt}")
    print("Almacenamiento local:")
    print(f"  - CORPOCMENTE_DATA_DIR: {storage_info['data_dir']}")
    print(f"  - Archivos eliminados: {storage_info['removed_files']}")
    print(f"  - Archivos restantes: {storage_info['remaining_files']}")


if __name__ == "__main__":
    main()
