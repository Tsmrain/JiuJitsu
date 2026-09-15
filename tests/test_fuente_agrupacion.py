# tests/test_fuente_agrupacion.py
"""Pruebas unitarias y de integración para la agrupación de fuentes por documento (Larman / Mannino).

Verifica que el acervo pedagógico presente a los instructores documentos consolidados (PDFs)
en lugar de fragmentos individuales (chunks), preservando el conteo de partes y la eliminación en cascada.
"""

import pytest
from unittest.mock import MagicMock
from src.application.fuente_controller import FuenteController
from src.domain.models import FuenteConocimiento
from src.infrastructure.persistence.postgres_repository import PostgresFuenteConocimientoRepository


class FakeCursor:
    def __init__(self, fetchall_data=None, rowcount=1):
        self.fetchall_data = fetchall_data or []
        self.rowcount = rowcount
        self.last_query = ""
        self.last_params = ()

    def execute(self, query, params=None):
        self.last_query = query
        self.last_params = params or ()

    def fetchall(self):
        return self.fetchall_data

    def fetchone(self):
        return self.fetchall_data[0] if self.fetchall_data else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class FakeConnection:
    def __init__(self, cursor_instance):
        self._cursor = cursor_instance

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_listar_fuentes_agrupa_por_documento_y_contiene_metadatos():
    """Verifica que listar_fuentes() devuelva los documentos consolidados con total_chunks."""
    # Simula retorno de PostgreSQL agrupado por documento
    datos_agrupados = [
        # (id_documento, id_tecnica, base_titulo, tipo_recurso, total_chunks, max_fecha, id_instructor)
        ("doc_123456", "armbar", "Manual de Armbar Avanzado", "Manual", 5, "2026-09-15T01:00:00Z", "inst_santiago"),
        ("doc_789012", None, "Fundamentos de Guardia", "PDF", 12, "2026-09-15T01:10:00Z", "inst_santiago"),
    ]
    cursor = FakeCursor(fetchall_data=datos_agrupados)
    conn = FakeConnection(cursor)
    mock_qdrant = MagicMock()

    repo = PostgresFuenteConocimientoRepository(
        db_connection=conn,
        qdrant_adapter=mock_qdrant,
    )
    controller = FuenteController(repository=repo, qdrant_adapter=mock_qdrant)

    resultado = controller.listar_fuentes()

    assert len(resultado) == 2
    doc1 = resultado[0]
    assert doc1["id_documento"] == "doc_123456"
    assert doc1["id_fuente"] == "doc_123456"
    assert doc1["titulo"] == "Manual de Armbar Avanzado"
    assert doc1["total_chunks"] == 5
    assert doc1["tipo_recurso"] == "Manual"

    doc2 = resultado[1]
    assert doc2["id_documento"] == "doc_789012"
    assert doc2["titulo"] == "Fundamentos de Guardia"
    assert doc2["total_chunks"] == 12


def test_eliminar_fuente_por_documento_llama_qdrant_y_postgres():
    """Verifica que eliminar un documento invoque eliminar_por_documento en Qdrant y elimine en Postgres."""
    cursor = FakeCursor(fetchall_data=[("doc_abc", "Manual BJJ", 3)], rowcount=3)
    conn = FakeConnection(cursor)
    mock_qdrant = MagicMock()

    repo = PostgresFuenteConocimientoRepository(
        db_connection=conn,
        qdrant_adapter=mock_qdrant,
    )
    controller = FuenteController(repository=repo, qdrant_adapter=mock_qdrant)

    res = controller.eliminar_fuente("doc_abc")

    assert res["id_fuente"] == "doc_abc"
    assert "eliminada exitosamente" in res["message"]
    # Debe haber invocado eliminar_por_documento en Qdrant
    mock_qdrant.eliminar_por_documento.assert_called_once_with("doc_abc")
    assert "DELETE FROM fuentes_conocimiento" in cursor.last_query


def test_pipeline_ingesta_genera_id_documento_en_postgres_y_qdrant():
    """Verifica que el PipelineIngestaRAG genere id_documento y lo propague a Postgres y Qdrant."""
    from src.infrastructure.persistence.rag_ingestion import PipelineIngestaRAG

    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    mock_qdrant = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.generar_embeddings_batch.return_value = [[0.05] * 2048, [0.05] * 2048]

    pipeline = PipelineIngestaRAG(
        db_connection=conn,
        embedding_service=mock_embedding,
        qdrant_adapter=mock_qdrant,
    )

    ids = pipeline.indexar_manual(
        id_tecnica="triangulo",
        titulo="Manual de Triángulo",
        texto_completo="A" * 1500,  # Generará 2 chunks
        id_instructor="inst_santiago",
    )

    assert len(ids) == 2
    # Verificar que Qdrant recibió id_documento en el payload
    assert mock_qdrant.upsert.call_count == 2
    primera_llamada_payload = mock_qdrant.upsert.call_args_list[0][1]["payload"]
    assert "id_documento" in primera_llamada_payload
    assert primera_llamada_payload["id_documento"].startswith("doc_")
    assert primera_llamada_payload["documento_titulo"] == "Manual de Triángulo"

    # Verificar que PostgreSQL recibió id_documento en la consulta INSERT
    assert "id_documento" in cursor.last_query

