# src/services/chunker_semantico.py
"""Adaptador protegido para fragmentación semántica de literatura técnica de BJJ.

Encapsula RecursiveCharacterTextSplitter de langchain_text_splitters bajo el patrón
Variaciones Protegidas de Larman, garantizando ventana deslizante de 1000 caracteres
y solapamiento de 200 caracteres para preservar la coherencia cinemática.
"""

from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChunkerSemanticoBJJ:
    """Adaptador protegido para chunking 1000/200 validado en Iteración 3."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def fragmentar(self, texto: str) -> List[str]:
        """Divide un texto en fragmentos coherentes con solapamiento controlado."""
        if not texto or not texto.strip():
            return []
        return self._splitter.split_text(texto)
