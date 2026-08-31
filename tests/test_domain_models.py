"""
Pruebas Unitarias - Capa de Dominio (TDD)

Pruebas para las entidades de negocio puras definidas en
src/domain/models.py. Siguiendo TDD, estas pruebas validan
la lógica de negocio sin dependencias externas.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

import uuid
from datetime import datetime

import pytest

from src.domain.models import (
    AnalisisBiomecanico,
    ReglaBiomecanica,
    TecnicaMaestra,
    VideoEjecucion,
)


# ──────────────────────────────────────────────
#  ReglaBiomecanica
# ──────────────────────────────────────────────


class TestReglaBiomecanica:
    """Pruebas para la entidad ReglaBiomecanica."""

    def _crear_regla(self, umbral: float = 90.0) -> ReglaBiomecanica:
        """Helper: crea una regla con umbral configurable."""
        return ReglaBiomecanica(
            articulacion_clave="codo_derecho",
            umbral_angular_tolerado=umbral,
            descripcion_error="Extensión excesiva del codo derecho",
        )

    def test_regla_biomecanica_evaluacion_exitosa(self) -> None:
        """Ángulo dentro del margen de 5° → no hay violación (False)."""
        regla = self._crear_regla(umbral=90.0)
        # 92° está a 2° del umbral (90°), dentro del margen de 5°
        assert regla.evaluar_discrepancia(92.0) is False

    def test_regla_biomecanica_evaluacion_fallida(self) -> None:
        """Ángulo fuera del margen de 5° → violación detectada (True)."""
        regla = self._crear_regla(umbral=90.0)
        # 110° está a 20° del umbral (90°), muy por encima del margen de 5°
        assert regla.evaluar_discrepancia(110.0) is True

    def test_regla_biomecanica_evaluacion_en_limite_exacto(self) -> None:
        """Ángulo exactamente en el margen (5°) → no hay violación."""
        regla = self._crear_regla(umbral=90.0)
        # 95° está a exactamente 5° del umbral → NO supera el margen
        assert regla.evaluar_discrepancia(95.0) is False

    def test_regla_biomecanica_atributos(self) -> None:
        """Los atributos se asignan correctamente."""
        regla = self._crear_regla()
        assert regla.articulacion_clave == "codo_derecho"
        assert regla.umbral_angular_tolerado == 90.0
        assert isinstance(regla.id_regla, uuid.UUID)


# ──────────────────────────────────────────────
#  TecnicaMaestra
# ──────────────────────────────────────────────


class TestTecnicaMaestra:
    """Pruebas para la entidad TecnicaMaestra."""

    def test_agregar_regla(self) -> None:
        """Se pueden agregar reglas biomecánicas a una técnica."""
        tecnica = TecnicaMaestra(
            nombre="Armbar",
            categoria="Sumisión",
            posicion_origen="Guardia Cerrada",
            video_url="https://storage.example.com/armbar_ref.mp4",
        )
        regla = ReglaBiomecanica(
            articulacion_clave="codo_derecho",
            umbral_angular_tolerado=180.0,
            descripcion_error="Hiperextensión del codo",
        )
        tecnica.agregar_regla(regla)

        assert len(tecnica.reglas) == 1
        assert tecnica.reglas[0].articulacion_clave == "codo_derecho"

    def test_ventana_sakoe_chiba_default(self) -> None:
        """El valor por defecto de ventana_sakoe_chiba es 0.15."""
        tecnica = TecnicaMaestra(
            nombre="Triangle Choke",
            categoria="Sumisión",
            posicion_origen="Guardia Cerrada",
            video_url="https://storage.example.com/triangle_ref.mp4",
        )
        assert tecnica.ventana_sakoe_chiba == 0.15


# ──────────────────────────────────────────────
#  AnalisisBiomecanico
# ──────────────────────────────────────────────


class TestAnalisisBiomecanico:
    """Pruebas para la entidad AnalisisBiomecanico."""

    def test_generar_diagnostico(self) -> None:
        """generar_diagnostico() retorna un diccionario con las claves esperadas."""
        analisis = AnalisisBiomecanico(
            desviacion_angular_maxima=12.5,
            articulacion_afectada="rodilla_izquierda",
            estado_computo="EXITOSO",
        )
        diagnostico = analisis.generar_diagnostico()

        assert isinstance(diagnostico, dict)
        assert diagnostico["desviacion_angular_maxima"] == 12.5
        assert diagnostico["articulacion_afectada"] == "rodilla_izquierda"
        assert diagnostico["estado_computo"] == "EXITOSO"
        assert "id_analisis" in diagnostico
        assert "fecha_procesamiento" in diagnostico

    def test_estado_computo_occlusion(self) -> None:
        """Un análisis con oclusión se registra correctamente."""
        analisis = AnalisisBiomecanico(
            desviacion_angular_maxima=0.0,
            articulacion_afectada="N/A",
            estado_computo="OCCLUSION",
        )
        assert analisis.estado_computo == "OCCLUSION"


# ──────────────────────────────────────────────
#  VideoEjecucion
# ──────────────────────────────────────────────


class TestVideoEjecucion:
    """Pruebas para la entidad VideoEjecucion."""

    def _crear_video(
        self,
        peso_mb: float = 4.0,
        duracion_segundos: float = 5.0,
    ) -> VideoEjecucion:
        """Helper: crea un VideoEjecucion con valores configurables."""
        return VideoEjecucion(
            duracion_segundos=duracion_segundos,
            peso_mb=peso_mb,
            video_url="https://storage.example.com/ejecucion_001.mp4",
        )

    def test_video_ejecucion_validacion_peso_excedido(self) -> None:
        """peso_mb > 5.0 → lanza ValueError."""
        video = self._crear_video(peso_mb=5.1)
        with pytest.raises(ValueError, match="peso del video"):
            video.validar_limites()

    def test_video_ejecucion_validacion_duracion_excedida(self) -> None:
        """duracion_segundos > 6.0 → lanza ValueError."""
        video = self._crear_video(duracion_segundos=7.0)
        with pytest.raises(ValueError, match="duración del video"):
            video.validar_limites()

    def test_video_ejecucion_validacion_exitosa(self) -> None:
        """Video dentro de límites → retorna True sin excepciones."""
        video = self._crear_video(peso_mb=4.5, duracion_segundos=5.0)
        assert video.validar_limites() is True

    def test_video_ejecucion_validacion_en_limite_exacto(self) -> None:
        """Video con valores exactamente en el límite → válido."""
        video = self._crear_video(peso_mb=5.0, duracion_segundos=6.0)
        assert video.validar_limites() is True
