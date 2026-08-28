"""
Pruebas Unitarias para el Anotador Visual OpenCVAnnotator (Craig Larman / TDD).
"""

import unittest
import cv2
import numpy as np
from src.services.opencv_annotator import OpenCVAnnotator


class TestOpenCVAnnotator(unittest.TestCase):

    def setUp(self) -> None:
        self.annotator = OpenCVAnnotator(radio_circulo=15, calidad_jpeg=85)

    def test_marcado_falla_retorna_bytes_jpg_valido(self) -> None:
        """Prueba 1: Verifica que marcar_falla retorne un stream de bytes JPEG válido y no vacío."""
        # Generar fotograma de prueba de 640x480
        frame_dummy = np.full((480, 640, 3), 200, dtype=np.uint8)
        coord_x, coord_y = 320, 240
        explicacion = "Error angular: Codo hiper-extendido en 35.5 grados"

        resultado_bytes = self.annotator.marcar_falla(frame_dummy, coord_x, coord_y, explicacion)

        self.assertIsInstance(resultado_bytes, bytes)
        self.assertGreater(len(resultado_bytes), 0)

    def test_tamano_imagen_respeta_techo_rp02(self) -> None:
        """Prueba 2: Verifica que el archivo JPG comprimido no supere los 100 KB (RP-02)."""
        # Simulación de fotograma realista de cámara de video (tatami con degradado y atletas)
        y = np.linspace(0, 255, 720, dtype=np.uint8)
        x = np.linspace(0, 255, 1280, dtype=np.uint8)
        xv, yv = np.meshgrid(x, y)
        frame_realista = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame_realista[:, :, 0] = xv
        frame_realista[:, :, 1] = yv
        frame_realista[:, :, 2] = 120

        coord_x, coord_y = 600, 350
        explicacion = "Desalineacion critica en rodilla derecha (> 25.0 deg)"

        resultado_bytes = self.annotator.marcar_falla(frame_realista, coord_x, coord_y, explicacion)

        tamano_kb = len(resultado_bytes) / 1024.0
        # Techo contractual de 100 KB
        self.assertLess(
            len(resultado_bytes),
            100_000,
            f"El tamaño del fotograma anotado ({tamano_kb:.2f} KB) debe ser inferior a 100 KB (RP-02)",
        )

    def test_verificacion_grafica_marcador_rojo(self) -> None:
        """Prueba 3: Decodifica la imagen resultante y comprueba la presencia del círculo rojo en la coordenada."""
        # Frame negro para facilitar la detección de color
        frame_negro = np.zeros((480, 640, 3), dtype=np.uint8)
        coord_x, coord_y = 200, 150
        explicacion = "Articulacion hombro izquierdo con apertura deficiente"

        resultado_bytes = self.annotator.marcar_falla(frame_negro, coord_x, coord_y, explicacion)

        # Decodificar el JPG resultante
        nparr = np.frombuffer(resultado_bytes, np.uint8)
        img_recuperada = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        self.assertIsNotNone(img_recuperada)
        pixel_centro = img_recuperada[coord_y, coord_x]
        azul, verde, rojo = int(pixel_centro[0]), int(pixel_centro[1]), int(pixel_centro[2])

        self.assertGreater(rojo, 180, f"El canal rojo debe ser dominante en el centro del marcador (R={rojo})")
        self.assertLess(azul, 60, f"El canal azul debe ser bajo en el centro del marcador (B={azul})")
        self.assertLess(verde, 60, f"El canal verde debe ser bajo en el centro del marcador (G={verde})")

    def test_entrada_bytes_comprimidos_valida(self) -> None:
        """Prueba 4: Comprueba que el anotador acepte también imágenes previamente codificadas en bytes."""
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        _, bytes_iniciales = cv2.imencode(".jpg", frame)

        resultado = self.annotator.marcar_falla(
            bytes_iniciales.tobytes(), 100, 100, "Prueba con entrada en bytes"
        )
        self.assertIsInstance(resultado, bytes)
        self.assertGreater(len(resultado), 0)


if __name__ == "__main__":
    unittest.main()
