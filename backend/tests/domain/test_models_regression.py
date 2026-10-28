"""
Tests de regresión para los fixes del pipeline biomecánico (C12.5).

Cubre:
  - EsqueletoBiomecanico.to_vector_array() retorna keypoints133 reales
  - EsqueletoBiomecanico acepta frame_idx del worker
  - to_vector_array() siempre retorna exactamente 133 dims
"""
import pytest
import math
from corpocmente.domain.entities.models import EsqueletoBiomecanico


# --- Vectores realistas (no [0.5]*133) para los tests ---
# Simula 17 keypoints COCO × 3 (x, y, conf) = 51 dims + 82 padding = 133
REALISTIC_KP = [
    # Nose
    0.523, 0.312, 0.95,
    # Left Eye
    0.545, 0.289, 0.93,
    # Right Eye
    0.501, 0.291, 0.92,
    # Left Ear
    0.578, 0.301, 0.88,
    # Right Ear
    0.468, 0.303, 0.87,
    # Left Shoulder
    0.612, 0.445, 0.96,
    # Right Shoulder
    0.434, 0.448, 0.95,
    # Left Elbow
    0.678, 0.578, 0.91,
    # Right Elbow
    0.367, 0.581, 0.90,
    # Left Wrist
    0.712, 0.689, 0.85,
    # Right Wrist
    0.334, 0.692, 0.84,
    # Left Hip
    0.589, 0.667, 0.97,
    # Right Hip
    0.456, 0.669, 0.96,
    # Left Knee
    0.601, 0.812, 0.93,
    # Right Knee
    0.445, 0.815, 0.92,
    # Left Ankle
    0.598, 0.945, 0.89,
    # Right Ankle
    0.448, 0.948, 0.88,
] + [0.0] * 82  # padding to 133


class TestEsqueletoBiomecanicoToVectorArray:
    """Regression tests for Fix 1.1: to_vector_array()."""

    def test_to_vector_array_returns_list_not_none(self):
        """to_vector_array() was returning None (pass). Must return a list."""
        esq = EsqueletoBiomecanico(keypoints133=REALISTIC_KP)
        result = esq.to_vector_array()
        assert result is not None, "to_vector_array() must not return None"
        assert isinstance(result, list), "Must return a list"

    def test_to_vector_array_returns_exact_133_dims(self):
        """Vector size must match Qdrant VectorParams(size=133)."""
        esq = EsqueletoBiomecanico(keypoints133=REALISTIC_KP)
        vec = esq.to_vector_array()
        assert len(vec) == 133, f"Expected 133 dims, got {len(vec)}"

    def test_to_vector_array_values_match_keypoints(self):
        """The returned vector must be a faithful copy of keypoints133."""
        esq = EsqueletoBiomecanico(keypoints133=REALISTIC_KP)
        vec = esq.to_vector_array()
        for i, (a, b) in enumerate(zip(vec, REALISTIC_KP)):
            assert math.isclose(a, b, rel_tol=1e-9), (
                f"Mismatch at index {i}: {a} != {b}"
            )

    def test_to_vector_array_returns_copy(self):
        """Returned list should be a copy (not a reference to the internal list)."""
        esq = EsqueletoBiomecanico(keypoints133=REALISTIC_KP)
        vec = esq.to_vector_array()
        vec[0] = 999.0
        assert esq.keypoints133[0] != 999.0, "Must return a copy, not a reference"


class TestEsqueletoBiomecanicoFrameIdx:
    """Regression tests for Fix 1.2: frame_idx field."""

    def test_frame_idx_default_zero(self):
        """frame_idx should default to 0 when not provided."""
        esq = EsqueletoBiomecanico(keypoints133=REALISTIC_KP)
        assert esq.frame_idx == 0

    def test_frame_idx_accepted_from_worker(self):
        """Pydantic must accept frame_idx from the Colab worker response dict."""
        worker_response = {
            "frame_idx": 42,
            "keypoints133": REALISTIC_KP,
            "angulos_articulares": {"codo_izq": 135.5},
        }
        esq = EsqueletoBiomecanico(**worker_response)
        assert esq.frame_idx == 42

    def test_frame_idx_preserved_in_dict(self):
        """frame_idx should be serialized back to dict."""
        esq = EsqueletoBiomecanico(frame_idx=17, keypoints133=REALISTIC_KP)
        d = esq.model_dump()
        assert "frame_idx" in d
        assert d["frame_idx"] == 17
