"""Capa de Servicios de Aplicación y Adaptadores Externos.

Siguiendo a Craig Larman (Variaciones Protegidas e Indirección), este módulo
expone adaptadores unificados para motores de visión artificial (YOLO) y
modelos de lenguaje generativo/embeddings (Gemini).
"""

from src.services.adapters import AdaptadorYOLO, AdaptadorGemini

__all__ = ["AdaptadorYOLO", "AdaptadorGemini"]
