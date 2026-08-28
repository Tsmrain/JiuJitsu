"""
Módulo de Filtrado Cinemático de Kalman (Craig Larman / RF-08, RF-11).
Suaviza coordenadas articulares (x, y) de MediaPipe y compensa oclusiones breves.
"""

from typing import List, Optional, Tuple
import numpy as np


class OclusionProlongadaError(Exception):
    """Excepción lanzada cuando una articulación sufre oclusión continua > 1.5s (RF-11)."""
    pass


class KalmanTracker:
    """
    Filtro de Kalman cinemático lineal de 4 dimensiones [x, y, vx, vy]^T.
    
    Permite suavizar las trayectorias de landmarks motrices y mantener la estimación
    de posición ante pérdidas momentáneas de detección visual. Si la oclusión
    excede 45 fotogramas continuos (1.5 segundos a 30 FPS), se aborta la estimación
    para cumplir con la directriz de Zero-Persistence (RF-11).
    """

    def __init__(
        self,
        dt: float = 1.0 / 30.0,
        proceso_ruido: float = 1e-2,
        medicion_ruido: float = 1e-1,
        umbral_confianza: float = 0.5,
        max_cuadros_oclusion: int = 45,
        x_inicial: float = 0.0,
        y_inicial: float = 0.0,
    ) -> None:
        self.dt = dt
        self.umbral_confianza = umbral_confianza
        self.max_cuadros_oclusion = max_cuadros_oclusion
        self.conteo_oclusion_consecutiva = 0

        # Estado: [x, y, vx, vy]^T
        self.x = np.array([[x_inicial], [y_inicial], [0.0], [0.0]], dtype=np.float64)

        # Matriz de transición de estado F
        self.F = np.array(
            [
                [1.0, 0.0, dt, 0.0],
                [0.0, 1.0, 0.0, dt],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )

        # Matriz de observación H (observamos posición [x, y])
        self.H = np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
            ],
            dtype=np.float64,
        )

        # Covarianza de error de estimación P
        self.P = np.eye(4, dtype=np.float64) * 1.0

        # Covarianza de ruido del proceso Q
        dt2 = (dt ** 2) / 2.0
        G = np.array([[dt2, 0.0], [0.0, dt2], [dt, 0.0], [0.0, dt]], dtype=np.float64)
        self.Q = G @ G.T * proceso_ruido

        # Covarianza de ruido de medición base R0
        self.R0 = np.eye(2, dtype=np.float64) * medicion_ruido
        self.I = np.eye(4, dtype=np.float64)
        self._inicializado = False

    def inicializar(self, x: float, y: float) -> None:
        """Inicializa el vector de estado con una medición certera."""
        self.x = np.array([[x], [y], [0.0], [0.0]], dtype=np.float64)
        self.P = np.eye(4, dtype=np.float64) * 1.0
        self.conteo_oclusion_consecutiva = 0
        self._inicializado = True

    def predict(self) -> Tuple[float, float]:
        """
        Fase de predicción cinemática a priori:
        x_priori = F * x
        P_priori = F * P * F^T + Q
        """
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return float(self.x[0, 0]), float(self.x[1, 0])

    def update(
        self,
        z: Optional[Tuple[float, float]],
        confidence: float = 1.0,
    ) -> Tuple[float, float]:
        """
        Fase de actualización con medición a posteriori.
        
        Si la confianza es inferior a 0.5 o la medición es None, se incrementa
        el contador de oclusión. Si supera max_cuadros_oclusion (45), se levanta
        OclusionProlongadaError. Si la confianza es baja pero tolerable, se confía
        predominantemente en la predicción interna.
        """
        if z is None or confidence < self.umbral_confianza:
            self.conteo_oclusion_consecutiva += 1
            if self.conteo_oclusion_consecutiva > self.max_cuadros_oclusion:
                raise OclusionProlongadaError(
                    f"Oclusión continua prolongada ({self.conteo_oclusion_consecutiva} frames > "
                    f"{self.max_cuadros_oclusion}). Cómputo abortado por política Zero-Persistence (RF-11)."
                )
            # En oclusión momentánea, dependemos de la predicción cinemática
            return float(self.x[0, 0]), float(self.x[1, 0])

        # Confianza suficiente: reseteamos contador de oclusión
        self.conteo_oclusion_consecutiva = 0

        if not self._inicializado:
            self.inicializar(z[0], z[1])
            return z[0], z[1]

        z_vec = np.array([[z[0]], [z[1]]], dtype=np.float64)
        
        factor_confianza = max(1e-3, float(confidence))
        R = self.R0 / factor_confianza

        # y = z - H * x
        y_residual = z_vec - self.H @ self.x

        # S = H * P * H^T + R
        S = self.H @ self.P @ self.H.T + R

        # K = P * H^T * inv(S)
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # x = x + K * y
        self.x = self.x + K @ y_residual

        # P = (I - K * H) * P
        self.P = (self.I - K @ self.H) @ self.P

        return float(self.x[0, 0]), float(self.x[1, 0])

    def procesar_fotograma(
        self,
        z: Optional[Tuple[float, float]],
        confidence: float = 1.0,
    ) -> Tuple[float, float]:
        """Ejecuta un ciclo completo de predict() seguido de update()."""
        self.predict()
        return self.update(z, confidence)

    def filtrar_trayectoria(
        self,
        puntos: List[Optional[Tuple[float, float]]],
        confianzas: List[float],
    ) -> List[Tuple[float, float]]:
        """Procesa una secuencia completa de fotogramas."""
        trayectoria_suavizada: List[Tuple[float, float]] = []
        for p, c in zip(puntos, confianzas):
            estimado = self.procesar_fotograma(p, c)
            trayectoria_suavizada.append(estimado)
        return trayectoria_suavizada


# Alias para total trazabilidad con el DCD (Craig Larman)
KalmanFilterTracker = KalmanTracker
