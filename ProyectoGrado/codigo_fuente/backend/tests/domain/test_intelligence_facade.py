import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter, VectorSearchResultDTO
from corpocmente.domain.entities.models import EsqueletoBiomecanico

def test_ejecutar_analisis_completo_flujo_exitoso():
    # Arrange
    tecnica_id = uuid4()
    mock_yolo = Mock(spec=YOLOPoseAdapter)
    mock_qdrant = Mock(spec=QdrantVectorAdapter)
    mock_gemini = Mock(spec=GeminiApiAdapter)
    
    # Simular extraccion YOLO
    mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
    mock_esqueleto.to_vector_array.return_value = [0.1, 0.2, 0.3]
    mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]
    
    # Simular busqueda en Qdrant
    mock_qdrant.buscar_similitud_pose.return_value = VectorSearchResultDTO(
        score=92.5,
        frame_path="/tmp/frame.jpg",
        discrepancias=["Cadera muy baja", "Agarre suelto"]
    )
    
    # Simular respuesta Gemini
    mock_gemini.generar_texto_feedback.return_value = "Feedback generado por IA."
    
    facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
    
    # Act
    resultado = facade.ejecutar_analisis_completo("/tmp/video.mp4", tecnica_id, "es")
    
    # Assert
    assert resultado.similitud == 92.5
    assert resultado.feedback == "Feedback generado por IA."
    mock_yolo.extraer_keypoints.assert_called_once_with("/tmp/video.mp4")
    mock_qdrant.buscar_similitud_pose.assert_called_once_with([0.1, 0.2, 0.3], tecnica_id)
    # Validar que Gemini fue llamado
    mock_gemini.generar_texto_feedback.assert_called_once()
