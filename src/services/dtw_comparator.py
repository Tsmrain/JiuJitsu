"""
Servicio de Dominio - DTWComparator (Alineación Temporal)

Implementa el algoritmo Dynamic Time Warping (DTW) con restricción
de banda de Sakoe-Chiba para comparar series temporales de ángulos
biomecánicos entre la técnica maestra (patrón) y la ejecución del
practicante.

La ventana de Sakoe-Chiba limita la deformación temporal permitida,
evitando alineamientos espurios y reduciendo la complejidad
computacional de O(n²) a O(n·w).

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import math
from typing import List, Union

import numpy as np


# Tipo para elementos de las series: escalares o vectores de ángulos
ElementoSerie = Union[float, List[float]]


class DTWComparator:
    """
    Comparador de series temporales basado en Dynamic Time Warping
    con restricción de banda de Sakoe-Chiba.

    Principio de diseño (Larman): Servicio de dominio puro. Recibe
    listas de valores numéricos y retorna distancias — sin dependencias
    de frameworks externos.
    """

    @staticmethod
    def _distancia_euclidiana(a: ElementoSerie, b: ElementoSerie) -> float:
        """Función de costo local: distancia euclidiana entre dos elementos.

        Soporta tanto escalares (ángulos individuales) como vectores
        (conjuntos de ángulos articulares por frame).

        Args:
            a: Elemento de la serie patrón (escalar o vector).
            b: Elemento de la serie ejecución (escalar o vector).

        Returns:
            Distancia euclidiana entre a y b.
        """
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(float(a) - float(b))

        # Caso vectorial: múltiples ángulos por frame
        vec_a = np.array(a, dtype=np.float64)
        vec_b = np.array(b, dtype=np.float64)
        return float(np.linalg.norm(vec_a - vec_b))

    def calcular_distancia_sakoe_chiba(
        self,
        serie_patron: List[ElementoSerie],
        serie_ejecucion: List[ElementoSerie],
        ventana: float,
    ) -> float:
        """Calcula la distancia DTW con restricción de banda de Sakoe-Chiba.

        El algoritmo construye una matriz de costos acumulados donde cada
        celda (i, j) contiene el costo mínimo de alinear las subseries
        serie_patron[:i+1] y serie_ejecucion[:j+1]. La banda de Sakoe-Chiba
        restringe |i - j| ≤ w, donde w = ceil(ventana * max(n, m)).

        Args:
            serie_patron: Serie temporal de referencia (técnica maestra).
            serie_ejecucion: Serie temporal del practicante.
            ventana: Proporción de la ventana de Sakoe-Chiba [0.0, 1.0].
                     0.0 = alineamiento diagonal estricto.
                     1.0 = DTW completo sin restricción.

        Returns:
            Costo acumulado mínimo DTW (distancia total de alineamiento).

        Raises:
            ValueError: Si alguna de las series está vacía.
        """
        n = len(serie_patron)
        m = len(serie_ejecucion)

        if n == 0 or m == 0:
            raise ValueError(
                "Las series temporales no pueden estar vacías para el "
                "cálculo DTW."
            )

        # Ancho de la banda de Sakoe-Chiba (en número de celdas)
        w = max(math.ceil(ventana * max(n, m)), abs(n - m))

        # Matriz de costos acumulados inicializada a infinito
        dtw_matrix = np.full((n + 1, m + 1), np.inf)
        dtw_matrix[0, 0] = 0.0

        for i in range(1, n + 1):
            # Rango de j permitido por la banda de Sakoe-Chiba
            j_inicio = max(1, i - w)
            j_fin = min(m, i + w)

            for j in range(j_inicio, j_fin + 1):
                costo = self._distancia_euclidiana(
                    serie_patron[i - 1],
                    serie_ejecucion[j - 1],
                )

                # Transiciones DTW: inserción, eliminación, coincidencia
                dtw_matrix[i, j] = costo + min(
                    dtw_matrix[i - 1, j],      # Inserción (avanza patrón)
                    dtw_matrix[i, j - 1],      # Eliminación (avanza ejecución)
                    dtw_matrix[i - 1, j - 1],  # Coincidencia (avanza ambos)
                )

        return float(dtw_matrix[n, m])
