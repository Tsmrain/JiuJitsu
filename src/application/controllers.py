# src/application/controllers.py
"""Controlador de Aplicación para el caso de uso CU-02: Cargar Video y Evaluar.

Aplica el patrón GRASP Controlador / Fachada de Sesión (Larman Cap. 16-17):
Coordina el flujo de evaluación biomecánica y delega la recuperación y síntesis
contextual al servicio SintesisPedagogicaService (Pure Fabrication), preservando
Alta Cohesión y Bajo Acoplamiento.
"""

from typing import Dict, Any, List, Optional
from src.domain.interfaces import (
    IInferenceEngine,
    IGenerationService,
    ITecnicaRepository,
    IFuenteConocimientoRepository,
)
from src.domain.models import CalculadoraBiomecanica, DesviacionArticular, ConfiguracionRAG
from src.services.sintesis_pedagogica_service import SintesisPedagogicaService
from src.infrastructure.mocks import InMemoryFuenteConocimientoRepository


class EvaluacionController:
    """Session Facade para el Caso de Uso CU-02: Evaluar Ejecución con Feedback Semántico."""

    def __init__(
        self,
        inference_engine: IInferenceEngine,
        generation_service: IGenerationService,
        tecnica_repository: ITecnicaRepository,
        fuente_repository: Optional[IFuenteConocimientoRepository] = None,
        config_rag: Optional[ConfiguracionRAG] = None,
        sintesis_service: Optional[SintesisPedagogicaService] = None,
    ):
        self._inference_engine = inference_engine
        self._generation_service = generation_service
        self._tecnica_repository = tecnica_repository
        self._fuente_repo = fuente_repository if fuente_repository is not None else InMemoryFuenteConocimientoRepository()
        self._config_rag = config_rag if config_rag is not None else ConfiguracionRAG()
        self._sintesis = (
            sintesis_service
            if sintesis_service is not None
            else SintesisPedagogicaService(repo=self._fuente_repo, config=self._config_rag)
        )
        self._calculadora = CalculadoraBiomecanica()

    def evaluar_ejecucion(
        self,
        video_path: str,
        id_tecnica: str,
        contexto_manual: Optional[str] = None,
        score_similitud: Optional[float] = None,
        embedding_desviacion: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Evalúa la ejecución técnica contrastándola con el patrón e incorpora Feedback RAG."""
        # 1. Obtener la técnica patrón de referencia
        patron_obj = self._tecnica_repository.obtener_patron(id_tecnica)
        if not patron_obj:
            raise ValueError(f"Técnica patrón '{id_tecnica}' no encontrada.")
        patron = getattr(patron_obj, "matriz_esqueletica", patron_obj)

        # 2. Extraer esqueleto 3D del video del alumno
        esqueleto_alumno = self._inference_engine.inferir_esqueleto_3d(video_path)

        # 3. Evaluar desviaciones usando la lógica pura de Dominio
        articulaciones_a_evaluar = [(6, 8, 10, "Codo Derecho")]
        desviaciones: List[DesviacionArticular] = self._calculadora.evaluar_desviaciones(
            esqueleto_alumno, patron, articulaciones_a_evaluar, umbral_tolerancia_grados=5.0
        )

        # 4. Integración RAG vía Pure Fabrication (SintesisPedagogicaService)
        articulacion_critica_nombre = desviaciones[0].nombre_articulacion if desviaciones else "General"

        # Compatibilidad con pruebas sintéticas donde se provee contexto manual y similitud simulada
        if contexto_manual is not None and score_similitud is not None:
            es_valido_contexto = score_similitud >= self._config_rag.umbral_similitud_minima
            texto_contexto_final = contexto_manual if es_valido_contexto else None
            score_final = score_similitud
            uso_fallback = not es_valido_contexto
        else:
            # Flujo dinámico CU-02 orquestado vía SintesisPedagogicaService
            info_rag = self._sintesis.generar_feedback_contextualizado(
                articulacion_critica=articulacion_critica_nombre,
                id_tecnica=id_tecnica,
                embedding_desviacion=embedding_desviacion,
            )
            texto_contexto_final = info_rag["contexto_recuperado"] if not info_rag["usó_fallback"] else None
            score_final = info_rag["score_similitud"]
            uso_fallback = info_rag["usó_fallback"]

        # 5. Generar consejo pedagógico con el servicio de IA
        consejo_raw = self._generation_service.generar_consejo(
            tecnica=patron_obj.nombre,
            desviaciones=desviaciones,
            contexto_manual=texto_contexto_final,
        )

        # Normalizar y estructurar el consejo pedagógico (Larman - GRASP & Variaciones Protegidas)
        if isinstance(consejo_raw, dict):
            def _normalizar_texto(val: Any) -> str:
                if isinstance(val, list):
                    return "\n".join(str(item) for item in val)
                return str(val) if val is not None else ""

            consejo_dict = {
                "analisis_postural": _normalizar_texto(consejo_raw.get("analisis_postural", "")),
                "riesgo_lesion": _normalizar_texto(consejo_raw.get("riesgo_lesion", "")),
                "paso_a_paso": _normalizar_texto(consejo_raw.get("paso_a_paso", "")),
                "resumen_ejecutivo": _normalizar_texto(consejo_raw.get("resumen_ejecutivo", "")),
            }
            resumen = consejo_dict["resumen_ejecutivo"]
            pasos = consejo_dict["paso_a_paso"]
            if resumen and pasos:
                consejo_str = f"{resumen}\n\nPaso a paso correctivo:\n{pasos}"
            else:
                consejo_str = resumen or pasos or str(consejo_raw)
        else:
            consejo_str = str(consejo_raw)
            consejo_dict = {
                "analisis_postural": consejo_str,
                "riesgo_lesion": "No especificado.",
                "paso_a_paso": consejo_str,
                "resumen_ejecutivo": consejo_str
            }

        # 6. Estructurar el DTO de respuesta para la PWA
        return {
            "id_tecnica": id_tecnica,
            "es_valido": len(desviaciones) == 0,
            "total_desviaciones": len(desviaciones),
            "desviaciones": [
                {
                    "articulacion": d.nombre_articulacion,
                    "esperado": d.angulo_esperado,
                    "real": d.angulo_real,
                    "desviacion": d.desviacion_grados,
                }
                for d in desviaciones
            ],
            "consejo_pedagogico": consejo_str,
            "consejo_estructurado": consejo_dict,
            "score_similitud_rag": score_final,
            "usó_fallback_rag": uso_fallback,
        }

    def solicitar_evaluacion(
        self,
        video_path: str,
        id_tecnica: str,
        contexto_manual: Optional[str] = None,
        score_similitud: Optional[float] = None,
        embedding_desviacion: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Realización formal del CU-02 con atributos de fotograma y coordenadas articulares."""
        resultado = self.evaluar_ejecucion(
            video_path=video_path,
            id_tecnica=id_tecnica,
            contexto_manual=contexto_manual,
            score_similitud=score_similitud,
            embedding_desviacion=embedding_desviacion,
        )
        art = resultado["desviaciones"][0] if resultado["desviaciones"] else None
        return {
            "fotograma_clave": None,
            "punto_rojo": {"x": 0.0, "y": 0.0} if not art else {"x": 0.5, "y": 0.5},
            "consejo": resultado["consejo_pedagogico"],
            "consejo_pedagogico": resultado["consejo_pedagogico"],
            "consejo_estructurado": resultado.get("consejo_estructurado"),
            "id_tecnica": resultado["id_tecnica"],
            "es_valido": resultado["es_valido"],
            "total_desviaciones": resultado["total_desviaciones"],
            "desviaciones": resultado["desviaciones"],
            "score_similitud_rag": resultado["score_similitud_rag"],
            "usó_fallback_rag": resultado["usó_fallback_rag"],
        }
