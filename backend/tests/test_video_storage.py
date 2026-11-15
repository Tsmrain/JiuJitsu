from pathlib import Path
from unittest.mock import MagicMock

from corpocmente.infrastructure.persistence import video_storage


def test_resolver_video_estatico_retorna_none_si_archivo_no_existe(tmp_path, monkeypatch):
    monkeypatch.setattr(video_storage, "VIDEOS_DIR", str(tmp_path / "videos"))
    monkeypatch.setattr(video_storage, "PERSISTENT_REF_VIDEOS_DIR", tmp_path / "persist")
    monkeypatch.setattr(video_storage, "REPO_ROOT", tmp_path / "empty_root")

    res = video_storage.resolver_video_estatico(
        "/tmp/corpocmente_videos/no_existe_1234.mp4",
        es_referencia=True,
        tecnica_id="00000000-0000-0000-0000-000000000001",
        tecnica_nombre="Técnica Inexistente",
    )
    assert res is None


def test_persistir_video_referencia_copia_con_uuid_a_videos_dir(tmp_path, monkeypatch):
    videos_dir = tmp_path / "videos"
    persist_dir = tmp_path / "persist"
    monkeypatch.setattr(video_storage, "VIDEOS_DIR", str(videos_dir))
    monkeypatch.setattr(video_storage, "PERSISTENT_REF_VIDEOS_DIR", persist_dir)

    src = tmp_path / "origen.mov"
    src.write_bytes(b"\x00" * 2048)

    canonical_path = video_storage.persistir_video_referencia(str(src))
    assert canonical_path.startswith(str(videos_dir))
    assert canonical_path.endswith(".mov")
    assert Path(canonical_path).is_file()
    assert (persist_dir / Path(canonical_path).name).is_file()


def test_autocuracion_desde_raiz_copia_a_videos_dir_y_actualiza_bd(tmp_path, monkeypatch):
    videos_dir = tmp_path / "videos"
    persist_dir = tmp_path / "persist"
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    maestro = repo_root / "MaestroAmericana.mov"
    maestro.write_bytes(b"MOVDATA" * 400)

    monkeypatch.setattr(video_storage, "VIDEOS_DIR", str(videos_dir))
    monkeypatch.setattr(video_storage, "PERSISTENT_REF_VIDEOS_DIR", persist_dir)
    monkeypatch.setattr(video_storage, "REPO_ROOT", repo_root)

    mock_db = MagicMock()
    url = video_storage.resolver_video_estatico(
        "/tmp/corpocmente_videos/archivo_perdido.mp4",
        es_referencia=True,
        tecnica_id="5f4566e0-44a8-4cf7-ab1b-341076c50098",
        tecnica_nombre="Americana Desde La Montada",
        profesor_id="7e455a7d-cbc8-4190-9a10-3b959f6425fc",
        db=mock_db,
    )

    assert url is not None
    assert url.startswith("/static/videos/")
    assert url.endswith(".mov")
    copied_name = Path(url).name
    assert (videos_dir / copied_name).is_file()
    mock_db.rpc.assert_called_once()
    rpc_name, rpc_params = mock_db.rpc.call_args[0]
    assert rpc_name == "admin_save_video_referencia"
    assert rpc_params["p_url_video"] == str(videos_dir / copied_name)
