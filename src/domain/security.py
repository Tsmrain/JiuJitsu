"""Utilidades criptográficas del dominio (PBKDF2-HMAC-SHA256, stdlib puro).

Aplica Experto en Información (Larman): el hashing es responsabilidad del dominio,
no de los controladores ni de la infraestructura.
"""

import hashlib
import hmac
import os
import time
from typing import Tuple, Dict, Any
import jwt

_ALGORITMO = "pbkdf2_sha256"
_ITERACIONES = 200_000
_SALT_BYTES = 16
_JWT_ALGORITHM = "HS256"

def _get_secret_key() -> str:
    return os.getenv("SECRET_KEY", "super-secret-default-key-for-dev")


def hash_password(password: str) -> str:
    """Genera un hash autocontenido con formato `algo$iteraciones$salt_hex$hash_hex`."""
    if not password or not isinstance(password, str):
        raise ValueError("La contraseña no puede ser vacía.")
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERACIONES)
    return f"{_ALGORITMO}${_ITERACIONES}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verifica una contraseña contra un hash almacenado con `hmac.compare_digest` (timing-safe)."""
    if not password or not stored:
        return False
    try:
        algo, iter_s, salt_hex, hash_hex = stored.split("$")
        if algo != _ALGORITMO:
            return False
        iterations = int(iter_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(dk, expected)
    except (ValueError, AttributeError):
        return False

def create_access_token(data: dict, expires_minutes: int = 60) -> str:
    """Genera un token JWT para la sesión de usuario."""
    to_encode = data.copy()
    expire = time.time() + (expires_minutes * 60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, _get_secret_key(), algorithm=_JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verifica y decodifica el token JWT."""
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[_JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("El token ha expirado.")
    except jwt.PyJWTError:
        raise ValueError("Token inválido.")
