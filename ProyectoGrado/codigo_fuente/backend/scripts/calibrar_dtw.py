#!/usr/bin/env python3
"""
Calibración y comparación de métricas DTW sobre 4 casos de referencia:
  1. auto-similitud  (maestro vs maestro)        → suelo inferior (100%)
  2. mismo + cropping temporal (10%)             → tolerancia desalineación (~95-98%)
  3. ruido gaussiano                              → techo de divergencia / suelo de similitud
  4. maestro vs alumno (real)                     → ejecución real
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from dtaidistance import dtw_ndim
from corpocmente.domain.biomechanics.pose_normalizer import normalizar, similitud_esqueletos


def cargar(path):
    d = json.load(open(path))
    return [e["keypoints133"] for e in d["esqueletos"]]


def evaluar_caso(kpts_a, kpts_b, nombre):
    va = np.array([normalizar(k)["vector"] for k in kpts_a], dtype=np.float64)
    vb = np.array([normalizar(k)["vector"] for k in kpts_b], dtype=np.float64)

    dist = float(dtw_ndim.distance_fast(va, vb))
    path = dtw_ndim.warping_path(va, vb)
    p_len = len(path)
    dtw_norm = dist / p_len if p_len > 0 else dist

    scores = []
    for i, j in path:
        if i < len(kpts_a) and j < len(kpts_b):
            ka, kb = kpts_a[i], kpts_b[j]
            if sum(1 for v in ka[:51] if v != 0) < 15 or sum(1 for v in kb[:51] if v != 0) < 15:
                continue
            scores.append(similitud_esqueletos(ka, kb)["score"])

    if scores:
        scores_ord = sorted(scores)
        n = len(scores_ord)
        corte = max(1, int(n * 0.05))
        scores_utiles = scores_ord[corte:] if n > 20 else scores_ord
        score_media = float(np.mean(scores_utiles))
        score_mediana = float(np.median(scores_utiles))
    else:
        score_media = 0.0
        score_mediana = 0.0

    print(f"| {nombre:<24} | dtw_norm: {dtw_norm:6.4f} | Media 5%: {score_media:6.2f}% | Mediana: {score_mediana:6.2f}% |")
    return dtw_norm, score_media


def main():
    maestro = cargar("/tmp/maestro_poses.json")
    alumno  = cargar("/tmp/alumno_poses.json")

    print(f"Dataset cargado: Maestro={len(maestro)} frames, Alumno={len(alumno)} frames\n")
    print(f"| {'Caso de Prueba':<24} | {'DTW Normalizado':<18} | {'Score Media 5%':<17} | {'Mediana':<16} |")
    print("|" + "-"*26 + "|" + "-"*20 + "|" + "-"*19 + "|" + "-"*18 + "|")

    # 1. Auto-similitud
    evaluar_caso(maestro, maestro, "1. Maestro vs Maestro")

    # 2. Cropping 10%
    trim = int(len(maestro) * 0.10)
    evaluar_caso(maestro, maestro[trim:-trim], "2. Cropping 10%")

    # 3. Ruido gaussiano
    rng = np.random.default_rng(42)
    ruido = [rng.normal(0, 100, 133).tolist() for _ in range(len(maestro))]
    evaluar_caso(maestro, ruido, "3. Ruido Gaussiano")

    # 4. Real
    evaluar_caso(maestro, alumno, "4. Maestro vs Alumno")


if __name__ == "__main__":
    main()
