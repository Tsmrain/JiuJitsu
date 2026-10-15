"""
Normalización biomecánica de esqueletos COCO-17 para comparación entre
personas de distinta complexión física.

Un esqueleto crudo (x, y) en píxeles depende de:
  • posición en el encuadre        → traslación
  • distancia a la cámara          → escala
  • orientación respecto al sensor → rotación
  • longitud de huesos             → antropometría

Este módulo proyecta el esqueleto a un frame canónico de cuerpo
(origen = caderas, escala = torso, eje Y = cadera→hombro) y añade
12 ángulos articulares invariantes.
"""

import numpy as np
from typing import List, Tuple, Dict

# ── Índices COCO-17 ──────────────────────────────────────────────────────────
NOSE = 0
L_EYE, R_EYE = 1, 2
L_EAR, R_EAR = 3, 4
L_SHOULDER, R_SHOULDER = 5, 6
L_ELBOW, R_ELBOW = 7, 8
L_WRIST, R_WRIST = 9, 10
L_HIP, R_HIP = 11, 12
L_KNEE, R_KNEE = 13, 14
L_ANKLE, R_ANKLE = 15, 16

# Tripleta (nombre, A, B, C): ángulo en B formado por b→a y b→c
ANGLE_TRIPLETS: List[Tuple[str, int, int, int]] = [
    ("codo_izq",    L_SHOULDER, L_ELBOW,    L_WRIST),
    ("codo_der",    R_SHOULDER, R_ELBOW,    R_WRIST),
    ("hombro_izq",  L_ELBOW,    L_SHOULDER, L_HIP),
    ("hombro_der",  R_ELBOW,    R_SHOULDER, L_HIP),
    ("cadera_izq",  L_SHOULDER, L_HIP,      L_KNEE),
    ("cadera_der",  R_SHOULDER, R_HIP,      R_KNEE),
    ("rodilla_izq", L_HIP,      L_KNEE,     L_ANKLE),
    ("rodilla_der", R_HIP,      R_KNEE,     R_ANKLE),
    ("cuello",      L_SHOULDER, NOSE,       R_SHOULDER),
    ("tronco",      L_SHOULDER, L_HIP,      R_HIP),
    ("pelvis",      L_HIP,      R_HIP,      R_KNEE),
    ("espalda",     L_SHOULDER, R_SHOULDER, R_HIP),
]

VECTOR_DIM = 17 * 2 + len(ANGLE_TRIPLETS)  # 34 + 12 = 46


