from typing import List, Tuple, Optional
import numpy as np

from ..interfaces import IDTWComparator
from ...config import VENTANA_DTW


class DTWComparatorImpl(IDTWComparator):
    """
    Servicio de alineación temporal elástica (DTW) con restricción de Sakoe-Chiba (Pure Fabrication - GRASP).
    Garantiza complejidad temporal cuasi-lineal O(N) para cumplir el SLA (RP-01).
    """

    def comparar(self, serie_a: List[float], serie_b: List[float]) -> Tuple[float, List[Tuple[int, int]]]:
        """
        Calcula la distancia DTW acumulada y el camino de alineación óptimo (warping path).
        """
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

        # Reconstrucción del camino de mínima deformación (Backtracking)
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
        """
        Extrae las series de una articulación específica y computa la distancia DTW.
        """
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
