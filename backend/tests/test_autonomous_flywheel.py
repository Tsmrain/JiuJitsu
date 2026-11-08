import os
import time
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch, MagicMock

from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.ui.api.tecnicas_routes import entrenar_y_actualizar_modelo_autonomo


def test_hot_swap_carga_y_recarga_modelo_autonomo(tmp_path):
    """
    Verifica que YOLOPoseAdapter._get_model() detecte yolo26n_autonomous.pt,
    lo cargue en memoria (Hot-Swap) y lo recargue automáticamente si cambia su mtime en disco.
    """
    repo_root = Path(__file__).resolve().parents[2]
    autonomous_file = repo_root / "yolo26n_autonomous.pt"

    adapter = YOLOPoseAdapter()

    with patch("ultralytics.YOLO") as mock_yolo_cls:
        mock_instance_1 = MagicMock()
        mock_instance_2 = MagicMock()
        mock_yolo_cls.side_effect = [mock_instance_1, mock_instance_2]

        # Crear archivo autónomo simulado si no existe aún
        created_temp = False
        if not autonomous_file.exists():
            autonomous_file.write_bytes(b"fake_weights_v1" * 100)
            created_temp = True

        try:
            # 1. Primera llamada: debe hacer Hot-Swap hacia yolo26n_autonomous.pt
            m1 = adapter._get_model()
            assert m1 is mock_instance_1
            assert getattr(m1, "path", "") == str(autonomous_path := autonomous_file)
            assert mock_yolo_cls.call_count == 1

            # 2. Segunda llamada sin cambios en disco: debe reutilizar caché en memoria
            m1_cached = adapter._get_model()
            assert m1_cached is mock_instance_1
            assert mock_yolo_cls.call_count == 1

            # 3. Simular que autonomous_flywheel.py promueve un nuevo modelo (actualiza mtime)
            new_mtime = autonomous_file.stat().st_mtime + 10.0
            os.utime(autonomous_file, (new_mtime, new_mtime))

            m2 = adapter._get_model()
            assert m2 is mock_instance_2
            assert mock_yolo_cls.call_count == 2
        finally:
            if created_temp and autonomous_file.exists():
                autonomous_file.unlink()


def test_entrenar_y_actualizar_modelo_autonomo_lanza_popen_desacoplado(tmp_path):
    """
    Verifica que entrenar_y_actualizar_modelo_autonomo copie el video a una ruta segura
    y lance subprocess.Popen con start_new_session=True sin bloquear FastAPI.
    """
    video_prueba = tmp_path / "profesor_americana.mov"
    # Crear archivo > 10 KB para simular un video real
    video_prueba.write_bytes(b"0" * 25_000)
    tecnica_id = str(uuid4())

    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        mock_popen.return_value = mock_proc

        pid = entrenar_y_actualizar_modelo_autonomo(str(video_prueba), tecnica_id)

        assert pid == 99999
        assert mock_popen.called
        args, kwargs = mock_popen.call_args
        cmd_list = args[0]
        assert "autonomous_flywheel.py" in cmd_list[1]
        assert tecnica_id == cmd_list[3]
        assert kwargs.get("start_new_session") is True

