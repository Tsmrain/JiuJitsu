import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    from dtaidistance import dtw_ndim
except Exception:
    dtw_ndim = None
    logger.warning("dtaidistance no disponible. Se usará fallback DTW en Python/NumPy.")

COCO_KEYPOINT_COUNT = 17
COORD_DIMS = COCO_KEYPOINT_COUNT * 3


def _limpiar_secuencia(secuencia: List[List[float]]) -> List[List[float]]:
    if not secuencia:
        raise ValueError("La secuencia está vacía.")

    arr = np.asarray(secuencia, dtype=np.float32)

    if arr.ndim != 2:
        raise ValueError(f"Secuencia inválida. Se esperaba 2D, se recibió shape={arr.shape}.")

    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return arr.tolist()


def _distancia_local(a: List[float], b: List[float]) -> float:
    av = np.asarray(a, dtype=np.float32)
    bv = np.asarray(b, dtype=np.float32)

    if av.shape != bv.shape:
        raise ValueError(f"Dimensiones incompatibles en DTW local: {av.shape} vs {bv.shape}")

    return float(np.linalg.norm(av - bv))


def _similitud_frame(a: List[float], b: List[float]) -> float:
    """
    Similitud combinada:
    - distancia euclidiana normalizada por saturación
    - coseno sobre componentes no nulas
    """
    av = np.asarray(a, dtype=np.float32)
    bv = np.asarray(b, dtype=np.float32)

    if av.shape != bv.shape:
        raise ValueError(f"Dimensiones incompatibles: {av.shape} vs {bv.shape}")

    dist = float(np.linalg.norm(av - bv))
    if dist < 1e-6:
        return 1.0

    base = 1.0 / (1.0 + dist)

    mask = (np.abs(av) > 1e-6) | (np.abs(bv) > 1e-6)
    cos = 0.0

    if int(mask.sum()) > 0:
        av_valid = av[mask]
        bv_valid = bv[mask]

        norm_a = float(np.linalg.norm(av_valid))
        norm_b = float(np.linalg.norm(bv_valid))

        if norm_a > 1e-9 and norm_b > 1e-9:
            cos = float(np.dot(av_valid, bv_valid) / (norm_a * norm_b))
            cos = max(0.0, min(1.0, cos))

    return float(0.75 * base + 0.25 * cos)


def detectar_articulaciones_criticas(
    vec_maestro: List[float],
    vec_alumno: List[float],
    top_k: int = 3,
) -> List[int]:
    """
    Asume que los primeros 51 dims son x,y,conf para 17 keypoints COCO.
    Devuelve índices de articulación con mayor discrepancia.
    """
    a = np.asarray(vec_maestro, dtype=np.float32)
    b = np.asarray(vec_alumno, dtype=np.float32)

    if len(a) < COORD_DIMS or len(b) < COORD_DIMS:
        return []

    diffs: List[Tuple[float, int]] = []

    for joint_idx in range(COCO_KEYPOINT_COUNT):
        base = joint_idx * 3

        ax = float(a[base])
        ay = float(a[base + 1])
        ac = float(a[base + 2])

        bx = float(b[base])
        by = float(b[base + 1])
        bc = float(b[base + 2])

        # Si alguno está muy ocluido/no confiable, ignorar.
        if ac < 0.2 or bc < 0.2:
            continue

        d = math.hypot(ax - bx, ay - by)
        diffs.append((d, joint_idx))

    if not diffs:
        return []

    diffs.sort(key=lambda x: x[0], reverse=True)
    max_diff = diffs[0][0]

    if max_diff <= 1e-6:
        return []

    threshold = max(1e-6, max_diff * 0.05)

    return [joint_idx for d, joint_idx in diffs[:top_k] if d >= threshold]


