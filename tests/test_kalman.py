"""
Pruebas Unitarias para el Filtro de Kalman Cinemático (Craig Larman / TDD).
"""

import unittest
import numpy as np
from src.services.kalman_filter import KalmanTracker, OclusionProlongadaError


class TestKalmanTracker(unittest.TestCase):

    def setUp(self) -> None:
        np.random.seed(42)
        self.dt = 1.0 / 30.0
        self.tracker = KalmanTracker(dt=self.dt, proceso_ruido=1e-3, medicion_ruido=0.05)

    def test_reduccion_error_cuadratico_medio(self) -> None:
        """Prueba 1: Verifica que el filtro reduzca el MSE frente a mediciones con ruido gaussiano."""
        n_frames = 60
        # Trayectoria lineal real: movimiento uniforme a velocidad constante
        t = np.linspace(0, n_frames * self.dt, n_frames)
        vx_true, vy_true = 0.5, 0.2
        x_true = vx_true * t + 0.1
        y_true = vy_true * t + 0.1

        # Generar mediciones con ruido gaussiano
        ruido_sigma = 0.08
        x_noisy = x_true + np.random.normal(0, ruido_sigma, n_frames)
        y_noisy = y_true + np.random.normal(0, ruido_sigma, n_frames)

        puntos_medidos = list(zip(x_noisy, y_noisy))
        confianzas = [0.95] * n_frames

        # Filtrar con Kalman
        puntos_filtrados = self.tracker.filtrar_trayectoria(puntos_medidos, confianzas)

        x_filt = np.array([p[0] for p in puntos_filtrados])
        y_filt = np.array([p[1] for p in puntos_filtrados])

        # Ignoramos los primeros 5 frames para dar tiempo de convergencia al filtro
        mse_noisy = np.mean((x_noisy[5:] - x_true[5:]) ** 2 + (y_noisy[5:] - y_true[5:]) ** 2)
        mse_filtered = np.mean((x_filt[5:] - x_true[5:]) ** 2 + (y_filt[5:] - y_true[5:]) ** 2)

        self.assertLess(
            mse_filtered,
            mse_noisy,
            f"El MSE filtrado ({mse_filtered:.6f}) debe ser menor al MSE ruidoso ({mse_noisy:.6f})",
        )

    def test_perdida_senal_corta_mantiene_suavidad(self) -> None:
        """Prueba 2: Simula pérdida de señal (confianza=0) por 10 frames y verifica estimación suave."""
        # Trayectoria inicial conocida
        for i in range(15):
            self.tracker.procesar_fotograma((float(i) * 0.1, float(i) * 0.05), confidence=1.0)

        pos_antes = (float(self.tracker.x[0, 0]), float(self.tracker.x[1, 0]))

        # Simular 10 fotogramas de oclusión visual temporal (C=0.0)
        posiciones_ocultas = []
        for _ in range(10):
            pos = self.tracker.procesar_fotograma(None, confidence=0.0)
            posiciones_ocultas.append(pos)

        # No debe lanzar error y la trayectoria debe avanzar cinemáticamente de forma monótona
        self.assertEqual(len(posiciones_ocultas), 10)
        self.assertGreater(posiciones_ocultas[-1][0], pos_antes[0])
        self.assertGreater(posiciones_ocultas[-1][1], pos_antes[1])

    def test_oclusion_prolongada_lanza_excepcion_rf11(self) -> None:
        """Prueba 3: Simula oclusión > 45 frames y verifica lanzamiento de OclusionProlongadaError."""
        # Inicializar con frame válido
        self.tracker.procesar_fotograma((0.5, 0.5), confidence=1.0)

        # Oclusión menor o igual a 45 frames: debe tolerarse
        for _ in range(45):
            self.tracker.procesar_fotograma(None, confidence=0.1)

        # El fotograma 46 supera el límite de 1.5s (45 frames a 30 FPS)
        with self.assertRaises(OclusionProlongadaError):
            self.tracker.procesar_fotograma(None, confidence=0.1)


if __name__ == "__main__":
    unittest.main()
