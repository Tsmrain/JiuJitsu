"""
Capa de Dominio - Entidades de Negocio Puras (Larman)

Este módulo contiene las clases de dominio del sistema de análisis biomecánico
para Brazilian Jiu-Jitsu. Siguiendo los principios de Larman (Proceso Unificado),
estas entidades son PURAS: no dependen de frameworks externos (ni SQLAlchemy,
ni Streamlit, ni ningún otro).

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List


class ReglaBiomecanica:
    """
    Representa una regla biomecánica que define los umbrales angulares
    permitidos para una articulación específica durante la ejecución
    de una técnica de Jiu-Jitsu.

    La regla evalúa si el ángulo detectado por el sistema de visión
    artificial se desvía significativamente del umbral tolerado.
    """

    MARGEN_ERROR_GRADOS: float = 5.0

    def __init__(
        self,
        articulacion_clave: str,
        umbral_angular_tolerado: float,
        descripcion_error: str,
        id_regla: uuid.UUID | None = None,
    ) -> None:
        self.id_regla: uuid.UUID = id_regla or uuid.uuid4()
        self.articulacion_clave: str = articulacion_clave
        self.umbral_angular_tolerado: float = umbral_angular_tolerado
        self.descripcion_error: str = descripcion_error

    def evaluar_discrepancia(self, angulo_detectado: float) -> bool:
        """Evalúa si el ángulo detectado viola la regla biomecánica.

        Args:
            angulo_detectado: Ángulo medido por el sistema de visión (grados).

        Returns:
            True si la discrepancia supera el margen de error (regla violada).
            False si el ángulo está dentro del margen aceptable.
        """
        discrepancia = abs(angulo_detectado - self.umbral_angular_tolerado)
        return discrepancia > self.MARGEN_ERROR_GRADOS


class TecnicaMaestra:
    """
    Representa una técnica maestra de referencia en Brazilian Jiu-Jitsu.

    Encapsula la información de la técnica ideal (video de referencia,
    categoría, posición de origen) junto con las reglas biomecánicas
    que definen su ejecución correcta.

    El atributo `ventana_sakoe_chiba` controla la flexibilidad del
    alineamiento temporal DTW (Dynamic Time Warping) al comparar
    la ejecución del practicante contra la técnica de referencia.
    """

    def __init__(
        self,
        nombre: str,
        categoria: str,
        posicion_origen: str,
        video_url: str,
        ventana_sakoe_chiba: float = 0.15,
        id_tecnica: uuid.UUID | None = None,
    ) -> None:
        self.id_tecnica: uuid.UUID = id_tecnica or uuid.uuid4()
        self.nombre: str = nombre
        self.categoria: str = categoria
        self.posicion_origen: str = posicion_origen
        self.ventana_sakoe_chiba: float = ventana_sakoe_chiba
        self.video_url: str = video_url
        self.reglas: List[ReglaBiomecanica] = []

    def agregar_regla(self, regla: ReglaBiomecanica) -> None:
        """Agrega una regla biomecánica a la técnica maestra.

        Args:
            regla: Instancia de ReglaBiomecanica a asociar.
        """
        self.reglas.append(regla)


class AnalisisBiomecanico:
    """
    Representa el resultado de un análisis biomecánico sobre la
    ejecución de una técnica por parte de un practicante.

    Contiene las métricas clave de la evaluación: desviación angular
    máxima, articulación afectada y estado del cómputo (EXITOSO,
    OCCLUSION, etc.).
    """

    def __init__(
        self,
        desviacion_angular_maxima: float,
        articulacion_afectada: str,
        estado_computo: str,
        fecha_procesamiento: datetime | None = None,
        id_analisis: uuid.UUID | None = None,
        video_id: uuid.UUID | None = None,
    ) -> None:
        self.id_analisis: uuid.UUID = id_analisis or uuid.uuid4()
        self.fecha_procesamiento: datetime = fecha_procesamiento or datetime.now()
        self.desviacion_angular_maxima: float = desviacion_angular_maxima
        self.articulacion_afectada: str = articulacion_afectada
        self.estado_computo: str = estado_computo
        self.video_id: uuid.UUID | None = video_id

    def generar_diagnostico(self) -> dict:
        """Genera un diccionario resumen del análisis biomecánico.

        Returns:
            Diccionario con las métricas clave del análisis.
        """
        return {
            "id_analisis": str(self.id_analisis),
            "fecha_procesamiento": self.fecha_procesamiento.isoformat(),
            "desviacion_angular_maxima": self.desviacion_angular_maxima,
            "articulacion_afectada": self.articulacion_afectada,
            "estado_computo": self.estado_computo,
        }


class VideoEjecucion:
    """
    Representa un video de ejecución subido por un practicante
    de Jiu-Jitsu para su análisis biomecánico.

    Impone restricciones de negocio sobre el tamaño y duración
    del video para garantizar un procesamiento eficiente.
    """

    PESO_MAXIMO_MB: float = 5.0
    DURACION_MAXIMA_SEGUNDOS: float = 6.0

    def __init__(
        self,
        duracion_segundos: float,
        peso_mb: float,
        video_url: str,
        id_video: uuid.UUID | None = None,
    ) -> None:
        self.id_video: uuid.UUID = id_video or uuid.uuid4()
        self.duracion_segundos: float = duracion_segundos
        self.peso_mb: float = peso_mb
        self.video_url: str = video_url

    def validar_limites(self) -> bool:
        """Valida que el video cumpla con los límites de negocio.

        Returns:
            True si el video está dentro de los límites permitidos.

        Raises:
            ValueError: Si el peso supera 5.0 MB o la duración supera 6.0 s.
        """
        if self.peso_mb > self.PESO_MAXIMO_MB:
            raise ValueError(
                f"El peso del video ({self.peso_mb} MB) excede el límite "
                f"permitido de {self.PESO_MAXIMO_MB} MB."
            )
        if self.duracion_segundos > self.DURACION_MAXIMA_SEGUNDOS:
            raise ValueError(
                f"La duración del video ({self.duracion_segundos} s) excede "
                f"el límite permitido de {self.DURACION_MAXIMA_SEGUNDOS} s."
            )
        return True
