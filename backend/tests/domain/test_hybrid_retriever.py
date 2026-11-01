import pytest
from unittest.mock import Mock, patch
from corpocmente.domain.glossary.glossary_service import (
    cargar_glosario,
    obtener_sinonimos_multilingues,
    expandir_query_con_glosario,
)
from corpocmente.domain.services.hybrid_retriever import HybridRetriever, QdrantBM25Corpus


def test_cargar_glosario_contiene_sinonimos_principales():
    glosario = cargar_glosario()
    assert "sinonimos" in glosario
    assert len(glosario["sinonimos"]) >= 10
    
    canonicals = [item.get("canonical") for item in glosario["sinonimos"]]
    assert "closed guard" in canonicals
    assert "side control" in canonicals
    assert "armbar" in canonicals
    assert "underhook" in canonicals


def test_obtener_sinonimos_multilingues_detecta_terminos():
    texto = "Quiero escapar de 100 kilos usando el underhook y puente"
    sinonimos = obtener_sinonimos_multilingues(texto)
    assert len(sinonimos) > 0
    # Debe detectar variantes de side control / 100 kilos
    assert any("side control" in s or "cem quilos" in s for s in sinonimos)
    # Debe detectar variantes de underhook / esgrima
    assert any("esgrima" in s or "underhook" in s for s in sinonimos)


def test_expandir_query_con_glosario_agrega_variantes():
    query = "escape de 100 kilos"
    expandida = expandir_query_con_glosario(query)
    assert "100 kilos" in expandida
    assert "side control" in expandida or "cem quilos" in expandida


def test_rrf_fusion_combina_ranks_correctamente():
    densos = [
        {"id": "doc_a", "score": 0.9, "contenido_texto": "Texto A"},
        {"id": "doc_b", "score": 0.8, "contenido_texto": "Texto B"},
        {"id": "doc_c", "score": 0.7, "contenido_texto": "Texto C"},
    ]
    bm25 = [
        {"id": "doc_b", "score": 10.0, "contenido_texto": "Texto B"},
        {"id": "doc_d", "score": 8.0, "contenido_texto": "Texto D"},
        {"id": "doc_a", "score": 5.0, "contenido_texto": "Texto A"},
    ]

    # RRF para doc_b: rank_dense=2 (1/62), rank_bm25=1 (1/61) -> ~0.01613 + ~0.01639 = ~0.0325
    # RRF para doc_a: rank_dense=1 (1/61), rank_bm25=3 (1/63) -> ~0.01639 + ~0.01587 = ~0.0322
    # doc_b debe ser rank 1 en la fusión
    fusionados = HybridRetriever.fusionar_rrf(densos, bm25, top_k=4, k_rrf=60)
    
    assert len(fusionados) == 4
    assert fusionados[0]["id"] == "doc_b"
    assert fusionados[1]["id"] == "doc_a"
    assert fusionados[0]["rrf_score"] > fusionados[1]["rrf_score"]


def test_rrf_fusion_aplica_bonus_visual():
    densos = [
        {"id": "doc_1", "score": 0.9, "contenido_texto": "Texto 1"},
    ]
    bm25 = [
        {"id": "doc_2", "score": 0.9, "contenido_texto": "Texto 2", "media_path": "/path/frame.jpg"},
    ]

    # Ambos tienen 1/61 (~0.01639), pero doc_2 tiene bonus visual (+0.005)
    fusionados = HybridRetriever.fusionar_rrf(densos, bm25, top_k=2, k_rrf=60)
    assert len(fusionados) == 2
    assert fusionados[0]["id"] == "doc_2"
    assert fusionados[0]["rrf_score"] > fusionados[1]["rrf_score"]


def test_hybrid_retriever_recuperar_en_modo_dense():
    mock_qdrant = Mock()
    mock_qwen = Mock()
    mock_qwen.generar_embedding_texto.return_value = [0.1] * 2048
    mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = [
        {"id": "d1", "score": 0.95, "contenido_texto": "Armbar"}
    ]

    res = HybridRetriever.recuperar(
        query_texto="armbar mount",
        qdrant_adapter=mock_qdrant,
        qwen_adapter=mock_qwen,
        limit=5,
        modo="dense",
    )

    assert len(res) == 1
    assert res[0]["id"] == "d1"
    mock_qdrant.recuperar_evidencias_rag_multimodal.assert_called_once()

