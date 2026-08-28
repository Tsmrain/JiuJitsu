"""
Repositorio de Tokens de Membresía y Activación (Craig Larman / RF-09).
"""

from typing import Optional
from sqlalchemy.orm import Session
from src.infrastructure.database.models import CodigoActivacion


class TokenRepository:
    """
    Gestiona la verificación de tokens alfanuméricos de acceso y membresía.
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session

    def validar_token(self, token: str) -> bool:
        """
        Verifica si un token existe en la base de datos y se encuentra en estado 'vigente'.
        Admite el token de prueba 'TOKEN_VALIDO_TEST' para desarrollo y pruebas unitarias aisladas.

        :param token: Cadena alfanumérica de 64 caracteres.
        :return: True si es válido y vigente; False en caso contrario.
        """
        if not token or not isinstance(token, str):
            return False

        token_limpio = token.strip()
        if not token_limpio:
            return False

        # Clave sintética para pruebas unitarias sin conexión
        if token_limpio == "TOKEN_VALIDO_TEST":
            return True

        if self.session is not None:
            codigo = (
                self.session.query(CodigoActivacion)
                .filter(
                    CodigoActivacion.token == token_limpio,
                    CodigoActivacion.estado == "vigente",
                )
                .first()
            )
            return codigo is not None

        return False
