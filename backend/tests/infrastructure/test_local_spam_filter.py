import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from corpocmente.infrastructure.ai.local_spam_filter import LocalSpamFilter

def _setup_filter(label_probs):
    f = LocalSpamFilter.__new__(LocalSpamFilter)
    f.clf = MagicMock()
    f.clf.predict_proba.return_value = np.array([label_probs])
    f.labels = ["guard", "standing"]
    f.min_bjj_ratio = 0.60
    f.min_interaction_frames = 1
    f.num_frames = 4
    f.yolo = MagicMock()
    return f

def test_bjj_acepta():
    f = _setup_filter([0.92, 0.08])
    with patch.object(f, "_extraer_poses", return_value=([[0]*51], [[0]*51])):
        with patch("cv2.VideoCapture") as m:
            cap = MagicMock(); cap.isOpened.return_value = True
            cap.get.return_value = 100; cap.read.return_value = (True, np.zeros((100,100,3)))
            m.return_value = cap
            assert f.validar_es_jiujitsu("/fake.mp4") is True

def test_standing_rechaza():
    f = _setup_filter([0.05, 0.95])
    with patch.object(f, "_extraer_poses", return_value=([[0]*51], [[0]*51])):
        with patch("cv2.VideoCapture") as m:
            cap = MagicMock(); cap.isOpened.return_value = True
            cap.get.return_value = 100; cap.read.return_value = (True, np.zeros((100,100,3)))
            m.return_value = cap
            assert f.validar_es_jiujitsu("/fake.mp4") is False

def test_sin_personas_rechaza():
    f = _setup_filter([0.5, 0.5])
    with patch.object(f, "_extraer_poses", return_value=None):
        with patch("cv2.VideoCapture") as m:
            cap = MagicMock(); cap.isOpened.return_value = True
            cap.get.return_value = 100; cap.read.return_value = (True, np.zeros((100,100,3)))
            m.return_value = cap
            assert f.validar_es_jiujitsu("/fake.mp4") is False

def test_guard_rechaza_evidencia_insuficiente():
    """Un video con solo 2 frames de interacción (< min_interaction_frames=5) se rechaza aunque ambos sean BJJ."""
    f = LocalSpamFilter.__new__(LocalSpamFilter)
    f.clf = MagicMock()
    f.clf.predict_proba.return_value = np.array([[0.95, 0.05]])
    f.labels = ["guard", "standing"]
    f.min_bjj_ratio = 0.60
    f.min_interaction_frames = 5
    f.num_frames = 10
    f.yolo = MagicMock()

    call_count = {"n": 0}
    def fake_poses(frame):
        call_count["n"] += 1
        # Solo los primeros 2 frames tienen 2 personas
        if call_count["n"] <= 2:
            return [[0]*51], [[0]*51]
        return None

    with patch.object(f, "_extraer_poses", side_effect=fake_poses):
        with patch("cv2.VideoCapture") as m:
            cap = MagicMock(); cap.isOpened.return_value = True
            cap.get.return_value = 100
            cap.read.return_value = (True, np.zeros((100,100,3)))
            m.return_value = cap
            assert f.validar_es_jiujitsu("/fake.mp4") is False
