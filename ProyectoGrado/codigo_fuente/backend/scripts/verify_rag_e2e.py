#!/usr/bin/env python3
"""
verify_rag_e2e.py — Verificación funcional end-to-end del sistema RAG.

Prueba de integración con el stack REAL (sin mocks):
  1. Preflight: Backend + Qdrant + Colab responden.
  2. Ingestión: Envía texto real a `/api/v1/conocimiento/teoria`.
  3. Persistencia: Verifica que los chunks llegaron a Qdrant.
  4. Recuperación: Consulta semántica vía Colab embedding + Qdrant search.

Uso:
    python scripts/verify_rag_e2e.py \
        --texto /ruta/a/teoria_real.txt \
        --tecnica-id d3b07384-d9a4-4f6c-947b-11347076a5b6 \
        --jwt <TOKEN_JWT>

Requiere que COLAB_TUNNEL_URL esté en .env o pase como --colab-url.
"""
import argparse
import os
import sys

import psycopg2
import requests

QDRANT_URL = "http://localhost:6333"
COLLECTION = "rag_knowledge"
DB_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/corpocmente")


def postgres_count(tecnica_id: str) -> int:
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM teoria_referencia WHERE tecnica_id = %s;", (tecnica_id,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"[WARN] Error al consultar PostgreSQL: {e}")
        return 0


def check_services(api_url: str, colab_url: str) -> bool:
    print("=" * 70)
    print("PREFLIGHT CHECKS")
    print("=" * 70)
    ok = True

    # Backend
    try:
        r = requests.get(f"{api_url}/health", timeout=5)
        r.raise_for_status()
        print(f"[OK] Backend: {r.json()}")
    except Exception as e:
        print(f"[FAIL] Backend no responde en {api_url}: {e}")
        ok = False

    # Qdrant
    try:
        r = requests.get(f"{QDRANT_URL}/collections", timeout=5)
        r.raise_for_status()
        colls = [c["name"] for c in r.json()["result"]["collections"]]
        print(f"[OK] Qdrant: {len(colls)} colecciones -> {colls}")
    except Exception as e:
        print(f"[FAIL] Qdrant no responde en {QDRANT_URL}: {e}")
        ok = False

    # Colab Worker
    if not colab_url or "placeholder" in colab_url:
        print("[FAIL] COLAB_TUNNEL_URL no configurado")
        ok = False
    else:
        try:
            r = requests.get(f"{colab_url.rstrip('/')}/health", timeout=15)
            r.raise_for_status()
            print(f"[OK] Colab: {r.json()}")
        except Exception as e:
            print(f"[FAIL] Colab no responde en {colab_url}: {e}")
            ok = False

    return ok


def qdrant_count() -> int:
    try:
        r = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/count",
            json={"exact": True},
            timeout=5,
        )
        return r.json().get("result", {}).get("count", 0)
    except Exception:
        return 0


def ingest(api_url: str, jwt: str, tecnica_id: str, texto: str) -> int | None:
    print("\n" + "=" * 70)
    print("FASE 1: INGESTIÓN (texto real -> Colab -> Qdrant + Postgres)")
    print("=" * 70)
    print(f"  Texto: {len(texto)} caracteres")

    r = requests.post(
        f"{api_url}/api/v1/conocimiento/teoria",
        headers={"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"},
        json={"tecnica_id": tecnica_id, "contenido_texto": texto},
        timeout=180,
    )
    print(f"  HTTP {r.status_code}")
    if r.status_code != 201:
        print(f"[FAIL] Ingestión falló: {r.text}")
        return None
    data = r.json()
    print(f"[OK] {data}")
    return data.get("chunks_procesados", 0)


def query(colab_url: str, tecnica_id: str, query_text: str):
    print("\n" + "=" * 70)
    print("FASE 2: RECUPERACIÓN (consulta semántica)")
    print("=" * 70)
    print(f"  Query: {query_text[:100]}")

    # Generar embedding de la query vía Colab
    r = requests.post(
        f"{colab_url.rstrip('/')}/embed_text",
        data={"texto": query_text},
        timeout=60,
    )
    if r.status_code != 200:
        print(f"[FAIL] Colab embedding: {r.status_code} {r.text[:200]}")
        return None
    emb_data = r.json()
    query_vec = emb_data["embeddings"][0]
    print(f"[OK] Query embedding: {len(query_vec)} dims")

    # Buscar en Qdrant
    r = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
        json={
            "vector": {"name": "dense", "vector": query_vec},
            "limit": 3,
            "filter": {
                "must": [
                    {"key": "tecnica_id", "match": {"value": tecnica_id}}
                ]
            },
            "with_payload": True,
        },
        timeout=30,
    )
    if r.status_code != 200:
        print(f"[FAIL] Qdrant search: {r.status_code} {r.text[:200]}")
        return None
    results = r.json().get("result", [])
    print(f"[OK] {len(results)} chunks recuperados\n")
    for i, hit in enumerate(results, 1):
        score = hit.get("score", 0)
        chunk = hit.get("payload", {}).get("contenido_texto", "")
        preview = chunk[:220].replace("\n", " ")
        print(f"  [{i}] score={score:.4f}")
        print(f"      {preview}...")
        print()
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--texto", required=True, help="Ruta al archivo de texto real")
    parser.add_argument("--tecnica-id", required=True)
    parser.add_argument("--jwt", required=True)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--colab-url", default=os.getenv("COLAB_TUNNEL_URL", ""))
    parser.add_argument("--query", default="¿Cómo se ejecuta correctamente la técnica?")
    args = parser.parse_args()

    if not os.path.exists(args.texto):
        print(f"[FAIL] Archivo no existe: {args.texto}")
        sys.exit(1)

    with open(args.texto, "r", encoding="utf-8") as f:
        texto = f.read().strip()

    if not texto:
        print(f"[FAIL] Archivo vacío: {args.texto}")
        sys.exit(1)

    if not check_services(args.api_url, args.colab_url):
        print("\n[ABORT] Preflight falló. Corrige los servicios antes de continuar.")
        sys.exit(1)

    pg_before = postgres_count(args.tecnica_id)
    count_before = qdrant_count()
    print(f"\n  Filas en Postgres ANTES: {pg_before}")
    print(f"  Puntos en Qdrant ANTES: {count_before}")

    chunks = ingest(args.api_url, args.jwt, args.tecnica_id, texto)
    if chunks is None:
        sys.exit(1)

    pg_after = postgres_count(args.tecnica_id)
    count_after = qdrant_count()
    pg_delta = pg_after - pg_before
    delta = count_after - count_before
    print(f"  Filas en Postgres DESPUÉS: {pg_after} (delta: {pg_delta})")
    print(f"  Puntos en Qdrant DESPUÉS: {count_after} (delta: {delta})")

    if pg_delta <= 0 or delta <= 0:
        print(f"\n[FAIL] Ingestión incompleta: Postgres delta={pg_delta}, Qdrant delta={delta}")
        sys.exit(1)

    query(args.colab_url, args.tecnica_id, args.query)

    print("=" * 70)
    print("✅ VERIFICACIÓN COMPLETA (Persistencia Dual: Postgres + Qdrant)")
    print("=" * 70)


if __name__ == "__main__":
    main()
