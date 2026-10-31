import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from corpocmente.main import app
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
from corpocmente.domain.services.session_manager import SessionStateManager, SessionState

client = TestClient(app)

# Tokens JWT de prueba existentes en el sistema
# Admin: 00000000-0000-0000-0000-000000000000
# Profesor: 7e455a7d-cbc8-4190-9a10-3b959f6425fc
# Alumno: bce12c1c-91f1-4bfb-813b-a18c5426b51e

import jwt as pyjwt
from corpocmente.config import settings

def make_token(role="profesor", uid="7e455a7d-cbc8-4190-9a10-3b959f6425fc"):
    return pyjwt.encode({"sub": "test_user", "uid": uid, "role": role}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def test_qdrant_guardar_y_recuperar_patron():
    """Prueba que QdrantVectorAdapter guarda, pagina y recupera en orden los 133 dims."""
    adapter = QdrantVectorAdapter()
    tecnica_id = uuid4()
    patron_id = uuid4()
    profesor_id = uuid4()

    # Generar 150 frames sintéticos de 133 dims con orden verificable
    secuencia = []
    for f in range(150):
        frame = [0.0] * 133
        frame[0] = float(f)  # Marcador del frame
        secuencia.append(frame)

    # 1. Guardar
    guardados = adapter.guardar_patron_secuencia(
        tecnica_id=tecnica_id,
        patron_id=patron_id,
        profesor_id=profesor_id,
        secuencia_kpts=secuencia
    )
    assert guardados == 150

    # 2. Recuperar
    recuperados = adapter.obtener_secuencia_referencia(tecnica_id=tecnica_id, patron_id=patron_id)
    assert len(recuperados) == 150
    # Verificar orden estricto de los frames
    for f in range(150):
        assert recuperados[f][0] == float(f)

    # 3. Eliminar
    adapter.eliminar_patron(patron_id)
    recuperados_post = adapter.obtener_secuencia_referencia(tecnica_id=tecnica_id, patron_id=patron_id)
    assert len(recuperados_post) == 0


def test_alumno_intenta_registrar_patron_retorna_403():
    """Un alumno intentando registrar un patrón biomecánico debe recibir 403 Forbidden."""
    alumno_token = make_token(role="alumno", uid="bce12c1c-91f1-4bfb-813b-a18c5426b51e")
    tecnica_id = "2de123c5-8ed3-4de5-a3f9-daeb2218d062"

    res = client.post(
        f"/api/v1/tecnicas/{tecnica_id}/patron",
        headers={"Authorization": f"Bearer {alumno_token}"},
        data={"session_id": "cualquiera"}
    )
    assert res.status_code == 403
    detail = res.json()["detail"]
    assert "Instructor or administrator privileges required" in detail or "profesor o administrador" in detail


def test_tecnica_inexistente_retorna_404():
    """Intentar registrar un patrón en una técnica que no existe retorna 404 Not Found."""
    prof_token = make_token(role="profesor")
    tecnica_falsa = str(uuid4())

    res = client.post(
        f"/api/v1/tecnicas/{tecnica_falsa}/patron",
        headers={"Authorization": f"Bearer {prof_token}"},
        data={"session_id": "cualquiera"}
    )
    assert res.status_code == 404


def test_patron_inexistente_get_retorna_404():
    """Consultar el patrón de una técnica sin patrón activo retorna 404 Not Found."""
    prof_token = make_token(role="profesor")
    tecnica_falsa = str(uuid4())

    res = client.get(
        f"/api/v1/tecnicas/{tecnica_falsa}/patron",
        headers={"Authorization": f"Bearer {prof_token}"}
    )
    assert res.status_code == 404


def test_tracking_insuficiente_retorna_422():
    """Si la cobertura del tracking es < 70%, debe retornar 422 Unprocessable Entity."""
    prof_token = make_token(role="profesor")
    res_t = client.get("/api/v1/tecnicas")
    tecnicas = res_t.json() if res_t.status_code == 200 else []
    tecnica_id = tecnicas[0]["id"] if tecnicas else "30a4afe4-23cc-4479-9f14-4f6d867de7dd"

    # Mockear YOLO para retornar cobertura baja
    with patch("corpocmente.infrastructure.ai.adapters.YOLOPoseAdapter.extraer_secuencia") as mock_ext:
        mock_ext.return_value = {
            "secuencia_kpts": [[0.0] * 133],
            "total_frames": 100,
            "frames_con_persona": 40,
            "cobertura": 0.40
        }
        res = client.post(
            f"/api/v1/tecnicas/{tecnica_id}/patron",
            headers={"Authorization": f"Bearer {prof_token}"},
            files={"video": ("test.mp4", b"dummy video content", "video/mp4")},
            data={"persona_idx": 0}
        )
        assert res.status_code == 422
        detail = res.json()["detail"]
        assert "Insufficient tracking" in detail or "Tracking insuficiente" in detail


def test_fallo_postgres_limpia_patron_huerfano_en_qdrant():
    """Si PostgreSQL falla al activar el nuevo patrón, Qdrant debe hacer rollback eliminando el patrón huérfano."""
    prof_token = make_token(role="profesor")
    tecnica_id = "2de123c5-8ed3-4de5-a3f9-daeb2218d062"
    adapter = QdrantVectorAdapter()

    frames_sinteticos = [[1.0] * 133 for _ in range(5)]

    with patch("corpocmente.infrastructure.ai.adapters.YOLOPoseAdapter.extraer_secuencia") as mock_ext, \
         patch("corpocmente.infrastructure.persistence.postgrest_client.PostgrestClient.rpc") as mock_rpc:

        mock_ext.return_value = {
            "secuencia_kpts": frames_sinteticos,
            "total_frames": 5,
            "frames_con_persona": 5,
            "cobertura": 1.0
        }
        # tecnica_exists retorna True, pero admin_activar_patron_tecnica explota
        def rpc_side_effect(fn_name, params):
            if fn_name == "tecnica_exists":
                return True
            if fn_name == "admin_activar_patron_tecnica":
                raise RuntimeError("Simulated DB connection failure during activation")
            return None

        mock_rpc.side_effect = rpc_side_effect

        with patch.object(adapter, "eliminar_patron", wraps=adapter.eliminar_patron) as spy_eliminar:
            with patch("corpocmente.infrastructure.persistence.qdrant_adapter.QdrantVectorAdapter", return_value=adapter):
                res = client.post(
                    f"/api/v1/tecnicas/{tecnica_id}/patron",
                    headers={"Authorization": f"Bearer {prof_token}"},
                    files={"video": ("test.mp4", b"dummy", "video/mp4")},
                    data={"persona_idx": 0}
                )
                assert res.status_code == 500
                detail = res.json()["detail"]
                assert "Failed to activate pattern in PostgreSQL" in detail or "Fallo al activar patrón en PostgreSQL" in detail
                assert spy_eliminar.called


def test_registro_y_reemplazo_patron_exitoso():
    """Registra un patrón sintético, verifica activación en PostgreSQL y Qdrant, y reemplazo seguro."""
    prof_token = make_token(role="profesor")
    tecnica_id = str(uuid4())
    adapter = QdrantVectorAdapter()

    frames_p1 = [[1.5] * 133 for _ in range(10)]
    frames_p2 = [[2.5] * 133 for _ in range(12)]

    active_patron = {}

    def mock_rpc(fn_name, params):
        if fn_name == "tecnica_exists":
            return True
        if fn_name == "admin_activar_patron_tecnica":
            tid = params["p_tecnica_id"]
            nuevo = params["p_patron_id"]
            ant = active_patron.get(tid)
            active_patron[tid] = nuevo
            return [{"tecnica_id": tid, "patron_activo_id": nuevo, "patron_anterior_id": ant}]
        if fn_name == "get_patron_activo":
            return active_patron.get(params["p_tecnica_id"])
        return None

    # 1. Registrar Patrón 1
    with patch("corpocmente.infrastructure.ai.adapters.YOLOPoseAdapter.extraer_secuencia") as mock_ext, \
         patch("corpocmente.infrastructure.persistence.postgrest_client.PostgrestClient.rpc", side_effect=mock_rpc):

        mock_ext.return_value = {
            "secuencia_kpts": frames_p1,
            "total_frames": 10,
            "frames_con_persona": 10,
            "cobertura": 1.0
        }
        res1 = client.post(
            f"/api/v1/tecnicas/{tecnica_id}/patron",
            headers={"Authorization": f"Bearer {prof_token}"},
            files={"video": ("patron1.mp4", b"video1", "video/mp4")},
            data={"persona_idx": 0}
        )
        assert res1.status_code == 201
        data1 = res1.json()
        patron_1_id = data1["patron_id"]
        assert data1["total_frames"] == 10

        # Verificar en Qdrant
        p1_recup = adapter.obtener_secuencia_referencia(tecnica_id=tecnica_id, patron_id=patron_1_id)
        assert len(p1_recup) == 10

        # 2. Registrar Patrón 2 (debe reemplazar a Patrón 1 y limpiar Qdrant)
        mock_ext.return_value = {
            "secuencia_kpts": frames_p2,
            "total_frames": 12,
            "frames_con_persona": 12,
            "cobertura": 1.0
        }
        res2 = client.post(
            f"/api/v1/tecnicas/{tecnica_id}/patron",
            headers={"Authorization": f"Bearer {prof_token}"},
            files={"video": ("patron2.mp4", b"video2", "video/mp4")},
            data={"persona_idx": 0}
        )
        assert res2.status_code == 201
        data2 = res2.json()
        patron_2_id = data2["patron_id"]
        assert patron_2_id != patron_1_id
        assert data2["patron_anterior_id"] == patron_1_id

        # Verificar que el patrón activo ahora es P2
        p2_recup = adapter.obtener_secuencia_referencia(tecnica_id=tecnica_id, patron_id=patron_2_id)
        assert len(p2_recup) == 12

        # Verificar que P1 ya fue eliminado de Qdrant
        p1_huerfano = adapter.obtener_secuencia_referencia(tecnica_id=tecnica_id, patron_id=patron_1_id)
        assert len(p1_huerfano) == 0

        # Limpiar al finalizar
        adapter.eliminar_patron(patron_2_id)


def test_fallo_insercion_qdrant_mantiene_patron_anterior():
    """Si la inserción en Qdrant falla, el patrón anterior sigue activo y no se toca PostgreSQL."""
    prof_token = make_token(role="profesor")
    tecnica_id = str(uuid4())
    adapter = QdrantVectorAdapter()

    frames = [[1.0] * 133 for _ in range(5)]
    patron_anterior_id = str(uuid4())

    def mock_rpc(fn_name, params):
        if fn_name == "tecnica_exists":
            return True
        if fn_name == "get_patron_activo":
            return patron_anterior_id
        if fn_name == "admin_activar_patron_tecnica":
            raise AssertionError("No se debe llamar a admin_activar_patron_tecnica si Qdrant falló")
        return None

    with patch("corpocmente.infrastructure.ai.adapters.YOLOPoseAdapter.extraer_secuencia") as mock_ext, \
         patch("corpocmente.infrastructure.persistence.postgrest_client.PostgrestClient.rpc", side_effect=mock_rpc), \
         patch.object(adapter, "guardar_patron_secuencia", side_effect=RuntimeError("Qdrant connection timeout")), \
         patch("corpocmente.infrastructure.persistence.qdrant_adapter.QdrantVectorAdapter", return_value=adapter):

        mock_ext.return_value = {
            "secuencia_kpts": frames,
            "total_frames": 5,
            "frames_con_persona": 5,
            "cobertura": 1.0
        }
        res = client.post(
            f"/api/v1/tecnicas/{tecnica_id}/patron",
            headers={"Authorization": f"Bearer {prof_token}"},
            files={"video": ("test.mp4", b"dummy", "video/mp4")},
            data={"persona_idx": 0}
        )
        assert res.status_code == 500
        detail = res.json()["detail"]
        assert "Failed to insert pattern in Qdrant" in detail or "Fallo al insertar patrón en Qdrant" in detail


def test_registro_patron_sin_persona_idx_retorna_422():
    """Si no se envía persona_idx al subir un video directo, debe retornar 422 Unprocessable Entity."""
    prof_token = make_token(role="profesor")
    tecnica_id = str(uuid4())

    with patch("corpocmente.infrastructure.persistence.postgrest_client.PostgrestClient.rpc", return_value=True):
        res = client.post(
            f"/api/v1/tecnicas/{tecnica_id}/patron",
            headers={"Authorization": f"Bearer {prof_token}"},
            files={"video": ("test.mp4", b"dummy video content", "video/mp4")}
        )
        assert res.status_code == 422
        assert "persona_idx is required" in res.json()["detail"]


def test_registro_patron_con_session_id_sin_persona_seleccionada_retorna_409(tmp_path):
    """Si se pasa session_id pero aún no se confirmó persona_idx en la sesión, retorna 409 Conflict."""
    from corpocmente.domain.services.session_manager import SessionStateManager
    prof_token = make_token(role="profesor")
    tecnica_id = str(uuid4())
    session_id = str(uuid4())

    fake_video = str(tmp_path / "vid.mp4")
    with open(fake_video, "wb") as f:
        f.write(b"fake")

    SessionStateManager.crear_sesion(
        session_id=session_id,
        video_path=fake_video,
        personas_detectadas=[{"idx": 0, "bbox": [0, 0, 10, 10], "confianza": 0.9, "keypoints_validos": 15}],
        frame_idx=0
    )

    with patch("corpocmente.infrastructure.persistence.postgrest_client.PostgrestClient.rpc", return_value=True):
        res = client.post(
            f"/api/v1/tecnicas/{tecnica_id}/patron",
            headers={"Authorization": f"Bearer {prof_token}"},
            data={"session_id": session_id}
        )
        assert res.status_code == 409
        assert "PERSONA_SELECTED" in res.json()["detail"]


def test_registro_patron_con_session_id_exitoso(tmp_path):
    """Registra patrón usando session_id con persona_idx previamente confirmada."""
    from corpocmente.domain.services.session_manager import SessionStateManager
    prof_token = make_token(role="profesor")
    tecnica_id = str(uuid4())
    session_id = str(uuid4())

    fake_video = str(tmp_path / "vid2.mp4")
    with open(fake_video, "wb") as f:
        f.write(b"fake2")

    SessionStateManager.crear_sesion(
        session_id=session_id,
        video_path=fake_video,
        personas_detectadas=[
            {"idx": 0, "bbox": [0, 0, 10, 10], "confianza": 0.9, "keypoints_validos": 15},
            {"idx": 1, "bbox": [20, 20, 50, 50], "confianza": 0.85, "keypoints_validos": 14}
        ],
        frame_idx=0
    )
    # Profesor selecciona explícitamente a la persona 1
    SessionStateManager.seleccionar_persona(session_id=session_id, persona_idx=1)

    frames = [[1.2] * 133 for _ in range(8)]
    with patch("corpocmente.infrastructure.ai.adapters.YOLOPoseAdapter.extraer_secuencia") as mock_ext, \
         patch("corpocmente.infrastructure.persistence.postgrest_client.PostgrestClient.rpc") as mock_rpc:

        def rpc_side_effect(fn_name, params):
            if fn_name == "tecnica_exists":
                return True
            if fn_name == "admin_activar_patron_tecnica":
                return [{"tecnica_id": tecnica_id, "patron_activo_id": str(uuid4()), "patron_anterior_id": None}]
            if fn_name == "admin_save_video_referencia":
                return True
            return None

        mock_rpc.side_effect = rpc_side_effect
        mock_ext.return_value = {
            "secuencia_kpts": frames,
            "total_frames": 8,
            "frames_con_persona": 8,
            "cobertura": 1.0
        }

        res = client.post(
            f"/api/v1/tecnicas/{tecnica_id}/patron",
            headers={"Authorization": f"Bearer {prof_token}"},
            data={"session_id": session_id, "persona_idx": 1}
        )
        assert res.status_code == 201
        assert res.json()["total_frames"] == 8
        # Verificar que a extraer_secuencia se le pasó persona_idx_inicial=1
        mock_ext.assert_called_once_with(fake_video, persona_idx_inicial=1)
