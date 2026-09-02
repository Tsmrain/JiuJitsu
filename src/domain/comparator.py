"""
Comparador biomecánico para evaluación de ejecución técnica articular.

Aplica el patrón GRASP Information Expert (Craig Larman), utilizando GeometryUtils
para contrastar los ángulos tridimensionales reales de las articulaciones (grados)
frente al umbral de tolerancia pedagógica (por defecto 15°).
"""

from typing import List, Optional, Tuple

from src.domain.entities import ComparisonResult
from src.domain.geometry_utils import GeometryUtils
from src.domain.interfaces import KeypointFrame

# Tripletes anatómicos estándar (COCO / Halpe 133):
# - Brazo Izquierdo: Hombro (5), Codo (7), Muñeca (9)
# - Brazo Derecho: Hombro (6), Codo (8), Muñeca (10)
# - Pierna Izquierda: Cadera (11), Rodilla (13), Tobillo (15)
# - Pierna Derecha: Cadera (12), Rodilla (14), Tobillo (16)
DEFAULT_ANATOMICAL_TRIPLETS: List[Tuple[int, int, int]] = [
    (5, 7, 9),
    (6, 8, 10),
    (11, 13, 15),
    (12, 14, 16),
]


class BiomechanicsComparator:
    """
    Servicio de dominio experto en la comparación y diagnóstico cinemático
    angular entre la técnica maestra (Head Coach) y la ejecución del alumno.
    """

    def compare(
        self,
        teacher_frames: List[KeypointFrame],
        student_frames: List[KeypointFrame],
        threshold_degrees: float = 15.0,
        triplets: Optional[List[Tuple[int, int, int]]] = None,
    ) -> ComparisonResult:
        """
        Compara la secuencia de fotogramas del maestro contra la del alumno
        evaluando las discrepancias en los ángulos articulares 3D reales.

        Args:
            teacher_frames: Secuencia temporal de landmarks de la técnica maestra.
            student_frames: Secuencia temporal de landmarks de la ejecución del alumno.
            threshold_degrees: Umbral de tolerancia de desviación angular en grados (por defecto 15.0°).
            triplets: Lista de tuplas (p1, p2, p3) con los índices de keypoints a evaluar.
                      Si es None, utiliza DEFAULT_ANATOMICAL_TRIPLETS.

        Returns:
            Instancia de ComparisonResult con el dictamen de corrección, la máxima desviación angular
            y las coordenadas del fotograma y articulación defectuosa.
        """
        if not teacher_frames or not student_frames:
            return ComparisonResult(
                is_correct=False,
                max_deviation_angle=0.0,
                error_frame_index=0,
                error_keypoint_index=0,
            )

        active_triplets = triplets if triplets is not None else DEFAULT_ANATOMICAL_TRIPLETS
        num_frames = min(len(teacher_frames), len(student_frames))

        max_deviation = 0.0
        worst_frame_idx = 0
        worst_keypoint_idx = active_triplets[0][1] if active_triplets else 0

        for f_idx in range(num_frames):
            t_frame = teacher_frames[f_idx]
            s_frame = student_frames[f_idx]

            t_kps = t_frame.keypoints
            s_kps = s_frame.keypoints

            for p1_idx, p2_idx, p3_idx in active_triplets:
                # Validar que los índices existan en ambos frames
                if (
                    p1_idx < len(t_kps)
                    and p2_idx < len(t_kps)
                    and p3_idx < len(t_kps)
                    and p1_idx < len(s_kps)
                    and p2_idx < len(s_kps)
                    and p3_idx < len(s_kps)
                ):
                    # Calcular ángulo articular del maestro (grados)
                    teacher_angle = GeometryUtils.calculate_3d_angle(
                        t_kps[p1_idx], t_kps[p2_idx], t_kps[p3_idx]
                    )

                    # Calcular ángulo articular del alumno (grados)
                    student_angle = GeometryUtils.calculate_3d_angle(
                        s_kps[p1_idx], s_kps[p2_idx], s_kps[p3_idx]
                    )

                    # Discrepancia angular absoluta
                    angular_diff = abs(teacher_angle - student_angle)

                    if angular_diff > max_deviation:
                        max_deviation = angular_diff
                        worst_frame_idx = f_idx
                        worst_keypoint_idx = p2_idx  # El vértice articular (ej. codo)

        is_correct = max_deviation <= threshold_degrees

        return ComparisonResult(
            is_correct=is_correct,
            max_deviation_angle=round(max_deviation, 4),
            error_frame_index=worst_frame_idx,
            error_keypoint_index=worst_keypoint_idx,
        )
