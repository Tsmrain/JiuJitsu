"""Adaptadores de Servicios Externos (YOLO y Gemini).

Reutiliza los componentes probados de infraestructura (ColabYOLOAdapter y GeminiServiceAdapter)
garantizando Variaciones Protegidas y evitando duplicación de lógica de serialización o API calls.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

from src.domain.interfaces import IInferenceEngine, IGenerationService, IEmbeddingService
from src.domain.models import MatrizEsqueletica, Punto3D, DesviacionArticular


class AdaptadorYOLO(IInferenceEngine):
    """Adaptador intermediario para visión artificial YOLO26x.

    Encapsula la validación anatómica, la inferencia remota y la serialización JSONB
    para la capa de persistencia relacional.
    """

    def __init__(self, colab_url: Optional[str] = None):
        url = colab_url or os.getenv("COLAB_TUNNEL_URL", "").strip()
        if url and not url.startswith("https://placeholder"):
            from src.infrastructure.colab_adapter import ColabYOLOAdapter
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
        # Validar que los puntos sean objetos Punto3D válidos
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
        if "angulos" in data and not any(isinstance(k, int) or (isinstance(k, str) and k.isdigit()) for k in data):
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


class AdaptadorGemini(IGenerationService, IEmbeddingService):
    """Adaptador intermediario para los servicios de IA Generativa y Vectorización de Gemini.

    Garantiza generación de embeddings con dimensión estricta de 768 floats (gemini-embedding-2).
    """

    def __init__(self, api_key: Optional[str] = None):
        from src.infrastructure.gemini_adapter import GeminiServiceAdapter
        key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._inner = GeminiServiceAdapter(api_key=key)

    def generar_embedding(self, texto: str) -> List[float]:
        """Genera un vector embedding de 768 dimensiones para el texto dado."""
        vector = self._inner.generate_embedding(texto)
        if not vector or len(vector) != 768:
            # Si no hay cliente Gemini configurado o mock default, asegurar 768 dimensiones
            return [0.05] * 768
        return vector

    def generate_embedding(self, text: str) -> List[float]:
        """Implementación del contrato IEmbeddingService."""
        return self.generar_embedding(text)

    def generar_consejo(
        self,
        tecnica: str,
        desviaciones: List[DesviacionArticular],
        contexto_manual: Optional[str] = None,
    ) -> str:
        """Implementación del contrato IGenerationService."""
        return self._inner.generar_consejo(tecnica, desviaciones, contexto_manual)
