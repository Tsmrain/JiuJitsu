from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from corpocmente.ui.api.routes import (
    _bbox_iou,
    _bbox_iomin,
    _limpiar_candidatos_bboxes,
    _resolver_cajas_fusionadas,
    _split_candidate_via_kmeans,
)


def test_bbox_iou_and_iomin():
    b1 = [0, 0, 100, 100]
    b2 = [50, 0, 150, 100]
    # Inter = 50 * 100 = 5000, Union = 10000 + 10000 - 5000 = 15000 -> IoU = 1/3
    assert abs(_bbox_iou(b1, b2) - 1.0 / 3.0) < 1e-4
    # IoMin = 5000 / 10000 = 0.5
    assert abs(_bbox_iomin(b1, b2) - 0.5) < 1e-4


def test_limpiar_candidatos_elimina_duplicados_directos():
    # Dos detecciones del mismo atleta (IoU > 0.60, cabezas a 15px)
    c1 = {
        "idx": 0,
        "pose": np.zeros((17, 3)),
        "bbox_raw": [100.0, 100.0, 300.0, 400.0],
        "confianza": 0.95,
        "keypoints_validos": 16,
        "center": np.array([200.0, 250.0]),
        "head": np.array([200.0, 110.0]),
        "pelvis": np.array([200.0, 260.0]),
    }
    c2 = {
        "idx": 1,
        "pose": np.zeros((17, 3)),
        "bbox_raw": [110.0, 105.0, 305.0, 395.0],
        "confianza": 0.88,
        "keypoints_validos": 15,
        "center": np.array([207.5, 250.0]),
        "head": np.array([205.0, 115.0]),
        "pelvis": np.array([205.0, 258.0]),
    }
    limpios = _limpiar_candidatos_bboxes([c1, c2], 1920, 1080)
    assert len(limpios) == 1
    assert limpios[0]["idx"] == 0
    assert limpios[0]["confianza"] == 0.95


def test_limpiar_candidatos_elimina_quimera_entre_dos_cuerpos():
    # Cuerpo A: Arriba a la izquierda
    cuerpa_a = {
        "idx": 0,
        "pose": np.zeros((17, 3)),
        "bbox_raw": [100.0, 100.0, 300.0, 300.0],
        "confianza": 0.95,
        "keypoints_validos": 16,
        "center": np.array([200.0, 200.0]),
        "head": np.array([200.0, 120.0]),
        "pelvis": np.array([200.0, 280.0]),
    }
    # Cuerpo B: Abajo a la derecha (sin solapar con A)
    cuerpa_b = {
        "idx": 2,
        "pose": np.zeros((17, 3)),
        "bbox_raw": [500.0, 500.0, 700.0, 700.0],
        "confianza": 0.91,
        "keypoints_validos": 16,
        "center": np.array([600.0, 600.0]),
        "head": np.array([600.0, 520.0]),
        "pelvis": np.array([600.0, 680.0]),
    }
    # Quimera C: Caja intermedia que se extiende sobre partes de A y de B (IoMin > 0.50 con ambos)
    quimera_c = {
        "idx": 1,
        "pose": np.zeros((17, 3)),
        "bbox_raw": [150.0, 150.0, 650.0, 650.0],
        "confianza": 0.93,
        "keypoints_validos": 16,
        "center": np.array([400.0, 400.0]),
        "head": np.array([590.0, 510.0]),
        "pelvis": np.array([210.0, 290.0]),
    }

    limpios = _limpiar_candidatos_bboxes([cuerpa_a, quimera_c, cuerpa_b], 1920, 1080)
    assert len(limpios) == 2
    indices = [c["idx"] for c in limpios]
    assert indices == [0, 2]


def test_limpiar_candidatos_preserva_pareja_jiujitsu_en_guardia():
    # Dos atletas en guardia cerrada que tienen un solapamiento moderado (IoU ~0.40)
    # pero son dos cuerpos distintos con cabezas y pelvis bien definidas
    atleta_arriba = {
        "idx": 0,
        "pose": np.zeros((17, 3)),
        "bbox_raw": [180.0, 150.0, 350.0, 450.0],
        "confianza": 0.85,
        "keypoints_validos": 15,
        "center": np.array([265.0, 300.0]),
        "head": np.array([265.0, 180.0]),
        "pelvis": np.array([265.0, 420.0]),
    }
    atleta_abajo = {
        "idx": 1,
        "pose": np.zeros((17, 3)),
        "bbox_raw": [180.0, 300.0, 350.0, 550.0],
        "confianza": 0.82,
        "keypoints_validos": 16,
        "center": np.array([265.0, 425.0]),
        "head": np.array([265.0, 520.0]),
        "pelvis": np.array([265.0, 320.0]),
    }
    limpios = _limpiar_candidatos_bboxes([atleta_arriba, atleta_abajo], 1080, 720)
    assert len(limpios) == 2
    assert [c["idx"] for c in limpios] == [0, 1]


