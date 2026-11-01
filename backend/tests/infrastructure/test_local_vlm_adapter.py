import pytest
from unittest.mock import MagicMock, patch
from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter


def test_parsear_json_directo():
    raw = '{"summary": "Elbow flaring", "correction": "Keep elbow tight."}'
    result = LocalVLMAdapter._parsear_json(raw)
    assert result["summary"] == "Elbow flaring"
    assert result["correction"] == "Keep elbow tight."


def test_parsear_json_en_bloque_markdown():
    raw = '```json\n{"summary": "Hip too high", "correction": "Lower hips."}\n```'
    result = LocalVLMAdapter._parsear_json(raw)
    assert result["summary"] == "Hip too high"
    assert result["correction"] == "Lower hips."


def test_parsear_fallback_texto_plano():
    raw = "The elbow is flaring. Keep it tight to your ribs."
    result = LocalVLMAdapter._parsear_json(raw)
    assert "elbow is flaring" in result["summary"].lower()
    assert "keep it tight" in result["correction"].lower()


def test_parsear_json_judge_fiel():
    raw = '{"faithfulness_score": 0.95, "unsupported_claims": [], "reasoning": "Respaldado por el manual."}'
    result = LocalVLMAdapter._parsear_json_judge(raw)
    assert result["faithfulness_score"] == 0.95
    assert result["unsupported_claims"] == []
    assert "Respaldado" in result["reasoning"]


def test_parsear_json_judge_con_alucinaciones_castiga_score():
    raw = '{"faithfulness_score": 0.90, "unsupported_claims": ["Patada voladora"], "reasoning": "Inventa patada."}'
    result = LocalVLMAdapter._parsear_json_judge(raw)
    assert result["faithfulness_score"] < 0.85
    assert "Patada voladora" in result["unsupported_claims"]


def test_evaluar_fidelidad_tecnica_correcta_retorna_1():
    adapter = object.__new__(LocalVLMAdapter)
    res = adapter.evaluar_fidelidad_grounding(
        respuesta={"summary": "Good technique", "correction": "Excellent form."},
        contexto="Cualquier contexto",
        mensaje_profesor="Cualquier mensaje",
    )
    assert res["faithfulness_score"] == 1.0
    assert res["unsupported_claims"] == []


