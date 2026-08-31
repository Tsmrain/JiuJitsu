"""
Interfaces de Repositorio e Infraestructura (Principio de Inversión de Dependencias)

Define los contratos abstractos (ABCs) que la capa de servicios y
controladores utilizan para interactuar con la infraestructura
(base de datos, almacenamiento cloud) sin acoplarse a implementaciones
concretas.

Esto sigue el Principio de Inversión de Dependencias (DIP - SOLID):
los módulos de alto nivel (controladores, servicios) dependen de
abstracciones, no de implementaciones concretas.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models import AnalisisBiomecanico, TecnicaMaestra, VideoEjecucion


class ITecnicaMaestraRepository(ABC):
    """Contrato para el repositorio de técnicas maestras (RF-02, RF-03).

    Define las operaciones CRUD necesarias para gestionar las técnicas
    de referencia de Brazilian Jiu-Jitsu en el sistema.
    """

    @abstractmethod
    def obtener_por_id(self, id_tecnica: str) -> Optional[TecnicaMaestra]:
        """Obtiene una técnica maestra por su identificador único.

        Args:
            id_tecnica: UUID de la técnica en formato string.

        Returns:
            La técnica encontrada, o None si no existe.
        """

    @abstractmethod
    def listar_todas(self) -> List[TecnicaMaestra]:
        """Lista todas las técnicas maestras registradas en el sistema.

        Returns:
            Lista de TecnicaMaestra disponibles.
        """

    @abstractmethod
    def guardar(self, tecnica: TecnicaMaestra) -> None:
        """Persiste una técnica maestra nueva o actualizada.

        Args:
            tecnica: Instancia de TecnicaMaestra a persistir.
        """

    @abstractmethod
    def eliminar(self, id_tecnica: str) -> bool:
        """Elimina una técnica maestra por su identificador.

        Args:
            id_tecnica: UUID de la técnica en formato string.

        Returns:
            True si se eliminó correctamente, False si no se encontró.
        """


class IAnalisisBiomecanicoRepository(ABC):
    """Contrato para el repositorio de análisis biomecánicos (RF-04).

    Define las operaciones de persistencia para los resultados
    de los análisis de ejecuciones de técnicas.
    """

    @abstractmethod
    def guardar(self, analisis: AnalisisBiomecanico) -> None:
        """Persiste un resultado de análisis biomecánico.

        Args:
            analisis: Instancia de AnalisisBiomecanico a persistir.
        """

    @abstractmethod
    def obtener_por_id(self, id_analisis: str) -> Optional[AnalisisBiomecanico]:
        """Obtiene un análisis por su identificador único.

        Args:
            id_analisis: UUID del análisis en formato string.

        Returns:
            El análisis encontrado, o None si no existe.
        """


class IVideoEjecucionRepository(ABC):
    """Contrato para el repositorio de videos de ejecución (RF-07).

    Define las operaciones de persistencia para los metadatos
    de los videos subidos por los practicantes.
    """

    @abstractmethod
    def guardar(self, video: VideoEjecucion) -> None:
        """Persiste los metadatos de un video de ejecución.

        Args:
            video: Instancia de VideoEjecucion a persistir.
        """


class IHuaweiOBSStorageAdapter(ABC):
    """Contrato para el adaptador de almacenamiento Huawei OBS (RF-07).

    Define las operaciones de subida de archivos multimedia al
    servicio de almacenamiento de objetos en la nube.
    """

    @abstractmethod
    def subir_video(self, video_bytes: bytes, nombre_archivo: str) -> str:
        """Sube un video al almacenamiento cloud.

        Args:
            video_bytes: Contenido binario del video.
            nombre_archivo: Nombre del archivo destino.

        Returns:
            URL pública o pre-firmada del video subido.
        """

    @abstractmethod
    def subir_fotograma(self, fotograma_bytes: bytes, nombre_archivo: str) -> str:
        """Sube un fotograma (imagen) al almacenamiento cloud.

        Args:
            fotograma_bytes: Contenido binario del fotograma.
            nombre_archivo: Nombre del archivo destino.

        Returns:
            URL pública o pre-firmada del fotograma subido.
        """
