import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter, VectorSearchResultDTO
from corpocmente.domain.entities.models import EsqueletoBiomecanico
from corpocmente.application.services.multimodal_rag_service import (
    obtener_evidencias_rag_multimodal,
)


def test_ejecutar_analisis_completo_flujo_exitoso():
    # Arrange
    tecnica_id = uuid4()
    mock_yolo = Mock(spec=YOLOPoseAdapter)
    mock_qdrant = Mock(spec=QdrantVectorAdapter)
    mock_gemini = Mock(spec=LocalVLMAdapter)
    
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
    
    # Simular respuesta VLM
    mock_gemini.generar_texto_feedback.return_value = "Feedback generado por IA."
    
    facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
    
    # Act
    resultado = facade.ejecutar_analisis_completo("/tmp/video.mp4", tecnica_id, "Armbar")
    
    # Assert
    assert resultado.similitud == 0.80
    assert resultado.feedback == "Feedback generado por IA."
    mock_yolo.extraer_keypoints.assert_called_once_with("/tmp/video.mp4")
    mock_qdrant.buscar_maxima_diferencia.assert_called_once()
    mock_gemini.generar_texto_feedback.assert_called_once()


def test_ejecutar_analisis_construye_query_y_recupera_rag_multimodal():
    tecnica_id = uuid4()
    mock_yolo = Mock(spec=YOLOPoseAdapter)
    mock_qdrant = Mock(spec=QdrantVectorAdapter)
    mock_gemini = Mock(spec=LocalVLMAdapter)
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

    mock_qwen.generar_embedding_texto.return_value = [0.05] * 2048
    mock_qwen.generar_embedding.return_value = [0.05] * 2048
    mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = [
        {
            "id": "1",
            "score": 0.9,
            "contenido_texto": "Teoría recuperada sobre control de cadera.",
            "modalidad": "texto"
        }
    ]

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
    mock_qwen.generar_embedding_texto.assert_called_once()
    query_usada = mock_qwen.generar_embedding_texto.call_args.args[0]
    assert "Armbar" in query_usada
    assert "Cadera alta" in query_usada or "Agarre flojo" in query_usada
    mock_qdrant.recuperar_evidencias_rag_multimodal.assert_called_once()
    assert resultado.feedback == "Feedback enriquecido con teoría."


def test_facada_puede_usar_embedding_de_imagen_cuando_existe_frame_critico():
    """
    RAG multimodal: si hay frame crítico, la fachada puede vectorizar imagen.
    """
    tecnica_id = uuid4()

    mock_qwen = Mock()
    mock_qwen.generar_embedding_texto.return_value = [0.1] * 2048
    mock_qwen.generar_embedding.return_value = [0.2] * 2048

    mock_qdrant = Mock()
    mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = [
        {
            "id": "x",
            "score": 0.91,
            "contenido_texto": "Referencia visual del profesor.",
            "modalidad": "imagen",
            "media_path": "/tmp/ref_frame.jpg",
            "video_path": "/tmp/profe.mp4",
            "timestamp_seconds": 4.0,
            "frame_idx": 120,
        }
    ]

    with patch("os.path.isfile", return_value=True):
        evidencias = obtener_evidencias_rag_multimodal(
            qwen_adapter=mock_qwen,
            qdrant_adapter=mock_qdrant,
            tecnica_id=tecnica_id,
            tecnica_nombre="Armbar",
            discrepancias=["Cadera alta", "Agarre flojo"],
            frame_critico_path="/tmp/alumno_frame.jpg",
            video_referencia_path="/tmp/profe.mp4",
            limit=3,
        )

    mock_qwen.generar_embedding.assert_called_once()
    mock_qwen.generar_embedding_texto.assert_called_once()
    mock_qdrant.recuperar_evidencias_rag_multimodal.assert_called_once()

    assert evidencias
    assert evidencias[0]["media_path"] == "/tmp/ref_frame.jpg"


def test_facada_degrada_a_texto_si_embedding_de_imagen_falla():
    mock_qwen = Mock()
    mock_qwen.generar_embedding.side_effect = RuntimeError("worker sin /embed_images")
    mock_qwen.generar_embedding_texto.return_value = [0.1] * 2048

    mock_qdrant = Mock()
    mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = []

    with patch("os.path.isfile", return_value=True):
        evidencias = obtener_evidencias_rag_multimodal(
            qwen_adapter=mock_qwen,
            qdrant_adapter=mock_qdrant,
            tecnica_id=uuid4(),
            tecnica_nombre="Kimura",
            discrepancias=["Hombro abierto"],
            frame_critico_path="/tmp/no_importa.jpg",
            limit=3,
        )

    mock_qwen.generar_embedding.assert_called_once()
    mock_qwen.generar_embedding_texto.assert_called_once()
    assert evidencias == []


