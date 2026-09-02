"""
Anotador gráfico de fotogramas para retroalimentación visual biomecánica.

Implementa la inyección de marcadores visuales (círculo rojo y texto explicativo)
en las coordenadas 2D exactas de la articulación biomecánica donde se detectó el fallo,
cumpliendo con los requisitos de retroalimentación pedagógica (RF-05).
"""

from typing import Any, Optional, Tuple


class FrameAnnotator:
    """
    Componente de infraestructura encargado del post-procesamiento gráfico de imágenes con OpenCV.
    """

    def annotate_error(
        self,
        frame: Any,
        keypoint_2d: Tuple[float, float],
        deviation_angle: Optional[float] = None,
        radius: int = 15,
        color: Tuple[int, int, int] = (0, 0, 255),  # Rojo BGR por defecto
        thickness: int = 3,
    ) -> Any:
        """
        Dibuja un círculo rojo en el fotograma sobre la articulación defectuosa y anota la desviación.

        Args:
            frame: Matriz de imagen o arreglo NumPy que representa el fotograma.
            keypoint_2d: Tupla (x, y) con las coordenadas espaciales del keypoint en la imagen.
            deviation_angle: Magnitud del error angular en grados (opcional).
            radius: Radio del círculo en píxeles (por defecto 15 px).
            color: Tupla BGR del color del marcador (por defecto Rojo: (0, 0, 255)).
            thickness: Grosor de la línea del círculo en píxeles (por defecto 3 px).

        Returns:
            Matriz de imagen con las anotaciones gráficas inyectadas.
        """
        if frame is None:
            return None

        # Clonar el fotograma para garantizar inmutabilidad del original
        if hasattr(frame, "copy"):
            annotated = frame.copy()
        else:
            annotated = frame

        center_x = int(round(float(keypoint_2d[0])))
        center_y = int(round(float(keypoint_2d[1])))
        center = (center_x, center_y)

        try:
            import cv2
            # 1. Dibujar círculo rojo sobre el nodo articular fallido
            cv2.circle(annotated, center, radius, color, thickness)

            # 2. Inyectar etiqueta de texto explicativo si se especifica el ángulo
            if deviation_angle is not None:
                text = f"Error: {deviation_angle:.1f} deg"
                text_pos = (center_x + radius + 5, max(25, center_y - 5))
                # Sombra negra para legibilidad sobre cualquier fondo
                cv2.putText(
                    annotated,
                    text,
                    text_pos,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 0),
                    3,
                    cv2.LINE_AA,
                )
                # Texto en color de alerta (rojo)
                cv2.putText(
                    annotated,
                    text,
                    text_pos,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                    cv2.LINE_AA,
                )
        except ImportError:
            # En entornos sin OpenCV, retornar el fotograma sin interrumpir la ejecución
            pass

        return annotated
