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


def test_pose_model_priority_prefers_generic_nano_over_finetuned_and_medium(tmp_path):
    """TAREA 1 y 2: Genérico yolo26n-pose.pt debe tener mayor prioridad que finetuned y medium."""
    from pathlib import Path
    repo_root = tmp_path / "repo"
    models_dir = tmp_path / "models"
    (repo_root / "backend").mkdir(parents=True)
    models_dir.mkdir(parents=True)

    candidates = YOLOPoseAdapter._pose_model_candidates(repo_root, models_dir)
    idx_generic_backend = candidates.index(str(repo_root / "backend" / "yolo26n-pose.pt"))
    idx_autonomous = candidates.index(str(repo_root / "yolo26n_autonomous.pt"))
    idx_americana = candidates.index(str(repo_root / "yolo26n_americana.pt"))
    idx_medium = candidates.index(str(models_dir / "yolo26m-pose.pt"))

    assert idx_generic_backend < idx_autonomous < idx_medium
    assert idx_generic_backend < idx_americana < idx_medium

    selected_path = YOLOPoseAdapter()._get_model().path
    assert "yolo26n-pose.pt" in str(selected_path)


def test_extraer_secuencia_con_frame_stride_y_opt_flags():
    """TAREA 3 y 4: Verifica vid_stride, imgsz=416, half=True y preservación de frame_idxs reales."""
    import torch
    from unittest.mock import patch

    def make_res(cx):
        r = MagicMock()
        r.boxes = None
        arr = np.zeros((1, 17, 3), dtype=np.float32)
        for j in range(17):
            arr[0, j] = [cx + (j % 3) * 4, 200.0 + (j // 3) * 4, 0.9]
        r.keypoints = MagicMock()
        r.keypoints.data = torch.from_numpy(arr)
        return r

    mock_model = MagicMock()
    mock_model.predict.return_value = [make_res(100.0), make_res(105.0), make_res(110.0)]

    adapter = YOLOPoseAdapter(colab_url="")
    adapter._get_model = MagicMock(return_value=mock_model)

    with patch("os.path.exists", return_value=True):
        res = adapter.extraer_secuencia("dummy.mp4", persona_idx_inicial=0, frame_stride=2)

    kwargs = mock_model.predict.call_args.kwargs
    assert kwargs["imgsz"] == 416
    assert kwargs["half"] is True
    assert kwargs["vid_stride"] == 2
    assert res["frame_idxs"] == [0, 2, 4]
    assert len(res["secuencia_kpts"]) == 3


def test_extraer_frame_y_dibujar_error_respeta_use_top_down_false(tmp_path):
    """TAREA 5: Cuando USE_TOP_DOWN=False no debe ejecutar _refinar_keypoints_top_down."""
    from unittest.mock import patch
    from corpocmente.config import settings

    video_path = str(tmp_path / "test_td.mp4")
    output_path = str(tmp_path / "critico_td.jpg")
    _crear_video_prueba(video_path, num_frames=2)

    kpts = []
    for _ in range(17):
        kpts.extend([0.5, 0.5, 0.9])
    kpts.extend([0.0] * (133 - len(kpts)))

    adapter = YOLOPoseAdapter(colab_url="")
    with patch.object(settings, "USE_TOP_DOWN", False), \
         patch.object(adapter, "_refinar_keypoints_top_down") as mock_td:
        res_path = adapter.extraer_frame_y_dibujar_error(
            video_path=video_path,
            frame_idx=0,
            keypoints133=kpts,
            articulaciones_criticas=[13],
            output_path=output_path,
        )
        assert os.path.exists(res_path)
        mock_td.assert_not_called()


def test_facade_pasa_frame_stride_y_mapea_frame_real(tmp_path):
    """TAREA 4: Facade usa FRAME_STRIDE, pasa frame_idxs a DTW y preserva frame_alumno_idx real."""
    from unittest.mock import patch
    from corpocmente.config import settings

    video_alumno = str(tmp_path / "alumno_stride.mp4")
    _crear_video_prueba(video_alumno, num_frames=6)

    def _valid_frame(offset: float):
        pts = []
        for j in range(17):
            pts.extend([0.3 + j * 0.01 + offset, 0.4 + j * 0.01, 0.95])
        pts.extend([0.0] * (133 - len(pts)))
        return pts

    ref_seq = [_valid_frame(0.0) for _ in range(6)]
    alu_seq = [_valid_frame(0.0), _valid_frame(0.15), _valid_frame(0.02)]

    mock_yolo = MagicMock()
    mock_yolo.extraer_secuencia.return_value = {
        "secuencia_kpts": alu_seq,
        "frame_idxs": [0, 2, 4],
        "total_frames": 3,
        "frames_con_persona": 3,
        "cobertura": 1.0,
    }
    mock_qdrant = MagicMock()
    mock_qdrant.obtener_todas_secuencias_referencia.return_value = [ref_seq]
    mock_qdrant.recuperar_contexto_rag.return_value = ""
    mock_gemini = MagicMock()
    mock_gemini.generar_texto_feedback.return_value = "Feedback ok."

    facade = IntelligenceAnalysisFacade(
        yolo_adapter=mock_yolo,
        qdrant_adapter=mock_qdrant,
        gemini_adapter=mock_gemini,
    )
    with patch.object(settings, "FRAME_STRIDE", 2):
        res = facade.ejecutar_analisis_completo(
            video_path=video_alumno,
            tecnica_id=uuid4(),
            tecnica_nombre="Americana",
            evaluacion_id="test-stride",
        )

    assert mock_yolo.extraer_secuencia.call_args.kwargs["frame_stride"] == 2
    assert res.frame_alumno_idx in (0, 2, 4)


def test_dtw_filtra_frames_vacios_y_evita_frame_critico_falso():
    """TAREA 3: Un frame negro/vacío ([0]*133) no debe colapsar el warp DTW ni forzar frame_critico=4."""
    from corpocmente.domain.biomechanics.dtw_comparator import comparar_secuencias_con_dtw

    def _pose(dx: float):
        pts = []
        for j in range(17):
            pts.extend([200.0 + j * 5.0 + dx, 150.0 + (j % 4) * 15.0, 0.95])
        return pts + [0.0] * 82

    seq_m = [_pose(i * 1.5) for i in range(25)]
    seq_a = [_pose(i * 1.5) for i in range(20)]
    # Inyectar frame vacío en alumno idx=3 (frame real 6) y discrepancia real en idx=15 (frame real 30)
    seq_a[3] = [0.0] * 133
    seq_a[15][6 * 3] += 120.0  # Desviación real en hombro derecho

    f_m = [i * 2 for i in range(len(seq_m))]
    f_a = [i * 2 for i in range(len(seq_a))]

    res = comparar_secuencias_con_dtw(
        seq_m, seq_a, frame_idxs_maestro=f_m, frame_idxs_alumno=f_a
    )
    assert res["frame_alumno_critico"] == 30
    assert all(p["similitud_frame"] > 0.0 for p in res["alineacion"])


def test_dtw_secuencia_toda_ceros_lanza_error():
    """TAREA 3: Una secuencia COCO de video (>10 frames) sin keypoints válidos debe fallar explícitamente."""
    from corpocmente.domain.biomechanics.dtw_comparator import comparar_secuencias_con_dtw

    seq_vacia = [[0.0] * 133 for _ in range(15)]
    seq_ok = [[100.0 + i, 120.0, 0.9] * 17 + [0.0] * 82 for i in range(15)]
    with pytest.raises(ValueError, match="keypoints detectados"):
        comparar_secuencias_con_dtw(seq_ok, seq_vacia)


@pytest.mark.xfail(
    reason="TAREA 4: documenta incoherencia conocida en datos v1 (dtw_normalizado=dtw_distance/max_len escala ~1/sqrt(N) vs score_similitud=mean(similitud_esqueletos)*100); pendiente confirmación de fórmula antes de modificar score_similitud.",
    strict=True,
)
def test_coherencia_dtw_vs_score():
    """Verifica que score_similitud y dtw_normalizado apunten en la misma dirección."""
    casos = [
        ("Americana", 0.209014, 49.34),
        ("EscapeGuardia", 0.264757, 60.91),
        ("Armbar_A", 0.158769, 53.51),
        ("Armbar_B", 0.136405, 22.81),
    ]
    ordenados = sorted(casos, key=lambda x: x[1])
    scores = [c[2] for c in ordenados]
    assert scores == sorted(scores, reverse=True), (
        f"Incoherencia métricas: {list(zip([c[0] for c in ordenados], scores))}. "
        f"dtw_normalizado bajo debería implicar score alto."
    )
