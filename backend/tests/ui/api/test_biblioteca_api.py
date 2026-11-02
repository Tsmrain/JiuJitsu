from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from uuid import uuid4

from corpocmente.main import app
from corpocmente.ui.api.auth_routes import _sign_token

client = TestClient(app)

def _auth_headers(role="alumno"):
    user_id = str(uuid4())
    token = _sign_token({
        "uid": user_id,
        "role": role,
        "email": f"{role}@test.com",
        "sucursal_id": str(uuid4())
    })
    return {"Authorization": f"Bearer {token}"}


def test_biblioteca_buscar_sin_auth_retorna_401():
    response = client.post(
        "/api/v1/conocimiento/biblioteca/buscar",
        json={"query": "armbar", "idioma": "es"}
    )
    assert response.status_code == 401


def test_biblioteca_buscar_query_vacia():
    headers = _auth_headers()
    response = client.post(
        "/api/v1/conocimiento/biblioteca/buscar",
        json={"query": "   ", "idioma": "es"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["resultados"] == []


@patch("corpocmente.infrastructure.persistence.qdrant_rag_adapter.QdrantRAGAdapter.__init__", return_value=None)
@patch("corpocmente.infrastructure.persistence.qdrant_rag_adapter.QdrantRAGAdapter.buscar_biblioteca")
@patch("corpocmente.infrastructure.ai.qwen_adapter.QwenEmbeddingAdapter.__init__", return_value=None)
@patch("corpocmente.infrastructure.ai.qwen_adapter.QwenEmbeddingAdapter.generar_embedding_texto")
def test_biblioteca_buscar_exitoso(mock_qwen_emb, mock_qwen_init, mock_rag_search, mock_rag_init):
    mock_qwen_emb.return_value = [0.1] * 2048
    mock_rag_search.return_value = [
        {
            "id": "item-1",
            "score": 0.89,
            "contenido_texto": "Keep your elbow tight on the armbar.",
            "media_url": "/api/v1/conocimiento/media/paginas/Jiu-Jitsu-University/pagina_555.jpg",
            "media_path": "/tmp/pagina_555.jpg",
            "pagina": 555,
            "fuente_nombre": "Jiu-Jitsu University.pdf",
            "cita": "Jiu-Jitsu University.pdf, p. 555"
        }
    ]

    headers = _auth_headers()
    response = client.post(
        "/api/v1/conocimiento/biblioteca/buscar",
        json={"query": "armbar", "idioma": "es", "limit": 5},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "armbar"
    assert data["total"] == 1
    assert len(data["resultados"]) == 1
    res = data["resultados"][0]
    assert res["pagina"] == 555
    assert "/pagina_555.jpg" in res["media_url"]
    assert "Keep your elbow tight" in res["contenido_texto"]


def test_listar_manuales_sin_auth_retorna_401():
    response = client.get("/api/v1/conocimiento/manuales")
    assert response.status_code == 401


def test_listar_manuales_autenticado_retorna_lista():
    headers = _auth_headers()
    response = client.get("/api/v1/conocimiento/manuales", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "Jiu-Jitsu University.pdf" in data


def test_servir_manual_sin_auth_retorna_401():
    response = client.get("/api/v1/conocimiento/manuales/Jiu-Jitsu%20University.pdf")
    assert response.status_code == 401


def test_servir_manual_autenticado_stream_pdf():
    headers = _auth_headers()
    response = client.get("/api/v1/conocimiento/manuales/Jiu-Jitsu%20University.pdf", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "inline" in response.headers.get("content-disposition", "")


def test_servir_manual_con_query_token():
    user_id = str(uuid4())
    token = _sign_token({"uid": user_id, "role": "alumno", "email": "a@test.com", "sucursal_id": str(uuid4())})
    response = client.get(f"/api/v1/conocimiento/manuales/Jiu-Jitsu%20University.pdf?token={token}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_servir_manual_inexistente_retorna_404():
    headers = _auth_headers()
    response = client.get("/api/v1/conocimiento/manuales/LibroQueNoExiste.pdf", headers=headers)
    assert response.status_code == 404


@patch("corpocmente.infrastructure.persistence.qdrant_rag_adapter.QdrantRAGAdapter.__init__", return_value=None)
@patch("corpocmente.infrastructure.persistence.qdrant_rag_adapter.QdrantRAGAdapter.buscar_biblioteca")
@patch("corpocmente.infrastructure.ai.qwen_adapter.QwenEmbeddingAdapter.__init__", return_value=None)
@patch("corpocmente.infrastructure.ai.qwen_adapter.QwenEmbeddingAdapter.generar_embedding_texto")
def test_biblioteca_query_rewriting_cognitivo(mock_qwen_emb, mock_qwen_init, mock_rag_search, mock_rag_init):
    mock_qwen_emb.return_value = [0.1] * 2048
    mock_rag_search.return_value = []

    headers = _auth_headers()
    response = client.post(
        "/api/v1/conocimiento/biblioteca/buscar",
        json={"query": "defensa de llave de brazo", "idioma": "es"},
        headers=headers
    )
    assert response.status_code == 200
    # Verifica que el embedding se genero usando la query expandida
    mock_qwen_emb.assert_called_once()
    called_query = mock_qwen_emb.call_args[0][0]
    assert "defensa" in called_query.lower()
    assert any(term in called_query.lower() for term in ["escape", "survive", "defend"])


@patch("corpocmente.infrastructure.persistence.qdrant_rag_adapter.QdrantRAGAdapter.__init__", return_value=None)
@patch("corpocmente.infrastructure.persistence.qdrant_rag_adapter.QdrantRAGAdapter.buscar_biblioteca_multimodal")
@patch("corpocmente.infrastructure.ai.qwen_adapter.QwenEmbeddingAdapter.__init__", return_value=None)
@patch("corpocmente.infrastructure.ai.qwen_adapter.QwenEmbeddingAdapter.generar_embedding_texto")
@patch("corpocmente.infrastructure.ai.qwen_adapter.QwenEmbeddingAdapter.generar_embedding_imagen")
def test_biblioteca_buscar_multimodal_con_imagen(mock_qwen_img, mock_qwen_txt, mock_qwen_init, mock_rag_search_multi, mock_rag_init, tmp_path):
    mock_qwen_txt.return_value = [0.1] * 2048
    mock_qwen_img.return_value = [0.2] * 2048
    mock_rag_search_multi.return_value = [
        {
            "id": "item-multi-1",
            "score": 0.95,
            "contenido_texto": "Defensa visual de llave de brazo desde la guardia.",
            "media_url": "/api/v1/conocimiento/media/paginas/Jiu-Jitsu-University/pagina_137.jpg",
            "pagina": 137,
            "fuente_nombre": "Jiu-Jitsu University.pdf",
            "cita": "Jiu-Jitsu University.pdf, p. 137"
        }
    ]

    # Crear frame dummy en /tmp/corpocmente_frames
    import os
    frames_dir = Path("/tmp/corpocmente_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    dummy_frame = frames_dir / "critico_dummy_test.jpg"
    with open(dummy_frame, "wb") as f:
        f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00")

    headers = _auth_headers()
    response = client.post(
        "/api/v1/conocimiento/biblioteca/buscar",
        json={
            "query": "escape de montada",
            "idioma": "es",
            "imagen_url": "/static/frames/critico_dummy_test.jpg",
            "limit": 5
        },
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["busqueda_multimodal"] is True
    assert data["imagen_procesada"] is not None
    assert "critico_dummy_test.jpg" in data["imagen_procesada"]
    assert data["total"] == 1
    assert data["resultados"][0]["id"] == "item-multi-1"
    mock_qwen_img.assert_called_once()
    mock_rag_search_multi.assert_called_once()


