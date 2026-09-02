"""
Entidades y Objetos de Valor del Dominio Biomecánico.

Contiene las estructuras de datos puras de la lógica de negocio (OOP / DDD).
"""

from dataclasses import dataclass


@dataclass
class ComparisonResult:
    """
    Resultado de la comparación biomecánica entre la ejecución del maestro y del alumno.

    Attributes:
        is_correct: Indica si la técnica ejecutada se encuentra dentro de los umbrales tolerados.
        max_deviation_angle: Magnitud máxima de desviación (en grados o distancia euclidiana).
        error_frame_index: Índice del fotograma específico donde se identificó el mayor desvío.
        error_keypoint_index: Índice del landmark o articulación anatómica que presentó el error.
    """
    is_correct: bool
    max_deviation_angle: float
    error_frame_index: int
    error_keypoint_index: int
