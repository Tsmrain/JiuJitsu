"""
Tests de regresión para buscar_maxima_diferencia (C12.5 Fix 2.1).

Verifica que el método reescrito:
  - Usa client.scroll() en vez de N queries individuales
  - Compara localmente con numpy (coseno)
  - Retorna el par alumno↔referencia con MENOR similitud
  - Score está en escala 0–100
"""
import pytest
import math
from unittest.mock import MagicMock, patch
from uuid import uuid4

from corpocmente.infrastructure.persistence.qdrant_adapter import (
    QdrantVectorAdapter,
    VectorSearchResultDTO,
)
from corpocmente.domain.entities.models import EsqueletoBiomecanico


# Vectores realistas (17 kp × 3 = 51 dims + 82 padding)
def _make_kp(seed: float) -> list[float]:
    """Genera un vector de 133 dims variando un seed."""
    import random
    rng = random.Random(int(seed * 1000))
    base = [rng.uniform(0.1, 0.9) for _ in range(51)]
    return base + [0.0] * 82


def _make_mock_point(vector: list[float], payload: dict):
    """Crea un mock de qdrant Record para scroll results."""
    p = MagicMock()
    p.vector = vector
    p.payload = payload
    return p


class TestBuscarMaximaDiferenciaScrollNumpy:

    def test_uses_scroll_not_search(self):
        """Debe usar client.scroll() una sola vez, no client.search() N veces."""
        mock_client = MagicMock()
        ref_vec = _make_kp(1.0)
        mock_client.scroll.return_value = (
            [_make_mock_point(ref_vec, {"frame_path": "/tmp/ref.jpg", "discrepancias": []})],
            None,
        )

        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")
        alumno = EsqueletoBiomecanico(keypoints133=_make_kp(2.0))

        adapter.buscar_maxima_diferencia([alumno], uuid4())

        mock_client.scroll.assert_called_once()
        mock_client.search.assert_not_called()

    def test_returns_worst_frame(self):
        """Debe retornar el par con MENOR similitud coseno."""
        mock_client = MagicMock()

        # Referencia: un solo vector
        ref_vec = _make_kp(1.0)
        mock_client.scroll.return_value = (
            [_make_mock_point(ref_vec, {
                "frame_path": "/tmp/ref_00010.jpg",
                "discrepancias": ["Cadera baja"],
            })],
            None,
        )

        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")

        # Alumno: dos frames, uno similar y otro muy diferente
        alumno_similar = EsqueletoBiomecanico(keypoints133=ref_vec[:])  # copia idéntica
        alumno_distinto = EsqueletoBiomecanico(keypoints133=_make_kp(99.0))

        result = adapter.buscar_maxima_diferencia(
            [alumno_similar, alumno_distinto], uuid4()
        )

        assert isinstance(result, VectorSearchResultDTO)
        # El score del frame idéntico sería ~100, el distinto será menor
        # Debe elegir el peor (menor score)
        assert result.score < 100.0

    def test_score_is_0_to_100_scale(self):
        """Score debe estar en escala 0–100 (no 0–1)."""
        mock_client = MagicMock()
        ref_vec = _make_kp(1.0)
        mock_client.scroll.return_value = (
            [_make_mock_point(ref_vec, {"frame_path": "", "discrepancias": []})],
            None,
        )

        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")
        alumno = EsqueletoBiomecanico(keypoints133=_make_kp(5.0))

        result = adapter.buscar_maxima_diferencia([alumno], uuid4())

        # Coseno similarity × 100 → debería estar entre 0 y 100
        assert 0.0 <= result.score <= 100.0, f"Score {result.score} fuera de rango 0–100"

    def test_raises_on_empty_references(self):
        """Debe lanzar ValueError si no hay referencias en Qdrant."""
        mock_client = MagicMock()
        mock_client.scroll.return_value = ([], None)

        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")
        alumno = EsqueletoBiomecanico(keypoints133=_make_kp(1.0))

        with pytest.raises(ValueError, match="No hay vectores de referencia"):
            adapter.buscar_maxima_diferencia([alumno], uuid4())

    def test_raises_on_empty_alumno_list(self):
        """Debe lanzar ValueError si la lista de esqueletos está vacía."""
        mock_client = MagicMock()
        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")

        with pytest.raises(ValueError, match="lista de esqueletos del alumno está vacía"):
            adapter.buscar_maxima_diferencia([], uuid4())

    def test_payload_propagated_to_result(self):
        """El frame_path y discrepancias del payload deben llegar al DTO."""
        mock_client = MagicMock()
        payload = {
            "frame_path": "/tmp/corpocmente_reference_frames/abc/ref_00025.jpg",
            "discrepancias": ["Rodilla en ángulo incorrecto", "Guardia abierta"],
        }
        mock_client.scroll.return_value = (
            [_make_mock_point(_make_kp(1.0), payload)],
            None,
        )

        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")
        alumno = EsqueletoBiomecanico(keypoints133=_make_kp(2.0))

        result = adapter.buscar_maxima_diferencia([alumno], uuid4())

        assert result.frame_path == payload["frame_path"]
        assert result.discrepancias == payload["discrepancias"]
