import os
import cv2
from .config import INDICES_COCO, FOTOGRAMAS_DIR


class FrameAnnotator:
    """
    Anotación gráfica de fotogramas clave con OpenCV
    para generar el entregable visual de error biomecánico (RF-05, RF-06).
    """

    @staticmethod
    def anotar_error(frame, keypoints, articulacion, error_angulo, frame_idx):
        """
        Inyecta un marcador visual (círculo rojo y texto descriptivo)
        en las coordenadas de la articulación con mayor desviación.
        """
        frame_copy = frame.copy()
        idx = INDICES_COCO.get(articulacion, 7)

        if len(keypoints) > idx:
            x, y = int(keypoints[idx][0]), int(keypoints[idx][1])

            # Círculos concéntricos rojos (RF-05)
            cv2.circle(frame_copy, (x, y), 20, (0, 0, 255), 2)
            cv2.circle(frame_copy, (x, y), 14, (0, 0, 255), -1)

            # Texto descriptivo del error angular
            nombre_art = articulacion.replace('_', ' ').upper()
            cv2.putText(
                frame_copy, f"ERROR: {error_angulo:.1f} DEG", (max(10, x - 80), max(20, y - 50)),
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
    def guardar(frame, nombre, directorio=None):
        """
        Guarda el fotograma anotado en formato JPG optimizado (~80 KB).
        """
        if directorio is None:
            directorio = FOTOGRAMAS_DIR

        os.makedirs(directorio, exist_ok=True)
        ruta = os.path.join(directorio, nombre)
        # Calidad JPEG 85 para balance óptimo de compresión y legibilidad (~80 KB)
        cv2.imwrite(ruta, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return ruta
