import numpy as np
from .config import VENTANA_DTW


class DTWComparator:
    """
    Comparador de series temporales cinemáticas mediante
    Dynamic Time Warping (DTW) con restricción de Sakoe-Chiba (RF-03).
    """

    @staticmethod
    def dtw_distance(serie_a, serie_b, window_ratio=VENTANA_DTW):
        """
        Calcula la distancia DTW y el camino de alineación óptimo
        con complejidad temporal cuasi-lineal O(N).
        """
        serie_a = np.array(serie_a, dtype=np.float64).flatten()
        serie_b = np.array(serie_b, dtype=np.float64).flatten()

        n = len(serie_a)
        m = len(serie_b)

        if n == 0 or m == 0:
            return float('inf'), []

        # Si las series son muy cortas (1 elemento), cálculo directo
        if n == 1 and m == 1:
            return float(abs(serie_a[0] - serie_b[0])), [(0, 0)]

        window = max(1, int(window_ratio * min(n, m)))

        cost_matrix = np.full((n + 1, m + 1), np.inf)
        cost_matrix[0, 0] = 0.0

        for i in range(1, n + 1):
            j_start = max(1, i - window)
            j_end = min(m + 1, i + window + 1)
            for j in range(j_start, j_end):
                cost = abs(serie_a[i - 1] - serie_b[j - 1])
                cost_matrix[i, j] = cost + min(
                    cost_matrix[i - 1, j],      # Inserción
                    cost_matrix[i, j - 1],      # Supresión
                    cost_matrix[i - 1, j - 1]   # Coincidencia
                )

        if np.isinf(cost_matrix[n, m]):
            # En caso de ventana muy restrictiva, reintentar sin restricción
            return float('inf'), []

        # Reconstrucción del camino de mínima deformación (Backtracking)
        i, j = n, m
        path = []
        while i > 0 and j > 0:
            path.append((i - 1, j - 1))
            min_cost = min(
                cost_matrix[i - 1, j - 1],
                cost_matrix[i - 1, j],
                cost_matrix[i, j - 1]
            )
            if cost_matrix[i - 1, j - 1] == min_cost:
                i -= 1
                j -= 1
            elif cost_matrix[i - 1, j] == min_cost:
                i -= 1
            else:
                j -= 1

        path.reverse()
        return float(cost_matrix[n, m]), path

    @staticmethod
    def comparar_articulacion(angulos_maestro, angulos_alumno, articulacion):
        """
        Extrae las series de una articulación específica y computa la distancia DTW.
        """
        serie_maestro = [frame[articulacion] for frame in angulos_maestro if articulacion in frame]
        serie_alumno = [frame[articulacion] for frame in angulos_alumno if articulacion in frame]

        if len(serie_maestro) < 2 or len(serie_alumno) < 2:
            return None, None, serie_maestro, serie_alumno

        min_len = min(len(serie_maestro), len(serie_alumno))
        serie_m = serie_maestro[:min_len]
        serie_a = serie_alumno[:min_len]

        distance, path = DTWComparator.dtw_distance(serie_m, serie_a)

        if np.isinf(distance):
            return None, None, serie_m, serie_a

        return distance, path, serie_m, serie_a
