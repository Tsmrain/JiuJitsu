import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter, VectorSearchResultDTO
from qdrant_client.models import ScoredPoint

@pytest.fixture
def mock_qdrant_client():
    client = MagicMock()
    # Simular que no existen colecciones
    mock_collection_description = MagicMock()
    mock_collection_description.name = "otras_colecciones"
    mock_collections_response = MagicMock()
    mock_collections_response.collections = [mock_collection_description]
    client.get_collections.return_value = mock_collections_response
    return client

def test_asegurar_coleccion_crea_nueva_coleccion(mock_qdrant_client):
    adapter = QdrantVectorAdapter(client=mock_qdrant_client, collection_name="vectores_jiujitsu")
    adapter.asegurar_coleccion(vector_size=133)

    mock_qdrant_client.create_collection.assert_called_once()

def test_insertar_vector_exitoso(mock_qdrant_client):
    adapter = QdrantVectorAdapter(client=mock_qdrant_client, collection_name="vectores_jiujitsu")
    vector_id = uuid4()
    vector = [0.1] * 133
    payload = {"tecnica_id": str(uuid4()), "frame_path": "/tmp/ref.jpg"}

    adapter.insertar_vector(vector_id, vector, payload)

    mock_qdrant_client.upsert.assert_called_once()

def test_buscar_similitud_pose_retorna_dto(mock_qdrant_client):
    adapter = QdrantVectorAdapter(client=mock_qdrant_client, collection_name="vectores_jiujitsu")
    tecnica_id = uuid4()
    vector_alumno = [0.5] * 133

    # Simular resultado de busqueda
    mock_scored_point = MagicMock(spec=ScoredPoint)
    mock_scored_point.score = 0.945
    mock_scored_point.payload = {
        "frame_path": "/tmp/maestro_pasaje.jpg",
        "discrepancias": ["Base de sustentación estrecha"]
    }
    mock_qdrant_client.search.return_value = [mock_scored_point]

    resultado = adapter.buscar_similitud_pose(vector_alumno, tecnica_id)

    assert isinstance(resultado, VectorSearchResultDTO)
    assert resultado.score == 94.5
    assert resultado.frame_path == "/tmp/maestro_pasaje.jpg"
    assert "Base de sustentación estrecha" in resultado.discrepancias
    mock_qdrant_client.search.assert_called_once()
