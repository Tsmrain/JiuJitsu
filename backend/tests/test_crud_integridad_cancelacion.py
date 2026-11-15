from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter
from corpocmente.ui.api.auth_routes import _sign_token


def _auth_header(role: str, uid: str | None = None) -> dict:
    token = _sign_token({
        "uid": uid or str(uuid4()),
        "role": role,
        "email": f"{role}@test.com",
        "sucursal_id": "b3000000-0000-0000-0000-000000000003",
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# FASE 1: Integridad Referencial Qdrant <-> Postgres + Eliminación Manuales/Técnicas
# ---------------------------------------------------------------------------

def test_qdrant_rag_adapter_eliminar_por_manual_y_tecnica():
    mock_client = MagicMock()
    p1 = SimpleNamespace(
        id="pt-1",
        payload={
            "fuente_nombre": "manual_bjj.pdf",
            "fuente_url": "http://localhost:8000/api/v1/conocimiento/archivos/uuid1.pdf",
        },
    )
    p2 = SimpleNamespace(
        id="pt-2",
        payload={
            "fuente_nombre": "otro_manual.pdf",
            "fuente_url": "http://localhost:8000/api/v1/conocimiento/archivos/uuid2.pdf",
        },
    )
    mock_client.scroll.return_value = ([p1, p2], None)
    mock_client.count.return_value = SimpleNamespace(count=3)

    adapter = QdrantRAGAdapter(client=mock_client)
    deleted_manual = adapter.eliminar_por_manual("uuid1.pdf")
    assert deleted_manual == 1
    mock_client.delete.assert_called_once()

    mock_client.reset_mock()
    deleted_tech = adapter.eliminar_por_tecnica("tec-123")
    assert deleted_tech == 3
    mock_client.delete.assert_called_once()


def test_qdrant_vector_adapter_eliminar_por_tecnica():
    mock_client = MagicMock()
    mock_client.count.return_value = SimpleNamespace(count=5)

    adapter = QdrantVectorAdapter(client=mock_client)
    deleted = adapter.eliminar_por_tecnica(uuid4())
    assert deleted == 5
    mock_client.delete.assert_called_once()


def test_delete_manual_requires_staff_and_cleans_all_stores(client, tmp_path):
    fake_db = MagicMock()
    fake_db.rpc.return_value = [
        {
            "deleted_count": 2,
            "deleted_qdrant_ids": [str(uuid4())],
            "deleted_urls": ["http://localhost:8000/api/v1/conocimiento/archivos/manual_test.pdf"],
        }
    ]

    manual_file = tmp_path / "manual_test.pdf"
    manual_file.write_bytes(b"%PDF-1.4 dummy")
    imgs_dir = tmp_path / "manual_test_imagenes"
    imgs_dir.mkdir()
    (imgs_dir / "page_1.png").write_bytes(b"png")

    # Alumno no puede eliminar
    resp_forbidden = client.delete(
        "/api/v1/conocimiento/manuales/manual_test.pdf",
        headers=_auth_header("alumno"),
    )
    assert resp_forbidden.status_code == 403

    with (
        patch("corpocmente.ui.api.routes.MANUALES_DIR", str(tmp_path)),
        patch("corpocmente.ui.api.routes.get_db", return_value=fake_db),
        patch("corpocmente.infrastructure.persistence.qdrant_rag_adapter.QdrantRAGAdapter") as mock_rag_cls,
    ):
        mock_rag = mock_rag_cls.return_value
        mock_rag.eliminar_por_manual.return_value = 2
        mock_rag.eliminar_puntos.return_value = 1

        resp = client.delete(
            "/api/v1/conocimiento/manuales/manual_test.pdf",
            headers=_auth_header("profesor"),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["qdrant_deleted"] == 2
    assert body["postgres_deleted"] == 2
    assert body["files_deleted"] >= 1
    assert not manual_file.exists()
    assert not imgs_dir.exists()
    mock_rag.eliminar_por_manual.assert_called_once_with("manual_test.pdf")
    fake_db.rpc.assert_called_once_with("admin_delete_manual_teoria", {"p_filename": "manual_test.pdf"})


def test_delete_tecnica_cascades_qdrant_pose_and_rag(client):
    tecnica_id = uuid4()
    fake_db = MagicMock()
    fake_db.rpc.return_value = True

    with (
        patch("corpocmente.ui.api.tecnicas_routes.get_db", return_value=fake_db),
        patch("corpocmente.infrastructure.persistence.qdrant_adapter.QdrantVectorAdapter") as mock_vec_cls,
        patch("corpocmente.infrastructure.persistence.qdrant_rag_adapter.QdrantRAGAdapter") as mock_rag_cls,
    ):
        resp = client.delete(
            f"/api/v1/tecnicas/{tecnica_id}",
            headers=_auth_header("profesor"),
        )

    assert resp.status_code == 204
    mock_vec_cls.return_value.eliminar_por_tecnica.assert_called_once_with(tecnica_id)
    mock_rag_cls.return_value.eliminar_por_tecnica.assert_called_once_with(str(tecnica_id))
    fake_db.rpc.assert_called_once_with("admin_delete_tecnica", {"p_tecnica_id": str(tecnica_id)})


# ---------------------------------------------------------------------------
# FASE 2: Cancelación Transaccional de Evaluaciones
# ---------------------------------------------------------------------------

def test_cancelar_evaluacion_owner_deletes_temp_video(client, tmp_path):
    eval_id = uuid4()
    owner_uid = str(uuid4())
    temp_video = tmp_path / f"alumno_{eval_id}.mp4"
    temp_video.write_bytes(b"video-data")

    fake_db = MagicMock()
    fake_db.rpc.return_value = [
        {
            "found": True,
            "authorized": True,
            "cancelled": True,
            "estado_actual": "cancelado",
            "url_video_alumno": str(temp_video),
        }
    ]

    with patch("corpocmente.ui.api.routes.get_db", return_value=fake_db):
        resp = client.post(
            f"/api/v1/evaluaciones/{eval_id}/cancelar",
            headers=_auth_header("alumno", uid=owner_uid),
        )

    assert resp.status_code == 200
    assert resp.json()["estado"] == "cancelado"
    assert resp.json()["cancelado"] is True
    assert not Path(temp_video).exists()


def test_cancelar_evaluacion_forbidden_and_not_found(client):
    eval_id = uuid4()
    fake_db = MagicMock()
    fake_db.rpc.return_value = [{"found": True, "authorized": False, "cancelled": False}]

    with patch("corpocmente.ui.api.routes.get_db", return_value=fake_db):
        resp_forbidden = client.post(
            f"/api/v1/evaluaciones/{eval_id}/cancelar",
            headers=_auth_header("alumno"),
        )
    assert resp_forbidden.status_code == 403

    fake_db.rpc.return_value = [{"found": False, "authorized": False, "cancelled": False}]
    with patch("corpocmente.ui.api.routes.get_db", return_value=fake_db):
        resp_nf = client.post(
            f"/api/v1/evaluaciones/{eval_id}/cancelar",
            headers=_auth_header("alumno"),
        )
    assert resp_nf.status_code == 404


# ---------------------------------------------------------------------------
# FASE 3: CRUD Usuarios - Eliminación por Administrador
# ---------------------------------------------------------------------------

def test_admin_delete_usuario_rbac_self_conflict_and_success(client):
    admin_uid = str(uuid4())
    target_uid = str(uuid4())

    # 1. Solo admin puede eliminar
    resp_forbidden = client.delete(
        f"/api/v1/auth/usuarios/{target_uid}",
        headers=_auth_header("profesor"),
    )
    assert resp_forbidden.status_code == 403

    # 2. Impide auto-eliminación
    resp_self = client.delete(
        f"/api/v1/auth/usuarios/{admin_uid}",
        headers=_auth_header("admin", uid=admin_uid),
    )
    assert resp_self.status_code == 400

    # 3. Conflicto 409 si profesor tiene contenido y no se reasigna
    fake_db = MagicMock()
    fake_db.rpc.return_value = [{"deleted": False, "reason": "PROFESOR_HAS_CONTENT", "reassigned_count": 3}]
    with patch("corpocmente.ui.api.auth_routes.get_db", return_value=fake_db):
        resp_conflict = client.delete(
            f"/api/v1/auth/usuarios/{target_uid}",
            headers=_auth_header("admin", uid=admin_uid),
        )
    assert resp_conflict.status_code == 409

    # 4. Eliminación exitosa con auto_reasignar=true
    fake_db.rpc.return_value = [{"deleted": True, "reason": "DELETED", "reassigned_count": 3}]
    with patch("corpocmente.ui.api.auth_routes.get_db", return_value=fake_db):
        resp_ok = client.delete(
            f"/api/v1/auth/usuarios/{target_uid}?auto_reasignar=true",
            headers=_auth_header("admin", uid=admin_uid),
        )
    assert resp_ok.status_code == 204
    fake_db.rpc.assert_called_with(
        "admin_delete_user",
        {
            "p_user_id": target_uid,
            "p_caller_id": admin_uid,
            "p_reasignar_a": admin_uid,
        },
    )
