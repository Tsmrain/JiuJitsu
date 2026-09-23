import pytest
from unittest.mock import patch, MagicMock
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.domain.entities.models import EsqueletoBiomecanico
import os

@patch("corpocmente.infrastructure.ai.adapters.os.path.exists")
@patch("corpocmente.infrastructure.ai.adapters.YOLO")
def test_yolo_pose_adapter_extraer_keypoints_success(mock_yolo_class, mock_exists):
    # Simular que el archivo de video existe
    mock_exists.return_value = True

    # Configurar el mock del modelo YOLO
    mock_model_instance = MagicMock()
    mock_yolo_class.return_value = mock_model_instance

    # Crear una respuesta simulada (mock) de YOLO
    mock_result = MagicMock()
    # Simular data de keypoints con forma (1, 17, 3) aplanado a 51 elementos.
    mock_result.keypoints.data = [MagicMock()]
    mock_result.keypoints.data[0].flatten.return_value.tolist.return_value = [0.5] * 51

    # Que predict devuelva una lista con 2 frames/resultados
    mock_model_instance.predict.return_value = [mock_result, mock_result]

    # Instanciar el adaptador y llamar al método
    adapter = YOLOPoseAdapter(model_path="dummy_model.pt")
    esqueletos = adapter.extraer_keypoints("dummy_video.mp4")

    # Aserciones
    assert len(esqueletos) == 2
    assert isinstance(esqueletos[0], EsqueletoBiomecanico)
    
    # Verificar que el padding a 133 funcionó
    assert len(esqueletos[0].keypoints133) == 133
    assert esqueletos[0].keypoints133[0] == 0.5  # Dato real simulado
    assert esqueletos[0].keypoints133[132] == 0.0 # Dato rellenado (padding)

    mock_model_instance.predict.assert_called_once_with(source="dummy_video.mp4", stream=True, verbose=False)

@patch("corpocmente.infrastructure.ai.adapters.os.path.exists")
@patch("corpocmente.infrastructure.ai.adapters.YOLO")
def test_yolo_pose_adapter_extraer_keypoints_file_not_found(mock_yolo_class, mock_exists):
    mock_exists.return_value = False
    
    mock_yolo_class.return_value = MagicMock()
    adapter = YOLOPoseAdapter(model_path="dummy_model.pt")
    
    with pytest.raises(FileNotFoundError):
        adapter.extraer_keypoints("missing_video.mp4")
