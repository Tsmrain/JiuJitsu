"""
Repositorio de Persistencia de Análisis Biomecánicos y Fotogramas (Craig Larman / RF-11).
"""

from typing import Any, Optional
from sqlalchemy.orm import Session
from src.infrastructure.database.models import AnalisisBiomecanico, FotogramaAnotado


class AnalisisBiomecanicoRepository:
    """
    Gestiona la persistencia transaccional atómica de análisis cinemáticos y fotogramas anotados.
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session

    def guardar_resultado(
        self,
        analisis: Any,
        fotograma: Optional[Any] = None,
    ) -> None:
        """
        Persiste atómicamente la entidad AnalisisBiomecanico y opcionalmente su FotogramaAnotado.
        Si la sesión está presente, ejecuta session.add() y session.commit().

        :param analisis: Objeto AnalisisBiomecanico a persistir.
        :param fotograma: Objeto FotogramaAnotado opcional (1:0..1).
        """
        if self.session is not None:
            self.session.add(analisis)
            if fotograma is not None:
                self.session.add(fotograma)
            self.session.commit()
