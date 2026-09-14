# src/services/sintesis_pedagogica_service.py
"""Servicio de Síntesis Pedagógica (Pure Fabrication - Larman p. 289).

Orquesta la recuperación contextual semántica RAG y la síntesis pedagógica
para contextualizar la retroalimentación biomecánica sin degradar la cohesión
de EvaluacionController.
"""

from typing import Optional, List, Dict, Any
from src.domain.models import ConfiguracionRAG


class SintesisPedagogicaService:
    """Pure Fabrication: Orquesta RAG + Gemini para feedback contextualizado."""

    def __init__(self, repo: Any, config: Optional[ConfiguracionRAG] = None):
        self._repo = repo
        self._config = config if config is not None else ConfiguracionRAG()

    def generar_feedback_contextualizado(
        self,
        articulacion_critica: str,
        id_tecnica: str,
        embedding_desviacion: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Busca contexto RAG y genera consejo pedagógico o activa fallback.

        Args:
            articulacion_critica: Nombre de la articulación con mayor desajuste.
            id_tecnica: ID de la técnica practicada.
            embedding_desviacion: Vector denso (opcional).

        Returns:
            Dict con 'consejo', 'contexto_recuperado', 'score_similitud', 'usó_fallback'.
        """
        # 1. Búsqueda semántica con umbral configurable
        try:
            resultados = self._repo.buscar_contexto(
                embedding=embedding_desviacion,
                id_tecnica=id_tecnica,
                limite=self._config.top_k_resultados,
            )
        except TypeError:
            resultados = self._repo.buscar_contexto(
                consulta_embedding=embedding_desviacion or [0.05] * 768,
                limite=self._config.top_k_resultados,
                id_tecnica=id_tecnica,
            )

        # 2. Aplicar umbral de similitud (Experto en Información)
        contextos_validos = []
        for r in (resultados or []):
            sim = r["similitud"] if isinstance(r, dict) else getattr(r, "similitud", 0.0)
            if sim >= self._config.umbral_similitud_minima:
                contextos_validos.append(r)

        # 3. Fallback pedagógico si ningún chunk supera umbral
        if not contextos_validos:
            plantilla = self._config.plantilla_fallback
            try:
                consejo_fallback = plantilla.format(articulacion=articulacion_critica)
            except (KeyError, IndexError, ValueError):
                consejo_fallback = f"{plantilla} ({articulacion_critica})"
            return {
                "consejo": consejo_fallback,
                "contexto_recuperado": None,
                "score_similitud": 0.0,
                "usó_fallback": True,
            }

        # 4. Retornar mejor contexto para inyección en Gemini
        def _obtener_similitud(x: Any) -> float:
            return float(x["similitud"] if isinstance(x, dict) else getattr(x, "similitud", 0.0))

        mejor_contexto = max(contextos_validos, key=_obtener_similitud)
        if isinstance(mejor_contexto, dict):
            texto = mejor_contexto.get("chunk_texto")
            sim_score = float(mejor_contexto.get("similitud", 0.0))
            titulo = mejor_contexto.get("titulo")
        else:
            texto = getattr(mejor_contexto, "chunk_texto", "")
            sim_score = float(getattr(mejor_contexto, "similitud", 0.0))
            titulo = getattr(mejor_contexto, "titulo", "")

        return {
            "consejo": None,  # Será sintetizado por EvaluacionController vía IGenerationService
            "contexto_recuperado": texto,
            "score_similitud": sim_score,
            "usó_fallback": False,
            "titulo_fuente": titulo,
        }
