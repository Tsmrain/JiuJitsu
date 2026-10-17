import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from fastapi import BackgroundTasks, HTTPException

from corpocmente.domain.biomechanics.dtw_comparator import (
    comparar_secuencias_con_dtw,
    resumen_alineacion,
    detectar_articulaciones_criticas,
)
from corpocmente.application.services.video_comparison_service import (
    crear_comparacion,
    obtener_comparacion,
    rutas_comparacion,
)
from corpocmente.application.services.rag_video_ingestion import (
    _mime_for_image,
    _validar_embedding_data,
)


def test_dtw_comparator_alineacion_completa():
    # Dos secuencias simples de 10 frames con 17 keypoints (51 dims)
    seq_m = [[float(i) * 0.1] * 51 for i in range(10)]
    seq_a = [[float(i) * 0.1] * 51 for i in range(10)]

    res = comparar_secuencias_con_dtw(seq_m, seq_a)

    assert "dtw_distance" in res
    assert "score_similitud" in res
    assert "alineacion" in res
    assert res["score_similitud"] == 100.0
    assert len(res["alineacion"]) >= 10
    assert "frame_maestro_idx" in res["alineacion"][0]
    assert "frame_alumno_idx" in res["alineacion"][0]
    assert "similitud_frame" in res["alineacion"][0]


def test_resumen_alineacion():
    alineacion = [{"frame_maestro_idx": i, "frame_alumno_idx": i, "video_idx": i} for i in range(300)]
    reducida = resumen_alineacion(alineacion, max_items=50)
    assert len(reducida) <= 50
    assert reducida[0]["frame_maestro_idx"] == 0
    assert reducida[-1]["frame_maestro_idx"] == 299
    assert reducida[-1]["video_idx"] == 299


def test_detectar_articulaciones_criticas():
    vec_m = [100.0, 100.0, 0.9] * 17
    vec_a = [100.0, 100.0, 0.9] * 17

    # Discrepancia grande en hombro izquierdo (joint 5)
    vec_a[5 * 3] = 200.0
    vec_a[5 * 3 + 1] = 200.0

    arts = detectar_articulaciones_criticas(vec_m, vec_a, top_k=3)
    assert 5 in arts


def test_mime_for_image():
    assert _mime_for_image(Path("frame.jpg")) == "image/jpeg"
    assert _mime_for_image(Path("frame.png")) == "image/png"
    assert _mime_for_image(Path("frame.webp")) == "image/webp"


def test_validar_embedding_data():
    valid = {
        "embeddings": [[0.1] * 2048, [0.2] * 2048],
        "chunks": ["A", "B"],
    }
    _validar_embedding_data(valid, esperado=2)

    with pytest.raises(ValueError):
        _validar_embedding_data({"embeddings": [[0.1] * 100], "chunks": ["A"]}, esperado=1)


def test_rutas_comparacion():
    alumno, maestro, out = rutas_comparacion("test-uuid")
    assert str(alumno).endswith("test-uuid_alumno.mp4")
    assert str(maestro).endswith("test-uuid_maestro.mp4")
    assert str(out).endswith("test-uuid_comparacion.mp4")


def test_crear_y_obtener_comparacion_memoria(monkeypatch):
    from corpocmente.application.services import video_comparison_service as service
    monkeypatch.setattr(service, "_db", lambda: (_ for _ in ()).throw(ConnectionError("PostgREST no está activo")))
    cid = crear_comparacion(
        tecnica_id="tecnica-123",
        idioma="es",
        persona_idx_alumno=0,
        persona_idx_maestro=0,
    )
    assert cid is not None
    data = obtener_comparacion(cid)
    assert data is not None
    assert data["id"] == cid
    assert data["estado"] == "procesando"


