"""
Módulo de Comparación Biomecánica mediante Dynamic Time Warping (DTW)
con Restricción de Ventana de Sakoe-Chiba (Craig Larman / RF-09, RF-10).
"""

from typing import List, Sequence, Tuple
import numpy as np


class DTWComparator:
    """
    Comparador no lineal de series temporales biomecánicas basado en DTW
    optimizado mediante Ventana de Sakoe-Chiba.
    
    Alinea temporalmente secuencias de ángulos articulares de duraciones dispares
    (ej. instructor a 4s vs. estudiante a 6s) garantizando una complejidad cuasi-lineal
    O(w * N) para ejecución eficiente en CPUs locales y Huawei Cloud FunctionGraph.
    """

    def __init__(self, ventana_sakoe_chiba: float = 0.15) -> None:
        """
        :param ventana_sakoe_chiba: Fracción porcentual de la longitud máxima (por defecto 0.15 / 15%).
        """
        if not (0.0 < ventana_sakoe_chiba <= 1.0):
            raise ValueError("ventana_sakoe_chiba debe ser un valor en el intervalo (0.0, 1.0].")
        self.ventana_fraccion = ventana_sakoe_chiba

    def calcular_distancia(
        self,
        serie_a: Sequence[float],
        serie_b: Sequence[float],
    ) -> Tuple[float, np.ndarray, List[Tuple[int, int]]]:
        """
        Calcula la distancia mínima acumulada DTW entre serie_a (referencia/maestra)
        y serie_b (ejecución del estudiante), restringida por la banda de Sakoe-Chiba.
        
        :param serie_a: Serie de ángulos patrón (longitud N).
        :param serie_b: Serie de ángulos evaluada (longitud M).
        :return: (distancia_minima_acumulada, matriz_costo_acumulado, camino_alineacion)
        """
        a = np.asarray(serie_a, dtype=np.float64)
        b = np.asarray(serie_b, dtype=np.float64)

        n = len(a)
        m = len(b)

        if n == 0 or m == 0:
            raise ValueError("Las series de entrada no pueden estar vacías.")

        # Ancho de ventana absoluto w
        longitud_maxima = max(n, m)
        w = max(1, int(np.ceil(self.ventana_fraccion * longitud_maxima)))

        # Matriz de costo acumulado inicializada a infinito
        D = np.full((n, m), np.inf, dtype=np.float64)

        # Relación de escala para mapeo de diagonal entre series de diferente longitud
        escala = float(m) / float(n)

        # Condición inicial
        D[0, 0] = abs(a[0] - b[0])

        # Inicialización de la primera columna
        for i in range(1, min(n, w + 1)):
            if abs(0 - int(np.round(i * escala))) <= w:
                D[i, 0] = D[i - 1, 0] + abs(a[i] - b[0])

        # Inicialización de la primera fila
        for j in range(1, min(m, w + 1)):
            if abs(j - 0) <= w:
                D[0, j] = D[0, j - 1] + abs(a[0] - b[j])

        # Programación dinámica acotada a la banda de Sakoe-Chiba: |j - i * (m/n)| <= w
        for i in range(1, n):
            j_centro = int(np.round(i * escala))
            j_min = max(1, j_centro - w)
            j_max = min(m, j_centro + w + 1)

            for j in range(j_min, j_max):
                costo_local = abs(a[i] - b[j])
                min_previo = min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
                D[i, j] = costo_local + min_previo

        distancia_acumulada = float(D[n - 1, m - 1])

        # Reconstrucción del camino de alineación óptimo (Backtracking)
        camino: List[Tuple[int, int]] = []
        curr_i, curr_j = n - 1, m - 1
        camino.append((curr_i, curr_j))

        while curr_i > 0 or curr_j > 0:
            if curr_i == 0:
                curr_j -= 1
            elif curr_j == 0:
                curr_i -= 1
            else:
                opciones = [
                    (D[curr_i - 1, curr_j - 1], curr_i - 1, curr_j - 1),  # Diagonal
                    (D[curr_i - 1, curr_j], curr_i - 1, curr_j),          # Paso horizontal
                    (D[curr_i, curr_j - 1], curr_i, curr_j - 1),          # Paso vertical
                ]
                _, curr_i, curr_j = min(opciones, key=lambda x: x[0])
            camino.append((curr_i, curr_j))

        camino.reverse()

        return distancia_acumulada, D, camino

    def extraer_pico_desviacion(
        self,
        serie_maestra: Sequence[float],
        serie_estudiante: Sequence[float],
        camino: List[Tuple[int, int]],
    ) -> Tuple[int, int, float]:
        """
        Identifica el punto temporal de máxima discrepancia angular en el camino alineado.
        
        :return: Tuple[frame_maestro, frame_estudiante, discrepancia_angular_maxima_grados]
        """
        max_error = -1.0
        frame_m_max = 0
        frame_e_max = 0

        for idx_m, idx_e in camino:
            error = abs(serie_maestra[idx_m] - serie_estudiante[idx_e])
            if error > max_error:
                max_error = error
                frame_m_max = idx_m
                frame_e_max = idx_e

        return frame_m_max, frame_e_max, float(max_error)
