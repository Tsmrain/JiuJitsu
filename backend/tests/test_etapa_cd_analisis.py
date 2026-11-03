import pytest
from uuid import uuid4
import jwt as pyjwt
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from corpocmente.main import app
from corpocmente.config import settings
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
from corpocmente.domain.services.session_manager import (
    SessionStateManager, SessionState, SessionConflictError, SessionNotFoundError
)

client = TestClient(app)

def make_token(role="alumno", uid="bce12c1c-91f1-4bfb-813b-a18c5426b51e"):
    return pyjwt.encode({"sub": "test_user", "uid": uid, "role": role, "estado_suscripcion": "activo"}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def test_analizar_tecnica_sin_patron_activo_retorna_404():
    """Si una técnica no tiene patrón activo registrado ni video referencia, debe retornar 404."""
    admin_uid = "00000000-0000-0000-0000-000000000000"
    token = make_token(role="admin", uid=admin_uid)
    tecnica_falsa = str(uuid4())

    res = client.post(
        "/api/v1/evaluaciones/analizar",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "tecnica_id": tecnica_falsa,
            "tecnica_nombre": "Técnica Inexistente",
            "alumno_id": admin_uid,
        },
        files={"video": ("test.mp4", b"dummy video", "video/mp4")}
    )
    assert res.status_code == 404
    detail = res.json()["detail"]
    assert "No active biomechanical pattern" in detail or "No existe un patrón biomecánico activo" in detail


def test_sesion_reutilizada_o_concurrencia_retorna_409():
    """Una sesión ya creada no puede re-crearse, y dos operaciones concurrentes retornan 409."""
    session_id = f"test_session_{uuid4()}"
    SessionStateManager.crear_sesion(session_id, "/tmp/video.mp4", [{"idx": 0}], 0)

    # Reutilizar creación debe dar error de conflicto
    with pytest.raises(SessionConflictError):
        SessionStateManager.crear_sesion(session_id, "/tmp/video2.mp4", [{"idx": 0}], 0)

    # Seleccionar persona y pasar a IN_USE
    SessionStateManager.seleccionar_persona(session_id, 0)
    SessionStateManager.iniciar_operacion(session_id)

    # Intentar segunda operación concurrente sobre la misma sesión
    with pytest.raises(SessionConflictError):
        SessionStateManager.iniciar_operacion(session_id)


def test_recuperacion_patron_tras_reiniciar_adaptador():
    """Verifica que un nuevo QdrantVectorAdapter() recupera íntegramente el patrón persistido."""
    res_t = client.get("/api/v1/tecnicas")
    tecnicas = res_t.json() if res_t.status_code == 200 else []
    tecnica_id = tecnicas[0]["id"] if tecnicas else "30a4afe4-23cc-4479-9f14-4f6d867de7dd"

    # Instancia 1
    adapter1 = QdrantVectorAdapter()
    patron_id = adapter1._get_patron_activo_db(tecnica_id)
    cleanup = False
    if not patron_id:
        patron_id = uuid4()
        secuencia_test = [[float(f)] + [0.1] * 132 for f in range(50)]
        adapter1.guardar_patron_secuencia(
            tecnica_id=tecnica_id,
            patron_id=patron_id,
            profesor_id=uuid4(),
            secuencia_kpts=secuencia_test
        )
        cleanup = True

    try:
        # Instancia 2 (simula reinicio de servicio/adaptador desacoplado)
        adapter2 = QdrantVectorAdapter()
        secuencia = adapter2.obtener_secuencia_referencia(tecnica_id=tecnica_id, patron_id=patron_id)
        assert len(secuencia) > 0, "La secuencia recuperada tras reiniciar el adaptador no debe estar vacía"
        assert len(secuencia[0]) == 133, "Cada vector debe ser de 133 dimensiones"
    finally:
        if cleanup and patron_id:
            adapter1.eliminar_patron(patron_id)