def _warping_path_fallback(
    s1: List[List[float]],
    s2: List[List[float]],
    window: Optional[int] = None,
) -> Tuple[float, List[Tuple[int, int]]]:
    n = len(s1)
    m = len(s2)

    INF = float("inf")

    D = np.full((n + 1, m + 1), INF, dtype=np.float64)
    B = np.zeros((n + 1, m + 1), dtype=np.int8)

    D[0, 0] = 0.0

    for i in range(1, n + 1):
        j_start = 1
        j_end = m

        if window is not None:
            j_start = max(1, i - window)
            j_end = min(m, i + window)

        for j in range(j_start, j_end + 1):
            cost = float(np.linalg.norm(
                np.asarray(s1[i - 1], dtype=np.float32)
                -
                np.asarray(s2[j - 1], dtype=np.float32)
            ))

            up = D[i - 1, j]
            left = D[i, j - 1]
            diag = D[i - 1, j - 1]

            best = min(up, left, diag)

            if best == diag:
                B[i, j] = 3
            elif best == up:
                B[i, j] = 1
            else:
                B[i, j] = 2

            D[i, j] = best + cost

    if not np.isfinite(D[n, m]) and window is not None:
        return _warping_path_fallback(s1, s2, window=None)

    i, j = n, m
    path: List[Tuple[int, int]] = []

    while i > 0 or j > 0:
        path.append((i - 1, j - 1))

        if i == 0:
            j -= 1
        elif j == 0:
            i -= 1
        else:
            b = int(B[i, j])

            if b == 3:
                i -= 1
                j -= 1
            elif b == 1:
                i -= 1
            elif b == 2:
                j -= 1
            else:
                up = D[i - 1, j]
                left = D[i, j - 1]
                diag = D[i - 1, j - 1]

                best = min(up, left, diag)

                if best == diag:
                    i -= 1
                    j -= 1
                elif best == up:
                    i -= 1
                else:
                    j -= 1

    path.reverse()
    return float(D[n, m]), path


def _dtw_distance_and_path(
    s1: List[List[float]],
    s2: List[List[float]],
    window: Optional[int] = None,
) -> Tuple[float, List[Tuple[int, int]]]:
    if dtw_ndim is not None:
        try:
            arr1 = np.asarray(s1, dtype=np.float64)
            arr2 = np.asarray(s2, dtype=np.float64)
            distance = float(dtw_ndim.distance(arr1, arr2, window=window))
            raw_path = dtw_ndim.warping_path(arr1, arr2, window=window)
            path = [(int(i), int(j)) for i, j in raw_path]
            return distance, path
        except Exception as exc:
            logger.warning("dtaidistance falló, usando fallback DTW: %s", exc)

    return _warping_path_fallback(s1, s2, window=window)


