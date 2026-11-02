import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter


def test_local_vlm_query_rewriting_cognitivo_defensa():
    vlm = LocalVLMAdapter()
    reescrita = vlm.reescribir_query_cognitiva("defensa de llave de brazo")
    assert "defensa" in reescrita.lower()
    assert any(term in reescrita.lower() for term in ["escape", "survive", "defend"])


def test_local_vlm_query_rewriting_cognitivo_ataque():
    vlm = LocalVLMAdapter()
    reescrita = vlm.reescribir_query_cognitiva("ataque de estrangulacion")
    assert "ataque" in reescrita.lower()
    assert any(term in reescrita.lower() for term in ["submission", "finish", "attack"])


def test_local_vlm_query_rewriting_vacio():
    vlm = LocalVLMAdapter()
    assert vlm.reescribir_query_cognitiva("   ") == ""


@patch("corpocmente.infrastructure.ai.adapters.os.path.exists", return_value=True)
@patch("ultralytics.YOLO")
def test_yolo_pose_adapter_data_flywheel_uncertainty(mock_yolo_class, mock_exists, tmp_path):
    mock_model = MagicMock()
    mock_yolo_class.return_value = mock_model

    # Frame 1: baja confianza (0.45)
    import torch
    r1 = MagicMock()
    r1.orig_img = np.zeros((100, 100, 3), dtype=np.uint8)
    r1.boxes = MagicMock()
    r1.boxes.__len__.return_value = 1
    r1.boxes.conf = torch.tensor([0.45], dtype=torch.float32)
    kpts1 = np.zeros((1, 17, 3), dtype=np.float32)
    kpts1[0, :5, 0] = 50.0
    kpts1[0, :5, 1] = 50.0
    kpts1[0, :5, 2] = 0.9
    r1.keypoints = MagicMock()
    r1.keypoints.data.cpu.return_value.numpy.return_value = kpts1

    mock_model.predict.return_value = [r1]

    adapter = YOLOPoseAdapter()
    
    # Ejecutar con tecnica_id de prueba
    test_tecnica = "test_flywheel_tech"
    res = adapter.extraer_secuencia("dummy_video.mp4", tecnica_id=test_tecnica)
    assert len(res["secuencia_kpts"]) == 1

    # Verificar que se creo la carpeta de incertidumbre y el log
    uncertainty_base = Path(__file__).resolve().parents[2] / "backend" / "storage" / "uncertainty_frames"
    flywheel_dir = uncertainty_base / test_tecnica
    log_csv = uncertainty_base / "log.csv"

    assert flywheel_dir.exists()
    saved_frames = list(flywheel_dir.glob("frame_*.jpg"))
    assert len(saved_frames) >= 1
    assert log_csv.exists()
    with open(log_csv, "r", encoding="utf-8") as f:
        content = f.read()
        assert test_tecnica in content
        assert "0.45" in content
