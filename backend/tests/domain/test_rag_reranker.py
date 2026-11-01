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


def test_rerank_con_cross_encoder_real_o_mockeado():
    from unittest.mock import patch
    from corpocmente.domain.services.rag_reranker import Qwen3VLRerankerCrossEncoder

    evidencias = [
        {"id": "c1", "score": 0.3, "contenido_texto": "Receta de cocina"},
        {"id": "c2", "score": 0.4, "contenido_texto": "Técnica de armbar desde la montada"},
    ]

    with patch.object(Qwen3VLRerankerCrossEncoder, "rerank_pairs", return_value=[0.05, 0.95]):
        res = rerank_evidencias_multilingue("armbar mount", evidencias, None, top_k=2)
        assert len(res) == 2
        assert res[0]["id"] == "c2"
        assert res[0]["cross_encoder_score"] == 0.95
        assert res[1]["id"] == "c1"
        assert res[1]["cross_encoder_score"] == 0.05


def test_cross_encoder_desactiva_think_mode():
    from unittest.mock import patch, MagicMock
    from corpocmente.domain.services.rag_reranker import Qwen3VLRerankerCrossEncoder

    mock_model = MagicMock()
    mock_proc = MagicMock()
    mock_model.rerank.return_value = MagicMock(tolist=lambda: [0.85])

    with patch.object(Qwen3VLRerankerCrossEncoder, "get_instance", return_value=(mock_model, mock_proc)):
        scores = Qwen3VLRerankerCrossEncoder.rerank_pairs("query", ["doc 1"])
        assert scores == [0.85]
        # Verificar que el payload contiene enable_thinking: False
        call_args = mock_model.rerank.call_args[0]
        payload = call_args[0]
        assert payload.get("enable_thinking") is False
        assert "Given a jiu-jitsu technique question" in payload.get("instruction")

