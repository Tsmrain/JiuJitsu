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

def test_recuperar_contexto_rag_exitoso():
    from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
    import uuid
    from unittest.mock import MagicMock
    
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.payload = {"contenido_texto": "El Jiu-Jitsu es un arte marcial..."}
    mock_client.search.return_value = [mock_result]
    
    adapter = QdrantVectorAdapter(client=mock_client)
    tecnica_id = uuid.uuid4()
    
    # Act
    texto = adapter.recuperar_contexto_rag([0.5]*2048, tecnica_id)
    
    # Assert
    assert texto == "El Jiu-Jitsu es un arte marcial..."
    mock_client.search.assert_called_once()

def test_recuperar_contexto_rag_usa_named_vector_y_concatena():
    """
    Regression test C11.4: recuperar_contexto_rag debe:
    1. Usar query_vector=("dense", vector) — named vector de la colección rag_knowledge.
    2. Solicitar limit=3 (top-3).
    3. Concatenar los chunks con el separador '\n\n---\n\n'.
    """
    from unittest.mock import MagicMock
    import uuid

    mock_client = MagicMock()
    # Simular 3 resultados con contenido
    r1 = MagicMock(); r1.payload = {"contenido_texto": "Chunk A sobre control de cadera."}
    r2 = MagicMock(); r2.payload = {"contenido_texto": "Chunk B sobre agarre del brazo."}
    r3 = MagicMock(); r3.payload = {"contenido_texto": "Chunk C sobre peso del cuerpo."}
    mock_client.search.return_value = [r1, r2, r3]

    adapter = QdrantVectorAdapter(client=mock_client)
    tecnica_id = uuid.uuid4()

    # Act
    texto = adapter.recuperar_contexto_rag([0.5] * 2048, tecnica_id)

    # Assert
    # 1. Debe llamar con named vector ("dense", ...) y limit=3
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["query_vector"] == ("dense", [0.5] * 2048), \
        "Debe usar named vector ('dense', vector) — fix C11.4"
    assert call_kwargs["limit"] == 3, "Debe solicitar top-3 (fix C11.4)"
    assert call_kwargs["collection_name"] == "rag_knowledge"

    # 2. Debe concatenar los 3 chunks
    assert "Chunk A" in texto
    assert "Chunk B" in texto
    assert "Chunk C" in texto
    assert "\n\n---\n\n" in texto, "Debe usar el separador '---' entre chunks"

