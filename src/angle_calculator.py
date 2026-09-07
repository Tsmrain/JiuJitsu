import numpy as np


class AngleCalculator:
    """
    Cálculo y normalización antropomórfica de ángulos articulares
    a partir de keypoints de la topología COCO de 17 puntos (RF-02).
    """

    @staticmethod
    def calcular_angulo(a, b, c):
        """
        Calcula el ángulo relativo en grados formado en el vértice b
        por los vectores ba = a - b y bc = c - b.
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
        angulo = np.arccos(cos_angulo)
        return float(np.degrees(angulo))

    @staticmethod
    def extraer_angulos(keypoints_frame):
        """
        Extrae los ángulos cinemáticos clave para el análisis de Jiu-Jitsu.
        Valida que los keypoints estén presentes (> 0).
        """
        angulos = {}

        if len(keypoints_frame) > 16:
            # Codo izquierdo: hombro(5) - codo(7) - muñeca(9)
            if all(keypoints_frame[[5, 7, 9], 0] > 0):
                angulos['codo_izq'] = AngleCalculator.calcular_angulo(
                    keypoints_frame[5], keypoints_frame[7], keypoints_frame[9]
                )

            # Codo derecho: hombro(6) - codo(8) - muñeca(10)
            if all(keypoints_frame[[6, 8, 10], 0] > 0):
                angulos['codo_der'] = AngleCalculator.calcular_angulo(
                    keypoints_frame[6], keypoints_frame[8], keypoints_frame[10]
                )

            # Rodilla izquierda: cadera(11) - rodilla(13) - tobillo(15)
            if all(keypoints_frame[[11, 13, 15], 0] > 0):
                angulos['rodilla_izq'] = AngleCalculator.calcular_angulo(
                    keypoints_frame[11], keypoints_frame[13], keypoints_frame[15]
                )

            # Rodilla derecha: cadera(12) - rodilla(14) - tobillo(16)
            if all(keypoints_frame[[12, 14, 16], 0] > 0):
                angulos['rodilla_der'] = AngleCalculator.calcular_angulo(
                    keypoints_frame[12], keypoints_frame[14], keypoints_frame[16]
                )

            # Cadera: cadera_izq(11) - cadera_der(12) - rodilla_der(14)
            if all(keypoints_frame[[11, 12, 14], 0] > 0):
                angulos['cadera'] = AngleCalculator.calcular_angulo(
                    keypoints_frame[11], keypoints_frame[12], keypoints_frame[14]
                )

            # Hombro: hombro_izq(5) - hombro_der(6) - codo_der(8)
            if all(keypoints_frame[[5, 6, 8], 0] > 0):
                angulos['hombro'] = AngleCalculator.calcular_angulo(
                    keypoints_frame[5], keypoints_frame[6], keypoints_frame[8]
                )

        return angulos

    @staticmethod
    def extraer_angulos_secuencia(keypoints_por_frame):
        """Extrae la secuencia temporal de diccionarios de ángulos para todos los frames."""
        return [AngleCalculator.extraer_angulos(kpts) for kpts in keypoints_por_frame]
