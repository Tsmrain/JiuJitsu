"""Comprueba que Qwen alinee una imagen con su descripción frente a una distractora.

Uso desde codigo_fuente/backend:
    ./venv/bin/python scripts/smoke_qwen_crossmodal.py --image /ruta/agarre.jpg
"""
import argparse
import json
import math
import mimetypes
import sys
from pathlib import Path

import requests

from corpocmente.config import settings

EXPECTED_DIM = 2048
HEADERS = {
    "ngrok-skip-browser-warning": "1",
    "User-Agent": "CorpocmenteBackend/1.0",
}


def _embedding(data: dict, label: str) -> list[float]:
    embeddings = data.get("embeddings") or []
    if not embeddings or len(embeddings[0]) != EXPECTED_DIM:
        raise ValueError(f"{label}: Qwen debe devolver un vector de {EXPECTED_DIM} dimensiones.")
    vector = [float(value) for value in embeddings[0]]
    if not all(math.isfinite(value) for value in vector):
        raise ValueError(f"{label}: el vector contiene valores no finitos.")
    return vector


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(value * value for value in left))
    norm_right = math.sqrt(sum(value * value for value in right))
    if not norm_left or not norm_right:
        raise ValueError("Qwen devolvió un vector de norma cero.")
    return dot / (norm_left * norm_right)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path, help="Imagen de una técnica de Jiu-Jitsu")
    parser.add_argument(
        "--positive",
        default="Jiu-Jitsu: control del brazo y extensión del codo para finalizar un armbar desde guardia.",
    )
    parser.add_argument(
        "--negative",
        default="Una persona realiza una sentadilla con barra en un gimnasio.",
    )
    args = parser.parse_args()
    worker_url = (settings.COLAB_TUNNEL_URL or "").strip().rstrip("/")
    if not worker_url or "placeholder" in worker_url:
        print("Configura COLAB_TUNNEL_URL con el worker activo de Colab.", file=sys.stderr)
        return 2
    if not args.image.is_file():
        print(f"No existe la imagen: {args.image}", file=sys.stderr)
        return 2

    try:
        mime_type = mimetypes.guess_type(args.image.name)[0] or "image/jpeg"
        with args.image.open("rb") as image_file:
            image_response = requests.post(
                f"{worker_url}/embed_images",
                data={"labels": args.positive, "texts_json": json.dumps([args.positive])},
                files={"files": (args.image.name, image_file, mime_type)},
                headers=HEADERS,
                timeout=180,
            )
        image_response.raise_for_status()
        image_vector = _embedding(image_response.json(), "Imagen")

        def embed_text(text: str) -> list[float]:
            response = requests.post(
                f"{worker_url}/embed_text",
                data={"texto": text},
                headers=HEADERS,
                timeout=120,
            )
            response.raise_for_status()
            return _embedding(response.json(), "Texto")

        positive_score = _cosine(image_vector, embed_text(args.positive))
        negative_score = _cosine(image_vector, embed_text(args.negative))
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        print(f"La comprobación no se completó: {exc}", file=sys.stderr)
        return 2

    print(f"Similitud imagen ↔ descripción: {positive_score:.4f}")
    print(f"Similitud imagen ↔ distractor:   {negative_score:.4f}")
    if positive_score <= negative_score:
        print("FALLO: el worker no priorizó la descripción relacionada con la imagen.")
        return 1
    print("OK: la imagen se alinea mejor con la descripción relacionada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
