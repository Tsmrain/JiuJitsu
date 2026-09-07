import pytest
import os
import cv2

# Marcar este módulo como "real_model" para no bloquear entornos ligeros de desarrollo
pytestmark = pytest.mark.real_model


class TestYOLOReal:
    """Pruebas de validación con el modelo real YOLO26-pose y videos de entrenamiento."""

    def setup_method(self):
        ultralytics = pytest.importorskip("ultralytics", reason="Librería ultralytics no instalada")
        self.YOLO = ultralytics.YOLO
        self.modelo_path = "yolo26n-pose.pt"
        self.video_maestro = "Videos/Maestro.mp4"
        self.video_alumno = "Videos/Alumno.mp4"

    def test_modelo_carga_correctamente(self):
        """Prueba: el modelo se carga y resuelve el dispositivo de ejecución."""
        model = self.YOLO(self.modelo_path)
        assert model is not None
        print(f"\n✅ Modelo cargado exitosamente en dispositivo: {model.device}")

    def test_deteccion_en_video_real(self):
        """Prueba: inferencia de 17 puntos COCO en un fotograma de video real (RF-02)."""
        if not os.path.exists(self.video_maestro):
            pytest.skip("Video de prueba Maestro.mp4 no disponible en ruta Videos/")

        cap = cv2.VideoCapture(self.video_maestro)
        ret, frame = cap.read()
        cap.release()

        assert ret, "No se pudo leer el primer frame del video Maestro.mp4"

        model = self.YOLO(self.modelo_path)
        results = model(frame, verbose=False)

        assert len(results) > 0
        assert results[0].keypoints is not None
        kpts = results[0].keypoints.xy.cpu().numpy()
        assert len(kpts) > 0
        assert kpts.shape[1] == 17  # 17 puntos COCO
        print(f"\n✅ Detección exitosa: {len(kpts)} persona(s) identificadas con 17 keypoints.")
