from typing import List, Dict
import numpy as np

from ..interfaces import IAngleCalculator


class AngleCalculatorImpl(IAngleCalculator):
    """
    Servicio de cálculo cinemático de ángulos articulares (Information Expert - GRASP).
    Conoce la geometría espacial y computa ángulos relativos a partir de keypoints COCO.
    """

    def calcular_angulo(self, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        """
        Calcula el ángulo en grados formado en el vértice b por los vectores ba y bc.
        """
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
        """
        Extrae los ángulos articulares clave para Jiu-Jitsu Brasileño (RF-02).
        """
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
        """Extrae la secuencia temporal de ángulos para todos los fotogramas."""
        return [self.extraer_angulos(k) for k in keypoints_por_frame]
