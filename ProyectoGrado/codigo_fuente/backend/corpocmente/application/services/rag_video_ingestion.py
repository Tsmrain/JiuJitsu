import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import cv2
import requests

from corpocmente.application.use_cases.ingest_knowledge_use_case import IngestKnowledgeUseCase
from corpocmente.config import settings

logger = logging.getLogger(__name__)

STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "rag_frames"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
BATCH_SIZE = 4
EXPECTED_DIM = 2048

NGROK_HEADERS = {
    "ngrok-skip-browser-warning": "1",
    "User-Agent": "CorpocmenteBackend/1.0",
}


def _worker_url() -> str:
    url = (settings.COLAB_TUNNEL_URL or "").strip()
    if not url or "placeholder" in url or url.startswith("https://placeholder"):
        raise RuntimeError(
            "COLAB_TUNNEL_URL no está configurada. No se pueden vectorizar frames."
        )
    return url.rstrip("/")


def _mime_for_image(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    if ext in (".tif", ".tiff"):
        return "image/tiff"
    if ext == ".bmp":
        return "image/bmp"
    return "image/jpeg"


def _muestrear_frames(
    video_path: str,
    output_dir: Path,
    sample_seconds: float = 2.0,
    max_frames: int = 30,
) -> List[Dict[str, Any]]:
    """
    Extrae frames cada X segundos y los guarda como JPG.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0

    frame_interval = max(1, int(round(fps * sample_seconds)))

    output_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    frame_idx = 0

    try:
        while len(frames) < max_frames:
            ok, frame = cap.read()
            if not ok:
                break

            if frame_idx % frame_interval == 0:
                timestamp = frame_idx / fps
                filename = f"frame_{frame_idx:06d}.jpg"
                filepath = output_dir / filename

                cv2.imwrite(str(filepath), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

                frames.append(
                    {
                        "frame_idx": frame_idx,
                        "timestamp": float(timestamp),
                        "media_path": str(filepath.resolve()),
                        "filename": filename,
                    }
                )

            frame_idx += 1
    finally:
        cap.release()

    return frames


def _validar_embedding_data(data: Dict[str, Any], esperado: int) -> None:
    embeddings = data.get("embeddings") or []
    chunks = data.get("chunks") or []

    if len(embeddings) != esperado:
        raise ValueError(
            f"El worker devolvió {len(embeddings)} embeddings, pero se esperaban {esperado}."
        )

    if len(chunks) != esperado:
        raise ValueError(
            f"El worker devolvió {len(chunks)} chunks, pero se esperaban {esperado}."
        )

    for i, emb in enumerate(embeddings):
        if not isinstance(emb, list) or len(emb) != EXPECTED_DIM:
            raise ValueError(
                f"Embedding {i} inválido: dimensión {len(emb) if isinstance(emb, list) else 'no-list'}. "
                f"Se esperaban {EXPECTED_DIM}."
            )


def indexar_frames_video_rag(
    tecnica_id: UUID | str,
    video_path: str,
    tecnica_nombre: str,
    profesor_id: Optional[str] = None,
    sucursal_id: Optional[str] = None,
    sample_seconds: float = 2.0,
    max_frames: int = 30,
) -> int:
    """
    Indexa frames del video del profesor como evidencia visual en Qdrant/Postgres.

    Esto es lo que convierte tu RAG en multimodal real:
    imagen -> embedding 2048 -> Qdrant -> recuperación visual.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video no encontrado: {video_path}")

    ext = os.path.splitext(video_path)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError(f"Extensión de video no soportada: {ext}")

    worker_url = _worker_url()
    tecnica_id_str = str(tecnica_id)

    output_dir = STORAGE_DIR / tecnica_id_str
    frames = _muestrear_frames(
        video_path=video_path,
        output_dir=output_dir,
        sample_seconds=sample_seconds,
        max_frames=max_frames,
    )

    if not frames:
        logger.warning("No se extrajeron frames del video: %s", video_path)
        return 0

    use_case = IngestKnowledgeUseCase()
    total_indexados = 0

    batches = [frames[i : i + BATCH_SIZE] for i in range(0, len(frames), BATCH_SIZE)]

    for batch in batches:
        archivos = []
        file_handles = []
        labels = []
        texts = []

        try:
            for item in batch:
                path = Path(item["media_path"])
                fh = open(path, "rb")
                file_handles.append(fh)

                label = (
                    f"{tecnica_nombre} | frame {item['frame_idx']} | "
                    f"minuto {item['timestamp'] / 60:.2f}"
                )

                archivos.append(
                    (
                        "files",
                        (
                            item["filename"],
                            fh,
                            _mime_for_image(path),
                        ),
                    )
                )

                labels.append(label)
                texts.append(label)

            response = requests.post(
                f"{worker_url}/embed_images",
                data={
                    "labels": "\n".join(labels),
                    "texts_json": json.dumps(texts, ensure_ascii=False),
                },
                files=archivos,
                headers=NGROK_HEADERS,
                timeout=240,
            )

            if response.status_code == 404:
                raise RuntimeError(
                    "El worker no expone /embed_images. Actualiza el Colab Worker multimodal."
                )

            response.raise_for_status()
            embed_data = response.json()
            _validar_embedding_data(embed_data, esperado=len(batch))

            metadata_por_chunk = [
                {
                    "modalidad": "imagen",
                    "media_path": item["media_path"],
                    "media_url": f"/api/v1/conocimiento/media/{tecnica_id_str}/{item['filename']}",
                    "video_path": video_path,
                    "timestamp_seconds": item["timestamp"],
                    "frame_idx": item["frame_idx"],
                    "contenido_texto": (
                        f"Video del profesor — {tecnica_nombre} — "
                        f"minuto {item['timestamp'] / 60:.2f} — frame {item['frame_idx']}"
                    ),
                    "texto_asociado": (
                        f"{tecnica_nombre}. Postura de referencia del profesor. "
                        f"Ejecución en minuto {item['timestamp'] / 60:.2f}, frame {item['frame_idx']}."
                    ),
                }
                for item in batch
            ]

            use_case.execute(
                tecnica_id=tecnica_id_str,
                contenido_texto="\n".join(labels),
                profesor_id=profesor_id,
                sucursal_id=sucursal_id,
                fuente_tipo="video",
                fuente_nombre=f"Video de referencia — {tecnica_nombre}",
                fuente_referencia="Fotogramas muestreados del video del profesor",
                fuente_url=None,
                alcance="tecnica",
                embedding_data=embed_data,
                metadata_por_chunk=metadata_por_chunk,
            )

            total_indexados += len(batch)
            logger.info(
                "Indexados %s frames visuales para técnica %s",
                len(batch),
                tecnica_id_str,
            )

        except Exception as exc:
            logger.warning("No se pudo indexar un lote de frames visuales: %s", exc)
        finally:
            for fh in file_handles:
                try:
                    fh.close()
                except Exception:
                    pass

    logger.info(
        "Ingesta visual de video completada: %s frames para técnica %s",
        total_indexados,
        tecnica_id_str,
    )

    return total_indexados
