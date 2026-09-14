# src/domain/validation_constants.py
"""Constantes de validación canónicas del dominio para Jiu-Jitsu Biomechanics.

Centraliza las reglas de negocio (regex de email, categorías, límites multimedia)
cumpliendo el principio de Variaciones Protegidas de Larman (fuente única de verdad).
"""

import re
from typing import List

EMAIL_REGEX_STR: str = r"^[\w\.-]+@[\w\.-]+\.\w+$"
EMAIL_REGEX: re.Pattern = re.compile(EMAIL_REGEX_STR)

CATEGORIAS_VALIDAS: List[str] = [
    "Guardia",
    "Pasada",
    "Sumisión",
    "Transición",
    "Escape",
    "Derribo"
]

MAX_VIDEO_MB: int = 50
MAX_VIDEO_BYTES: int = MAX_VIDEO_MB * 1024 * 1024
FORMATOS_VIDEO_PERMITIDOS: List[str] = [".mp4", "video/mp4"]
