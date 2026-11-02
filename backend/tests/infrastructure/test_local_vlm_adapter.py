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


def test_parsear_json_valida_idioma_portugues_exitoso():
    raw = '{"summary": "Cotovelo aberto", "correction": "Mantenha o cotovelo colado ao corpo e abaixe o quadril (p. 555)."}'
    res = LocalVLMAdapter._parsear_json(raw, idioma="pt")
    assert res["summary"] == "Cotovelo aberto"
    assert "quadril" in res["correction"]


def test_parsear_json_rechaza_ingles_cuando_pide_portugues():
    raw = '{"summary": "Elbow flaring", "correction": "Keep your elbow tight against the ribs and lower hips."}'
    with pytest.raises(ValueError, match="Respuesta del VLM rechazada.*se esperaba idioma 'pt'"):
        LocalVLMAdapter._parsear_json(raw, idioma="pt")


def test_parsear_json_rechaza_espanol_cuando_pide_portugues():
    raw = '{"summary": "Codo abierto", "correction": "Mantén el codo pegado a las costillas del alumno y baja la cadera (p. 555)."}'
    with pytest.raises(ValueError, match="Respuesta del VLM rechazada.*se esperaba idioma 'pt'"):
        LocalVLMAdapter._parsear_json(raw, idioma="pt")


def test_parsear_json_valida_idioma_espanol_exitoso():
    raw = '{"summary": "Codo abierto", "correction": "Mantén el codo pegado a las costillas y baja la cadera (p. 555)."}'
    res = LocalVLMAdapter._parsear_json(raw, idioma="es")
    assert res["summary"] == "Codo abierto"
    assert "cadera" in res["correction"]


def test_parsear_json_rechaza_ingles_cuando_pide_espanol():
    raw = '{"summary": "Elbow flaring", "correction": "Keep your elbow tight against the ribs and lower hips."}'
    with pytest.raises(ValueError, match="Respuesta del VLM rechazada.*se esperaba idioma 'es'"):
        LocalVLMAdapter._parsear_json(raw, idioma="es")



