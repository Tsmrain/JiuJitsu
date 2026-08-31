"""
Pruebas Unitarias - Pipeline Biomecánico y Controlador GRASP (TDD)

Pruebas con mocks para el PipelineBiomecanicoEngine (Fachada GoF) y
el AnalisisBiomecanicoController (Controlador GRASP). Siguiendo TDD,
todas las dependencias de infraestructura se sustituyen por mocks.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import uuid
from typing import List, Optional, Tuple
from unittest.mock import MagicMock, patch

import pytest

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
from src.services.dtw_comparator import DTWComparator
from src.services.landmark_adapter import LandmarkAdapter
from src.services.pipeline_engine import PipelineBiomecanicoEngine
from src.services.controllers.analisis_controller import (
    AnalisisBiomecanicoController,
)


# ──────────────────────────────────────────────
#  Helpers: Generación de keypoints simulados
# ──────────────────────────────────────────────


def _generar_frame_keypoints(
    angulo_codo_offset: float = 0.0,
) -> List[Tuple[float, ...]]:
    """Genera un frame de 17 keypoints COCO con ángulos controlados.

    El offset modifica la posición de la muñeca derecha para variar
    el ángulo del codo (base 90°).
    """
    frame: List[Tuple[float, ...]] = [(0.0, 0.0, 0.0)] * 17

    frame_list = list(frame)
    # Codo derecho → 90° + offset
    frame_list[6] = (0.0, 1.0, 0.0)       # hombro derecho
    frame_list[8] = (0.0, 0.0, 0.0)       # codo derecho (vértice)
    frame_list[10] = (1.0, angulo_codo_offset, 0.0)  # muñeca derecha

    # Codo izquierdo → 90°
    frame_list[5] = (0.0, 1.0, 1.0)
    frame_list[7] = (0.0, 0.0, 1.0)
    frame_list[9] = (1.0, 0.0, 1.0)

    # Rodilla derecha → 180° (pierna extendida)
    frame_list[12] = (0.0, 2.0, 0.0)
    frame_list[14] = (0.0, 1.0, 0.0)
    frame_list[16] = (0.0, 0.0, 0.0)

    # Rodilla izquierda → 180°
    frame_list[11] = (1.0, 2.0, 0.0)
    frame_list[13] = (1.0, 1.0, 0.0)
    frame_list[15] = (1.0, 0.0, 0.0)

    return frame_list


def _crear_tecnica_mock() -> TecnicaMaestra:
    """Crea una TecnicaMaestra de prueba."""
    return TecnicaMaestra(
        nombre="Armbar",
        categoria="Sumisión",
        posicion_origen="Guardia Cerrada",
        video_url="https://obs.example.com/armbar_ref.mp4",
        ventana_sakoe_chiba=0.15,
    )


# ──────────────────────────────────────────────
#  PipelineBiomecanicoEngine (Fachada GoF)
# ──────────────────────────────────────────────


class TestPipelineBiomecanicoEngine:
    """Pruebas para la Fachada del pipeline biomecánico."""

    def setup_method(self) -> None:
        """Inicializa servicios reales para pruebas de integración."""
        self.adapter = LandmarkAdapter()
        self.comparator = DTWComparator()
        self.engine = PipelineBiomecanicoEngine(
            landmark_adapter=self.adapter,
            dtw_comparator=self.comparator,
        )

    def test_pipeline_engine_ejecucion_exitosa(self) -> None:
        """Pipeline completo con keypoints simulados retorna diagnóstico válido.

        Patrón: 3 frames con codo a 90°.
        Ejecución: 3 frames con codo desviado (muñeca desplazada).
        """
        tecnica = _crear_tecnica_mock()

        keypoints_patron = [_generar_frame_keypoints(0.0) for _ in range(3)]
        keypoints_ejecucion = [_generar_frame_keypoints(0.5) for _ in range(3)]

        resultado = self.engine.ejecutar_pipeline_completo(
            keypoints_patron=keypoints_patron,
            keypoints_ejecucion=keypoints_ejecucion,
            tecnica=tecnica,
        )

        # Verificar estructura del diagnóstico
        assert "distancia_dtw" in resultado
        assert "pico_desviacion" in resultado
        assert "articulacion_afectada" in resultado
        assert "fotograma_error" in resultado
        assert "resultados_por_articulacion" in resultado

        # Debe haber distancia > 0 porque la ejecución difiere del patrón
        # en el codo derecho (offset de muñeca)
        assert isinstance(resultado["distancia_dtw"], float)
        assert isinstance(resultado["fotograma_error"], int)

    def test_pipeline_engine_secuencias_identicas(self) -> None:
        """Keypoints idénticos → distancia DTW = 0 en todas las articulaciones."""
        tecnica = _crear_tecnica_mock()

        keypoints = [_generar_frame_keypoints(0.0) for _ in range(3)]

        resultado = self.engine.ejecutar_pipeline_completo(
            keypoints_patron=keypoints,
            keypoints_ejecucion=keypoints,
            tecnica=tecnica,
        )

        assert resultado["distancia_dtw"] == 0.0
        assert resultado["pico_desviacion"] == 0.0

        for distancia in resultado["resultados_por_articulacion"].values():
            assert distancia == 0.0

    def test_pipeline_engine_series_vacias(self) -> None:
        """Series vacías de keypoints → lanza ValueError."""
        tecnica = _crear_tecnica_mock()

        with pytest.raises(ValueError, match="vacías"):
            self.engine.ejecutar_pipeline_completo(
                keypoints_patron=[],
                keypoints_ejecucion=[_generar_frame_keypoints()],
                tecnica=tecnica,
            )

    def test_pipeline_engine_detecta_articulacion_afectada(self) -> None:
        """El pipeline identifica correctamente la articulación más desviada."""
        tecnica = _crear_tecnica_mock()

        # Patrón: codo a ~90°
        keypoints_patron = [_generar_frame_keypoints(0.0) for _ in range(3)]
        # Ejecución: codo significativamente desviado
        keypoints_ejecucion = [_generar_frame_keypoints(2.0) for _ in range(3)]

        resultado = self.engine.ejecutar_pipeline_completo(
            keypoints_patron=keypoints_patron,
            keypoints_ejecucion=keypoints_ejecucion,
            tecnica=tecnica,
        )

        # La articulación afectada debe ser el codo derecho (es la que cambiamos)
        assert resultado["articulacion_afectada"] == "codo_derecho"
        assert resultado["pico_desviacion"] > 0.0


# ──────────────────────────────────────────────
#  AnalisisBiomecanicoController (Controlador GRASP)
# ──────────────────────────────────────────────


class TestAnalisisBiomecanicoController:
    """Pruebas para el Controlador GRASP con mocks de infraestructura."""

    def setup_method(self) -> None:
        """Configura mocks para todas las dependencias de infraestructura."""
        self.mock_tecnica_repo = MagicMock(spec=ITecnicaMaestraRepository)
        self.mock_analisis_repo = MagicMock(spec=IAnalisisBiomecanicoRepository)
        self.mock_video_repo = MagicMock(spec=IVideoEjecucionRepository)
        self.mock_obs_adapter = MagicMock(spec=IHuaweiOBSStorageAdapter)

        # Pipeline con servicios reales
        adapter = LandmarkAdapter()
        comparator = DTWComparator()
        engine = PipelineBiomecanicoEngine(adapter, comparator)

        self.controller = AnalisisBiomecanicoController(
            pipeline_engine=engine,
            tecnica_repository=self.mock_tecnica_repo,
            analisis_repository=self.mock_analisis_repo,
            video_repository=self.mock_video_repo,
            obs_adapter=self.mock_obs_adapter,
        )

    def _video_bytes_valido(self) -> bytes:
        """Genera bytes de video dentro del límite (< 5 MB)."""
        return b"\x00" * (1024 * 1024)  # 1 MB

    def test_controller_ejecutar_analisis_exitoso(self) -> None:
        """Flujo completo CU-02 con mocks: valida, sube, analiza, persiste."""
        tecnica = _crear_tecnica_mock()
        self.mock_tecnica_repo.obtener_por_id.return_value = tecnica
        self.mock_obs_adapter.subir_video.return_value = (
            "https://obs.example.com/ejecucion_001.mp4"
        )

        resultado = self.controller.ejecutar_analisis(
            video_bytes=self._video_bytes_valido(),
            id_tecnica=str(tecnica.id_tecnica),
            duracion_segundos=5.0,
            nombre_archivo="ejecucion_001.mp4",
        )

        # Verificar diagnóstico retornado
        assert "distancia_dtw" in resultado
        assert "articulacion_afectada" in resultado
        assert resultado["estado_computo"] == "EXITOSO"
        assert resultado["video_url"] == "https://obs.example.com/ejecucion_001.mp4"
        assert "id_analisis" in resultado

        # Verificar interacciones con mocks
        self.mock_tecnica_repo.obtener_por_id.assert_called_once_with(
            str(tecnica.id_tecnica)
        )
        self.mock_obs_adapter.subir_video.assert_called_once()
        self.mock_analisis_repo.guardar.assert_called_once()
        self.mock_video_repo.guardar.assert_called_once()

    def test_controller_video_excede_limite_peso(self) -> None:
        """Video > 5 MB → lanza ValueError antes de cualquier procesamiento."""
        video_bytes_grande = b"\x00" * int(5.1 * 1024 * 1024)  # 5.1 MB

        with pytest.raises(ValueError, match="peso del video"):
            self.controller.ejecutar_analisis(
                video_bytes=video_bytes_grande,
                id_tecnica="fake-id",
                duracion_segundos=5.0,
                nombre_archivo="video_grande.mp4",
            )

        # No debe haberse llamado a ningún servicio
        self.mock_obs_adapter.subir_video.assert_not_called()
        self.mock_tecnica_repo.obtener_por_id.assert_not_called()

    def test_controller_video_excede_limite_duracion(self) -> None:
        """Video > 6 segundos → lanza ValueError."""
        with pytest.raises(ValueError, match="duración del video"):
            self.controller.ejecutar_analisis(
                video_bytes=self._video_bytes_valido(),
                id_tecnica="fake-id",
                duracion_segundos=7.0,
                nombre_archivo="video_largo.mp4",
            )

    def test_controller_tecnica_no_encontrada(self) -> None:
        """Técnica inexistente → lanza ValueError con mensaje descriptivo."""
        self.mock_tecnica_repo.obtener_por_id.return_value = None
        self.mock_obs_adapter.subir_video.return_value = "https://obs.example.com/v.mp4"

        with pytest.raises(ValueError, match="no fue encontrada"):
            self.controller.ejecutar_analisis(
                video_bytes=self._video_bytes_valido(),
                id_tecnica="uuid-inexistente",
                duracion_segundos=5.0,
                nombre_archivo="video.mp4",
            )

    def test_controller_crud_registrar_tecnica(self) -> None:
        """Registrar técnica maestra: sube video y persiste en el repositorio."""
        self.mock_obs_adapter.subir_video.return_value = (
            "https://obs.example.com/armbar_ref.mp4"
        )

        tecnica = self.controller.registrar_tecnica_maestra(
            nombre="Armbar",
            categoria="Sumisión",
            posicion_origen="Guardia Cerrada",
            video_bytes=b"\x00" * 1024,
            nombre_archivo="armbar_ref.mp4",
        )

        assert tecnica.nombre == "Armbar"
        assert tecnica.categoria == "Sumisión"
        assert tecnica.video_url == "https://obs.example.com/armbar_ref.mp4"
        assert isinstance(tecnica.id_tecnica, uuid.UUID)

        self.mock_obs_adapter.subir_video.assert_called_once()
        self.mock_tecnica_repo.guardar.assert_called_once_with(tecnica)

    def test_controller_crud_listar_tecnicas(self) -> None:
        """Listar técnicas delega al repositorio mockeado."""
        tecnicas_mock = [_crear_tecnica_mock(), _crear_tecnica_mock()]
        self.mock_tecnica_repo.listar_todas.return_value = tecnicas_mock

        resultado = self.controller.listar_tecnicas()

        assert len(resultado) == 2
        self.mock_tecnica_repo.listar_todas.assert_called_once()

    def test_controller_crud_eliminar_tecnica(self) -> None:
        """Eliminar técnica delega al repositorio mockeado."""
        self.mock_tecnica_repo.eliminar.return_value = True

        resultado = self.controller.eliminar_tecnica("some-uuid")

        assert resultado is True
        self.mock_tecnica_repo.eliminar.assert_called_once_with("some-uuid")
