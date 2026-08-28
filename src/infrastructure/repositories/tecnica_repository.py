"""
Repositorio del Catálogo Curricular de Técnicas Maestras (Craig Larman / RF-01).
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.models import ReglaBiomecanica as DomainRegla
from src.domain.models import TecnicaMaestra as DomainTecnica
from src.infrastructure.database.models import TecnicaMaestra as DBTecnica


class TecnicaMaestraRepository:
    """
    Gestiona la recuperación de técnicas maestras homologadas y sus reglas biomecánicas asociadas.
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session

    def obtener_tecnica_y_reglas(self, id_tecnica: UUID) -> DomainTecnica:
        """
        Recupera una técnica maestra junto con su catálogo determinista de reglas por su UUID.
        Si no se encuentra en sesión o no hay sesión activa, retorna un molde canónico de prueba.

        :param id_tecnica: Identificador único de la técnica maestra.
        :return: Entidad de dominio pura TecnicaMaestra.
        """
        if self.session is not None:
            tecnica_db = (
                self.session.query(DBTecnica)
                .filter(DBTecnica.id_tecnica == id_tecnica)
                .first()
            )
            if tecnica_db is not None:
                reglas_dominio = [
                    DomainRegla(
                        id=r.id_regla,
                        articulacion_clave=r.articulacion_clave,
                        umbral_angular_tolerado=float(r.umbral_angular_tolerado),
                        descripcion_error=r.descripcion_error,
                    )
                    for r in tecnica_db.reglas
                ]
                return DomainTecnica(
                    id=tecnica_db.id_tecnica,
                    nombre=tecnica_db.nombre,
                    categoria_tecnica=tecnica_db.categoria_tecnica,
                    posicion_origen=tecnica_db.posicion_origen,
                    ventana_sakoe_chiba=float(tecnica_db.ventana_sakoe_chiba),
                    video_url=tecnica_db.video_url,
                    reglas=reglas_dominio,
                )

        # Retorno de fallback canónico para desarrollo y pruebas simuladas
        return DomainTecnica(
            id=id_tecnica,
            nombre="Armbar desde Guardia Cerrada",
            categoria_tecnica="Llave de Brazo",
            posicion_origen="Guardia Cerrada",
            ventana_sakoe_chiba=0.15,
            video_url="https://obs.la-south-2.myhuaweicloud.com/bjj-videos-input/armbar_patron.mp4",
            reglas=[
                DomainRegla(
                    id=id_tecnica,
                    articulacion_clave="codo_derecho",
                    umbral_angular_tolerado=15.0,
                    descripcion_error="Brazo hiper-extendido sin control de muneca",
                )
            ],
        )
