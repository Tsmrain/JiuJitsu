import os
import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from .config import MODELOS_DIR, MODELO_YOLO, IS_COLAB


class PoseExtractor:
    """
    Adaptador de inferencia para extracción de poses y keypoints
    utilizando la arquitectura YOLO26-pose (Ultralytics).
    """

    def __init__(self, modelo_path=None):
        if YOLO is None:
            raise ImportError(
                "La librería 'ultralytics' no está instalada. "
                "Ejecute 'pip install ultralytics>=8.4.0' para habilitar inferencia con YOLO26-pose."
            )
        if modelo_path is None:
            modelo_path = MODELO_YOLO
        
        # Si está en Colab y el modelo existe en Drive, priorizarlo
        if IS_COLAB:
            drive_modelo = os.path.join(MODELOS_DIR, MODELO_YOLO)
            if os.path.exists(drive_modelo):
                modelo_path = drive_modelo

        self.model = YOLO(modelo_path)
        print(f"✅ Modelo YOLO cargado exitosamente. Dispositivo asignado: {self.model.device}")

    def extraer_keypoints_video(self, ruta_video, limite_frames=None):
        """
        Extrae la matriz de keypoints [N, 17, 2] y la lista de fotogramas
        a partir de un archivo de video.
        """
        if not os.path.exists(ruta_video):
            raise FileNotFoundError(f"No se encontró el video en la ruta: {ruta_video}")

        cap = cv2.VideoCapture(ruta_video)
        if not cap.isOpened():
            raise IOError(f"No se pudo abrir el archivo de video: {ruta_video}")

        keypoints_por_frame = []
        frames = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if limite_frames is not None and frame_count >= limite_frames:
                break

            results = self.model(frame, verbose=False)

            if len(results) > 0 and results[0].keypoints is not None:
                kpts = results[0].keypoints.xy.cpu().numpy()
                if len(kpts) > 0:
                    keypoints_por_frame.append(kpts[0])
                    frames.append(frame)

            frame_count += 1

        cap.release()
        return np.array(keypoints_por_frame), frames

    def procesar_video(self, ruta_video):
        """Procesa un video completo y devuelve keypoints y fotogramas leídos."""
        return self.extraer_keypoints_video(ruta_video)
