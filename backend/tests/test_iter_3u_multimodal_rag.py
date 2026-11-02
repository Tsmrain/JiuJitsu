from types import SimpleNamespace
from unittest.mock import MagicMock

from corpocmente.application.services import multimodal_rag_service
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter


def test_mensaje_profesor_es_forzado_en_top_k_aun_sin_embeddings():
    qdrant = MagicMock()
    qdrant.obtener_mensaje_profesor_rag.return_value = [{
        "id": "mensaje-actual", "fuente_tipo": "instructor_message",
        "contenido_texto": "Mantén la cadera alta.", "media_path": None,
    }]
    qwen = MagicMock()
    qwen.generar_embedding_texto.side_effect = RuntimeError("sin modelo")

    resultado = multimodal_rag_service.obtener_evidencias_rag_multimodal(
        qwen, qdrant, "tech-1", "Armbar", ["cadera baja"], limit=5
    )

    assert resultado == qdrant.obtener_mensaje_profesor_rag.return_value


def test_ingesta_mensaje_guarda_payload_exacto_y_sin_media():
    client = MagicMock()
    client.get_collections.return_value.collections = []
    rag = QdrantRAGAdapter(client=client)
    rag.ingestar_desde_respuesta(
        {"chunks": ["Cierra el codo."], "embeddings": [[0.1] * 2048]},
        tecnica_id="tech-1", fuente_tipo="instructor_message",
        metadata_por_chunk=[{"media_path": None}],
    )
    point = client.upsert.call_args.kwargs["points"][0]
    assert point.payload["tecnica_id"] == "tech-1"
    assert point.payload["fuente_tipo"] == "instructor_message"
    assert point.payload["contenido_texto"] == "Cierra el codo."
    assert point.payload["media_path"] is None


def test_rag_adapter_recupera_mensaje_sin_busqueda_semantica():
    client = MagicMock()
    client.scroll.return_value = ([SimpleNamespace(id="m-1", payload={
        "contenido_texto": "No cruces los pies.", "tecnica_id": "tech-1",
        "alcance": "tecnica", "modalidad": "texto",
    })], None)
    adapter = MagicMock()
    adapter.rag_collection_name = "rag_knowledge"
    adapter.client = client
    from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
    resultado = QdrantVectorAdapter.obtener_mensaje_profesor_rag(adapter, "tech-1")
    assert resultado[0]["fuente_tipo"] == "instructor_message"
    assert resultado[0]["contenido_texto"] == "No cruces los pies."
