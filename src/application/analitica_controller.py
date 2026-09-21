# src/application/analitica_controller.py
from typing import Dict, Any, List
from src.domain.interfaces import IHistorialRepository, ITecnicaRepository

class AnaliticaController:
    """Controlador (Session Facade) para el panel de analítica del profesor."""

    def __init__(
        self,
        historial_repository: IHistorialRepository,
        tecnica_repository: ITecnicaRepository,
    ):
        self._historial_repo = historial_repository
        self._tecnica_repo = tecnica_repository

    def generar_panel_tecnica(self, id_tecnica: str) -> Dict[str, Any]:
        """Recupera y consolida las estadísticas de una técnica."""
        patron = self._tecnica_repo.obtener_patron(id_tecnica)
        if not patron:
            raise ValueError(f"La técnica '{id_tecnica}' no existe en el catálogo.")

        reporte = self._historial_repo.obtener_analitica_por_tecnica(id_tecnica)
        
        return {
            "id_tecnica": reporte.id_tecnica,
            "nombre_tecnica": reporte.nombre_tecnica,
            "total_evaluaciones": reporte.total_evaluaciones,
            "evaluaciones_aprobadas": reporte.evaluaciones_aprobadas,
            "tasa_aprobacion": reporte.tasa_aprobacion,
            "articulaciones_criticas": [
                {
                    "nombre_articulacion": a.nombre_articulacion.replace("_", " ").title(),
                    "total_detecciones": a.total_detecciones,
                    "desviacion_promedio_grados": a.desviacion_promedio_grados,
                    "severidad": a.severidad
                } for a in reporte.articulaciones_criticas
            ],
            "fecha_generacion": reporte.fecha_generacion.isoformat()
        }

    def listar_tecnicas_mas_evaluadas(self, limite: int = 5) -> List[Dict[str, Any]]:
        """Devuelve el ranking de técnicas más evaluadas."""
        ranking = self._historial_repo.listar_tecnicas_mas_evaluadas(limite=limite)
        for r in ranking:
            patron = self._tecnica_repo.obtener_patron(r["id_tecnica"])
            r["nombre_tecnica"] = patron.nombre if patron else r["id_tecnica"].replace("_", " ").title()
        return ranking
