from io import BytesIO
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PIL import Image

from corpocmente.ui.api import routes as knowledge_routes


def test_subir_imagen_global_la_guarda_y_la_indexa_en_qdrant(monkeypatch):
    image = Image.new("RGB", (2, 2), color=(20, 40, 60))
    image_buffer = BytesIO()
    image.save(image_buffer, format="PNG")
    calls = {}

    monkeypatch.setattr(knowledge_routes, "require_auth", lambda _token: {
        "uid": "a0f2f77c-e9d3-42d8-9d53-b48c6d06d301",
        "role": "profesor",
        "sucursal_id": None,
    })
    monkeypatch.setattr(knowledge_routes.settings, "COLAB_TUNNEL_URL", "https://worker.test")

    response_from_worker = MagicMock()
    response_from_worker.status_code = 200
    response_from_worker.json.return_value = {
        "chunks": ["Imagen: agarre.png"],
        "embeddings": [[0.1] * 2048],
    }
    response_from_worker.raise_for_status.return_value = None
    monkeypatch.setattr(knowledge_routes.requests, "post", lambda *args, **kwargs: response_from_worker)

    class FakeIngestUseCase:
        def execute(self, **kwargs):
            calls.update(kwargs)
            return SimpleNamespace(chunks_procesados=1)

    monkeypatch.setattr(knowledge_routes, "IngestKnowledgeUseCase", FakeIngestUseCase)

    class FakeUpload:
        filename = "agarre.png"

        async def read(self, _limit):
            return image_buffer.getvalue()

    import asyncio

    background_tasks = knowledge_routes.BackgroundTasks()
    body = asyncio.run(knowledge_routes.ingerir_archivo_teoria(
        request=SimpleNamespace(base_url="http://localhost/"),
        background_tasks=background_tasks,
        archivo=FakeUpload(),
        alcance="global",
        fuente_nombre="Guía visual de agarres",
        authorization="Bearer fake",
    ))
    assert body.status_code == 202
    task = background_tasks.tasks[0]
    task.func(*task.args, **task.kwargs)
    body = knowledge_routes._knowledge_jobs[json.loads(body.body)["job_id"]]

    assert body["estado"] == "completado"
    assert body["avance"] == 100
    assert body["imagenes_indexadas"] == 1
    assert body["chunks_procesados"] == 1
    assert calls["alcance"] == "global"
    assert calls["metadata_por_chunk"][0]["modalidad"] == "multimodal"
    assert calls["metadata_por_chunk"][0]["media_path"].endswith(".png")
    assert calls["metadata_por_chunk"][0]["media_url"].startswith("/api/v1/conocimiento/media/imagenes/")
    assert len(calls["metadata_por_chunk"][0]["imagen_hash"]) == 64
    assert len(calls["embedding_data"]["embeddings"][0]) == 2048


def test_servir_imagen_conocimiento_restringe_path_traversal(monkeypatch, tmp_path):
    import asyncio
    from fastapi import HTTPException

    monkeypatch.setattr(knowledge_routes, "require_auth", lambda _token: {"uid": "user", "role": "alumno"})
    monkeypatch.setattr(knowledge_routes, "MANUALES_DIR", tmp_path / "manuales")
    root = tmp_path / "manuales"
    root.mkdir()
    (root / "safe.png").write_bytes(b"safe")

    response = asyncio.run(knowledge_routes.servir_imagen_conocimiento("safe.png", "Bearer fake"))
    assert response.path.name == "safe.png"
    with pytest.raises(HTTPException) as traversal:
        asyncio.run(knowledge_routes.servir_imagen_conocimiento("../../outside.png", "Bearer fake"))
    assert traversal.value.status_code == 400
