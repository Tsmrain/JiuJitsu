import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from corpocmente.domain.biomechanics.dtw_comparator import (
    comparar_secuencias_con_dtw,
    resumen_alineacion,
)
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.config import settings
from corpocmente.infrastructure.video.comparador_visual import generar_video_comparacion

logger = logging.getLogger(__name__)

STORAGE_DIR = settings.comparaciones_dir
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

TABLE = "comparaciones_video"

# Fallback en memoria si la tabla aún no existe en PostgREST.
_STORE: Dict[str, Dict[str, Any]] = {}


def _db() -> PostgrestClient:
    return PostgrestClient()


def rutas_comparacion(comparacion_id: str):
    return (
        STORAGE_DIR / f"{comparacion_id}_alumno.mp4",
        STORAGE_DIR / f"{comparacion_id}_maestro.mp4",
        STORAGE_DIR / f"{comparacion_id}_comparacion.mp4",
    )


def crear_comparacion(
    comparacion_id: Optional[str] = None,
    tecnica_id: Optional[str] = None,
    idioma: str = "es",
    persona_idx_alumno: int = 0,
    persona_idx_maestro: int = 0,
    alumno_id: Optional[str] = None,
    token: Optional[str] = None,
    video_alumno_nombre: Optional[str] = None,
    video_maestro_nombre: Optional[str] = None,
) -> str:
    comparacion_id = comparacion_id or str(uuid.uuid4())

    data = {
        "id": comparacion_id,
        "alumno_id": alumno_id,
        "video_alumno_nombre": video_alumno_nombre,
        "video_maestro_nombre": video_maestro_nombre,
        "estado": "procesando",
        "tecnica_id": tecnica_id,
        "idioma": idioma,
        "persona_idx_alumno": persona_idx_alumno,
        "persona_idx_maestro": persona_idx_maestro,
        "score_similitud": None,
        "dtw_distance": None,
        "dtw_normalizado": None,
        "frame_alumno_critico": None,
        "frame_maestro_critico": None,
        "articulaciones_criticas": None,
        "alineacion": None,
        "error_message": None,
    }

    try:
        _db().post(TABLE, data, token=token)
    except Exception as exc:
        logger.warning("No se pudo insertar comparación en Postgres, usando memoria: %s", exc)
        _STORE[comparacion_id] = data

    return comparacion_id


