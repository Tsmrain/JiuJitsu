"""
Pruebas Unitarias para el Comparador DTW con Ventana de Sakoe-Chiba (Craig Larman / TDD).
"""

import unittest
import numpy as np
from src.services.dtw_comparator import DTWComparator


class TestDTWComparator(unittest.TestCase):

    def setUp(self) -> None:
        self.dtw = DTWComparator(ventana_sakoe_chiba=0.15)

    def test_secuencias_identicas_retornan_distancia_cero(self) -> None:
        """Prueba 1: Dos secuencias idénticas deben arrojar distancia DTW = 0.0."""
        # Curva angular simulada de flexión articular de codo (en grados)
        angulos = [45.0, 52.0, 68.0, 90.0, 110.0, 95.0, 70.0, 48.0]
        distancia, matriz_d, camino = self.dtw.calcular_distancia(angulos, angulos)

        self.assertAlmostEqual(distancia, 0.0, places=6)
        self.assertEqual(len(camino), len(angulos))
        # En secuencias idénticas, el camino óptimo es la diagonal exacta
        for idx_a, idx_b in camino:
            self.assertEqual(idx_a, idx_b)

    def test_secuencia_desplazada_temporalmente_supera_a_distancia_euclidiana(self) -> None:
        """
        Prueba 2: Frente a una secuencia desplazada temporalmente (time-shifted),
        DTW debe lograr una distancia sensiblemente menor a la distancia euclidiana directa.
        """
        t = np.linspace(0, 2 * np.pi, 50)
        # Serie A: señal motriz senoidal patrón
        serie_a = 90.0 + 30.0 * np.sin(t)
        # Serie B: la misma señal motriz ejecutada con retardo temporal (shift de 4 frames)
        serie_b = 90.0 + 30.0 * np.sin(t - 0.5)

        # Distancia euclidiana directa punto a punto
        dist_euclidiana = float(np.sum(np.abs(serie_a - serie_b)))

        # Distancia DTW con Sakoe-Chiba
        dist_dtw, _, camino = self.dtw.calcular_distancia(serie_a, serie_b)

        self.assertLess(
            dist_dtw,
            dist_euclidiana,
            f"La distancia DTW ({dist_dtw:.2f}) debe ser significativamente menor que la euclidiana ({dist_euclidiana:.2f})",
        )
        # El camino debe existir y abarcar toda la secuencia
        self.assertEqual(camino[0], (0, 0))
        self.assertEqual(camino[-1], (len(serie_a) - 1, len(serie_b) - 1))

    def test_ventana_sakoe_chiba_restringe_espacio_de_busqueda(self) -> None:
        """
        Prueba 3: Verifica que la matriz de costos acumulada conserve celdas con infinito
        fuera del ancho de banda fijado por Sakoe-Chiba, demostrando el límite O(w*N).
        """
        n = 40
        serie_a = [float(i) for i in range(n)]
        serie_b = [float(i) for i in range(n)]

        ventana_pct = 0.15
        dtw_acotado = DTWComparator(ventana_sakoe_chiba=ventana_pct)
        _, matriz_d, _ = dtw_acotado.calcular_distancia(serie_a, serie_b)

        w = int(np.ceil(ventana_pct * n))  # ceil(0.15 * 40) = 6

        # Verificar que esquinas lejanas a la diagonal (ej. (0, n-1) y (n-1, 0)) permanecen en inf
        self.assertTrue(
            np.isinf(matriz_d[0, n - 1]),
            "Celdas alejadas de la diagonal deben permanecer inexploradas (np.inf)",
        )
        self.assertTrue(
            np.isinf(matriz_d[n - 1, 0]),
            "Celdas alejadas de la diagonal deben permanecer inexploradas (np.inf)",
        )

        # Verificar que celdas en la diagonal o a distancia <= w fueron evaluadas (finitas)
        for i in range(n):
            self.assertFalse(
                np.isinf(matriz_d[i, i]),
                f"La celda diagonal ({i}, {i}) debe haber sido calculada",
            )

    def test_extraccion_pico_desviacion(self) -> None:
        """Prueba 4: Verifica la correcta detección del fotograma con máxima desviación angular."""
        # Serie patrón estable a 90 grados
        serie_maestra = [90.0] * 10
        # Serie estudiante con un error puntual de quiebre articular en el frame 5 (135 grados = error 45)
        serie_estudiante = [90.0, 90.0, 90.0, 90.0, 90.0, 135.0, 90.0, 90.0, 90.0, 90.0]

        _, _, camino = self.dtw.calcular_distancia(serie_maestra, serie_estudiante)
        frame_m, frame_e, max_err = self.dtw.extraer_pico_desviacion(
            serie_maestra, serie_estudiante, camino
        )

        self.assertEqual(frame_e, 5)
        self.assertAlmostEqual(max_err, 45.0, places=4)


if __name__ == "__main__":
    unittest.main()
