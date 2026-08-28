"""
Módulo de Anotación Visual y Compresión Digital de Imágenes (OpenCV / RF-05, RP-02).
Genera el fotograma clave JPG con marcador gráfico sobre la articulación fallida y explicación pedagógica.
"""

from typing import Tuple, Union
import cv2
import numpy as np


class OpenCVAnnotator:
    """
    Componente visual encargado de superponer marcadores gráficos deterministas
    sobre fotogramas clave y comprimir el entregable en formato JPEG optimizado
    para respetar el techo de transferencia de salida (RP-02, <= 100 KB).
    """

    def __init__(
        self,
        radio_circulo: int = 15,
        color_marcador: Tuple[int, int, int] = (0, 0, 255),  # Rojo puro en BGR
        calidad_jpeg: int = 85,
        techo_bytes: int = 98_000,  # Límite estricto inferior a 100 KB
    ) -> None:
        self.radio_circulo = radio_circulo
        self.color_marcador = color_marcador
        self.calidad_jpeg = calidad_jpeg
        self.techo_bytes = techo_bytes

    def marcar_falla(
        self,
        frame_data: Union[bytes, np.ndarray],
        coord_x: int,
        coord_y: int,
        explicacion: str,
    ) -> bytes:
        """
        Superpone un marcador circular sobre la articulación anómala y una caja de texto
        con la explicación técnica pedagógica, retornando los bytes comprimidos en JPG.

        :param frame_data: Fotograma en bytes comprimidos o como matriz NumPy BGR.
        :param coord_x: Coordenada horizontal del píxel del error articular.
        :param coord_y: Coordenada vertical del píxel del error articular.
        :param explicacion: Cadena de texto descriptiva de la falla biomecánica.
        :return: Bytes del fotograma anotado en formato JPG (~80 KB).
        """
        if isinstance(frame_data, bytes):
            nparr = np.frombuffer(frame_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("No se pudo decodificar el flujo de bytes en una imagen válida.")
        elif isinstance(frame_data, np.ndarray):
            img = frame_data.copy()
        else:
            raise TypeError("frame_data debe ser de tipo bytes o np.ndarray.")

        alto, ancho = img.shape[:2]

        # 1. Dibujar círculo rojo sólido en (coord_x, coord_y)
        centro = (int(coord_x), int(coord_y))
        cv2.circle(
            img,
            centro,
            radius=self.radio_circulo,
            color=self.color_marcador,
            thickness=-1,
            lineType=cv2.LINE_AA,
        )

        # 2. Dibujar anillo exterior blanco para contraste visual de alta definición
        cv2.circle(
            img,
            centro,
            radius=self.radio_circulo + 3,
            color=(255, 255, 255),
            thickness=2,
            lineType=cv2.LINE_AA,
        )

        # 3. Preparar dimensiones del texto y caja de fondo semitransparente
        fuente = cv2.FONT_HERSHEY_SIMPLEX
        escala_fuente = 0.5
        grosor_fuente = 1
        padding = 8

        (ancho_texto, alto_texto), linea_base = cv2.getTextSize(
            explicacion, fuente, escala_fuente, grosor_fuente
        )

        pos_y = coord_y + self.radio_circulo + 25
        if pos_y + alto_texto + padding > alto:
            pos_y = max(alto_texto + padding, coord_y - self.radio_circulo - 15)

        pos_x = max(padding, min(coord_x - (ancho_texto // 2), ancho - ancho_texto - padding))

        x1 = max(0, pos_x - padding)
        y1 = max(0, pos_y - alto_texto - padding)
        x2 = min(ancho, pos_x + ancho_texto + padding)
        y2 = min(alto, pos_y + linea_base + padding)

        overlay = img.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 0), thickness=-1)
        alpha = 0.65
        cv2.addWeighted(overlay, alpha, img, 1.0 - alpha, 0, img)

        cv2.putText(
            img,
            explicacion,
            (pos_x, pos_y),
            fuente,
            escala_fuente,
            (255, 255, 255),
            grosor_fuente,
            lineType=cv2.LINE_AA,
        )

        # 4. Compresión JPEG adaptativa con salvaguarda contractual RP-02 (< 100 KB)
        calidad = self.calidad_jpeg
        exito, imagen_codificada = cv2.imencode(
            ".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), calidad]
        )

        # Si el tamaño supera el umbral, reducir calidad o redimensionar progresivamente
        while len(imagen_codificada) > self.techo_bytes and calidad > 30:
            calidad -= 15
            exito, imagen_codificada = cv2.imencode(
                ".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), calidad]
            )

        if len(imagen_codificada) > self.techo_bytes:
            # Si aún con calidad 30 excede (ej. ruido masivo sintético), reducir resolución un 20%
            factor_escala = 0.8
            img_reducida = cv2.resize(
                img, (int(ancho * factor_escala), int(alto * factor_escala)), interpolation=cv2.INTER_AREA
            )
            exito, imagen_codificada = cv2.imencode(
                ".jpg", img_reducida, [int(cv2.IMWRITE_JPEG_QUALITY), 65]
            )

        if not exito:
            raise RuntimeError("Error en la compresión JPEG del fotograma anotado.")

        return imagen_codificada.tobytes()