def _obtener_row(comparacion_id: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        rows = _db().get(TABLE, {"id": f"eq.{comparacion_id}"}, token=token)
        if rows:
            return rows[0]
    except Exception as exc:
        logger.warning("No se pudo leer comparación de Postgres: %s", exc)

    return _STORE.get(comparacion_id)


def _actualizar_row(comparacion_id: str, data: Dict[str, Any], token: Optional[str] = None) -> None:
    data = dict(data)
    data["actualizado_en"] = "NOW()"

    try:
        _db().patch(TABLE, {"id": f"eq.{comparacion_id}"}, data, token=token)
    except Exception as exc:
        logger.warning("No se pudo actualizar comparación en Postgres: %s", exc)

    if comparacion_id in _STORE:
        _STORE[comparacion_id].update(data)


def procesar_comparacion_video_a_video(
    comparacion_id: str,
    tecnica_id: Optional[str] = None,
    idioma: str = "es",
    persona_idx_alumno: int = 0,
    persona_idx_maestro: int = 0,
    token: Optional[str] = None,
    track_id_alumno: Optional[int] = None,
    track_id_maestro: Optional[int] = None,
    tracker_name: str = "bjj_botsort.yaml",
) -> None:
    """
    Tarea de fondo:
    1. Lee videos del alumno y maestro.
    2. Extrae secuencias de keypoints con YOLO Pose + tracking persistente.
    3. Valida track_id y cobertura mínima.
    4. Compara con DTW.
    5. Genera video side-by-side.
    6. Persiste resultado.
    """
    path_alumno, path_maestro, path_output = rutas_comparacion(comparacion_id)

    try:
        _actualizar_row(comparacion_id, {"estado": "procesando"}, token=token)

        if not path_alumno.exists():
            raise FileNotFoundError(f"Video del alumno no encontrado: {path_alumno}")

        if not path_maestro.exists():
            raise FileNotFoundError(f"Video del maestro no encontrado: {path_maestro}")

        from corpocmente.config import settings
        frame_stride = max(1, int(getattr(settings, "FRAME_STRIDE", 1)))
        yolo = YOLOPoseAdapter()

        logger.info("Extrayendo pose del alumno: %s (stride=%d, tracker=%s)", path_alumno, frame_stride, tracker_name)
        res_alumno = yolo.extraer_secuencia(
            str(path_alumno),
            persona_idx_inicial=persona_idx_alumno,
            frame_stride=frame_stride,
            tracker_name=tracker_name,
            track_id_objetivo=track_id_alumno,
        )

        logger.info("Extrayendo pose del maestro: %s (stride=%d, tracker=%s)", path_maestro, frame_stride, tracker_name)
        res_maestro = yolo.extraer_secuencia(
            str(path_maestro),
            persona_idx_inicial=persona_idx_maestro,
            frame_stride=frame_stride,
            tracker_name=tracker_name,
            track_id_objetivo=track_id_maestro,
        )

        tracking_alumno = None
        tracking_maestro = None
        if isinstance(res_alumno, dict):
            secuencia_alumno = res_alumno.get("secuencia_kpts", [])
            cobertura_alumno = float(res_alumno.get("cobertura", 0.0))
            frame_idxs_alumno = res_alumno.get("frame_idxs")
            frames_detectados_alumno = int(res_alumno.get("frames_con_persona", 0))
            total_frames_alumno = int(res_alumno.get("total_frames", len(secuencia_alumno)))
            tracking_alumno = res_alumno.get("tracking_stats")
        else:
            secuencia_alumno = res_alumno
            cobertura_alumno = 1.0
            frame_idxs_alumno = None
            frames_detectados_alumno = len(secuencia_alumno)
            total_frames_alumno = len(secuencia_alumno)

        if isinstance(res_maestro, dict):
            secuencia_maestro = res_maestro.get("secuencia_kpts", [])
            cobertura_maestro = float(res_maestro.get("cobertura", 0.0))
            frame_idxs_maestro = res_maestro.get("frame_idxs")
            frames_detectados_maestro = int(res_maestro.get("frames_con_persona", 0))
            total_frames_maestro = int(res_maestro.get("total_frames", len(secuencia_maestro)))
            tracking_maestro = res_maestro.get("tracking_stats")
        else:
            secuencia_maestro = res_maestro
            cobertura_maestro = 1.0
            frame_idxs_maestro = None
            frames_detectados_maestro = len(secuencia_maestro)
            total_frames_maestro = len(secuencia_maestro)

        if comparacion_id in _STORE:
            _STORE[comparacion_id].update({
                "tracking_alumno": tracking_alumno,
                "tracking_maestro": tracking_maestro,
            })

        if (
            path_alumno.resolve() == path_maestro.resolve()
            and tracking_alumno
            and tracking_maestro
            and tracking_alumno.get("id_principal") is not None
            and tracking_alumno.get("id_principal") == tracking_maestro.get("id_principal")
        ):
            raise ValueError(
                f"Colisión de track_id={tracking_alumno.get('id_principal')} para alumno y maestro en el mismo video."
            )

        if tracking_alumno and tracking_alumno.get("perdido_definitivamente_en_frame") is not None:
            raise ValueError(
                f"El track del alumno (ID={tracking_alumno.get('id_principal')}) se perdió en el frame "
                f"{tracking_alumno.get('perdido_definitivamente_en_frame')}. Ajusta la configuración del tracker o recorta el video."
            )

        if tracking_maestro and tracking_maestro.get("perdido_definitivamente_en_frame") is not None:
            raise ValueError(
                f"El track del maestro (ID={tracking_maestro.get('id_principal')}) se perdió en el frame "
                f"{tracking_maestro.get('perdido_definitivamente_en_frame')}. Ajusta la configuración del tracker o recorta el video."
            )

        if tracking_alumno:
            cobertura_alumno_eval = float(tracking_alumno.get("cobertura_principal", cobertura_alumno))
        else:
            cobertura_alumno_eval = cobertura_alumno

        if tracking_maestro:
            cobertura_maestro_eval = float(tracking_maestro.get("cobertura_principal", cobertura_maestro))
        else:
            cobertura_maestro_eval = cobertura_maestro

        if not secuencia_alumno:
            raise ValueError("No se detectó esqueleto válido en el video del alumno.")

        if not secuencia_maestro:
            raise ValueError("No se detectó esqueleto válido en el video del maestro.")

        min_cobertura = float(getattr(settings, "MIN_COBERTURA_COMPARACION", 0.40))

        if cobertura_alumno_eval < min_cobertura:
            logger.warning(
                "Cobertura insuficiente: %.2f%% (umbral=%.2f%%) en video=%s. "
                "Frames totales=%d, detectados=%d, persona_idx=%d",
                cobertura_alumno_eval * 100,
                min_cobertura * 100,
                path_alumno,
                total_frames_alumno,
                frames_detectados_alumno,
                persona_idx_alumno,
            )
            raise ValueError(
                f"Cobertura insuficiente en alumno: {cobertura_alumno_eval * 100:.1f}%. "
                f"Se requiere al menos {min_cobertura * 100:.0f}%."
            )

        if cobertura_maestro_eval < min_cobertura:
            logger.warning(
                "Cobertura insuficiente: %.2f%% (umbral=%.2f%%) en video=%s. "
                "Frames totales=%d, detectados=%d, persona_idx=%d",
                cobertura_maestro_eval * 100,
                min_cobertura * 100,
                path_maestro,
                total_frames_maestro,
                frames_detectados_maestro,
                persona_idx_maestro,
            )
            raise ValueError(
                f"Cobertura insuficiente en maestro: {cobertura_maestro_eval * 100:.1f}%. "
                f"Se requiere al menos {min_cobertura * 100:.0f}%."
            )

        logger.info("Comparando secuencias con DTW...")
        comparacion = comparar_secuencias_con_dtw(
            secuencia_maestro=secuencia_maestro,
            secuencia_alumno=secuencia_alumno,
            window=None,
            top_k_articulaciones=3,
            frame_idxs_maestro=frame_idxs_maestro,
            frame_idxs_alumno=frame_idxs_alumno,
        )

        logger.info("Generando video comparativo: %s", path_output)
        generar_video_comparacion(
            video_alumno=str(path_alumno),
            video_maestro=str(path_maestro),
            alineacion=comparacion["alineacion"],
            output_path=str(path_output),
            fps=24,
            width=1280,
            height=720,
        )

        alineacion_para_guardar = [
            {**pair, "video_idx": index}
            for index, pair in enumerate(comparacion["alineacion"])
        ]
        if len(alineacion_para_guardar) > 2000:
            alineacion_para_guardar = resumen_alineacion(alineacion_para_guardar, max_items=240)

        if comparacion_id in _STORE:
            _STORE[comparacion_id].update({
                "tracking_alumno": tracking_alumno,
                "tracking_maestro": tracking_maestro,
            })

        _actualizar_row(
            comparacion_id,
            {
                "estado": "completado",
                "score_similitud": comparacion["score_similitud"],
                "dtw_distance": comparacion["dtw_distance"],
                "dtw_normalizado": comparacion["dtw_normalizado"],
                "frame_alumno_critico": comparacion["frame_alumno_critico"],
                "frame_maestro_critico": comparacion["frame_maestro_critico"],
                "articulaciones_criticas": comparacion["articulaciones_criticas"],
                "alineacion": alineacion_para_guardar,
                "video_comparacion_path": str(path_output),
                "error_message": None,
            },
            token=token,
        )

    except Exception as exc:
        logger.exception("Falló comparación video a video %s: %s", comparacion_id, exc)
        _actualizar_row(
            comparacion_id,
            {
                "estado": "error_procesamiento",
                "error_message": str(exc),
            },
            token=token,
        )


def obtener_comparacion(comparacion_id: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    row = _obtener_row(comparacion_id, token=token)
    if not row:
        return None

    output = dict(row)

    video_path = output.get("video_comparacion_path")
    video_disponible = bool(video_path and os.path.exists(str(video_path)))

    output.pop("video_alumno_path", None)
    output.pop("video_maestro_path", None)
    output.pop("video_comparacion_path", None)

    output["video_disponible"] = video_disponible
    output["video_url"] = (
        f"/api/v1/comparaciones/{comparacion_id}/video"
        if video_disponible and output.get("estado") == "completado"
        else None
    )

    return output