def comparar_secuencias_con_dtw(
    secuencia_maestro: List[List[float]],
    secuencia_alumno: List[List[float]],
    window: Optional[int] = None,
    top_k_articulaciones: int = 3,
    use_fast: bool = True,
    frame_idxs_maestro: Optional[List[int]] = None,
    frame_idxs_alumno: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Compara dos secuencias biomecánicas usando DTW multidimensional.

    Devuelve:
    - métricas globales
    - frame crítico (mapeado a frame real de video si se proveen frame_idxs)
    - alineación completa frame por frame con seq_idx y frame_idx real
    """
    sec_maestro = _limpiar_secuencia(secuencia_maestro)
    sec_alumno = _limpiar_secuencia(secuencia_alumno)

    if not sec_maestro:
        raise ValueError("La secuencia del maestro está vacía.")

    if not sec_alumno:
        raise ValueError("La secuencia del alumno está vacía.")

    real_f_maestro = frame_idxs_maestro if frame_idxs_maestro is not None else list(range(len(sec_maestro)))
    real_f_alumno = frame_idxs_alumno if frame_idxs_alumno is not None else list(range(len(sec_alumno)))
    if len(real_f_maestro) != len(sec_maestro):
        raise ValueError("frame_idxs_maestro debe tener un índice por cada frame de la secuencia maestro.")
    if len(real_f_alumno) != len(sec_alumno):
        raise ValueError("frame_idxs_alumno debe tener un índice por cada frame de la secuencia alumno.")

    dtw_distance, warp_path = _dtw_distance_and_path(
        sec_maestro,
        sec_alumno,
        window=window,
    )

    max_len = max(len(sec_maestro), len(sec_alumno))
    dtw_normalizado = dtw_distance / max_len if max_len > 0 else 0.0

    alineacion: List[Dict[str, Any]] = []
    scores_por_paso: List[float] = []

    peor_sim = 2.0
    seq_maestro_critico = 0
    seq_alumno_critico = 0
    frame_maestro_critico = int(real_f_maestro[0]) if real_f_maestro else 0
    frame_alumno_critico = int(real_f_alumno[0]) if real_f_alumno else 0
    articulaciones_criticas_globales: List[int] = []

    for i, j in warp_path:
        kp_maestro = sec_maestro[i]
        kp_alumno = sec_alumno[j]

        distancia_local = _distancia_local(kp_maestro, kp_alumno)
        similitud = _similitud_frame(kp_maestro, kp_alumno)
        artes = detectar_articulaciones_criticas(
            kp_maestro,
            kp_alumno,
            top_k=top_k_articulaciones,
        )

        scores_por_paso.append(similitud)

        real_m_idx = int(real_f_maestro[i]) if i < len(real_f_maestro) else int(i)
        real_a_idx = int(real_f_alumno[j]) if j < len(real_f_alumno) else int(j)

        alineacion.append(
            {
                "seq_maestro_idx": int(i),
                "seq_alumno_idx": int(j),
                "frame_maestro_idx": real_m_idx,
                "frame_alumno_idx": real_a_idx,
                "distancia_local": round(distancia_local, 6),
                "similitud_frame": round(similitud, 6),
                "articulaciones_criticas": artes,
            }
        )

        if similitud < peor_sim:
            peor_sim = similitud
            seq_maestro_critico = int(i)
            seq_alumno_critico = int(j)
            frame_maestro_critico = real_m_idx
            frame_alumno_critico = real_a_idx
            articulaciones_criticas_globales = artes

    if scores_por_paso:
        scores_ord = sorted(scores_por_paso)
        n = len(scores_ord)

        # Descarta el 5% peor para robustez ante frames de transición/oclusión.
        corte = max(1, int(n * 0.05)) if n > 20 else 0
        scores_utiles = scores_ord[corte:] if corte > 0 else scores_ord

        score_similitud = float(np.mean(scores_utiles)) * 100.0
    else:
        score_similitud = 0.0

    return {
        "dtw_distance": round(float(dtw_distance), 6),
        "dtw_normalizado": round(float(dtw_normalizado), 6),
        "score_similitud": round(float(score_similitud), 2),
        "path_length": len(warp_path),
        "seq_maestro_critico": seq_maestro_critico,
        "seq_alumno_critico": seq_alumno_critico,
        "frame_maestro_critico": frame_maestro_critico,
        "frame_alumno_critico": frame_alumno_critico,
        "articulaciones_criticas": articulaciones_criticas_globales,
        "alineacion": alineacion,
        "n_frames_maestro": len(sec_maestro),
        "n_frames_alumno": len(sec_alumno),
    }


def resumen_alineacion(
    alineacion: List[Dict[str, Any]],
    max_items: int = 120,
) -> List[Dict[str, Any]]:
    """
    Reduce la alineación para responses/API sin perder puntos críticos.
    """
    if not alineacion:
        return []

    if len(alineacion) <= max_items:
        return alineacion

    indices = np.linspace(0, len(alineacion) - 1, max_items, dtype=int)
    indices = sorted(set(int(x) for x in indices))

    return [alineacion[i] for i in indices]
