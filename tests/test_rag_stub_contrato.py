# tests/test_rag_stub_contrato.py
import inspect
from src.infrastructure.persistence.rag_ingestion import (
    IngestorRAGStub,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
)


def test_ingestor_rag_stub_tiene_metodos_requeridos():
    ingestor = IngestorRAGStub()
    assert hasattr(ingestor, "fragmentar_texto")
    sig = inspect.signature(ingestor.fragmentar_texto)
    assert "tamano_chunk" in sig.parameters
    assert "solapamiento" in sig.parameters


def test_ingestor_rag_stub_fragmenta_con_solapamiento():
    ingestor = IngestorRAGStub()
    texto = "A" * 1500
    chunks = ingestor.fragmentar_texto(texto, tamano_chunk=1000, solapamiento=200)
    assert len(chunks) == 2
    assert len(chunks[0]) == 1000
    assert len(chunks[1]) == 700


def test_constantes_rag_configuradas():
    assert CHUNK_SIZE == 1000
    assert CHUNK_OVERLAP == 200
    assert EMBEDDING_DIM == 2048
    assert EMBEDDING_MODEL == "Qwen3-VL-Embedding-2B"
