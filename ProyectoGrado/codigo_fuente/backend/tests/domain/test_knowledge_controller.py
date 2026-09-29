import pytest

pytestmark = pytest.mark.skip(reason="Tests de KnowledgeController serán reescritos para IngestKnowledgeUseCase en iteración C11.3")


def test_placeholder_migracion_pendiente():
    """
    Este archivo se mantiene como marcador de deuda técnica.
    La migración a IngestKnowledgeUseCase requiere tests nuevos con mocks de Colab y Qdrant.
    Se abordará en la iteración C11.3 (Test-First, Larman).
    """
    pass
