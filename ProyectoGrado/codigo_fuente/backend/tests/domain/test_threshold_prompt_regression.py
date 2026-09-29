"""
Tests de regresión para el fix del umbral y la estrategia de prompt (C12.5).

Cubre:
  - Fix 3.1: UMBRAL_ACEPTABLE = 85.0 (escala 0–100, no 0.85)
  - Fix 3.2: SpanishPromptStrategy incluye "FOTOGRAMA CRÍTICO" y pide articulaciones
"""
import pytest
from unittest.mock import Mock
from uuid import uuid4

from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter, VectorSearchResultDTO
from corpocmente.domain.entities.models import EsqueletoBiomecanico
from corpocmente.domain.strategies.prompt_strategies import SpanishPromptStrategy


class TestUmbralAceptableEscala:
    """Regression tests para Fix 3.1: el umbral debe estar en escala 0–100."""

    def test_score_75_triggers_gemini(self):
        """
        Con score=75.0 (escala 0–100) la similitud está BAJO el umbral (85.0).
        Gemini DEBE ser invocado. Con el bug anterior (0.85), 75.0 >= 0.85
        era True → Gemini nunca se llamaba.
        """
        mock_yolo = Mock(spec=YOLOPoseAdapter)
        mock_qdrant = Mock(spec=QdrantVectorAdapter)
        mock_gemini = Mock(spec=GeminiApiAdapter)

        mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
        mock_esqueleto.to_vector_array.return_value = [0.5] * 133
        mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

        # Score 75 → bajo el umbral → Gemini debería invocarse
        mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
            score=75.0,
            frame_path="/tmp/frame.jpg",
            discrepancias=["Cadera alta"]
        )
        mock_yolo.dibujar_error_en_frame.return_value = "/tmp/resaltado.jpg"
        mock_gemini.generar_texto_feedback.return_value = "Feedback correctivo real."

        facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
        resultado = facade.ejecutar_analisis_completo("/tmp/video.mp4", uuid4(), "Armbar")

        # Gemini DEBE haber sido llamado
        mock_gemini.generar_texto_feedback.assert_called_once()
        assert resultado.feedback == "Feedback correctivo real."
        assert resultado.feedback != "¡Técnica ejecutada correctamente. Excelente trabajo!"

    def test_score_90_skips_gemini(self):
        """
        Con score=90.0, la similitud está SOBRE el umbral (85.0).
        Gemini NO debe ser invocado → respuesta genérica positiva.
        """
        mock_yolo = Mock(spec=YOLOPoseAdapter)
        mock_qdrant = Mock(spec=QdrantVectorAdapter)
        mock_gemini = Mock(spec=GeminiApiAdapter)

        mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
        mock_esqueleto.to_vector_array.return_value = [0.5] * 133
        mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

        mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
            score=90.0,
            frame_path="/tmp/frame.jpg",
            discrepancias=[]
        )

        facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
        resultado = facade.ejecutar_analisis_completo("/tmp/video.mp4", uuid4(), "Armbar")

        mock_gemini.generar_texto_feedback.assert_not_called()
        assert "Excelente" in resultado.feedback or "correctamente" in resultado.feedback


class TestSpanishPromptStrategyEnhanced:
    """Regression tests para Fix 3.2: prompt mejorado con contexto de frame."""

    def test_prompt_contains_fotograma_critico(self):
        """El prompt debe mencionar 'FOTOGRAMA CRÍTICO' para dar contexto a Gemini."""
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            "Armbar desde guardia",
            ["Cadera alta", "Agarre suelto"]
        )
        assert "FOTOGRAMA CRÍTICO" in prompt

    def test_prompt_contains_tecnica_nombre(self):
        """El prompt debe incluir el nombre de la técnica."""
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            "Triangle choke",
            ["Ángulo de pierna incorrecto"]
        )
        assert "Triangle choke" in prompt

    def test_prompt_lists_all_discrepancias(self):
        """Todas las discrepancias deben aparecer en el prompt."""
        strategy = SpanishPromptStrategy()
        discrepancias = ["Rodilla en 45°", "Cadera elevada", "Agarre débil"]
        prompt = strategy.construir_prompt_evaluacion("Omoplata", discrepancias)
        for d in discrepancias:
            assert d in prompt, f"Discrepancia '{d}' no encontrada en el prompt"

    def test_prompt_asks_for_articulacion(self):
        """El prompt mejorado debe pedir a Gemini que mencione articulaciones."""
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion("Kimura", ["Hombro rotado"])
        assert "articulación" in prompt.lower()
