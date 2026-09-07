from typing import Optional, List
from uuid import UUID

from .pipeline import BiomechanicsPipeline
from ..domain.entities import AnalisisBiomecanico, TecnicaMaestra
from ..infrastructure.repositories import TecnicaMaestraRepository, AnalisisRepository


class AnalysisAppService:
    """
    Servicio de Aplicación (Application Service - Larman).
    Coordina casos de uso de análisis, trazabilidad y persistencia en repositorio.
    """

    def __init__(
        self,
        pipeline: BiomechanicsPipeline,
        analisis_repo: Optional[AnalisisRepository] = None,
        tecnica_repo: Optional[TecnicaMaestraRepository] = None
    ):
        self.pipeline = pipeline
        self.analisis_repo = analisis_repo or AnalisisRepository()
        self.tecnica_repo = tecnica_repo or TecnicaMaestraRepository()

    def analizar_ejecucion(
        self, video_maestro: str, video_alumno: str, tecnica_id: Optional[UUID] = None
    ) -> AnalisisBiomecanico:
        """Ejecuta el análisis y almacena el resultado en el repositorio."""
        tecnica = self.tecnica_repo.obtener_por_id(tecnica_id) if tecnica_id else None
        nombre_tecnica = tecnica.nombre if tecnica else None

        analisis = self.pipeline.ejecutar(video_maestro, video_alumno, tecnica=nombre_tecnica)
        self.analisis_repo.guardar(analisis)
        return analisis

    def obtener_historial_analisis(self) -> List[AnalisisBiomecanico]:
        return self.analisis_repo.obtener_todos()
