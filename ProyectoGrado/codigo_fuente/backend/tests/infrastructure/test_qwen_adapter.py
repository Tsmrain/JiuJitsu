import pytest
from corpocmente.infrastructure.ai.adapters import QwenRerankerAdapter

def test_qwen_reranker_adapter_init():
    adapter = QwenRerankerAdapter()
    assert adapter.model_name == "Qwen/Qwen3-VL-Reranker-2B"

def test_qwen_reranker_rerank_frames_exitoso():
    adapter = QwenRerankerAdapter()
    candidatos = ["/tmp/frame_01.jpg", "/tmp/frame_02.jpg", "/tmp/frame_03.jpg"]
    video_alumno = "/tmp/video_alumno.mp4"
    
    frame_seleccionado = adapter.rerank_frames(candidatos, video_alumno)
    assert frame_seleccionado == candidatos[0]

def test_qwen_reranker_candidatos_vacios():
    adapter = QwenRerankerAdapter()
    with pytest.raises(ValueError, match="La lista de fotogramas candidatos para el Re-ranking está vacía."):
        adapter.rerank_frames([], "/tmp/video_alumno.mp4")
