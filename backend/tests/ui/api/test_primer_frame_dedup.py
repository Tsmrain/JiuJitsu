import numpy as np
import pytest
from corpocmente.ui.api.routes import _bbox_iou, _bbox_iomin, _limpiar_candidatos_bboxes


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
