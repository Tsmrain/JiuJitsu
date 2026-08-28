"""
Controlador de Caso de Uso para Análisis Biomecánico (Craig Larman / GRASP Controller).
Desacopla la interfaz de usuario Streamlit de los motores algorítmicos, OBS y PostgreSQL.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4

from src.infrastructure.database.models import AnalisisBiomecanico, FotogramaAnotado
from src.infrastructure.repositories.analisis_repository import AnalisisBiomecanicoRepository
from src.infrastructure.repositories.tecnica_repository import TecnicaMaestraRepository
from src.infrastructure.repositories.token_repository import TokenRepository
from src.infrastructure.storage.obs_adapter import HuaweiOBSStorageAdapter
from src.services.pipeline_engine import PipelineBiomecanicoEngine


class TokenInvalidoError(Exception):
    """Excepción lanzada cuando el token de activación es inexistente, revocado o expirado."""
    pass


@dataclass
class DiagnosticoDTO:
    """Objeto de Transferencia de Datos retornado a la interfaz de usuario Streamlit."""
    estado: str  # 'EXITOSO', 'SIN_FALLAS', 'ABORTADO_OCLUSION', 'ERROR'
    imagen_url: Optional[str]
    explicacion_error: str
    desviacion_maxima: float
    articulacion_afectada: str


class AnalisisBiomecanicoController:
    """
    Controlador de Caso de Uso (GRASP Controller / Craig Larman).
    
    Recibe los eventos del sistema disparados por la interfaz de usuario, coordina
    la validación de membresía, dispara la ejecución del motor serverless y orquesta
    la persistencia relacional y el almacenamiento en Huawei Cloud OBS.
    """

    def __init__(
        self,
        token_repo: TokenRepository,
        tecnica_repo: TecnicaMaestraRepository,
        analisis_repo: AnalisisBiomecanicoRepository,
        storage_adapter: HuaweiOBSStorageAdapter,
        pipeline_engine: PipelineBiomecanicoEngine,
    ) -> None:
        self.token_repo = token_repo
        self.tecnica_repo = tecnica_repo
        self.analisis_repo = analisis_repo
        self.storage_adapter = storage_adapter
        self.pipeline_engine = pipeline_engine

    def ejecutar_analisis(
        self,
        token: str,
        video_bytes: bytes,
        id_tecnica: UUID,
        id_video: Optional[UUID] = None,
    ) -> DiagnosticoDTO:
        """
        Orquesta el ciclo completo de análisis biomecánico:
        1. Valida el token con TokenRepository (lanza TokenInvalidoError si es inválido).
        2. Recupera la técnica maestra con TecnicaMaestraRepository.
        3. Ejecuta el pipeline serverless.
        4. Zero-Persistence (RF-11): si aborta por oclusión, no guarda nada en OBS ni BD.
        5. Flujo exitoso: sube fotograma a OBS y persiste el análisis en PostgreSQL.

        :param token: Token alfanumérico ingresado por el practicante.
        :param video_bytes: Bytes del archivo de video MP4 cargado.
        :param id_tecnica: Identificador único de la técnica maestra a comparar.
        :param id_video: Identificador opcional del video para vinculación relacional.
        :return: DiagnosticoDTO con el resultado procesado.
        """
        # 1. Validación estricta del token de membresía
        if not self.token_repo.validar_token(token):
            raise TokenInvalidoError("Token de activación o membresía inválido, expirado o revocado.")

        # 2. Obtención de la técnica curricular patrón y sus tolerancias
        tecnica_maestra = self.tecnica_repo.obtener_tecnica_y_reglas(id_tecnica)

        # 3. Disparo del motor algorítmico serverless
        resultado_pipeline = self.pipeline_engine.ejecutar_pipeline_completo(
            video_bytes=video_bytes,
            tecnica_maestra=tecnica_maestra,
        )

        # 4. Salvaguarda de Zero-Persistence ante oclusión prolongada (RF-11)
        if resultado_pipeline.estado_computo == "ABORTADO_OCLUSION":
            return DiagnosticoDTO(
                estado="ABORTADO_OCLUSION",
                imagen_url=None,
                explicacion_error=resultado_pipeline.explicacion_error,
                desviacion_maxima=0.0,
                articulacion_afectada="",
            )

        # 5. Flujo Exitoso con persistencia atómica
        imagen_url: Optional[str] = None
        id_video_real = id_video or uuid4()
        id_analisis_nuevo = uuid4()

        if resultado_pipeline.imagen_jpg_bytes is not None:
            # Subir fotograma anotado a Huawei Cloud OBS
            object_key = f"fotogramas/{id_analisis_nuevo}_anotado.jpg"
            imagen_url = self.storage_adapter.subir_fotograma(
                foto_bytes=resultado_pipeline.imagen_jpg_bytes,
                object_key=object_key,
            )

            # Instanciar modelos ORM de persistencia
            analisis_db = AnalisisBiomecanico(
                id_analisis=id_analisis_nuevo,
                video_id=id_video_real,
                desviacion_angular_maxima=resultado_pipeline.desviacion_maxima,
                articulacion_afectada=resultado_pipeline.articulacion_afectada,
                estado_computo="completado",
            )

            fotograma_db = FotogramaAnotado(
                id_fotograma=uuid4(),
                analisis_id=id_analisis_nuevo,
                imagen_url=imagen_url,
                coordenada_error_x=resultado_pipeline.coordenada_error_x or 0,
                coordenada_error_y=resultado_pipeline.coordenada_error_y or 0,
                explicacion_causa=resultado_pipeline.explicacion_error,
            )

            # Persistir en base de datos PostgreSQL
            self.analisis_repo.guardar_resultado(analisis_db, fotograma_db)

        return DiagnosticoDTO(
            estado=resultado_pipeline.estado_computo,
            imagen_url=imagen_url,
            explicacion_error=resultado_pipeline.explicacion_error,
            desviacion_maxima=resultado_pipeline.desviacion_maxima,
            articulacion_afectada=resultado_pipeline.articulacion_afectada,
        )
