# src/infrastructure/colab_adapter.py
import requests
from typing import Dict, Any, Optional
from src.domain.interfaces import IInferenceEngine
from src.domain.models import MatrizEsqueletica, Punto3D

class ColabYOLOAdapter(IInferenceEngine):
    """Adaptador HTTP para comunicación remota con el pipeline YOLO26x en Colab o Cloud."""

    def __init__(self, colab_tunnel_url: str):
        self._endpoint = f"{colab_tunnel_url.rstrip('/')}/inferir"
        self.ultimo_frame_base64: Optional[str] = None

    def inferir_esqueleto_3d(self, video_path: str) -> MatrizEsqueletica:
        with open(video_path, 'rb') as video_file:
            response = requests.post(self._endpoint, files={'file': video_file}, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # Capturar el fotograma real retornado por Colab si está presente
            if 'frame_base64' in data and data['frame_base64']:
                self.ultimo_frame_base64 = data['frame_base64']

            puntos = {
                int(k): Punto3D(float(v['x']), float(v['y']), float(v['z'])) 
                for k, v in data['keypoints_3d'].items()
            }
            return MatrizEsqueletica(puntos_3d=puntos)
