"""
Controladores de Caso de Uso (GRASP Controllers - Craig Larman OOAD).
Especializados en proteger variaciones entre los roles Head Coach y Estudiante (Protected Variations & High Cohesion).
"""

import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.application.pipeline import AnalysisPipeline
from src.infrastructure.repositories import TecnicaMaestraRepository, AnalisisRepository, SQLiteDB
from src.domain.entities import TecnicaMaestra, ReglaBiomecanica, AnalisisBiomecanico


class CoachController:
    """
    Controlador de caso de uso para el Head Coach / Profesor (CU-01).
    Responsabilidad: Homologar y administrar el catálogo de técnicas maestras y reglas biomecánicas.
    """

    def __init__(self, tecnica_repo: Optional[TecnicaMaestraRepository] = None, pipeline: Optional[AnalysisPipeline] = None):
        self.tecnica_repo = tecnica_repo or TecnicaMaestraRepository()
        self.pipeline = pipeline or AnalysisPipeline()

    def homologar_tecnica(
        self,
        nombre: str,
        categoria: str,
        posicion: str,
        video_url: str = "",
        reglas: Optional[List[ReglaBiomecanica]] = None,
        ventana_sakoe_chiba: float = 0.15
    ) -> TecnicaMaestra:
        """
        CU-01: Homologa una nueva técnica patrón en el sistema.
        Crea la técnica y genera reglas biomecánicas por defecto si no son proporcionadas (RF-01).
        """
        t_id = uuid.uuid4()
        if not reglas:
            reglas = [
                ReglaBiomecanica(articulacion_clave="codo_der", umbral_angular_tolerado=15.0, descripcion_error="Alineación angular de codo fuera de rango"),
                ReglaBiomecanica(articulacion_clave="rodilla_der", umbral_angular_tolerado=15.0, descripcion_error="Apertura articular de rodilla no canónica"),
                ReglaBiomecanica(articulacion_clave="cadera", umbral_angular_tolerado=20.0, descripcion_error="Desviación en ángulo de flexión de cadera")
            ]

        tecnica = TecnicaMaestra(
            id=t_id,
            nombre=nombre,
            categoria=categoria,
            posicion_origen=posicion,
            video_url=video_url,
            ventana_sakoe_chiba=ventana_sakoe_chiba,
            reglas=reglas
        )
        return self.tecnica_repo.guardar(tecnica)

    def listar_tecnicas(self) -> List[TecnicaMaestra]:
        """Recupera el catálogo completo de técnicas homologadas."""
        return self.tecnica_repo.obtener_todas()

    def eliminar_tecnica(self, id_tecnica: str) -> bool:
        """Elimina una técnica y sus reglas asociadas."""
        return self.tecnica_repo.eliminar(id_tecnica)


class StudentController:
    """
    Controlador de caso de uso para el Estudiante / Atleta (CU-02).
    Responsabilidad: Auditar ejecuciones técnicas y consultar progreso longitudinal.
    """

    def __init__(self, pipeline: Optional[AnalysisPipeline] = None):
        self.pipeline = pipeline or AnalysisPipeline()

    def auditar_ejecucion_desde_colab(
        self,
        colab_json_path: str,
        video_id: str,
        tecnica_id: str
    ) -> AnalisisBiomecanico:
        """
        CU-02: Procesa el resultado de inferencia del motor IA remoto (Google Colab Pro)
        y persiste el análisis en la base de datos local (Mannino).
        """
        return self.pipeline.procesar_resultado_colab(
            colab_json_path,
            video_id=video_id,
            tecnica_id=tecnica_id
        )

    def consultar_historial(self, estudiante_id: str) -> List[Dict[str, Any]]:
        """Consulta el historial longitudinal de auditorías del alumno."""
        return self.pipeline.obtener_historial_estudiante(estudiante_id)
