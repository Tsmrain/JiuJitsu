from unittest.mock import MagicMock, patch

from corpocmente.application.services.instructor_message_ingestion import sincronizar_mensaje_profesor


@patch("corpocmente.application.services.instructor_message_ingestion.QwenEmbeddingAdapter")
@patch("corpocmente.application.services.instructor_message_ingestion.QdrantRAGAdapter")
def test_mensaje_profesor_reemplaza_el_anterior_y_guarda_el_texto_exacto(rag_cls, qwen_cls):
    rag = rag_cls.return_value
    qwen_cls.return_value.generar_embedding_texto.return_value = [0.1] * 2048

    total = sincronizar_mensaje_profesor("tech-1", "  Cierra el codo.  ")

    assert total == 1
    rag.eliminar_mensaje_profesor.assert_called_once_with("tech-1")
    qwen_cls.return_value.generar_embedding_texto.assert_called_once_with("Cierra el codo.")
    kwargs = rag.ingestar_desde_respuesta.call_args.kwargs
    assert kwargs["tecnica_id"] == "tech-1"
    assert kwargs["fuente_tipo"] == "instructor_message"
    assert kwargs["metadata_por_chunk"] == [{"media_path": None, "media_url": None, "modalidad": "texto"}]


@patch("corpocmente.application.services.instructor_message_ingestion.QdrantRAGAdapter")
def test_mensaje_vacio_elimina_la_version_anterior(rag_cls):
    assert sincronizar_mensaje_profesor("tech-1", "   ") == 0
    rag_cls.return_value.eliminar_mensaje_profesor.assert_called_once_with("tech-1")
    rag_cls.return_value.ingestar_desde_respuesta.assert_not_called()
