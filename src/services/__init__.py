"""Servicios de Aplicación Transversales (Pure Fabrication — Larman, Cap. 16).

Contiene servicios de orquestación que no pertenecen a ninguna entidad de dominio
pero tampoco son infraestructura pura. Siguiendo Pure Fabrication de Larman, estos
servicios mejoran la cohesión evitando sobrecargar las entidades de dominio.

Módulos:
    chunker_semantico         — Fragmentación semántica de literatura técnica (LangChain)
    sintesis_pedagogica_service — Orquestación RAG + Gemini para feedback contextualizado
"""

__all__ = [
    "ChunkerSemanticoBJJ",
    "SintesisPedagogicaService",
]
