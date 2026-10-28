#!/usr/bin/env python3
"""
reconcile_rag.py — Auditoría y reconciliación Postgres ↔ Qdrant.

Detecta orphans en ambas direcciones y, con --fix, elimina los orphans de Qdrant
(Postgres es la fuente de verdad; Qdrant es índice reconstruible desde teoria_referencia).

Uso:
    python scripts/reconcile_rag.py              # solo detecta, no modifica
    python scripts/reconcile_rag.py --fix        # detecta y limpia orphans en Qdrant
"""
import argparse
import os
import sys
import psycopg2
import requests

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "host=localhost dbname=corpocmente user=postgres password=postgres")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "rag_knowledge"


def fetch_postgres_ids() -> set[str]:
    """Retorna el conjunto de qdrant_point_id registrados en teoria_referencia."""
    with psycopg2.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT qdrant_point_id FROM teoria_referencia;")
            return {str(row[0]) for row in cur.fetchall()}


def fetch_qdrant_ids() -> set[str]:
    """Retorna el conjunto de IDs de puntos en la colección rag_knowledge."""
    r = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
        json={"limit": 10000, "with_payload": False},
        timeout=30,
    )
    r.raise_for_status()
    points = r.json().get("result", {}).get("points", [])
    return {p["id"] for p in points}


def delete_qdrant_points(ids: list[str]) -> None:
    """Borra los puntos indicados en Qdrant."""
    if not ids:
        return
    r = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/delete",
        json={"points": ids},
        timeout=30,
    )
    r.raise_for_status()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="Elimina orphans en Qdrant")
    args = parser.parse_args()

    print("=" * 70)
    print("RECONCILIACIÓN POSTGRES ↔ QDRANT")
    print("=" * 70)

    pg_ids = fetch_postgres_ids()
    qdrant_ids = fetch_qdrant_ids()

    print(f"Postgres (fuente de verdad): {len(pg_ids)} chunks")
    print(f"Qdrant (índice):             {len(qdrant_ids)} puntos")

    orphans_qdrant = qdrant_ids - pg_ids       # en Qdrant pero no en Postgres
    orphans_postgres = pg_ids - qdrant_ids     # en Postgres pero no en Qdrant

    print()
    if not orphans_qdrant and not orphans_postgres:
        print("✅ CONSISTENCIA TOTAL — Sin orphans en ninguna dirección.")
        return 0

    if orphans_qdrant:
        print(f"⚠️  {len(orphans_qdrant)} orphan(s) en Qdrant (sin fila en Postgres):")
        for oid in sorted(orphans_qdrant):
            print(f"    - {oid}")

    if orphans_postgres:
        print(f"🚨 {len(orphans_postgres)} orphan(s) en Postgres (sin punto en Qdrant):")
        for oid in sorted(orphans_postgres):
            print(f"    - {oid}")
        print("    ⚠️  Postgres es la fuente de verdad — investigar manualmente.")

    if args.fix and orphans_qdrant:
        print()
        print(f"🔧 Aplicando --fix: eliminando {len(orphans_qdrant)} orphan(s) de Qdrant...")
        delete_qdrant_points(sorted(orphans_qdrant))
        print("✅ Eliminados. Re-ejecuta sin --fix para verificar consistencia.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
