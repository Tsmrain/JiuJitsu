"""
Servicio de Aplicación para Análisis Biomecánico y Diagnóstico de Técnicas.

Implementa el patrón GRASP Controller (Use Case Controller de Craig Larman),
orquestando el flujo completo de evaluación:
Almacenamiento -> Inferencia Pose 3D -> Comparación Biomecánica -> Anotación Visual.
"""

from typing import Any, Dict, Optional

from src.domain.comparator import BiomechanicsComparator
from src.domain.interfaces import IPoseEstimator, IStorageProvider
from src.infrastructure.vision.frame_annotator import FrameAnnotator


class TechniqueAnalysisService:
    """
    Controlador de caso de uso para la evaluación biomecánica y feedback al alumno.
    """

    def __init__(
        self,
        storage: IStorageProvider,
        estimator: IPoseEstimator,
        comparator: BiomechanicsComparator,
        annotator: FrameAnnotator,
    ):
        """
        Inyección de dependencias de la arquitectura en capas.
        """
        self.storage = storage
        self.estimator = estimator
        self.comparator = comparator
        self.annotator = annotator

    def analyze_technique(
        self,
        teacher_video_path: str,
        student_video_path: str,
        technique_name: str = "Defensa de Montada",
        threshold_degrees: float = 15.0,
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de análisis biomecánico:
        1. Extrae landmarks articulares 3D de ambos videos con RTMPose3D.
        2. Compara los ángulos articulares frame a frame contra la referencia maestra.
        3. Si la técnica es incorrecta, extrae el frame del fallo y anota el círculo rojo en la articulación.

        Args:
            teacher_video_path: Ruta al video canónico del Head Coach.
            student_video_path: Ruta al video de ejecución del alumno.
            technique_name: Nombre identificador de la técnica de Jiu-Jitsu.
            threshold_degrees: Umbral de tolerancia angular en grados.

        Returns:
            Diccionario estructurado con el resultado del análisis y el fotograma anotado.
        """
        # 1. Extracción de poses 3D (Inferencia)
        teacher_frames = self.estimator.extract_keypoints(teacher_video_path)
        student_frames = self.estimator.extract_keypoints(student_video_path)

        # 2. Comparación angular biomecánica (Dominio)
        result = self.comparator.compare(
            teacher_frames=teacher_frames,
            student_frames=student_frames,
            threshold_degrees=threshold_degrees,
        )

        annotated_frame = None

        # 3. Anotación gráfica si se detecta error técnico (Post-procesamiento)
        if not result.is_correct and student_frames:
            error_f_idx = result.error_frame_index
            error_k_idx = result.error_keypoint_index

            # Obtener el fotograma sin procesar desde el proveedor de almacenamiento
            raw_frame = self.storage.get_frame(student_video_path, error_f_idx)

            # Obtener coordenadas del keypoint defectuoso
            if error_f_idx < len(student_frames):
                frame_data = student_frames[error_f_idx]
                if error_k_idx < len(frame_data.keypoints):
                    kp = frame_data.keypoints[error_k_idx]
                    keypoint_2d = (kp.x, kp.y)

                    annotated_frame = self.annotator.annotate_error(
                        frame=raw_frame,
                        keypoint_2d=keypoint_2d,
                        deviation_angle=result.max_deviation_angle,
                    )

        return {
            "technique_name": technique_name,
            "is_correct": result.is_correct,
            "max_deviation_angle": result.max_deviation_angle,
            "error_frame_index": result.error_frame_index,
            "error_keypoint_index": result.error_keypoint_index,
            "annotated_frame": annotated_frame,
            "comparison_result": result,
        }
