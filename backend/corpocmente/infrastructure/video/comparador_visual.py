import logging
import os
from typing import Any, Dict, List

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _leer_frame_con_cache(
    cap: cv2.VideoCapture,
    frame_idx: int,
    cache: Dict[int, Any],
    fallback_shape: tuple,
):
    if frame_idx in cache:
        return cache[frame_idx]

    cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
    ok, frame = cap.read()

    if not ok or frame is None:
        frame = np.full(fallback_shape, 25, dtype=np.uint8)

    cache.clear()
    cache[frame_idx] = frame
    return frame


def generar_video_comparacion(
    video_alumno: str,
    video_maestro: str,
    alineacion: List[Dict[str, Any]],
    output_path: str,
    fps: int = 24,
    width: int = 1280,
    height: int = 720,
) -> str:
    """
    Genera un video side-by-side:
    izquierda = maestro
    derecha = alumno
    usando la alineación DTW frame por frame.
    """
    if not alineacion:
        raise ValueError("No hay alineación para generar video comparativo.")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    cap_maestro = cv2.VideoCapture(video_maestro)
    cap_alumno = cv2.VideoCapture(video_alumno)

    if not cap_maestro.isOpened():
        raise ValueError(f"No se pudo abrir video del maestro: {video_maestro}")

    if not cap_alumno.isOpened():
        raise ValueError(f"No se pudo abrir video del alumno: {video_alumno}")

    half_w = width // 2
    fallback_shape = (height, half_w, 3)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, float(fps), (width, height))

    if not out.isOpened():
        cap_maestro.release()
        cap_alumno.release()
        raise RuntimeError(f"No se pudo crear el video de salida: {output_path}")

    cache_maestro: Dict[int, Any] = {}
    cache_alumno: Dict[int, Any] = {}

    try:
        for pair in alineacion:
            idx_maestro = int(pair.get("frame_maestro_idx", 0))
            idx_alumno = int(pair.get("frame_alumno_idx", 0))
            sim = float(pair.get("similitud_frame", 0.0))

            frame_m = _leer_frame_con_cache(
                cap_maestro,
                idx_maestro,
                cache_maestro,
                fallback_shape,
            )
            frame_a = _leer_frame_con_cache(
                cap_alumno,
                idx_alumno,
                cache_alumno,
                fallback_shape,
            )

            frame_m = cv2.resize(frame_m, (half_w, height))
            frame_a = cv2.resize(frame_a, (half_w, height))

            canvas = np.hstack([frame_m, frame_a])

            if sim >= 0.75:
                color = (0, 255, 0)
                etiqueta = "BUENA SIMILITUD"
            elif sim >= 0.50:
                color = (0, 255, 255)
                etiqueta = "SIMILITUD MEDIA"
            else:
                color = (0, 0, 255)
                etiqueta = "DISCREPANCIA ALTA"

            cv2.rectangle(canvas, (0, 0), (width - 1, height - 1), color, 3)

            texto = (
                f"Maestro #{idx_maestro} | Alumno #{idx_alumno} | "
                f"Similitud: {sim:.2f} | {etiqueta}"
            )

            cv2.rectangle(canvas, (0, height - 42), (width, height), (0, 0, 0), -1)
            cv2.putText(
                canvas,
                texto,
                (10, height - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.58,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

            out.write(canvas)

    finally:
        cap_maestro.release()
        cap_alumno.release()
        out.release()

    return output_path
