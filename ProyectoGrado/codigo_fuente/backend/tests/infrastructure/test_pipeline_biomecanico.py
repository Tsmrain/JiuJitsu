import os
import cv2
import numpy as np
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, COCO_JOINT_NAMES
from corpocmente.infrastructure.persistence.qdrant_adapter import (
    QdrantVectorAdapter,
    VectorSearchResultDTO,
)
from corpocmente.domain.entities.models import EsqueletoBiomecanico
from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade


def _crear_video_prueba(path: str, num_frames: int = 5, width: int = 320, height: int = 240):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, 10.0, (width, height))
    for i in range(num_frames):
        # Crear frame con gradiente de color
        frame = np.full((height, width, 3), i * 40, dtype=np.uint8)
        out.write(frame)
    out.release()


def test_extraer_frame_y_dibujar_error_genera_imagen_valida(tmp_path):
    video_path = str(tmp_path / "test_video.mp4")
    output_path = str(tmp_path / "critico.jpg")
    _crear_video_prueba(video_path, num_frames=3)

    # 17 keypoints normalizados centrados en la imagen
    kpts = []
    for _ in range(17):
        kpts.extend([0.5, 0.5, 0.9])
    kpts.extend([0.0] * (133 - len(kpts)))

    adapter = YOLOPoseAdapter(colab_url="https://placeholder")
    result_path = adapter.extraer_frame_y_dibujar_error(
        video_path=video_path,
        frame_idx=1,
        keypoints133=kpts,
        articulaciones_criticas=[13, 14],  # Rodillas
        output_path=output_path,
        tecnica_nombre="Armbar"
    )

    assert os.path.exists(result_path)
    img = cv2.imread(result_path)
    assert img is not None
    assert img.shape[0] == 240
    assert img.shape[1] == 320


def test_buscar_maxima_diferencia_detecta_peor_frame_y_articulaciones():
    mock_client = MagicMock()

    # Referencia del profesor (17 kp en 0.5 normalizado)
    ref_vec = [0.5] * 51 + [0.0] * 82
    ref_point = MagicMock()
    ref_point.vector = ref_vec
    ref_point.payload = {"frame_path": "/tmp/ref_001.jpg", "discrepancias": []}
    mock_client.scroll.return_value = ([ref_point], None)

    adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")

    # Alumno Frame 0: muy similar a referencia (0.5)
    f0 = EsqueletoBiomecanico(frame_idx=0, keypoints133=ref_vec[:])

    # Alumno Frame 1: rodillas muy desviadas (índices 13 y 14 en 0.9)
    f1_kpts = ref_vec[:]
    f1_kpts[13 * 3] = 0.95
    f1_kpts[13 * 3 + 1] = 0.95
    f1_kpts[14 * 3] = 0.95
    f1_kpts[14 * 3 + 1] = 0.95
    f1 = EsqueletoBiomecanico(frame_idx=1, keypoints133=f1_kpts)

    resultado = adapter.buscar_maxima_diferencia([f0, f1], uuid4())

    assert isinstance(resultado, VectorSearchResultDTO)
    # El frame con mayor error biomecánico debe ser el Frame 1
    assert resultado.frame_alumno_idx == 1
    # Debe haber identificado las rodillas o articulaciones críticas
    assert len(resultado.articulaciones_criticas) > 0
    assert 13 in resultado.articulaciones_criticas or 14 in resultado.articulaciones_criticas
    # Las discrepancias deben describir la articulación
    assert any("Rodilla" in d for d in resultado.discrepancias)


def test_asegurar_poses_referencia_autoingesta(tmp_path):
    mock_client = MagicMock()
    # Primera llamada a scroll: devuelve vacío (no hay puntos)
    mock_client.scroll.return_value = ([], None)
    mock_client.get_collections.return_value.collections = []

    video_ref = str(tmp_path / "ref.mp4")
    _crear_video_prueba(video_ref, num_frames=6)

    mock_yolo = MagicMock()
    mock_yolo.extraer_keypoints.return_value = [
        EsqueletoBiomecanico(frame_idx=0, keypoints133=[0.5] * 133),
        EsqueletoBiomecanico(frame_idx=5, keypoints133=[0.6] * 133)
    ]

    adapter = QdrantVectorAdapter(client=mock_client, collection_name="vectores_poses_jiujitsu")
    puntos_insertados = adapter.asegurar_poses_referencia(
        tecnica_id=uuid4(),
        video_referencia_path=video_ref,
        yolo_adapter=mock_yolo,
        tecnica_nombre="Triángulo",
        every_n=3
    )

    assert puntos_insertados == 2
    mock_client.upsert.assert_called_once()


def test_facade_orquestacion_completa_con_dibujo_y_gemini(tmp_path):
    video_alumno = str(tmp_path / "alumno.mp4")
    _crear_video_prueba(video_alumno, num_frames=4)

    mock_yolo = MagicMock()
    kpts = [0.5] * 133
    mock_yolo.extraer_keypoints.return_value = [
        EsqueletoBiomecanico(frame_idx=0, keypoints133=kpts),
        EsqueletoBiomecanico(frame_idx=1, keypoints133=kpts),
    ]

    mock_qdrant = MagicMock()
    mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
        score=72.5,
        frame_path="/tmp/ref.jpg",
        discrepancias=["Desviación en Rodilla derecha"],
        frame_alumno_idx=1,
        articulaciones_criticas=[14],
        keypoints_alumno=kpts,
        keypoints_referencia=kpts
    )
    mock_qdrant.recuperar_contexto_rag.return_value = "Presión de cadera y alineación de rodillas."

    mock_gemini = MagicMock()
    mock_gemini.generar_texto_feedback.return_value = "Feedback detallado del Maestro: Ajusta la rodilla derecha."

    facade = IntelligenceAnalysisFacade(
        yolo_adapter=mock_yolo,
        qdrant_adapter=mock_qdrant,
        gemini_adapter=mock_gemini
    )

    resultado = facade.ejecutar_analisis_completo(
        video_path=video_alumno,
        tecnica_id=uuid4(),
        tecnica_nombre="Armbar",
        evaluacion_id="test-eval-123"
    )

    assert resultado.similitud == 72.5
    assert "Ajusta la rodilla derecha" in resultado.feedback
    assert resultado.frame_alumno_idx == 1
    assert resultado.frame_critico_path is not None
    # Verificar que el fotograma crítico fue extraído y dibujado con OpenCV
    assert os.path.exists(resultado.frame_critico_path)

    # Validar que Gemini fue invocado con el prompt y la imagen del frame crítico
    mock_gemini.generar_texto_feedback.assert_called_once()
    args, _ = mock_gemini.generar_texto_feedback.call_args
    prompt_usado, imagen_usada = args
    assert "Armbar" in prompt_usado
    assert imagen_usada == resultado.frame_critico_path
