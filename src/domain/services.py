from typing import List, Tuple, Optional, Dict
import numpy as np
import cv2

from .interfaces import IAngleCalculator, IDTWComparator, IFrameAnnotator
from ..config import INDICES_COCO, VENTANA_DTW


class AngleCalculatorImpl(IAngleCalculator):
    """
    Servicio de cálculo de ángulos cinemáticos (Information Expert).
    """

    def calcular_angulo(self, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        a = np.array(a, dtype=np.float64)
        b = np.array(b, dtype=np.float64)
        c = np.array(c, dtype=np.float64)

        ba = a - b
        bc = c - b

        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        prod_norm = norm_ba * norm_bc

        if prod_norm <= 1e-9:
            return 0.0

        cos_angulo = np.dot(ba, bc) / prod_norm
        cos_angulo = np.clip(cos_angulo, -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_angulo)))

    def extraer_angulos(self, keypoints: np.ndarray) -> Dict[str, float]:
        angulos = {}
        if len(keypoints) > 16:
            # Codo izquierdo (5, 7, 9)
            if all(keypoints[[5, 7, 9], 0] > 0):
                angulos['codo_izq'] = self.calcular_angulo(keypoints[5], keypoints[7], keypoints[9])

            # Codo derecho (6, 8, 10)
            if all(keypoints[[6, 8, 10], 0] > 0):
                angulos['codo_der'] = self.calcular_angulo(keypoints[6], keypoints[8], keypoints[10])

            # Rodilla izquierda (11, 13, 15)
            if all(keypoints[[11, 13, 15], 0] > 0):
                angulos['rodilla_izq'] = self.calcular_angulo(keypoints[11], keypoints[13], keypoints[15])

            # Rodilla derecha (12, 14, 16)
            if all(keypoints[[12, 14, 16], 0] > 0):
                angulos['rodilla_der'] = self.calcular_angulo(keypoints[12], keypoints[14], keypoints[16])

            # Cadera (11, 12, 14)
            if all(keypoints[[11, 12, 14], 0] > 0):
                angulos['cadera'] = self.calcular_angulo(keypoints[11], keypoints[12], keypoints[14])

            # Hombro (5, 6, 8)
            if all(keypoints[[5, 6, 8], 0] > 0):
                angulos['hombro'] = self.calcular_angulo(keypoints[5], keypoints[6], keypoints[8])

        return angulos

    def extraer_angulos_secuencia(self, keypoints_por_frame: List[np.ndarray]) -> List[Dict[str, float]]:
        return [self.extraer_angulos(k) for k in keypoints_por_frame]


class DTWComparatorImpl(IDTWComparator):
    """
    Servicio de alineación temporal DTW con ventana de Sakoe-Chiba (Pure Fabrication).
    """

    def comparar(self, serie_a: List[float], serie_b: List[float]) -> Tuple[float, List[Tuple[int, int]]]:
        a = np.array(serie_a, dtype=np.float64).flatten()
        b = np.array(serie_b, dtype=np.float64).flatten()

        n = len(a)
        m = len(b)

        if n == 0 or m == 0:
            return float('inf'), []

        if n == 1 and m == 1:
            return float(abs(a[0] - b[0])), [(0, 0)]

        window = max(1, int(VENTANA_DTW * min(n, m)))
        cost_matrix = np.full((n + 1, m + 1), np.inf)
        cost_matrix[0, 0] = 0.0

        for i in range(1, n + 1):
            j_start = max(1, i - window)
            j_end = min(m + 1, i + window + 1)
            for j in range(j_start, j_end):
                cost = abs(a[i - 1] - b[j - 1])
                cost_matrix[i, j] = cost + min(
                    cost_matrix[i - 1, j],
                    cost_matrix[i, j - 1],
                    cost_matrix[i - 1, j - 1]
                )

        if np.isinf(cost_matrix[n, m]):
            return float('inf'), []

        # Backtracking
        i, j = n, m
        path = []
        while i > 0 and j > 0:
            path.append((i - 1, j - 1))
            min_c = min(
                cost_matrix[i - 1, j - 1],
                cost_matrix[i - 1, j],
                cost_matrix[i, j - 1]
            )
            if cost_matrix[i - 1, j - 1] == min_c:
                i -= 1
                j -= 1
            elif cost_matrix[i - 1, j] == min_c:
                i -= 1
            else:
                j -= 1

        path.reverse()
        return float(cost_matrix[n, m]), path

    def comparar_articulacion(
        self, angulos_maestro: List[dict], angulos_alumno: List[dict], articulacion: str
    ) -> Tuple[Optional[float], Optional[List[Tuple[int, int]]], List[float], List[float]]:
        serie_m = [f[articulacion] for f in angulos_maestro if articulacion in f]
        serie_a = [f[articulacion] for f in angulos_alumno if articulacion in f]

        if len(serie_m) < 2 or len(serie_a) < 2:
            return None, None, serie_m, serie_a

        min_len = min(len(serie_m), len(serie_a))
        sm = serie_m[:min_len]
        sa = serie_a[:min_len]

        dist, path = self.comparar(sm, sa)
        if np.isinf(dist):
            return None, None, sm, sa

        return dist, path, sm, sa


class FrameAnnotatorImpl(IFrameAnnotator):
    """
    Servicio de anotación de fotogramas con OpenCV (Pure Fabrication).
    """

    def anotar_error(
        self, frame: np.ndarray, keypoints: np.ndarray,
        articulacion: str, error: float, frame_idx: int
    ) -> np.ndarray:
        frame_copy = frame.copy()
        idx = INDICES_COCO.get(articulacion, 7)

        if len(keypoints) > idx:
            x, y = int(keypoints[idx][0]), int(keypoints[idx][1])

            cv2.circle(frame_copy, (x, y), 20, (0, 0, 255), 2)
            cv2.circle(frame_copy, (x, y), 14, (0, 0, 255), -1)

            nombre_art = articulacion.replace('_', ' ').upper()
            cv2.putText(
                frame_copy, f"ERROR: {error:.1f} DEG", (max(10, x - 80), max(20, y - 50)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2, cv2.LINE_AA
            )
            cv2.putText(
                frame_copy, nombre_art, (max(10, x - 80), max(40, y - 25)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2, cv2.LINE_AA
            )
            cv2.putText(
                frame_copy, f"Frame: {frame_idx}", (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA
            )

        return frame_copy
