# src/application/controllers.py
from typing import Dict, Any, List, Optional
from src.domain.interfaces import IInferenceEngine, IGenerationService, ITecnicaRepository
from src.domain.models import CalculadoraBiomecanica, DesviacionArticular

class EvaluacionController:
    """Controlador de Aplicación para el caso de uso CU-02: Cargar Video y Evaluar."""
    
    def __init__(
        self, 
        inference_engine: IInferenceEngine,
        generation_service: IGenerationService,
        tecnica_repository: ITecnicaRepository
    ):
        self._inference_engine = inference_engine
        self._generation_service = generation_service
        self._tecnica_repository = tecnica_repository
        self._calculadora = CalculadoraBiomecanica()

    def evaluar_ejecucion(
        self, 
        video_path: str, 
        id_tecnica: str, 
        contexto_manual: Optional[str] = None, 
        score_similitud: float = 1.0
    ) -> Dict[str, Any]:
        """Evalúa la ejecución técnica contrastándola con el patrón e incorpora Fallback RAG."""
        # 1. Obtener la técnica patrón de referencia
        patron = self._tecnica_repository.obtener_patron(id_tecnica)
        if not patron:
            raise ValueError(f"Técnica patrón '{id_tecnica}' no encontrada.")

        # 2. Extraer esqueleto 3D del video del alumno
        esqueleto_alumno = self._inference_engine.inferir_esqueleto_3d(video_path)

        # 3. Evaluar desviaciones usando la lógica pura de Dominio
        articulaciones_a_evaluar = [(6, 8, 10, "Codo Derecho")]
        desviaciones: List[DesviacionArticular] = self._calculadora.evaluar_desviaciones(
            esqueleto_alumno, patron, articulaciones_a_evaluar, umbral_tolerancia_grados=5.0
        )

        # Regla de Fallback Larman: Si la similitud semántica es baja (< 0.65), se descarta el contexto
        texto_contexto_final = contexto_manual if (contexto_manual and score_similitud >= 0.65) else None

        # 4. Generar consejo pedagógico con la IA
        consejo = self._generation_service.generar_consejo(
            id_tecnica, 
            desviaciones, 
            contexto_manual=texto_contexto_final
        )

        # 5. Estructurar el DTO de respuesta para la PWA
        return {
            "id_tecnica": id_tecnica,
            "es_valido": len(desviaciones) == 0,
            "total_desviaciones": len(desviaciones),
            "desviaciones": [
                {
                    "articulacion": d.nombre_articulacion,
                    "esperado": d.angulo_esperado,
                    "real": d.angulo_real,
                    "desviacion": d.desviacion_grados
                }
                for d in desviaciones
            ],
            "consejo_pedagogico": consejo
        }
