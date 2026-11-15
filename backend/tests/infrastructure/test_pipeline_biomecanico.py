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

    # Validar que el VLM fue invocado con el prompt y la imagen del frame crítico
    mock_gemini.generar_texto_feedback.assert_called_once()
    args, _ = mock_gemini.generar_texto_feedback.call_args
    prompt_usado, imagen_usada = args
    assert "Armbar" in prompt_usado
    assert imagen_usada == resultado.frame_critico_path


def test_top_down_crop_padding_y_mapeo_coordenadas():
    import torch

    adapter = YOLOPoseAdapter(colab_url="https://placeholder")
    frame = np.zeros((400, 600, 3), dtype=np.uint8)

    # Caja persona: [100, 50, 300, 250] -> bw=200, bh=200 -> 10% padding => crop [80, 30, 320, 270]
    pts_orig = {
        5: (150, 100, 0.9),
        6: (250, 100, 0.9),
        11: (160, 200, 0.9),
        12: (240, 200, 0.9),
    }

    full_res = MagicMock()
    full_res.boxes = MagicMock()
    full_res.boxes.xyxy = torch.tensor([[100.0, 50.0, 300.0, 250.0]])
    full_res.keypoints = None

    crop_kpts = np.zeros((1, 17, 3), dtype=np.float32)
    # 5 keypoints válidos dentro del recorte [80:320, 30:270]
    crop_kpts[0, 5] = [70.0, 70.0, 0.95]   # global: (70+80=150, 70+30=100)
    crop_kpts[0, 6] = [170.0, 70.0, 0.95]  # global: (170+80=250, 70+30=100)
    crop_kpts[0, 7] = [60.0, 120.0, 0.92]  # global: (140, 150)
    crop_kpts[0, 11] = [80.0, 170.0, 0.91] # global: (160, 200)
    crop_kpts[0, 12] = [160.0, 170.0, 0.91]

    crop_res = MagicMock()
    crop_res.keypoints = MagicMock()
    crop_res.keypoints.data = torch.from_numpy(crop_kpts)

    mock_model = MagicMock()
    mock_model.predict.side_effect = [[full_res], [crop_res]]
    adapter._get_model = MagicMock(return_value=mock_model)

    refined, _ = adapter._refinar_keypoints_top_down(frame, pts_orig, persona_idx=0)
    assert refined is not None
    # Verificar tamaño exacto del recorte con 10% padding: (270-30=240, 320-80=240)
    assert mock_model.predict.call_count == 2
    crop_arg = mock_model.predict.call_args_list[1].kwargs["source"]
    assert crop_arg.shape[:2] == (240, 240)
    # Verificar mapeo de vuelta a coordenadas globales sumando (cx1=80, cy1=30)
    assert refined[5][:2] == (150, 100)
    assert refined[7][:2] == (140, 150)
    assert refined[12][:2] == (240, 200)


def test_top_down_fallback_si_recorte_no_detecta_persona():
    import torch

    adapter = YOLOPoseAdapter(colab_url="https://placeholder")
    frame = np.zeros((400, 600, 3), dtype=np.uint8)
    pts_orig = {5: (150, 100, 0.9), 6: (250, 100, 0.9)}

    full_res = MagicMock()
    full_res.boxes = MagicMock()
    full_res.boxes.xyxy = torch.tensor([[100.0, 50.0, 300.0, 250.0]])
    full_res.keypoints = None

    crop_res_empty = MagicMock()
    crop_res_empty.keypoints = None

    mock_model = MagicMock()
    mock_model.predict.side_effect = [[full_res], [crop_res_empty]]
    adapter._get_model = MagicMock(return_value=mock_model)

    refined, _ = adapter._refinar_keypoints_top_down(frame, pts_orig, persona_idx=0)
    assert refined is None


def test_top_down_aisla_por_kmeans_si_caja_supera_40_porciento():
    import torch

    adapter = YOLOPoseAdapter(colab_url="https://placeholder")
    frame = np.zeros((400, 1000, 3), dtype=np.uint8)

    # Caja ancha = 600px de 1000px (60% > 40%): incluye atacante en x=300..450 y punto lejano en x=880
    pts_orig = {
        5: (310, 100, 0.9),
        6: (430, 100, 0.9),
        7: (300, 200, 0.9),
        8: (440, 200, 0.9),
        11: (320, 300, 0.9),
        12: (420, 300, 0.9),
        15: (880, 320, 0.9),
        16: (890, 330, 0.9),
    }

    full_res = MagicMock()
    full_res.boxes = MagicMock()
    full_res.boxes.xyxy = torch.tensor([[290.0, 80.0, 900.0, 360.0]])  # 610px = 61% > 40%
    full_res.keypoints = None

    crop_kpts = np.zeros((1, 17, 3), dtype=np.float32)
    crop_kpts[0, 5] = [80.0, 40.0, 0.95]
    crop_kpts[0, 6] = [180.0, 40.0, 0.95]
    crop_kpts[0, 7] = [70.0, 140.0, 0.95]
    crop_kpts[0, 11] = [90.0, 240.0, 0.95]
    crop_kpts[0, 12] = [170.0, 240.0, 0.95]

    crop_res = MagicMock()
    crop_res.keypoints = MagicMock()
    crop_res.keypoints.data = torch.from_numpy(crop_kpts)

    mock_model = MagicMock()
    mock_model.predict.side_effect = [[full_res], [crop_res]]
    adapter._get_model = MagicMock(return_value=mock_model)

    refined, _ = adapter._refinar_keypoints_top_down(frame, pts_orig, persona_idx=0)
    assert refined is not None
    crop_arg = mock_model.predict.call_args_list[1].kwargs["source"]
    # El ancho del recorte aislado debe haberse reducido a <= 40% de 1000px (<= 400px)
    assert crop_arg.shape[1] <= 400
