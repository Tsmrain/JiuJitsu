"""
Utilidades geométricas y cálculos cinemáticos 3D para análisis biomecánico.

Aplica el patrón GRASP Information Expert (Craig Larman), centralizando las operaciones
trigonométricas vectoriales en el espacio tridimensional (R3).
"""

import math
from typing import Any, Sequence, Union

from src.domain.interfaces import Keypoint


class GeometryUtils:
    """
    Experto en Información para cálculo de vectores, distancias y ángulos 3D.
    """

    @staticmethod
    def _extract_coords(point: Any) -> Sequence[float]:
        """
        Extrae las coordenadas (x, y, z) de un objeto Keypoint, array numpy, tupla o lista.
        """
        if isinstance(point, Keypoint):
            return (point.x, point.y, point.z)
        if hasattr(point, "tolist"):
            point = point.tolist()
        if isinstance(point, (list, tuple)):
            x = float(point[0])
            y = float(point[1])
            z = float(point[2]) if len(point) > 2 else 0.0
            return (x, y, z)
        raise TypeError(f"Tipo de dato de punto no soportado: {type(point)}")

    @staticmethod
    def calculate_3d_angle(
        p1: Union[Keypoint, Sequence[float], Any],
        p2: Union[Keypoint, Sequence[float], Any],
        p3: Union[Keypoint, Sequence[float], Any],
    ) -> float:
        """
        Calcula el ángulo articular 3D en grados formado por tres puntos (p1 - p2 - p3),
        donde p2 representa el vértice articular (ej. codo, rodilla o cadera).

        Fórmula matemática:
            v1 = p1 - p2
            v2 = p3 - p2
            cos(theta) = (v1 . v2) / (||v1|| * ||v2||)
            theta_deg = arccos(cos(theta)) * (180 / pi)

        Args:
            p1: Punto extremo 1 (ej. hombro).
            p2: Vértice del ángulo (ej. codo).
            p3: Punto extremo 2 (ej. muñeca).

        Returns:
            Ángulo en grados en el rango [0.0, 180.0]. Retorna 0.0 en caso de puntos degenerados o idénticos.
        """
        c1 = GeometryUtils._extract_coords(p1)
        c2 = GeometryUtils._extract_coords(p2)
        c3 = GeometryUtils._extract_coords(p3)

        # Vectores directores relativos al vértice p2
        v1 = (c1[0] - c2[0], c1[1] - c2[1], c1[2] - c2[2])
        v2 = (c3[0] - c2[0], c3[1] - c2[1], c3[2] - c2[2])

        # Producto escalar (dot product)
        dot_product = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

        # Magnitudes euclidianas (normas)
        norm_v1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2])
        norm_v2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1] + v2[2] * v2[2])

        # Manejo de casos límite / división por cero (puntos superpuestos o colapsados)
        if norm_v1 == 0.0 or norm_v2 == 0.0:
            return 0.0

        # Coseno del ángulo acotado a [-1.0, 1.0] para evitar errores de precisión de punto flotante
        cos_theta = dot_product / (norm_v1 * norm_v2)
        cos_theta = max(-1.0, min(1.0, cos_theta))

        # Conversión a grados sexagesimales
        angle_radians = math.acos(cos_theta)
        angle_degrees = math.degrees(angle_radians)

        return float(round(angle_degrees, 4))
