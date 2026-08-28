"""
Repositorio del Catálogo Curricular de Técnicas Maestras (Craig Larman / RF-01, CU-01).
"""

from typing import Dict, List, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from src.domain.models import ReglaBiomecanica as DomainRegla
from src.domain.models import TecnicaMaestra as DomainTecnica
from src.infrastructure.database.models import ReglaBiomecanica as DBRegla
from src.infrastructure.database.models import TecnicaMaestra as DBTecnica

ID_TECNICA_DEFAULT = UUID("00000000-0000-0000-0000-000000000001")


class TecnicaMaestraRepository:
    """
    Gestiona el almacenamiento y recuperación de técnicas maestras homologadas por el Head Coach.
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session
        # Catálogo en memoria para funcionamiento en modo desarrollo / demostración local
        self._catalogo_en_memoria: Dict[UUID, DomainTecnica] = {}
        self._inicializar_catalogo_base()

    def _inicializar_catalogo_base(self) -> None:
        """Carga técnicas base de referencia enseñadas por el profesor."""
        id_montada = UUID("00000000-0000-0000-0000-000000000002")
        tecnica_montada = DomainTecnica(
            id=id_montada,
            nombre="Cómo escapar de la montada (Puente Upa y Codo-Rodilla)",
            categoria_tecnica="Escape / Defensa",
            posicion_origen="Montada",
            ventana_sakoe_chiba=0.15,
            video_url="https://obs.la-south-2.myhuaweicloud.com/bjj-videos-input/escape_montada_profesor.mp4",
            reglas=[
                DomainRegla(
                    id=uuid4(),
                    articulacion_clave="cadera_derecha",
                    umbral_angular_tolerado=15.0,
                    descripcion_error="Falta elevación pélvica explosiva en el puente antes de girar hacia el lado del bloqueo.",
                )
            ],
        )

        tecnica_armbar = DomainTecnica(
            id=ID_TECNICA_DEFAULT,
            nombre="Armbar desde Guardia Cerrada",
            categoria_tecnica="Llave / Sumisión",
            posicion_origen="Guardia Cerrada",
            ventana_sakoe_chiba=0.15,
            video_url="https://obs.la-south-2.myhuaweicloud.com/bjj-videos-input/armbar_profesor.mp4",
            reglas=[
                DomainRegla(
                    id=uuid4(),
                    articulacion_clave="codo_derecho",
                    umbral_angular_tolerado=15.0,
                    descripcion_error="Brazo hiper-extendido sin fijación de muñeca contra el pecho.",
                )
            ],
        )

        self._catalogo_en_memoria[id_montada] = tecnica_montada
        self._catalogo_en_memoria[ID_TECNICA_DEFAULT] = tecnica_armbar

    def listar_tecnicas(self) -> List[DomainTecnica]:
        """
        Retorna la lista de todas las técnicas maestras registradas en el currículo oficial.
        """
        if self.session is not None:
            tecnicas_db = self.session.query(DBTecnica).all()
            if tecnicas_db:
                resultado = []
                for t in tecnicas_db:
                    reglas_d = [
                        DomainRegla(
                            id=r.id_regla,
                            articulacion_clave=r.articulacion_clave,
                            umbral_angular_tolerado=float(r.umbral_angular_tolerado),
                            descripcion_error=r.descripcion_error,
                        )
                        for r in t.reglas
                    ]
                    resultado.append(
                        DomainTecnica(
                            id=t.id_tecnica,
                            nombre=t.nombre,
                            categoria_tecnica=t.categoria_tecnica,
                            posicion_origen=t.posicion_origen,
                            ventana_sakoe_chiba=float(t.ventana_sakoe_chiba),
                            video_url=t.video_url,
                            reglas=reglas_d,
                        )
                    )
                return resultado

        return list(self._catalogo_en_memoria.values())

    def obtener_tecnica_y_reglas(self, id_tecnica: UUID) -> DomainTecnica:
        """
        Recupera una técnica maestra y sus reglas por su identificador.
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

        if id_tecnica in self._catalogo_en_memoria:
            return self._catalogo_en_memoria[id_tecnica]

        # Si no existe, retorna la técnica patrón base
        return self._catalogo_en_memoria[ID_TECNICA_DEFAULT]

    def guardar_tecnica(self, tecnica: DomainTecnica) -> None:
        """
        Persiste una nueva técnica maestra y sus reglas biomecánicas (CU-01 / RF-01).
        """
        self._catalogo_en_memoria[tecnica.id] = tecnica

        if self.session is not None:
            db_tecnica = DBTecnica(
                id_tecnica=tecnica.id,
                nombre=tecnica.nombre,
                categoria_tecnica=tecnica.categoria_tecnica,
                posicion_origen=tecnica.posicion_origen,
                ventana_sakoe_chiba=tecnica.ventana_sakoe_chiba,
                video_url=tecnica.video_url,
            )
            for r in tecnica.reglas:
                db_regla = DBRegla(
                    id_regla=r.id,
                    tecnica_id=tecnica.id,
                    articulacion_clave=r.articulacion_clave,
                    umbral_angular_tolerado=r.umbral_angular_tolerado,
                    descripcion_error=r.descripcion_error,
                )
                db_tecnica.reglas.append(db_regla)

            self.session.add(db_tecnica)
            self.session.commit()
