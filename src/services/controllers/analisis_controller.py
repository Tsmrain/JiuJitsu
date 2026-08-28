"""
Controlador de Caso de Uso para Análisis Biomecánico (Craig Larman / GRASP Controller).
Desacopla la interfaz de usuario Streamlit de los motores algorítmicos, OBS y PostgreSQL.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from src.infrastructure.database.models import AnalisisBiomecanico, FotogramaAnotado
from src.infrastructure.repositories.analisis_repository import AnalisisBiomecanicoRepository
from src.infrastructure.repositories.tecnica_repository import TecnicaMaestraRepository
from src.infrastructure.repositories.token_repository import TokenRepository
from src.infrastructure.storage.obs_adapter import HuaweiOBSStorageAdapter
from src.services.pipeline_engine import PipelineBiomecanicoEngine

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


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
        video_profesor_bytes: Optional[bytes] = None,
    ) -> DiagnosticoDTO:
        """
        Orquesta el ciclo completo de análisis biomecánico:
        1. Valida el token con TokenRepository (lanza TokenInvalidoError si es inválido).
        2. Recupera la técnica maestra con TecnicaMaestraRepository.
        3. Obtiene los bytes del video demostrativo del profesor (desde assets/videos_patron/{id}.mp4 o OBS).
        4. Ejecuta el pipeline serverless real (MediaPipe + Kalman + DTW + OpenCV).
        5. Zero-Persistence (RF-11): si aborta por oclusión, no guarda nada en OBS ni BD.
        6. Flujo exitoso: sube fotograma a OBS (o fallback local) y persiste el análisis en PostgreSQL.

        :param token: Token alfanumérico ingresado por el practicante.
        :param video_bytes: Bytes del archivo de video MP4 cargado.
        :param id_tecnica: Identificador único de la técnica maestra a comparar.
        :param id_video: Identificador opcional del video para vinculación relacional.
        :param video_profesor_bytes: Bytes opcionales del video demostrativo del profesor.
        :return: DiagnosticoDTO con el resultado procesado.
        """
        # 1. Validación estricta del token de membresía
        if not self.token_repo.validar_token(token):
            raise TokenInvalidoError("Token de activación o membresía inválido, expirado o revocado.")

        # 2. Obtención de la técnica curricular patrón y sus tolerancias
        tecnica_maestra = self.tecnica_repo.obtener_tecnica_y_reglas(id_tecnica)

        # 3. Buscar video patrón del profesor
        video_patron_bytes = video_profesor_bytes
        if video_patron_bytes is None:
            # Buscar en caché local de videos del profesor
            ruta_video_local = ROOT_DIR / "assets" / "videos_patron" / f"{id_tecnica}.mp4"
            if ruta_video_local.exists():
                try:
                    video_patron_bytes = ruta_video_local.read_bytes()
                except Exception:
                    pass

            # Si no está en disco local, intentar descargar desde Huawei Cloud OBS
            if video_patron_bytes is None and tecnica_maestra.video_url and not tecnica_maestra.video_url.startswith("http"):
                try:
                    video_patron_bytes = self.storage_adapter.descargar_objeto(
                        object_key=tecnica_maestra.video_url,
                        bucket_name=self.storage_adapter.bucket_input,
                    )
                except Exception:
                    pass

        # 4. Disparo del motor algorítmico serverless real
        resultado_pipeline = self.pipeline_engine.ejecutar_pipeline_completo(
            video_bytes=video_bytes,
            tecnica_maestra=tecnica_maestra,
            video_profesor_bytes=video_patron_bytes,
        )

        # 5. Salvaguarda de Zero-Persistence ante oclusión prolongada (RF-11)
        if resultado_pipeline.estado_computo == "ABORTADO_OCLUSION":
            return DiagnosticoDTO(
                estado="ABORTADO_OCLUSION",
                imagen_url=None,
                explicacion_error=resultado_pipeline.explicacion_error,
                desviacion_maxima=0.0,
                articulacion_afectada="",
            )

        # 6. Flujo Exitoso con persistencia
        imagen_url: Optional[str] = None
        id_video_real = id_video or uuid4()
        id_analisis_nuevo = uuid4()

        if resultado_pipeline.imagen_jpg_bytes is not None:
            # Subir fotograma anotado a Huawei Cloud OBS con fallback local si estamos offline
            object_key = f"fotogramas/{id_analisis_nuevo}_anotado.jpg"
            try:
                imagen_url = self.storage_adapter.subir_fotograma(
                    foto_bytes=resultado_pipeline.imagen_jpg_bytes,
                    object_key=object_key,
                )
            except Exception:
                # Fallback de persistencia local para desarrollo
                dir_local = ROOT_DIR / "assets" / "fotogramas_anotados"
                dir_local.mkdir(parents=True, exist_ok=True)
                ruta_local_foto = dir_local / f"{id_analisis_nuevo}_anotado.jpg"
                with open(ruta_local_foto, "wb") as f:
                    f.write(resultado_pipeline.imagen_jpg_bytes)
                imagen_url = str(ruta_local_foto)

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

    def listar_tecnicas(self):
        """Retorna las técnicas maestras registradas en el currículo."""
        return self.tecnica_repo.listar_tecnicas()

    def registrar_tecnica_maestra(
        self,
        nombre: str,
        categoria: str,
        posicion: str,
        ventana_sakoe: float,
        video_bytes: bytes,
        reglas_datos: list,
    ):
        """
        Orquesta el Caso de Uso CU-01 (Head Coach):
        1. Sube el video patrón grabado por el profesor a Huawei Cloud OBS.
        2. Construye la técnica maestra con sus reglas biomecánicas de tolerancia.
        3. Persiste la técnica en la base de datos para que los alumnos se comparen contra ella.
        """
        from src.domain.models import ReglaBiomecanica, TecnicaMaestra

        id_tecnica_nueva = uuid4()
        nombre_limpio = nombre.strip() or "Técnica Maestra Oficial"
        slug_nombre = nombre_limpio.lower().replace(" ", "_").replace("/", "_")
        object_key = f"patrones_maestros/{id_tecnica_nueva}_{slug_nombre}.mp4"

        # 1. Almacenar video patrón en Huawei Cloud OBS (con fallback si offline)
        try:
            video_url = self.storage_adapter.subir_video(video_bytes, object_key)
        except Exception:
            video_url = f"https://obs.la-south-2.myhuaweicloud.com/bjj-videos-input/{object_key}"

        # Guardar en copia local de videos patrón
        dir_videos = ROOT_DIR / "assets" / "videos_patron"
        dir_videos.mkdir(parents=True, exist_ok=True)
        with open(dir_videos / f"{id_tecnica_nueva}.mp4", "wb") as f:
            f.write(video_bytes)

        # 2. Configurar reglas biomecánicas
        reglas = []
        for r in reglas_datos:
            reglas.append(
                ReglaBiomecanica(
                    id=uuid4(),
                    articulacion_clave=r.get("articulacion_clave", "codo_derecho"),
                    umbral_angular_tolerado=float(r.get("umbral_angular_tolerado", 15.0)),
                    descripcion_error=r.get("descripcion_error", "Desviación angular detectada."),
                )
            )

        tecnica = TecnicaMaestra(
            id=id_tecnica_nueva,
            nombre=nombre_limpio,
            categoria_tecnica=categoria.strip(),
            posicion_origen=posicion.strip(),
            ventana_sakoe_chiba=float(ventana_sakoe),
            video_url=video_url,
            reglas=reglas,
        )

        # 3. Persistir en repositorio
        self.tecnica_repo.guardar_tecnica(tecnica)
        return tecnica

    def actualizar_tecnica_maestra(self, id_tecnica: UUID, nuevo_nombre: str):
        """Actualiza el nombre de una técnica maestra existente (Update en CRUD)."""
        return self.tecnica_repo.actualizar_tecnica(id_tecnica, nuevo_nombre.strip())

    def eliminar_tecnica_maestra(self, id_tecnica: UUID) -> bool:
        """Elimina una técnica maestra del catálogo oficial (Delete en CRUD)."""
        return self.tecnica_repo.eliminar_tecnica(id_tecnica)
