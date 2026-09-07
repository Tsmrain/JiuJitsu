import os
import cv2
import numpy as np
from typing import Tuple, List, Optional

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from ...domain.interfaces import IPoseExtractor
from ...domain.value_objects import Keypoint, Frame
from ...config import MODELO_YOLO, IS_COLAB, MODELOS_DIR


class YOLOPoseExtractor(IPoseExtractor):
    """
    Adaptador de inferencia para la arquitectura YOLO26-pose (Protected Variations).
    Implementa la interfaz de dominio IPoseExtractor aislando la dependencia de Ultralytics.
    """

    def __init__(self, modelo_path: Optional[str] = None):
        if YOLO is None:
            raise ImportError(
                "La librería 'ultralytics' no está instalada. "
                "Ejecute 'pip install ultralytics>=8.4.0' para habilitar inferencia con YOLO26-pose."
            )

        if modelo_path is None:
            modelo_path = MODELO_YOLO

        # Si estamos en Colab y el modelo existe en Drive, priorizarlo
        if IS_COLAB:
            drive_modelo = os.path.join(MODELOS_DIR, MODELO_YOLO)
            if os.path.exists(drive_modelo):
                modelo_path = drive_modelo

        self.modelo = YOLO(modelo_path)
        self._dispositivo = str(getattr(self.modelo, 'device', 'cpu'))
        print(f"✅ YOLOPoseExtractor inicializado exitosamente en dispositivo: {self._dispositivo}")

    def extraer_keypoints(self, video_path: str, limite_frames: Optional[int] = None) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        Extrae keypoints [N, 17, 2] y fotogramas leídos de un video.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"No se pudo abrir el video: {video_path}")

        keypoints_por_frame = []
        frames = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if limite_frames is not None and frame_count >= limite_frames:
                break

            results = self.modelo(frame, verbose=False)

            if len(results) > 0 and results[0].keypoints is not None:
                kpts = results[0].keypoints.xy.cpu().numpy()
                if len(kpts) > 0:
                    keypoints_por_frame.append(kpts[0])
                    frames.append(frame)

            frame_count += 1

        cap.release()
        return np.array(keypoints_por_frame), frames

    def extraer_keypoints_por_frame(self, video_path: str) -> List[Frame]:
        """
        Extrae keypoints encapsulados en objetos de valor Frame y Keypoint inmutables.
        """
        kpts_array, frames = self.extraer_keypoints(video_path)
        frames_obj = []

        for i, (kpts, img) in enumerate(zip(kpts_array, frames)):
            keypoints = [
                Keypoint(x=float(kpt[0]), y=float(kpt[1]), confianza=1.0)
                for kpt in kpts
            ]
            frames_obj.append(Frame(index=i, keypoints=keypoints, image=img))

        return frames_obj

    def get_dispositivo(self) -> str:
        return self._dispositivo
