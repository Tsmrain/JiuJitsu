#!/usr/bin/env python3
"""
ingest_reference_video.py — Ingesta REAL del video de referencia de un profesor.

Flujo:
  1. Extrae frames del video (muestreo cada N) y los guarda como JPG en /tmp.
  2. Envía el video al Colab Worker (/extraer_poses) para obtener keypoints reales.
  3. Persiste en Qdrant con payload {tecnica_id, frame_idx, frame_path, discrepancias}.
  4. Las discrepancias se rellenan luego con un experto (o vacío inicialmente).

Uso:
    python scripts/ingest_reference_video.py \
        --video /ruta/armbar_miguel.mp4 \
        --tecnica-id d3b07384-d9a4-4f6c-947b-11347076a5b6 \
        --tecnica-nombre "Armbar desde guardia"
"""
import argparse
import os
import sys
import uuid

import cv2
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# Añadir el directorio padre al path para importar corpocmente
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from corpocmente.config import settings

FRAMES_DIR = "/tmp/corpocmente_reference_frames"
os.makedirs(FRAMES_DIR, exist_ok=True)


def extract_frames(video_path: str, tecnica_id: str, every_n: int = 5) -> dict[int, str]:
    """Extrae 1 de cada N frames como JPG. Retorna {frame_idx: jpg_path}."""
    out_dir = os.path.join(FRAMES_DIR, tecnica_id)
    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir el video: {video_path}")

    mapping: dict[int, str] = {}
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % every_n == 0:
            path = os.path.join(out_dir, f"ref_{idx:05d}.jpg")
            cv2.imwrite(path, frame)
            mapping[idx] = path
        idx += 1
    cap.release()
    print(f"  Total frames en video: {idx}")
    return mapping


def request_poses(video_path: str, colab_url: str) -> list[dict]:
    """Llama al worker real de Colab. Sin fallback a vectores dummy."""
    if not colab_url or "placeholder" in colab_url:
        raise RuntimeError(
            "COLAB_TUNNEL_URL no está configurada en .env "
            "(vacía o contiene 'placeholder'). "
            "Ejecutar el notebook colab_worker.ipynb y copiar la URL de ngrok."
        )

    endpoint = f"{colab_url.rstrip('/')}/extraer_poses"
    print(f"→ POST {endpoint}")
    with open(video_path, "rb") as f:
        resp = requests.post(
            endpoint,
            files={"video": f},
            headers={"ngrok-skip-browser-warning": "1"},
            timeout=600,
        )
    resp.raise_for_status()
    data = resp.json()
    esqueletos = data.get("esqueletos", [])
    if not esqueletos:
        raise RuntimeError("El worker no devolvió esqueletos. Revisar video y endpoint.")
    print(f"✓ {len(esqueletos)} frames con pose detectada.")
    return esqueletos


def ensure_collection(client: QdrantClient, collection_name: str):
    """Crea la colección con size=133, distance=COSINE si no existe."""
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=133, distance=Distance.COSINE),
        )
        print(f"✓ Colección '{collection_name}' creada (size=133, COSINE).")
    else:
        print(f"  Colección '{collection_name}' ya existe.")


def main():
    ap = argparse.ArgumentParser(
        description="Ingesta REAL de video de referencia → Colab Worker → Qdrant"
    )
    ap.add_argument("--video", required=True, help="Ruta al video de referencia del profesor")
    ap.add_argument("--tecnica-id", required=True, help="UUID de la técnica (e.g. d3b07384-...)")
    ap.add_argument("--tecnica-nombre", default="", help="Nombre legible de la técnica")
    ap.add_argument("--colab-url", default=None,
                    help="URL del tunnel ngrok (default: lee de .env COLAB_TUNNEL_URL)")
    ap.add_argument("--every-n", type=int, default=5,
                    help="Muestreo de frames para JPG (1 = todos, 5 = 1 de cada 5)")
    args = ap.parse_args()

    colab_url = args.colab_url or settings.COLAB_TUNNEL_URL

    if not os.path.exists(args.video):
        print(f"❌ Video no encontrado: {args.video}")
        sys.exit(1)

    print(f"=== Ingesta de referencia: {args.tecnica_nombre or args.tecnica_id} ===")
    print(f"  Video: {args.video}")
    print(f"  Técnica ID: {args.tecnica_id}")
    print(f"  Colab URL: {colab_url}")
    print(f"  Muestreo: 1 de cada {args.every_n} frames")
    print()

    # 1. Extraer frames reales del video como JPG
    frame_map = extract_frames(args.video, args.tecnica_id, every_n=args.every_n)
    print(f"✓ {len(frame_map)} frames extraídos a {FRAMES_DIR}/{args.tecnica_id}")

    # 2. Extraer keypoints reales del worker de Colab (YOLO26-pose)
    esqueletos = request_poses(args.video, colab_url)

    # 3. Persistir en Qdrant
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    ensure_collection(client, settings.QDRANT_COLLECTION)

    points = []
    skipped = 0
    for esk in esqueletos:
        fidx = esk.get("frame_idx")
        kp = esk.get("keypoints133", [])

        # Validar que el frame tiene keypoints de 133 dims
        if len(kp) != 133:
            skipped += 1
            continue

        # Mapear al JPG correspondiente si existe
        frame_path = frame_map.get(fidx, "")

        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=kp,
            payload={
                "tecnica_id": args.tecnica_id,
                "tecnica_nombre": args.tecnica_nombre,
                "frame_idx": fidx,
                "frame_path": frame_path,
                "discrepancias": [],  # el profesor/experto las anota después
            },
        ))

    if skipped:
        print(f"  ⚠ {skipped} esqueletos descartados (keypoints != 133 dims)")

    if not points:
        print("❌ Ningún punto válido para insertar. Verifica el worker y el muestreo.")
        sys.exit(1)

    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    print(f"\n✅ {len(points)} puntos persistidos en '{settings.QDRANT_COLLECTION}'.")
    print(f"   Frames JPG guardados en: {FRAMES_DIR}/{args.tecnica_id}")

    # 4. Verificación rápida
    info = client.get_collection(settings.QDRANT_COLLECTION)
    print(f"   Total puntos en colección: {info.points_count}")


if __name__ == "__main__":
    main()