def test_limpiar_candidatos_elimina_reflejo_espejo_diminuto():
    # Atleta principal en primer plano: área 400x600 = 240,000 px^2
    atleta_principal = {
        "idx": 0,
        "pose": np.zeros((17, 3)),
        "bbox_raw": [100.0, 100.0, 500.0, 700.0],
        "confianza": 0.95,
        "keypoints_validos": 16,
        "center": np.array([300.0, 400.0]),
        "head": np.array([300.0, 150.0]),
        "pelvis": np.array([300.0, 450.0]),
    }
    # Reflejo en espejo del fondo (Instructor #2): área 50x70 = 3,500 px^2 (< 10% del área principal)
    reflejo_espejo = {
        "idx": 2,
        "pose": np.zeros((17, 3)),
        "bbox_raw": [800.0, 50.0, 850.0, 120.0],
        "confianza": 0.65,
        "keypoints_validos": 8,
        "center": np.array([825.0, 85.0]),
        "head": np.array([825.0, 60.0]),
        "pelvis": np.array([825.0, 100.0]),
    }

    limpios = _limpiar_candidatos_bboxes([atleta_principal, reflejo_espejo], 1920, 1080)
    assert len(limpios) == 1
    assert limpios[0]["idx"] == 0


def test_resolver_cajas_fusionadas_usa_segmentacion_si_detecta_dos_cuerpos():
    frame = np.zeros((800, 500, 3), dtype=np.uint8)
    pose = np.zeros((17, 3), dtype=np.float32)
    pose[:, 0] = 200.0
    pose[:, 1] = 400.0
    pose[:, 2] = 0.9

    merged = [{
        "idx": 0,
        "pose": pose,
        "bbox_raw": [20.0, 200.0, 380.0, 650.0],  # 360px / 500px = 72% > 40%
        "confianza": 0.95,
        "keypoints_validos": 17,
    }]

    mock_box_data = MagicMock()
    mock_box_data.__len__.return_value = 3
    mock_box_data.xyxy.cpu.return_value.numpy.return_value = np.array([
        [20.0, 210.0, 180.0, 580.0],
        [200.0, 220.0, 375.0, 620.0],
        [5.0, 5.0, 20.0, 25.0],  # Ruido diminuto < 12% área
    ])
    mock_box_data.conf.cpu.return_value.numpy.return_value = np.array([0.88, 0.86, 0.20])
    mock_masks = SimpleNamespace(xy=[
        np.array([[25.0, 215.0], [175.0, 215.0], [175.0, 575.0]]),
        np.array([[205.0, 225.0], [370.0, 225.0], [370.0, 615.0]]),
        np.array([[5.0, 5.0], [20.0, 5.0], [20.0, 25.0]]),
    ])
    mock_seg_model = MagicMock()
    mock_seg_model.predict.return_value = [SimpleNamespace(boxes=mock_box_data, masks=mock_masks)]

    with patch("corpocmente.ui.api.routes.get_yolo_seg_model", return_value=mock_seg_model):
        res = _resolver_cajas_fusionadas(frame, merged, 500, 800)

    assert len(res) == 2
    assert [r["idx"] for r in res] == [0, 1]
    assert res[0]["bbox_raw"][2] < res[1]["bbox_raw"][0]


def test_resolver_cajas_fusionadas_fallback_kmeans_cuando_seg_falla():
    frame = np.zeros((832, 464, 3), dtype=np.uint8)
    pose = np.zeros((17, 3), dtype=np.float32)
    # 7 puntos en izquierda-abajo y 10 puntos en derecha-arriba (17 válidos > 10)
    for i in range(7):
        pose[i] = [70.0 + i * 10.0, 500.0 + i * 5.0, 0.9]
    for i in range(7, 17):
        pose[i] = [240.0 + (i - 7) * 8.0, 330.0 + (i - 7) * 8.0, 0.9]

    merged = [{
        "idx": 0,
        "pose": pose,
        "bbox_raw": [60.0, 280.0, 340.0, 640.0],  # 280px / 464px = 60.3% > 40%
        "confianza": 0.96,
        "keypoints_validos": 17,
    }]

    mock_seg_model = MagicMock()
    # Simular que seg tampoco logra separar en 2 cuerpos
    mock_box_data = MagicMock()
    mock_box_data.__len__.return_value = 1
    mock_seg_model.predict.return_value = [SimpleNamespace(boxes=mock_box_data, masks=None)]

    with patch("corpocmente.ui.api.routes.get_yolo_seg_model", return_value=mock_seg_model):
        res = _resolver_cajas_fusionadas(frame, merged, 464, 832)

    assert len(res) == 2
    assert res[0]["keypoints_validos"] == 7
    assert res[1]["keypoints_validos"] == 10
    assert res[0]["bbox_raw"][2] < 160.0
    assert res[1]["bbox_raw"][0] >= 240.0
