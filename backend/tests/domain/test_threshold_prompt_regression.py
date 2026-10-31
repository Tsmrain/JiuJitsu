"""
Tests de regresión para el fix del umbral y la estrategia de prompt (C12.5).

Cubre:
  - Fix 3.1: UMBRAL_ACEPTABLE = 85.0 (escala 0–100, no 0.85)
  - Fix 3.2: SpanishPromptStrategy incluye "FOTOGRAMA CRÍTICO" y pide articulaciones
"""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter, VectorSearchResultDTO
from corpocmente.domain.entities.models import EsqueletoBiomecanico
from corpocmente.domain.strategies.prompt_strategies import SpanishPromptStrategy, EnglishPromptStrategy


class TestUmbralAceptableEscala:
    """Regression tests para Fix 3.1: el umbral debe estar en escala 0–100."""

    def test_score_75_triggers_vlm(self):
        """
        Con score=75.0 (escala 0–100) la similitud está BAJO el umbral (85.0).
        El VLM DEBE ser invocado. Con el bug anterior (0.85), 75.0 >= 0.85
        era True → VLM nunca se llamaba.
        """
        mock_yolo = Mock(spec=YOLOPoseAdapter)
        mock_qdrant = Mock(spec=QdrantVectorAdapter)
        mock_gemini = Mock(spec=LocalVLMAdapter)

        mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
        mock_esqueleto.to_vector_array.return_value = [0.5] * 133
        mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

        # Score 75 → bajo el umbral → VLM debería invocarse
        mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
            score=75.0,
            frame_path="/tmp/frame.jpg",
            discrepancias=["Cadera alta"]
        )
        mock_yolo.dibujar_error_en_frame.return_value = "/tmp/resaltado.jpg"
        mock_gemini.generar_texto_feedback.return_value = "Feedback correctivo real."

        facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
        resultado = facade.ejecutar_analisis_completo("/tmp/video.mp4", uuid4(), "Armbar")

        # VLM DEBE haber sido llamado
        mock_gemini.generar_texto_feedback.assert_called_once()
        assert resultado.feedback == "Feedback correctivo real."
        assert resultado.feedback != "¡Técnica ejecutada correctamente. Excelente trabajo!"

    def test_score_90_skips_vlm(self):
        """
        Con score=90.0, la similitud está SOBRE el umbral (85.0).
        El VLM NO debe ser invocado → respuesta genérica positiva.
        """
        mock_yolo = Mock(spec=YOLOPoseAdapter)
        mock_qdrant = Mock(spec=QdrantVectorAdapter)
        mock_gemini = Mock(spec=LocalVLMAdapter)

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
        assert any(w in resultado.feedback.lower() for w in ["excelente", "correctamente", "excellent", "correctly"])


class TestSpanishPromptStrategyEnhanced:
    """Regression tests para Fix 3.2: prompt mejorado con contexto de frame."""

    def test_prompt_contains_fotograma_critico(self):
        """El prompt debe mencionar 'FOTOGRAMA CRÍTICO' para dar contexto al VLM."""
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
        """El prompt mejorado debe pedir al VLM que mencione articulaciones."""
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion("Kimura", ["Hombro rotado"])
        assert "articulación" in prompt.lower()


class TestEnglishPromptStrategyMensajeProfesor:
    """Tests para Iteración 3E: Inyección del mensaje del profesor en el prompt VLM."""

    def test_english_prompt_injects_mensaje_profesor(self):
        strategy = EnglishPromptStrategy()
        mensaje = "Keep your hips low and elbows tight against the ribcage."
        prompt = strategy.construir_prompt_evaluacion(
            "Mount Escape",
            ["Elbow flared out"],
            mensaje_profesor=mensaje
        )
        assert "The instructor has provided the following specific instructions for this technique:" in prompt
        assert mensaje in prompt
        assert "Ensure your correction aligns strictly with these instructions." in prompt

    def test_english_prompt_omits_instruction_when_empty(self):
        strategy = EnglishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            "Mount Escape",
            ["Elbow flared out"],
            mensaje_profesor=""
        )
        assert "The instructor has provided the following specific instructions" not in prompt


class TestNombresArticulacionesCriticas:
    """Tests para Iteración 3F: Mapeo legible de articulaciones críticas."""

    def test_nombres_articulaciones_dto_support(self):
        from corpocmente.domain.entities.models import AnalisisResultDTO
        dto = AnalisisResultDTO(
            similitud=75.0,
            feedback="Fix your posture.",
            articulaciones_criticas=[7, 13, 8],
            nombres_articulaciones_criticas=["Left Elbow", "Left Knee", "Right Elbow"]
        )
        assert dto.articulaciones_criticas == [7, 13, 8]
        assert dto.nombres_articulaciones_criticas == ["Left Elbow", "Left Knee", "Right Elbow"]

    def test_nombres_articulaciones_facade_mapping(self):
        from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
        from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
        from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
        from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter, VectorSearchResultDTO
        from corpocmente.domain.entities.models import EsqueletoBiomecanico

        mock_yolo = Mock(spec=YOLOPoseAdapter)
        mock_qdrant = Mock(spec=QdrantVectorAdapter)
        mock_gemini = Mock(spec=LocalVLMAdapter)

        mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
        mock_esqueleto.to_vector_array.return_value = [0.1] * 133
        mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

        vec_result = VectorSearchResultDTO(
            score=95.0,
            frame_path="/tmp/frame.jpg",
            discrepancias=[]
        )
        vec_result.articulaciones_criticas = [7, 13]
        mock_qdrant.buscar_maxima_diferencia.return_value = vec_result

        facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
        resultado = facade.ejecutar_analisis_completo("/tmp/nonexistent.mp4", uuid4(), "Mount Escape")
        assert resultado.articulaciones_criticas == [7, 13]
        assert resultado.nombres_articulaciones_criticas == ["Left Elbow", "Left Knee"]

