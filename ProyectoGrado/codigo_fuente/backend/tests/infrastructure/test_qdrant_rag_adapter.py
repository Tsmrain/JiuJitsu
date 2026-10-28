import pytest
from unittest.mock import MagicMock

from corpocmente.config import settings
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter


def fake_client():
    client = MagicMock()
    client.get_collections.return_value.collections = []
    return client


def test_qdrant_adapters_use_separate_configured_collections(monkeypatch):
    monkeypatch.setattr(settings, "QDRANT_COLLECTION", "pose_vectors")
    monkeypatch.setattr(settings, "QDRANT_RAG_COLLECTION", "multimodal_knowledge")
    pose_client = fake_client()
    rag_client = fake_client()

    pose = QdrantVectorAdapter(client=pose_client)
    rag = QdrantRAGAdapter(client=rag_client)

    assert pose.pose_collection_name == "pose_vectors"
    assert pose.rag_collection_name == "multimodal_knowledge"
    assert rag.collection_name == "multimodal_knowledge"
    rag_client.create_collection.assert_called_once()
    assert rag_client.create_collection.call_args.kwargs["vectors_config"]["dense"].size == 2048


def test_pose_and_rag_collection_cannot_be_the_same(monkeypatch):
    monkeypatch.setattr(settings, "QDRANT_COLLECTION", "same")
    monkeypatch.setattr(settings, "QDRANT_RAG_COLLECTION", "same")
    with pytest.raises(ValueError, match="deben ser distintas"):
        QdrantVectorAdapter(client=fake_client())
    with pytest.raises(ValueError, match="no puede compartir"):
        QdrantRAGAdapter(client=fake_client())


def test_qdrant_rag_rechaza_dimensiones_falsas_antes_de_upsert():
    client = fake_client()
    adapter = QdrantRAGAdapter(client=client)
    with pytest.raises(ValueError, match="2048 dimensiones"):
        adapter.ingestar_desde_respuesta(
            {"chunks": ["texto"], "embeddings": [[0.1] * 133]},
            tecnica_id="tech-1",
        )
    client.upsert.assert_not_called()


def test_qdrant_rag_rechaza_embeddings_y_chunks_desalineados():
    adapter = QdrantRAGAdapter(client=fake_client())
    with pytest.raises(ValueError, match="distinta cantidad"):
        adapter.ingestar_desde_respuesta(
            {"chunks": ["uno", "dos"], "embeddings": [[0.1] * 2048]},
            tecnica_id="tech-1",
        )
