"""
Motor de Pipeline Biomecánico - Fachada GoF (Facade Pattern)

Orquesta los servicios de dominio (LandmarkAdapter y DTWComparator)
en un pipeline unificado que transforma keypoints 3D crudos en un
diagnóstico biomecánico estructurado.

El patrón Fachada simplifica la interacción con el subsistema de
análisis: el controlador solo necesita invocar un método para
ejecutar toda la cadena de procesamiento.

Requisitos cubiertos: RF-03 (Comparación DTW), RF-04 (Diagnóstico).

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.domain.models import TecnicaMaestra
from src.services.landmark_adapter import LandmarkAdapter
from src.services.dtw_comparator import DTWComparator


class PipelineBiomecanicoEngine:
    """
    Fachada (GoF) que orquesta el pipeline completo de análisis
    biomecánico para una ejecución de técnica de Jiu-Jitsu.

    Flujo del pipeline:
        1. Adaptación de keypoints → ángulos articulares (por frame)
        2. Alineación temporal DTW con banda de Sakoe-Chiba
        3. Detección del pico de desviación angular máxima
        4. Generación de diagnóstico estructurado
    """

    def __init__(
        self,
        landmark_adapter: LandmarkAdapter,
        dtw_comparator: DTWComparator,
    ) -> None:
        self.landmark_adapter = landmark_adapter
        self.dtw_comparator = dtw_comparator

    def ejecutar_pipeline_completo(
        self,
        keypoints_patron: List[List[Tuple[float, ...]]],
        keypoints_ejecucion: List[List[Tuple[float, ...]]],
        tecnica: TecnicaMaestra,
    ) -> Dict[str, Any]:
        """Orquesta el pipeline biomecánico completo.

        Args:
            keypoints_patron: Serie temporal de frames del video de referencia.
                Cada frame es una lista de 17+ keypoints COCO (x, y, z).
            keypoints_ejecucion: Serie temporal de frames del video del practicante.
                Mismo formato que keypoints_patron.
            tecnica: TecnicaMaestra con la configuración de ventana Sakoe-Chiba
                y las reglas biomecánicas asociadas.

        Returns:
            Diccionario con el diagnóstico estructurado:
                - distancia_dtw: Distancia DTW de la articulación más afectada.
                - pico_desviacion: Máxima desviación angular (grados) en un frame.
                - articulacion_afectada: Nombre de la articulación con mayor DTW.
                - fotograma_error: Índice del frame con máxima desviación.
                - resultados_por_articulacion: Dict con distancia DTW por articulación.

        Raises:
            ValueError: Si las series de keypoints están vacías.
        """
        if not keypoints_patron or not keypoints_ejecucion:
            raise ValueError(
                "Las series de keypoints no pueden estar vacías para "
                "ejecutar el pipeline biomecánico."
            )

        # ── Paso 1: Adaptación de keypoints → ángulos articulares ──
        angulos_patron = [
            self.landmark_adapter.adaptar_keypoints_a_angulos(frame)
            for frame in keypoints_patron
        ]
        angulos_ejecucion = [
            self.landmark_adapter.adaptar_keypoints_a_angulos(frame)
            for frame in keypoints_ejecucion
        ]

        # ── Paso 2: Alineación temporal DTW por articulación ──
        articulaciones = list(angulos_patron[0].keys())
        resultados_dtw: Dict[str, float] = {}

        for articulacion in articulaciones:
            serie_patron = [frame[articulacion] for frame in angulos_patron]
            serie_ejecucion = [frame[articulacion] for frame in angulos_ejecucion]

            distancia = self.dtw_comparator.calcular_distancia_sakoe_chiba(
                serie_patron=serie_patron,
                serie_ejecucion=serie_ejecucion,
                ventana=tecnica.ventana_sakoe_chiba,
            )
            resultados_dtw[articulacion] = distancia

        # ── Paso 3: Detección de pico de desviación máxima ──
        articulacion_afectada = max(resultados_dtw, key=resultados_dtw.get)  # type: ignore[arg-type]
        distancia_dtw_max = resultados_dtw[articulacion_afectada]

        # Encontrar el frame con mayor desviación angular en la articulación afectada
        fotograma_error, pico_desviacion = self._encontrar_pico_desviacion(
            angulos_patron=angulos_patron,
            angulos_ejecucion=angulos_ejecucion,
            articulacion=articulacion_afectada,
        )

        # ── Paso 4: Diagnóstico estructurado ──
        return {
            "distancia_dtw": distancia_dtw_max,
            "pico_desviacion": pico_desviacion,
            "articulacion_afectada": articulacion_afectada,
            "fotograma_error": fotograma_error,
            "resultados_por_articulacion": resultados_dtw,
        }

    @staticmethod
    def _encontrar_pico_desviacion(
        angulos_patron: List[Dict[str, float]],
        angulos_ejecucion: List[Dict[str, float]],
        articulacion: str,
    ) -> Tuple[int, float]:
        """Encuentra el frame con la mayor desviación angular.

        Compara frame a frame (hasta la longitud de la serie más corta)
        y retorna el índice y valor de la desviación máxima.

        Args:
            angulos_patron: Ángulos por frame del video de referencia.
            angulos_ejecucion: Ángulos por frame del video del practicante.
            articulacion: Nombre de la articulación a evaluar.

        Returns:
            Tupla (índice_frame, desviación_máxima_en_grados).
        """
        longitud_comun = min(len(angulos_patron), len(angulos_ejecucion))

        if longitud_comun == 0:
            return (0, 0.0)

        fotograma_error = 0
        pico_desviacion = 0.0

        for i in range(longitud_comun):
            desviacion = abs(
                angulos_patron[i][articulacion]
                - angulos_ejecucion[i][articulacion]
            )
            if desviacion > pico_desviacion:
                pico_desviacion = desviacion
                fotograma_error = i

        return (fotograma_error, pico_desviacion)
