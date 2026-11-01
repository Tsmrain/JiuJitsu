import pytest
from unittest.mock import Mock
from corpocmente.domain.services.rag_reranker import rerank_evidencias_multilingue, _cos_sim


def test_cos_sim_vectores_identicos_da_uno():
    v = [1.0, 2.0, 3.0]
    sim = _cos_sim(v, v)
    assert pytest.approx(sim, 0.001) == 1.0


def test_cos_sim_vectores_ortogonales_da_cero():
    v1 = [1.0, 0.0]
    v2 = [0.0, 1.0]
    assert pytest.approx(_cos_sim(v1, v2), 0.001) == 0.0


def test_rerank_lista_vacia_retorna_vacia():
    assert rerank_evidencias_multilingue("query", [], None) == []


def test_rerank_un_solo_elemento_retorna_sin_modificar():
    ev = [{"id": "1", "score": 0.8}]
    res = rerank_evidencias_multilingue("query", ev, None)
    assert res == ev


def test_rerank_ordena_por_afinidad_semantica_multilingue():
    mock_qwen = Mock()
    def fake_emb(text):
        if "Armbar" in text or "S-Mount" in text:
            return [0.95, 0.05, 0.0]
        elif "guard" in text.lower():
            return [0.1, 0.9, 0.0]
        return [1.0, 0.0, 0.0]

    mock_qwen.generar_embedding_texto.side_effect = fake_emb

    evidencias = [
        {"id": "2", "score": 0.5, "contenido_texto": "Pass the closed guard by standing up."},
        {"id": "1", "score": 0.5, "contenido_texto": "Secure the arm and slide to S-Mount for armbar."},
    ]

    res = rerank_evidencias_multilingue(
        query_texto="Armbar mount execution",
        evidencias=evidencias,
        qwen_adapter=mock_qwen,
        top_k=2,
    )

    assert len(res) == 2
    assert res[0]["id"] == "1"
    assert res[1]["id"] == "2"
    assert res[0]["rerank_score"] > res[1]["rerank_score"]
