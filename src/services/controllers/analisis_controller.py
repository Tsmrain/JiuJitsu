"""
Controlador GRASP - Caso de Uso CU-02: Análisis Biomecánico

Orquesta el caso de uso principal del sistema: recibir un video
de ejecución de un practicante, validarlo, compararlo contra la
técnica maestra de referencia y generar un diagnóstico biomecánico.

Patrón aplicado: Controlador (GRASP) — asigna la responsabilidad
de coordinar el flujo del caso de uso a un objeto dedicado que
no contiene lógica de dominio, solo orquestación.

Requisitos cubiertos: RF-02 (Registro de técnicas), RF-03 (Comparación),
RF-04 (Diagnóstico), RF-07 (Validación de video).

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.domain.models import (
    AnalisisBiomecanico,
    TecnicaMaestra,
    VideoEjecucion,
)
from src.infrastructure.interfaces import (
    IAnalisisBiomecanicoRepository,
    IHuaweiOBSStorageAdapter,
    ITecnicaMaestraRepository,
    IVideoEjecucionRepository,
)
from src.services.pipeline_engine import PipelineBiomecanicoEngine


class AnalisisBiomecanicoController:
    """
    Controlador GRASP que orquesta los casos de uso del módulo
    de análisis biomecánico de Brazilian Jiu-Jitsu.

    Responsabilidades:
        - Validación de entrada (RF-07: límites de video)
        - Coordinación del pipeline biomecánico (RF-03, RF-04)
        - Persistencia de resultados a través de repositorios
        - CRUD de técnicas maestras (RF-02)

    No contiene lógica de dominio — delega a las entidades y servicios.
    """

    def __init__(
        self,
        pipeline_engine: PipelineBiomecanicoEngine,
        tecnica_repository: ITecnicaMaestraRepository,
        analisis_repository: IAnalisisBiomecanicoRepository,
        video_repository: IVideoEjecucionRepository,
        obs_adapter: IHuaweiOBSStorageAdapter,
    ) -> None:
        self.pipeline_engine = pipeline_engine
        self.tecnica_repository = tecnica_repository
        self.analisis_repository = analisis_repository
        self.video_repository = video_repository
        self.obs_adapter = obs_adapter

    # ──────────────────────────────────────────────
    #  CU-02: Ejecutar Análisis Biomecánico
    # ──────────────────────────────────────────────

    def ejecutar_analisis(
        self,
        video_bytes: bytes,
        id_tecnica: str,
        duracion_segundos: float,
        nombre_archivo: str,
    ) -> Dict[str, Any]:
        """Orquesta el caso de uso CU-02: Análisis Biomecánico Completo.

        Flujo:
            1. Crear VideoEjecucion y validar límites (RF-07)
            2. Subir video a almacenamiento cloud (OBS)
            3. Obtener técnica maestra del repositorio
            4. Extraer keypoints del video (simulado en esta iteración)
            5. Ejecutar pipeline biomecánico completo
            6. Persistir resultados (análisis + metadatos de video)
            7. Retornar diagnóstico estructurado

        Args:
            video_bytes: Contenido binario del video de ejecución.
            id_tecnica: UUID de la técnica maestra a comparar.
            duracion_segundos: Duración del video en segundos.
            nombre_archivo: Nombre original del archivo de video.

        Returns:
            Diccionario con el diagnóstico biomecánico completo.

        Raises:
            ValueError: Si el video excede los límites de peso/duración,
                        o si la técnica no existe.
        """
        # ── Paso 1: Validar límites del video (RF-07) ──
        peso_mb = len(video_bytes) / (1024 * 1024)
        video = VideoEjecucion(
            duracion_segundos=duracion_segundos,
            peso_mb=peso_mb,
            video_url="",  # Se asignará tras la subida
        )
        video.validar_limites()  # Lanza ValueError si excede límites

        # ── Paso 2: Subir video a almacenamiento cloud ──
        video_url = self.obs_adapter.subir_video(video_bytes, nombre_archivo)
        video.video_url = video_url

        # ── Paso 3: Obtener técnica maestra ──
        tecnica = self.tecnica_repository.obtener_por_id(id_tecnica)
        if tecnica is None:
            raise ValueError(
                f"La técnica maestra con ID '{id_tecnica}' no fue "
                f"encontrada en el repositorio."
            )

        # ── Paso 4: Extraer keypoints (simulado — Iter. futura) ──
        keypoints_patron = self._extraer_keypoints_simulados()
        keypoints_ejecucion = self._extraer_keypoints_simulados()

        # ── Paso 5: Ejecutar pipeline biomecánico ──
        diagnostico = self.pipeline_engine.ejecutar_pipeline_completo(
            keypoints_patron=keypoints_patron,
            keypoints_ejecucion=keypoints_ejecucion,
            tecnica=tecnica,
        )

        # ── Paso 6: Persistir resultados ──
        self.video_repository.guardar(video)

        analisis = AnalisisBiomecanico(
            desviacion_angular_maxima=diagnostico["pico_desviacion"],
            articulacion_afectada=diagnostico["articulacion_afectada"],
            estado_computo="EXITOSO",
            video_id=video.id_video,
        )
        self.analisis_repository.guardar(analisis)

        # ── Paso 7: Retornar diagnóstico enriquecido ──
        diagnostico["id_analisis"] = str(analisis.id_analisis)
        diagnostico["video_url"] = video_url
        diagnostico["video_id"] = str(video.id_video)
        diagnostico["estado_computo"] = "EXITOSO"

        return diagnostico

    # ──────────────────────────────────────────────
    #  CRUD: Técnicas Maestras (RF-02)
    # ──────────────────────────────────────────────

    def registrar_tecnica_maestra(
        self,
        nombre: str,
        categoria: str,
        posicion_origen: str,
        video_bytes: bytes,
        nombre_archivo: str,
        ventana_sakoe_chiba: float = 0.15,
    ) -> TecnicaMaestra:
        """Registra una nueva técnica maestra en el sistema (RF-02).

        Args:
            nombre: Nombre de la técnica (ej. 'Armbar').
            categoria: Categoría de la técnica (ej. 'Sumisión').
            posicion_origen: Posición de inicio (ej. 'Guardia Cerrada').
            video_bytes: Contenido binario del video de referencia.
            nombre_archivo: Nombre del archivo de video.
            ventana_sakoe_chiba: Flexibilidad DTW (default 0.15).

        Returns:
            Instancia de TecnicaMaestra creada y persistida.
        """
        video_url = self.obs_adapter.subir_video(video_bytes, nombre_archivo)

        tecnica = TecnicaMaestra(
            nombre=nombre,
            categoria=categoria,
            posicion_origen=posicion_origen,
            video_url=video_url,
            ventana_sakoe_chiba=ventana_sakoe_chiba,
        )

        self.tecnica_repository.guardar(tecnica)
        return tecnica

    def listar_tecnicas(self) -> List[TecnicaMaestra]:
        """Lista todas las técnicas maestras disponibles.

        Returns:
            Lista de TecnicaMaestra registradas.
        """
        return self.tecnica_repository.listar_todas()

    def eliminar_tecnica(self, id_tecnica: str) -> bool:
        """Elimina una técnica maestra del sistema.

        Args:
            id_tecnica: UUID de la técnica a eliminar.

        Returns:
            True si se eliminó, False si no se encontró.
        """
        return self.tecnica_repository.eliminar(id_tecnica)

    # ──────────────────────────────────────────────
    #  Métodos internos (stubs para iteraciones futuras)
    # ──────────────────────────────────────────────

    @staticmethod
    def _extraer_keypoints_simulados() -> List[List[Tuple[float, ...]]]:
        """Genera keypoints 3D simulados para desarrollo incremental.

        En iteraciones futuras, este método será reemplazado por la
        integración real con RTMPose3D / MMPose para extraer keypoints
        del video de forma automática.

        Returns:
            Lista de 3 frames con 17 keypoints COCO cada uno.
        """
        # Frame base con ángulo de 90° en codo derecho y 180° en rodilla derecha
        frame_base: List[Tuple[float, ...]] = [(0.0, 0.0, 0.0)] * 17
        frame_list = list(frame_base)

        # Codo derecho: hombro(6) - codo(8) - muñeca(10) → 90°
        frame_list[6] = (0.0, 1.0, 0.0)
        frame_list[8] = (0.0, 0.0, 0.0)
        frame_list[10] = (1.0, 0.0, 0.0)

        # Codo izquierdo: hombro(5) - codo(7) - muñeca(9) → 90°
        frame_list[5] = (0.0, 1.0, 1.0)
        frame_list[7] = (0.0, 0.0, 1.0)
        frame_list[9] = (1.0, 0.0, 1.0)

        # Rodilla derecha: cadera(12) - rodilla(14) - tobillo(16) → 180°
        frame_list[12] = (0.0, 2.0, 0.0)
        frame_list[14] = (0.0, 1.0, 0.0)
        frame_list[16] = (0.0, 0.0, 0.0)

        # Rodilla izquierda: cadera(11) - rodilla(13) - tobillo(15) → 180°
        frame_list[11] = (1.0, 2.0, 0.0)
        frame_list[13] = (1.0, 1.0, 0.0)
        frame_list[15] = (1.0, 0.0, 0.0)

        return [list(frame_list)] * 3  # 3 frames idénticos
