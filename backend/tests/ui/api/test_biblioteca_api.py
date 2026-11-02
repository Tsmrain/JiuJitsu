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
