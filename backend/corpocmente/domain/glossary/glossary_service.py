import logging
import os
import re
from typing import Any, Dict, List, Optional, Set
import yaml

logger = logging.getLogger(__name__)

_GLOSSARY_CACHE: Optional[Dict[str, Any]] = None


def _get_glossary_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "jj_glossary.yaml")


def cargar_glosario(force_reload: bool = False) -> Dict[str, Any]:
    """Carga y cachea el glosario multilingüe de Jiu-Jitsu."""
    global _GLOSSARY_CACHE
    if _GLOSSARY_CACHE is not None and not force_reload:
        return _GLOSSARY_CACHE

    path = _get_glossary_path()
    if not os.path.exists(path):
        logger.warning("Archivo de glosario no encontrado en: %s", path)
        return {"sinonimos": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            _GLOSSARY_CACHE = data
            return data
    except Exception as exc:
        logger.error("Error cargando glosario YAML (%s): %s", path, exc)
        return {"sinonimos": []}


def obtener_sinonimos_multilingues(texto: str) -> Set[str]:
    """
    Busca términos clave del glosario presentes en el texto (con límites de palabra estrictos)
    y retorna el conjunto de todos sus sinónimos equivalentes en español, portugués e inglés.
    """
    if not texto or not texto.strip():
        return set()

    glosario = cargar_glosario()
    items = glosario.get("sinonimos", [])
    texto_lower = texto.lower()
    sinonimos_encontrados: Set[str] = set()

    for entry in items:
        canonical = entry.get("canonical", "")
        todas_variantes: Set[str] = set()
        for lang_key in ("es", "pt", "en"):
            for v in entry.get(lang_key, []):
                todas_variantes.add(v.lower().strip())
        if canonical:
            todas_variantes.add(canonical.lower().strip())

        # Coincidencia con límites de palabra (regex \b) para evitar falsos positivos
        coincide = False
        for v in todas_variantes:
            if not v:
                continue
            pattern = r'\b' + re.escape(v) + r'\b'
            if re.search(pattern, texto_lower):
                coincide = True
                break

        if coincide:
            sinonimos_encontrados.update(todas_variantes)

    return sinonimos_encontrados


def expandir_query_con_glosario(query: str, max_sinonimos: int = 10) -> str:
    """
    Toma una consulta de texto y la expande con términos equivalentes del glosario
    para potenciar el Recall léxico (BM25) a través de idiomas.
    """
    if not query or not query.strip():
        return ""

    sinonimos = obtener_sinonimos_multilingues(query)
    if not sinonimos:
        return query.strip()

    # Combinar query original con los sinónimos multilingües únicos
    texto_lower = query.lower()
    terminos_extra = [s for s in sorted(sinonimos) if not re.search(r'\b' + re.escape(s.lower()) + r'\b', texto_lower)]
    if not terminos_extra:
        return query.strip()

    return f"{query.strip()} {' '.join(terminos_extra[:max_sinonimos])}".strip()
