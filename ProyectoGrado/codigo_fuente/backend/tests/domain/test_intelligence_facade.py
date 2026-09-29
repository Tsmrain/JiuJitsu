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
    mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
        score=0.80,
        frame_path="/tmp/frame.jpg",
        discrepancias=["Cadera muy baja", "Agarre suelto"]
    )
    
    # Simular respuesta Gemini
    mock_gemini.generar_texto_feedback.return_value = "Feedback generado por IA."
    
    facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
    
    # Act
    resultado = facade.ejecutar_analisis_completo("/tmp/video.mp4", tecnica_id, "Armbar")
    
    # Assert
    assert resultado.similitud == 0.80
    assert resultado.feedback == "Feedback generado por IA."
    mock_yolo.extraer_keypoints.assert_called_once_with("/tmp/video.mp4")
    mock_qdrant.buscar_maxima_diferencia.assert_called_once_with([mock_esqueleto], tecnica_id)
    # Validar que Gemini fue llamado
    mock_gemini.generar_texto_feedback.assert_called_once()

def test_ejecutar_analisis_construye_query_textual_para_rag():
    """
    Regression test C11.4: cuando se inyecta un qwen_adapter, la fachada debe:
    1. Construir una query textual con tecnica_nombre + discrepancias.
    2. Llamar a `generar_embedding_texto` (NO al método deprecado de imagen).
    3. Pasar esa query textual a `recuperar_contexto_rag`.
    """
    from unittest.mock import Mock
    from uuid import uuid4
    from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
    from corpocmente.infrastructure.persistence.qdrant_adapter import VectorSearchResultDTO

    # Arrange
    tecnica_id = uuid4()
    mock_yolo = Mock(spec=YOLOPoseAdapter)
    mock_qdrant = Mock(spec=QdrantVectorAdapter)
    mock_gemini = Mock(spec=GeminiApiAdapter)
    mock_qwen = Mock(spec=QwenEmbeddingAdapter)

    mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
    mock_esqueleto.to_vector_array.return_value = [0.1, 0.2, 0.3]
    mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

    # Simular baja similitud para forzar el camino RAG
    mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
        score=0.60,
        frame_path="/tmp/frame.jpg",
        discrepancias=["Cadera alta", "Agarre flojo"]
    )
    mock_yolo.dibujar_error_en_frame.return_value = "/tmp/frame_resaltado.jpg"

    # Simular el embedding textual (2048 dims) y la teoría recuperada
    mock_qwen.generar_embedding_texto.return_value = [0.05] * 2048
    mock_qdrant.recuperar_contexto_rag.return_value = "Teoría recuperada sobre control de cadera."

    mock_gemini.generar_texto_feedback.return_value = "Feedback enriquecido con teoría."

    facade = IntelligenceAnalysisFacade(
        yolo_adapter=mock_yolo,
        qdrant_adapter=mock_qdrant,
        gemini_adapter=mock_gemini,
        qwen_adapter=mock_qwen
    )

    # Act
    resultado = facade.ejecutar_analisis_completo(
        video_path="/tmp/video.mp4",
        tecnica_id=tecnica_id,
        tecnica_nombre="Armbar"
    )

    # Assert
    # 1. Debe llamar a generar_embedding_texto (no a generar_embedding de imagen)
    mock_qwen.generar_embedding_texto.assert_called_once()
    mock_qwen.generar_embedding.assert_not_called()

    # 2. La query debe contener el nombre de la técnica y las discrepancias
    query_usada = mock_qwen.generar_embedding_texto.call_args.args[0]
    assert "Armbar" in query_usada, "La query textual debe incluir el nombre de la técnica"
    assert "Cadera alta" in query_usada or "Agarre flojo" in query_usada, \
        "La query textual debe incluir las discrepancias"

    # 3. Debe recuperar contexto RAG con el embedding textual
    mock_qdrant.recuperar_contexto_rag.assert_called_once()

    # 4. El feedback debe seguir generándose
    assert resultado.feedback == "Feedback enriquecido con teoría."

