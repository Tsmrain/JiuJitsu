"""
Comparador de secuencias de esqueletos usando Dynamic Time Warping (DTW).

DTW alinea dos secuencias temporales (el movimiento del maestro y del alumno)
incluso si tienen distinta duración o ritmo, encontrando la distancia mínima
de alineación. Crítico para técnicas de Jiu-Jitsu (movimientos continuos).

NOTA: dtaidistance.dtw es univariado. Para series multivariadas (N, D) hay
que usar dtaidistance.dtw_ndim (n-dimensional).
"""

import numpy as np
from typing import List, Dict
from dtaidistance import dtw_ndim  # ← CORREGIDO

from corpocmente.domain.biomechanics.pose_normalizer import (
    normalizar,
    similitud_esqueletos,
    articulaciones_criticas,
)


def comparar_secuencias_con_dtw(
    secuencia_maestro: List[List[float]],
    secuencia_alumno: List[List[float]],
    use_fast: bool = True,
    window: int = None,
) -> Dict[str, object]:
    """
    Compara dos secuencias de esqueletos (listas de keypoints133) usando DTW.

    Args:
        secuencia_maestro: Lista de keypoints crudos (133 dims) del video del maestro.
        secuencia_alumno:  Lista de keypoints crudos (133 dims) del video del alumno.
        use_fast:          Usar implementación C de dtaidistance (recomendado).
        window:            Ventana Sakoe-Chiba opcional. None = DTW completo.

    Returns:
        {
          "dtw_distance": float,
          "dtw_normalizado": float,
          "score_similitud": float,   # [0, 100]
          "path_length": int,
          "frame_maestro_critico": int,
          "frame_alumno_critico": int,
          "articulaciones_criticas": [int, ...],
          "n_frames_maestro": int,
          "n_frames_alumno": int,
        }
    """
    if not secuencia_maestro or not secuencia_alumno:
        raise ValueError("Ambas secuencias deben contener al menos un frame.")

    # 1. Normalizar cada frame a su vector canónico de 46 dims
    vectores_maestro = np.array(
        [normalizar(kp)["vector"] for kp in secuencia_maestro],
        dtype=np.float64,
    )
    vectores_alumno = np.array(
        [normalizar(kp)["vector"] for kp in secuencia_alumno],
        dtype=np.float64,
    )

    # 2. Calcular distancia DTW n-dimensional
    dtw_func = dtw_ndim.distance_fast if use_fast else dtw_ndim.distance

    if window is not None:
        dtw_distance = float(dtw_func(vectores_maestro, vectores_alumno, window=window))
    else:
        dtw_distance = float(dtw_func(vectores_maestro, vectores_alumno))

    # 3. Camino de alineación
    path = dtw_ndim.warping_path(vectores_maestro, vectores_alumno)
    path_length = len(path)

    # 4. Normalizar la distancia para diagnóstico
    dtw_normalizado = dtw_distance / path_length if path_length > 0 else dtw_distance

    # 5. NUEVA MÉTRICA: media de similitudes por paso alineado (interpretable y robusta)
    scores_por_paso = []
    peor_sim = float("inf")
    frame_maestro_critico, frame_alumno_critico = 0, 0

    n_path = len(path)
    i_ini, i_fin = int(n_path * 0.20), int(n_path * 0.80)

    for k, (i, j) in enumerate(path):
        if i < len(secuencia_maestro) and j < len(secuencia_alumno):
            kp_m = secuencia_maestro[i]
            kp_a = secuencia_alumno[j]
            nz_m = sum(1 for v in kp_m[:51] if v != 0.0)
            nz_a = sum(1 for v in kp_a[:51] if v != 0.0)
            if nz_m < 15 or nz_a < 15:
                continue

            res = similitud_esqueletos(kp_m, kp_a)
            score_paso = res["score"]
            scores_por_paso.append(score_paso)

            # Búsqueda del frame crítico en la ventana central (20%-80%)
            if i_ini <= k <= i_fin and score_paso < peor_sim:
                peor_sim = score_paso
                frame_maestro_critico = int(i)
                frame_alumno_critico = int(j)

    if scores_por_paso:
        scores_ord = sorted(scores_por_paso)
        n = len(scores_ord)
        corte = max(1, int(n * 0.05))
        scores_utiles = scores_ord[corte:] if n > 20 else scores_ord
        score_similitud = float(np.mean(scores_utiles))
    else:
        score_similitud = 0.0

    # 6. Articulaciones más divergentes en el peor frame alineado
    arts_criticas = articulaciones_criticas(
        secuencia_maestro[frame_maestro_critico],
        secuencia_alumno[frame_alumno_critico],
        top_k=3,
    )

    return {
        "dtw_distance": round(dtw_distance, 4),
        "dtw_normalizado": round(dtw_normalizado, 4),
        "score_similitud": round(score_similitud, 2),
        "path_length": path_length,
        "frame_maestro_critico": frame_maestro_critico,
        "frame_alumno_critico": frame_alumno_critico,
        "articulaciones_criticas": arts_criticas,
        "n_frames_maestro": len(secuencia_maestro),
        "n_frames_alumno": len(secuencia_alumno),
    }