def test_comparacion_dtw_con_secuencias_reales():
    """Ejecuta comparación DTW directa entre secuencias reales y valida determinismo y métrica."""
    from corpocmente.domain.biomechanics.dtw_comparator import comparar_secuencias_con_dtw

    res_t = client.get("/api/v1/tecnicas")
    tecnicas = res_t.json() if res_t.status_code == 200 else []
    tecnica_id = tecnicas[0]["id"] if tecnicas else "30a4afe4-23cc-4479-9f14-4f6d867de7dd"
    adapter = QdrantVectorAdapter()
    secuencia_maestro = adapter.obtener_secuencia_referencia(tecnica_id=tecnica_id)
    cleanup = False
    patron_id = None
    if not secuencia_maestro:
        patron_id = uuid4()
        secuencia_maestro = [[float(f)] + [0.1] * 132 for f in range(60)]
        adapter.guardar_patron_secuencia(
            tecnica_id=tecnica_id,
            patron_id=patron_id,
            profesor_id=uuid4(),
            secuencia_kpts=secuencia_maestro
        )
        cleanup = True

    try:
        assert len(secuencia_maestro) > 0

        # Auto-comparación (Sanity check: distancia 0, score ~100%)
        res_auto = comparar_secuencias_con_dtw(secuencia_maestro, secuencia_maestro)
        assert res_auto["dtw_distance"] == 0.0
        assert res_auto["score_similitud"] == 100.0

        # Comparación con versión recortada (temporalmente desfasada)
        secuencia_recortada = secuencia_maestro[10:-10]
        res_crop = comparar_secuencias_con_dtw(secuencia_maestro, secuencia_recortada)
        assert res_crop["score_similitud"] > 80.0, "DTW no debe penalizar severamente por desalineación temporal"
    finally:
        if cleanup and patron_id:
            adapter.eliminar_patron(patron_id)


def test_tracking_desplazamiento_y_oclusion_parcial():
    """Valida que el tracking mantiene la identidad ante desplazamiento suave y oclusión parcial (≤5 frames)."""
    import numpy as np
    from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
    import torch
    import ultralytics

    adapter = YOLOPoseAdapter()

    # Simular candidatos para 6 frames en resolución 1000x1000
    # Persona 0 (alumno en tatami): (~200, ~200)
    # Persona 1 (espectador de pie): (~800, ~100)
    def make_kpts(center_x, center_y, conf=0.9):
        # 17 keypoints alrededor de center_x, center_y
        arr = np.zeros((17, 3), dtype=np.float32)
        for i in range(17):
            arr[i] = [center_x + (i % 3) * 5, center_y + (i // 3) * 5, conf]
        return arr

    # Frames:
    # 0: p0=(200, 200), p1=(800, 100) -> Selecciona p0 (idx=0)
    # 1: p0=(210, 205), p1=(800, 100) -> Rastreo normal
    # 2: vacío (oclusión frame 1) -> Memoria de gracia
    # 3: vacío (oclusión frame 2) -> Memoria de gracia
    # 4: p0=(215, 210), p1=(800, 100) -> Recuperación exitosa de p0, sin saltar a p1
    # 5: p0=(220, 215), p1=(800, 100) -> Rastreo normal continuo

    frames_detections = [
        [make_kpts(200, 200), make_kpts(800, 100)],
        [make_kpts(210, 205), make_kpts(800, 100)],
        [], # oclusión
        [], # oclusión
        [make_kpts(215, 210), make_kpts(800, 100)],
        [make_kpts(220, 215), make_kpts(800, 100)],
    ]

    class MockResult:
        def __init__(self, kpts_list):
            if kpts_list:
                stacked = np.stack(kpts_list, axis=0) # shape (N, 17, 3)
                self.keypoints = MagicMock()
                self.keypoints.data = torch.from_numpy(stacked)
            else:
                self.keypoints = None

    mock_results = [MockResult(k) for k in frames_detections]

    with patch("os.path.exists", return_value=True), \
         patch("cv2.VideoCapture") as mock_cap_class, \
         patch("ultralytics.YOLO") as mock_yolo_class:

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: 1000.0 # width & height = 1000
        mock_cap_class.return_value = mock_cap

        mock_yolo_instance = MagicMock()
        mock_yolo_instance.predict.return_value = mock_results
        mock_yolo_class.return_value = mock_yolo_instance

        res = adapter.extraer_secuencia(
            video_path="dummy.mp4",
            persona_idx_inicial=0,
            max_disp_norm=0.25
        )

        assert res["total_frames"] == 6
        assert res["frames_con_persona"] == 4  # frames 0, 1, 4, 5 detectados
        sec = res["secuencia_kpts"]
        assert len(sec) == 6

        # Frame 0: p0 en x~200
        assert 190 < sec[0][0] < 210
        # Frame 1: p0 en x~210
        assert 200 < sec[1][0] < 220
        # Frames 2 y 3: oclusión (relleno ceros)
        assert sec[2][0] == 0.0
        assert sec[3][0] == 0.0
        # Frame 4: recuperación en x~215, NO saltó al espectador (x~800)
        assert 205 < sec[4][0] < 225
        assert sec[4][0] < 500  # Confirma que jamás saltó a 800
        # Frame 5: p0 en x~220
        assert 210 < sec[5][0] < 230
