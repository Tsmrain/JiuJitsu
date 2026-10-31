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

