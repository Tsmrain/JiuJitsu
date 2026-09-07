import os
import cv2
import numpy as np

from ..domain.interfaces import IFrameAnnotator
from ..config import INDICES_COCO, FOTOGRAMAS_DIR


class FrameAnnotatorImpl(IFrameAnnotator):
    """
    Servicio de infraestructura para inyección de marcadores visuales con OpenCV (Pure Fabrication).
    Genera el entregable visual JPG optimizado (~80 KB) sobre la articulación defectuosa (RF-05, RF-06).
    """

    def anotar_error(
        self, frame: np.ndarray, keypoints: np.ndarray,
        articulacion: str, error: float, frame_idx: int
    ) -> np.ndarray:
        """
        Inyecta círculos concéntricos rojos y texto descriptivo en las coordenadas de la articulación.
        """
        frame_copy = frame.copy()
        idx = INDICES_COCO.get(articulacion, 7)

        if len(keypoints) > idx:
            x, y = int(keypoints[idx][0]), int(keypoints[idx][1])

            # Círculos concéntricos rojos (RF-05)
            cv2.circle(frame_copy, (x, y), 20, (0, 0, 255), 2)
            cv2.circle(frame_copy, (x, y), 14, (0, 0, 255), -1)

            # Rótulo de diagnóstico
            nombre_art = articulacion.replace('_', ' ').upper()
            cv2.putText(
                frame_copy, f"ERROR: {error:.1f} DEG", (max(10, x - 80), max(20, y - 50)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2, cv2.LINE_AA
            )
            cv2.putText(
                frame_copy, nombre_art, (max(10, x - 80), max(40, y - 25)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2, cv2.LINE_AA
            )
            cv2.putText(
                frame_copy, f"Frame: {frame_idx}", (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA
            )

        return frame_copy

    @staticmethod
    def guardar(frame: np.ndarray, nombre: str, directorio: str = None) -> str:
        """Guarda un fotograma como imagen JPEG optimizada."""
        if directorio is None:
            directorio = FOTOGRAMAS_DIR
        os.makedirs(directorio, exist_ok=True)
        ruta = os.path.join(directorio, nombre)
        cv2.imwrite(ruta, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return ruta