def test_api_comparaciones_endpoints(monkeypatch):
    from corpocmente.application.services import video_comparison_service as service
    from corpocmente.api.routes import comparaciones as routes
    monkeypatch.setattr(service, "_db", lambda: (_ for _ in ()).throw(ConnectionError("PostgREST no está activo")))
    monkeypatch.setattr(routes, "require_auth", lambda _token: {"uid": "test-user", "role": "alumno"})

    class FakeUpload:
        def __init__(self, filename):
            self.filename = filename
            self.content = b"\x00" * 1024
            self.offset = 0

        async def read(self, size):
            chunk = self.content[self.offset:self.offset + size]
            self.offset += len(chunk)
            return chunk

    import asyncio

    with pytest.raises(HTTPException) as invalid:
        asyncio.run(routes.comparar_video_a_video(
            BackgroundTasks(), FakeUpload("test.txt"), FakeUpload("maestro.mp4"), authorization="Bearer test-token"
        ))
    assert invalid.value.status_code == 415

    with patch.object(routes, "procesar_comparacion_video_a_video"):
        body = asyncio.run(routes.comparar_video_a_video(
            BackgroundTasks(), FakeUpload("alumno.mp4"), FakeUpload("maestro.mp4"),
            video_maestro_nombre="Mestre Mike — Escape de guardia",
            authorization="Bearer test-token",
        ))
        assert "comparacion_id" in body
        assert body["estado"] == "procesando"
        cid = body["comparacion_id"]
        status_data = asyncio.run(routes.leer_comparacion(cid, authorization="Bearer test-token"))
        assert status_data["id"] == cid
        assert status_data["video_alumno_nombre"] == "alumno.mp4"
        assert status_data["video_maestro_nombre"] == "Mestre Mike — Escape de guardia"
        with pytest.raises(HTTPException) as not_ready:
            asyncio.run(routes.descargar_video_comparacion(cid, authorization="Bearer test-token"))
        assert not_ready.value.status_code == 409


def test_dtw_mapea_frame_indices_reales():
    # Maestro sampled every 10 frames: [0, 10, 20]
    # Alumno sampled every 5 frames: [100, 105, 110]
    seq_m = [[0.1] * 51, [0.2] * 51, [0.3] * 51]
    seq_a = [[0.1] * 51, [0.2] * 51, [0.3] * 51]
    frame_idxs_m = [0, 10, 20]
    frame_idxs_a = [100, 105, 110]

    res = comparar_secuencias_con_dtw(
        secuencia_maestro=seq_m,
        secuencia_alumno=seq_a,
        frame_idxs_maestro=frame_idxs_m,
        frame_idxs_alumno=frame_idxs_a,
    )

    assert "alineacion" in res
    assert len(res["alineacion"]) >= 3
    primer_paso = res["alineacion"][0]

    # seq_idx es el paso en el array
    assert primer_paso["seq_maestro_idx"] == 0
    assert primer_paso["seq_alumno_idx"] == 0

    # frame_idx es el fotograma real del video original
    assert primer_paso["frame_maestro_idx"] == 0
    assert primer_paso["frame_alumno_idx"] == 100

    ultimo_paso = res["alineacion"][-1]
    assert ultimo_paso["frame_maestro_idx"] == 20
    assert ultimo_paso["frame_alumno_idx"] == 110


def test_dtw_rechaza_indices_reales_con_longitud_incorrecta():
    with pytest.raises(ValueError, match="frame_idxs_maestro"):
        comparar_secuencias_con_dtw(
            secuencia_maestro=[[0.1] * 51, [0.2] * 51],
            secuencia_alumno=[[0.1] * 51],
            frame_idxs_maestro=[10],
        )


def test_servir_frame_rag_endpoints_seguridad():
    import asyncio
    from corpocmente.ui.api.routes import servir_frame_rag_conocimiento
    from corpocmente.ui.api.tecnicas_routes import servir_frame_rag_tecnica

    for call in (
        lambda: servir_frame_rag_conocimiento("tecnica-uuid", "../../etc/passwd"),
        lambda: servir_frame_rag_tecnica("../hack", "frame_000001.jpg"),
        lambda: servir_frame_rag_conocimiento("fake-uuid", "no_existe.jpg"),
    ):
        with pytest.raises(HTTPException):
            asyncio.run(call())
