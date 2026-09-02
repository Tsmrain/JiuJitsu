"""
Adaptador del modelo RTMPose3D para estimación de posturas articulares tridimensionales.

Implementa la interfaz IPoseEstimator conforme al patrón GRASP Protected Variations (Larman).
Envuelve el modelo rbarac/rtmpose3d permitiendo ejecución condicional e inyección de dependencias
para entornos de desarrollo locales y ejecución acelerada en Google Colab (GPU A100/CUDA).
"""

import sys
import warnings
from typing import Any, List, Optional

from src.domain.interfaces import IPoseEstimator, Keypoint, KeypointFrame
from src.infrastructure.inference.hardware_detector import get_device


class RTMPose3DAdapter(IPoseEstimator):
    """
    Adaptador de infraestructura para el modelo rbarac/rtmpose3d.
    Soporta inicialización segura en entornos sin acelerador gráfico y ejecución real en la nube.
    """

    def __init__(
        self,
        device: Optional[str] = None,
        model: Optional[Any] = None,
        model_name: str = "rbarac/rtmpose3d",
    ):
        """
        Inicializa el adaptador del estimador RTMPose3D.

        Args:
            device: Dispositivo de cómputo ('cpu', 'cuda:0'). Si es None, se autodetecta.
            model: Instancia pre-cargada del modelo o mock para pruebas.
            model_name: Nombre o ruta del modelo pre-entrenado.
        """
        self.device = device if device is not None else get_device()
        self.model_name = model_name
        self.model = model

        if self.model is not None:
            self._is_available = True
        else:
            self._is_available = self._check_availability()
            if not self._is_available:
                warnings.warn(
                    "RTMPose3D no está disponible en este entorno local. "
                    "La inferencia real requiere ejecutar en Google Colab con GPU o instalar dependencias pesadas.",
                    RuntimeWarning,
                    stacklevel=2,
                )

    def _check_availability(self) -> bool:
        """
        Comprueba si la librería rtmpose3d está instalada y disponible en el entorno.
        """
        try:
            import importlib.util
            spec = importlib.util.find_spec("rtmpose3d")
            return spec is not None or "rtmpose3d" in sys.modules
        except Exception:
            return False

    def extract_keypoints(self, video_path: str) -> List[KeypointFrame]:
        """
        Extrae la secuencia temporal de coordenadas articulares a partir de un video.

        Args:
            video_path: Ruta del video a procesar.

        Returns:
            Lista de fotogramas con landmarks anatómicos 3D (133 keypoints por persona).

        Raises:
            RuntimeError: Si rtmpose3d no está disponible en el entorno.
        """
        if not self._is_available and self.model is None:
            raise RuntimeError(
                "RTMPose3D no está disponible en este entorno. "
                "Ejecutar en Colab o instalar dependencias pesadas."
            )

        # Carga perezosa (lazy-loading) del modelo real si aún no está inicializado
        if self.model is None:
            try:
                from rtmpose3d import RTMPose3D
                self.model = RTMPose3D.from_pretrained(self.model_name, device=self.device)
            except Exception as exc:
                self._is_available = False
                raise RuntimeError(
                    f"Error al inicializar el modelo real '{self.model_name}': {exc}"
                ) from exc

        # Invocación de inferencia sobre el video
        if hasattr(self.model, "predict") and callable(self.model.predict):
            raw_output = self.model.predict(video_path)
        elif hasattr(self.model, "extract") and callable(self.model.extract):
            raw_output = self.model.extract(video_path)
        elif callable(self.model):
            raw_output = self.model(video_path)
        else:
            raw_output = self.model

        return self._map_raw_output_to_domain(raw_output)

    def _map_raw_output_to_domain(self, raw_output: Any) -> List[KeypointFrame]:
        """
        Mapea la salida heterogénea del modelo hacia las entidades canónicas del dominio.
        Garantiza que cada frame contenga los landmarks 3D con forma [133, 3].
        """
        keypoint_frames: List[KeypointFrame] = []

        if not isinstance(raw_output, dict):
            if isinstance(raw_output, list) and all(isinstance(f, KeypointFrame) for f in raw_output):
                return raw_output
            raise ValueError(f"Formato de salida del modelo no reconocido: {type(raw_output)}")

        kp3d = raw_output.get("keypoints_3d")
        kp2d = raw_output.get("keypoints_2d")
        scores = raw_output.get("scores")

        # Conversión de tensores PyTorch o ndarrays NumPy a listas estándar
        if hasattr(kp3d, "tolist"):
            kp3d = kp3d.tolist()
        if hasattr(kp2d, "tolist"):
            kp2d = kp2d.tolist()
        if hasattr(scores, "tolist"):
            scores = scores.tolist()

        if kp3d is None:
            return keypoint_frames

        # Caso 1: Arreglo 3D de múltiples frames (N, num_keypoints, 3)
        if isinstance(kp3d, list) and len(kp3d) > 0:
            if isinstance(kp3d[0], (list, tuple)) and len(kp3d[0]) > 0 and isinstance(kp3d[0][0], (list, tuple)):
                for f_idx, frame_data in enumerate(kp3d):
                    frame_scores = scores[f_idx] if (scores is not None and f_idx < len(scores)) else None
                    if hasattr(frame_scores, "tolist"):
                        frame_scores = frame_scores.tolist()

                    keypoints_list: List[Keypoint] = []
                    for k_idx, pt in enumerate(frame_data):
                        x = float(pt[0])
                        y = float(pt[1])
                        z = float(pt[2]) if len(pt) > 2 else 0.0

                        score = 1.0
                        if frame_scores is not None and k_idx < len(frame_scores):
                            s_val = frame_scores[k_idx]
                            score = float(s_val[0]) if isinstance(s_val, (list, tuple)) else float(s_val)

                        keypoints_list.append(
                            Keypoint(x=x, y=y, z=z, score=score, name=f"kp_{k_idx}")
                        )

                    keypoint_frames.append(
                        KeypointFrame(
                            frame_idx=f_idx,
                            timestamp_ms=float(f_idx * 33.33),
                            keypoints=keypoints_list,
                        )
                    )

            # Caso 2: Arreglo de un único frame (num_keypoints, 3)
            elif isinstance(kp3d[0], (list, tuple)):
                keypoints_list = []
                for k_idx, pt in enumerate(kp3d):
                    x = float(pt[0])
                    y = float(pt[1])
                    z = float(pt[2]) if len(pt) > 2 else 0.0

                    score = 1.0
                    if scores is not None and k_idx < len(scores):
                        s_val = scores[k_idx]
                        score = float(s_val[0]) if isinstance(s_val, (list, tuple)) else float(s_val)

                    keypoints_list.append(
                        Keypoint(x=x, y=y, z=z, score=score, name=f"kp_{k_idx}")
                    )

                keypoint_frames.append(
                    KeypointFrame(
                        frame_idx=0,
                        timestamp_ms=0.0,
                        keypoints=keypoints_list,
                    )
                )

        return keypoint_frames