def _extract_xy(kpts_flat: List[float]) -> np.ndarray:
    """Desde [x0,y0,z0, x1,y1,z1, ..., x16,y16,z16, ...] (133 dims),
    extrae (17, 2) de (x, y) en píxeles."""
    arr = np.asarray(kpts_flat[:51], dtype=np.float64).reshape(17, 3)
    return arr[:, :2].copy()


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Ángulo en b formado por b→a y b→c, en grados [0, 180]. Retorna NaN si hay oclusión."""
    if np.all(a == 0) or np.all(b == 0) or np.all(c == 0):
        return float(np.nan)
    v1, v2 = a - b, c - b
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-8 or n2 < 1e-8:
        return float(np.nan)
    cos_t = float(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))
    return float(np.degrees(np.arccos(cos_t)))


def normalizar(kpts_flat: List[float]) -> Dict[str, np.ndarray]:
    """
    Proyecta un esqueleto COCO-17 al frame canónico de cuerpo.

    Returns:
        {
          "posiciones": (34,) float32,
          "angulos":    (12,) float32,   # grados [0, 180] (NaN en oclusiones)
          "vector":     (46,) float32,   # concatenación para DTW/Qdrant (sin NaNs)
        }
    """
    xy = _extract_xy(kpts_flat)

    # 1. Traslación: origen en punto medio de caderas
    hip_mid = (xy[L_HIP] + xy[R_HIP]) / 2.0
    p = xy - hip_mid

    # 2. Escala: dividir por longitud del torso (con protección contra oclusión)
    shoulder_mid = (xy[L_SHOULDER] + xy[R_SHOULDER]) / 2.0
    torso = shoulder_mid - hip_mid
    raw_scale = float(np.linalg.norm(torso))

    if raw_scale < 10.0:
        valid = xy[np.any(xy > 0, axis=1)]
        if len(valid) >= 2:
            bbox_diag = float(np.linalg.norm(np.ptp(valid, axis=0)))
            scale = max(bbox_diag * 0.5, 10.0)
        else:
            scale = 100.0
    else:
        scale = raw_scale

    p = p / scale

    # 3. Rotación: alinear torso al eje +Y del frame corporal
    if raw_scale >= 10.0:
        tx, ty = torso / raw_scale
        theta = np.arctan2(tx, ty)
        ca, sa = np.cos(-theta), np.sin(-theta)
        R = np.array([[ca, -sa], [sa, ca]])
        p_rot = p @ R.T
    else:
        p_rot = p

    # 4. Ángulos articulares (invariantes, NaN si algún punto está ocluido)
    angulos = np.array(
        [_angle(xy[a], xy[b], xy[c]) for _, a, b, c in ANGLE_TRIPLETS],
        dtype=np.float64,
    )

    # 5. Vector final de 46 dims
    posiciones = p_rot.flatten().astype(np.float32)
    angulos_scaled = ((angulos - 90.0) / 90.0).astype(np.float32)
    # Neutralizar NaNs a 0.0 (equivalente a 90°) para DTW numérico robusto
    angulos_scaled = np.nan_to_num(angulos_scaled, nan=0.0)
    vector = np.concatenate([posiciones, angulos_scaled]).astype(np.float32)

    return {
        "posiciones": posiciones,
        "angulos": angulos.astype(np.float32),
        "vector": vector,
    }


def similitud_esqueletos(
    kpts_a: List[float],
    kpts_b: List[float],
    w_pos: float = 0.55,
    w_ang: float = 0.45,
) -> Dict[str, object]:
    """Similitud combinada entre dos esqueletos crudos, ignorando articulaciones ocluidas."""
    na, nb = normalizar(kpts_a), normalizar(kpts_b)

    va, vb = na["posiciones"], nb["posiciones"]
    sim_pos = float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-9))
    sim_pos = max(0.0, min(1.0, sim_pos))

    ang_a, ang_b = na["angulos"], nb["angulos"]
    valid_angles = ~np.isnan(ang_a) & ~np.isnan(ang_b)
    if np.any(valid_angles):
        diffs = np.abs(ang_a[valid_angles] - ang_b[valid_angles])
        mean_diff = float(np.mean(diffs))
        sim_ang = max(0.0, 1.0 - mean_diff / 90.0)
    else:
        sim_ang = 0.5

    score = (w_pos * sim_pos + w_ang * sim_ang) * 100.0

    return {
        "score": round(score, 2),
        "sim_pos": round(sim_pos, 4),
        "sim_ang": round(sim_ang, 4),
        "angulos_a": {name: None if np.isnan(v) else round(float(v), 2)
                      for (name, *_), v in zip(ANGLE_TRIPLETS, na["angulos"])},
        "angulos_b": {name: None if np.isnan(v) else round(float(v), 2)
                      for (name, *_), v in zip(ANGLE_TRIPLETS, nb["angulos"])},
    }


def articulaciones_criticas(
    kpts_a: List[float],
    kpts_b: List[float],
    top_k: int = 3,
) -> List[int]:
    """Índices COCO-17 con mayor divergencia. Faciales pesan menos (0.4 vs 1.0)."""
    raw_a = _extract_xy(kpts_a)
    raw_b = _extract_xy(kpts_b)

    na, nb = normalizar(kpts_a), normalizar(kpts_b)
    pa = na["posiciones"].reshape(17, 2)
    pb = nb["posiciones"].reshape(17, 2)
    dists = np.linalg.norm(pa - pb, axis=1)
    pesos = np.array([0.4]*5 + [1.0]*12)
    dists = dists * pesos

    # Descartar keypoints no detectados en píxeles crudos (0, 0)
    undetected_a = (raw_a[:, 0] == 0) & (raw_a[:, 1] == 0)
    undetected_b = (raw_b[:, 0] == 0) & (raw_b[:, 1] == 0)
    invalidos = undetected_a | undetected_b
    dists[invalidos] = -1.0   # nunca serán críticos

    orden = np.argsort(dists)[::-1]
    return [int(i) for i in orden[:top_k] if dists[i] > 0]


def vector_para_qdrant(kpts_flat: List[float]) -> List[float]:
    """Atajo: vector de 46 dims listo para Qdrant."""
    return normalizar(kpts_flat)["vector"].tolist()