def test_facade_separa_frame_limpio_para_rag_y_frame_resaltado_para_gemini(tmp_path):
    tecnica_id = uuid4()
    mock_yolo = Mock(spec=YOLOPoseAdapter)
    mock_qdrant = Mock(spec=QdrantVectorAdapter)
    mock_gemini = Mock(spec=LocalVLMAdapter)
    mock_qwen = Mock(spec=QwenEmbeddingAdapter)

    mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
    mock_esqueleto.to_vector_array.return_value = [0.1, 0.2, 0.3]
    mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

    mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
        score=0.50,
        frame_path="/tmp/frame.jpg",
        discrepancias=["Error en codo"],
    )

    clean_file = tmp_path / "clean.jpg"
    clean_file.write_bytes(b"\xff\xd8\xff")
    annotated_file = tmp_path / "annotated.jpg"
    annotated_file.write_bytes(b"\xff\xd8\xff")

    def fake_extraer(video_path, frame_idx, keypoints133, articulaciones_criticas, output_path, clean_output_path=None, tecnica_nombre=""):
        if clean_output_path:
            with open(clean_output_path, "wb") as f:
                f.write(b"clean_data")
        with open(output_path, "wb") as f:
            f.write(b"annotated_data")
        return output_path

    mock_yolo.extraer_frame_y_dibujar_error.side_effect = fake_extraer

    mock_qwen.generar_embedding_texto.return_value = [0.01] * 2048
    mock_qwen.generar_embedding.return_value = [0.02] * 2048
    mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = []
    mock_gemini.generar_texto_feedback.return_value = "Feedback corregido."

    facade = IntelligenceAnalysisFacade(
        yolo_adapter=mock_yolo,
        qdrant_adapter=mock_qdrant,
        gemini_adapter=mock_gemini,
        qwen_adapter=mock_qwen,
    )

    with patch("os.path.exists", return_value=True):
        res = facade.ejecutar_analisis_completo(
            video_path=str(tmp_path / "video.mp4"),
            tecnica_id=tecnica_id,
            tecnica_nombre="Armbar",
        )

    # Qwen generar_embedding debe haber sido llamado con el frame limpio (clean_*.jpg), no con el anotado (critico_*.jpg)
    img_llamada = mock_qwen.generar_embedding.call_args.kwargs.get("image_path") or mock_qwen.generar_embedding.call_args.args[0]
    assert "clean_" in img_llamada

    # VLM debe recibir el frame crítico anotado para feedback visual pedagógico
    gemini_frame = mock_gemini.generar_texto_feedback.call_args.args[1]
    assert "critico_" in gemini_frame
    assert res.feedback == "Feedback corregido."


def test_facade_no_rompe_si_ambos_embeddings_fallan(tmp_path):
    tecnica_id = uuid4()
    mock_yolo = Mock(spec=YOLOPoseAdapter)
    mock_qdrant = Mock(spec=QdrantVectorAdapter)
    mock_gemini = Mock(spec=LocalVLMAdapter)
    mock_qwen = Mock(spec=QwenEmbeddingAdapter)

    mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
    mock_esqueleto.to_vector_array.return_value = [0.1, 0.2, 0.3]
    mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

    mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
        score=0.50,
        frame_path="/tmp/frame.jpg",
        discrepancias=["Error en cadera"],
    )

    mock_yolo.extraer_frame_y_dibujar_error.return_value = "/tmp/critico.jpg"

    # Ambos embeddings fallan (worker de Colab completamente caído)
    mock_qwen.generar_embedding_texto.side_effect = RuntimeError("Worker no disponible")
    mock_qwen.generar_embedding.side_effect = RuntimeError("Worker no disponible")

    mock_gemini.generar_texto_feedback.return_value = "Feedback sin RAG."

    facade = IntelligenceAnalysisFacade(
        yolo_adapter=mock_yolo,
        qdrant_adapter=mock_qdrant,
        gemini_adapter=mock_gemini,
        qwen_adapter=mock_qwen,
    )

    with patch("os.path.exists", return_value=True):
        res = facade.ejecutar_analisis_completo(
            video_path=str(tmp_path / "video.mp4"),
            tecnica_id=tecnica_id,
            tecnica_nombre="Triángulo",
        )

    # Qdrant RAG no debe llamarse porque no hay vectores válidos
    mock_qdrant.recuperar_evidencias_rag_multimodal.assert_not_called()
    assert res.feedback == "Feedback sin RAG."
