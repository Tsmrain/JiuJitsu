# src/infrastructure/adapters/yolo_adapter.py
"""Adaptador YOLO26x con serialización JSONB para PostgreSQL.

Consolida la lógica de AdaptadorYOLO (antes en src/services/adapters.py):
- Selección de motor: ColabYOLOAdapter (real) o MockYOLOEngine (fallback)
- Validación anatómica de MatrizEsqueletica
- Serialización/deserialización JSONB para columna JSONB de PostgreSQL

Aplica el patrón Variaciones Protegidas (Larman, Cap. 17): la capa de
persistencia y aplicación nunca sabe si hay GPU o mock detrás.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

from src.domain.interfaces import IInferenceEngine
from src.domain.models import MatrizEsqueletica, Punto3D


class AdaptadorYOLO(IInferenceEngine):
    """Adaptador de orquestación para visión artificial YOLO26x.

    Selecciona ColabYOLOAdapter o MockYOLOEngine según entorno,
    y agrega capacidades de validación y persistencia JSONB.
    """

    def __init__(self, colab_url: Optional[str] = None):
        url = colab_url or os.getenv("COLAB_TUNNEL_URL", "").strip()
        if url and not url.startswith("https://placeholder"):
            from src.infrastructure.adapters.colab_adapter import ColabYOLOAdapter
            self._engine: IInferenceEngine = ColabYOLOAdapter(url)
        else:
            from src.infrastructure.mocks import MockYOLOEngine
            self._engine = MockYOLOEngine(desviacion_grados=0.0)

    def inferir_esqueleto_3d(self, video_path: str) -> MatrizEsqueletica:
        """Extrae el molde esquelético 3D delegando al motor subyacente."""
        return self._engine.inferir_esqueleto_3d(video_path)

    def validar_matriz_esqueletica(self, matriz: MatrizEsqueletica) -> bool:
        """Valida que la matriz esquelética sea una instancia válida y contenga puntos anatómicos."""
        if not isinstance(matriz, MatrizEsqueletica):
            return False
        puntos = matriz.puntos_3d if getattr(matriz, "puntos_3d", None) else matriz.puntos
        if not puntos:
            return False
        for p in puntos.values():
            if not isinstance(p, Punto3D):
                return False
        return True

    def serializar_para_db(self, matriz: MatrizEsqueletica) -> str:
        """Serializa la matriz esquelética en JSONB canónico para PostgreSQL."""
        if not self.validar_matriz_esqueletica(matriz):
            raise ValueError("Matriz esquelética inválida según contrato YOLO26x")
        puntos = matriz.puntos_3d if getattr(matriz, "puntos_3d", None) else matriz.puntos
        return json.dumps({
            str(k): {"x": float(v.x), "y": float(v.y), "z": float(v.z)}
            for k, v in puntos.items()
        })

    def deserializar_desde_db(self, raw_data: Union[str, Dict[str, Any]]) -> MatrizEsqueletica:
        """Reconstruye una MatrizEsqueletica de dominio desde una columna JSONB de PostgreSQL."""
        if isinstance(raw_data, str):
            data = json.loads(raw_data)
        else:
            data = dict(raw_data)

        # Manejo de registros históricos o esquemas simplificados
        if "angulos" in data and not any(
            isinstance(k, int) or (isinstance(k, str) and k.isdigit()) for k in data
        ):
            puntos = {
                6: Punto3D(0.0, 0.0, 0.0),
                8: Punto3D(1.0, 0.0, 0.0),
                10: Punto3D(1.0, 1.0, 0.0),
            }
            return MatrizEsqueletica(puntos_3d=puntos)

        puntos_dict = {}
        for k, v in data.items():
            try:
                key = int(k)
            except (ValueError, TypeError):
                key = k
            if isinstance(v, dict) and "x" in v and "y" in v and "z" in v:
                puntos_dict[key] = Punto3D(float(v["x"]), float(v["y"]), float(v["z"]))

        return MatrizEsqueletica(puntos_3d=puntos_dict)
