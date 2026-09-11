# src/infrastructure/mocks.py
import math
from typing import List, Optional
from src.domain.interfaces import IInferenceEngine, IGenerationService, ITecnicaRepository
from src.domain.models import MatrizEsqueletica, Punto3D, DesviacionArticular

class MockYOLOEngine(IInferenceEngine):
    """Simula la extracción de keypoints 3D de YOLO26x."""
    def __init__(self, desviacion_grados: float = 0.0):
        self._desviacion = desviacion_grados

    def inferir_esqueleto_3d(self, video_path: str) -> MatrizEsqueletica:
        rad = math.radians(90.0 + self._desviacion)
        puntos = {
            6: Punto3D(0.0, 0.0, 0.0),                   # Hombro dcho
            8: Punto3D(1.0, 0.0, 0.0),                   # Codo dcho
            10: Punto3D(1.0 + math.cos(rad), math.sin(rad), 0.0) # Muñeca dcha
        }
        return MatrizEsqueletica(puntos_3d=puntos)

class MockGeminiService(IGenerationService):
    """Simula la respuesta pedagógica de Gemini 3.8 Flash."""
    def generar_consejo(
        self, 
        tecnica: str, 
        desviaciones: List[DesviacionArticular], 
        contexto_manual: Optional[str] = None
    ) -> str:
        if not desviaciones:
            return f"¡Excelente ejecución de {tecnica}! Mantienes la postura del patrón."
        
        falla = desviaciones[0]
        base_msg = (
            f"En {tecnica}, se detectó un desajuste en {falla.nombre_articulacion} "
            f"de {falla.desviacion_grados:.1f}°. Recuerda ajustar el ángulo."
        )
        if contexto_manual:
            return f"{base_msg} Contexto aplicado: {contexto_manual}"
        return base_msg

class MockTecnicaRepository(ITecnicaRepository):
    """Simula el repositorio con el patrón del maestro."""
    def obtener_patron(self, id_tecnica: str) -> Optional[MatrizEsqueletica]:
        puntos_patron = {
            6: Punto3D(0.0, 0.0, 0.0),
            8: Punto3D(1.0, 0.0, 0.0),
            10: Punto3D(1.0, 1.0, 0.0) # Codo a 90 grados exactos
        }
        return MatrizEsqueletica(puntos_3d=puntos_patron)
