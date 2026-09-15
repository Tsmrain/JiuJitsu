# tests/test_rag_real.py
"""Pruebas Unitarias TDD para Subsistema RAG con Qwen3-VL-Embedding (2048d) y Qdrant Local.

Verifica:
1. Dimensión canónica estricta de 2048 floats en QwenEmbeddingAdapter.
2. Contrato IEmbeddingService y alias generate_embedding.
3. Generación en lote (batch) de embeddings de 2048 dimensiones.
4. ChunkerSemanticoBJJ encapsulando langchain_text_splitters (1000/200).
5. ConfiguracionRAG como Experto en Información inyectado en repositorios.
6. Integración con QdrantAdapter Local (colección bjj_knowledge).
"""

from unittest.mock import MagicMock, patch
import pytest
from src.domain.models import ConfiguracionRAG, FuenteConocimiento
from src.services.chunker_semantico import ChunkerSemanticoBJJ
from src.infrastructure.adapters.qwen_embedding_adapter import QwenEmbeddingAdapter
from src.infrastructure.persistence import PostgresFuenteConocimientoRepository
from src.infrastructure.persistence.rag_ingestion import PipelineIngestaRAG


class TestQwenEmbeddingAdapter:
    """Valida el adaptador para Qwen3-VL-Embedding-2B (2048 dimensiones)."""

    def test_generar_embedding_dimension_2048(self):
        adapter = QwenEmbeddingAdapter()
        resultado = adapter.generar_embedding("escape de guardia cerrada")
        assert len(resultado) == 2048

    def test_generate_embedding_alias_contrato(self):
        adapter = QwenEmbeddingAdapter()
        vec = adapter.generate_embedding("armbar biomecánica")
        assert len(vec) == 2048

    def test_generar_embeddings_batch_dimensiones_y_longitud(self):
        adapter = QwenEmbeddingAdapter()
        textos = ["Técnica 1", "Técnica 2", "Técnica 3"]
        vectores = adapter.generar_embeddings_batch(textos)
        assert len(vectores) == 3
        for v in vectores:
            assert len(v) == 2048

    def test_generar_embeddings_batch_textos_vacios_retorna_vacio(self):
        adapter = QwenEmbeddingAdapter()
        assert adapter.generar_embeddings_batch([]) == []

    def test_llamar_colab_remoto_mock(self):
        adapter = QwenEmbeddingAdapter()
        adapter.colab_url = "https://mock-colab-tunnel.ngrok.io"
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"embeddings": [[0.02] * 2048, [0.03] * 2048]}
            mock_post.return_value = mock_resp

            vectores = adapter.generar_embeddings_batch(["chunk 1", "chunk 2"])
            assert len(vectores) == 2
            assert len(vectores[0]) == 2048
            assert mock_post.called


class TestChunkerSemanticoBJJ:
    """Valida que el fragmentador encapsule la implementación oficial de LangChain."""

    def test_chunker_utiliza_langchain_recursive_splitter(self):
        chunker = ChunkerSemanticoBJJ(chunk_size=1000, chunk_overlap=200)
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        assert isinstance(chunker._splitter, RecursiveCharacterTextSplitter)

    def test_chunker_fragmenta_texto_extenso_respetando_solapamiento(self):
        chunker = ChunkerSemanticoBJJ(chunk_size=500, chunk_overlap=100)
        parrafos = [f"Párrafo de biomecánica BJJ número {i}. " * 15 for i in range(1, 10)]
        texto_completo = "\n\n".join(parrafos)

        chunks = chunker.fragmentar(texto_completo)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 600  # Margen por separadores semánticos

    def test_chunker_retorna_vacio_si_texto_nulo_o_blancos(self):
        chunker = ChunkerSemanticoBJJ()
        assert chunker.fragmentar("") == []
        assert chunker.fragmentar("   \n\t  ") == []


class TestConfiguracionRAGYPersistencia:
    """Valida el patrón Experto en Información para umbrales RAG y delegación a Qdrant."""

    def test_configuracion_rag_valores_por_defecto_y_congelada(self):
        cfg = ConfiguracionRAG()
        assert cfg.umbral_similitud_minima == 0.65
        assert cfg.top_k_resultados == 3

        # Inmutabilidad (frozen dataclass)
        with pytest.raises(Exception):
            cfg.umbral_similitud_minima = 0.75  # type: ignore

    def test_inyeccion_configuracion_rag_en_repositorio_postgres_y_delegacion_qdrant(self):
        """Verifica que el repositorio recibe ConfiguracionRAG y delega la búsqueda a Qdrant."""
        mock_conn = MagicMock()
        mock_qdrant = MagicMock()
        mock_qdrant.buscar.return_value = [
            {
                "id_fuente": "f1",
                "id_tecnica": "armbar",
                "titulo": "Guía Armbar",
                "tipo_recurso": "Manual",
                "chunk_texto": "Texto del armbar",
                "similitud": 0.89,
            }
        ]

        config_instructor = ConfiguracionRAG(umbral_similitud_minima=0.72, top_k_resultados=5)
        repo = PostgresFuenteConocimientoRepository(
            db_connection=mock_conn,
            config_rag=config_instructor,
            qdrant_adapter=mock_qdrant,
        )

        embedding_consulta = [0.02] * 2048
        resultados = repo.buscar_contexto(embedding_consulta)

        assert len(resultados) == 1
        assert resultados[0].id_fuente == "f1"
        assert resultados[0].similitud == 0.89
        assert mock_qdrant.buscar.called
        _, kwargs = mock_qdrant.buscar.call_args
        # Verificar que el umbral usado es 0.72 inyectado, NO 0.65 hardcodeado
        assert kwargs["umbral_similitud"] == 0.72
        assert kwargs["limite"] == 5

    def test_buscar_contexto_con_filtro_id_tecnica_en_qdrant(self):
        mock_conn = MagicMock()
        mock_qdrant = MagicMock()
        mock_qdrant.buscar.return_value = []

        config_custom = ConfiguracionRAG(umbral_similitud_minima=0.80, top_k_resultados=2)
        repo = PostgresFuenteConocimientoRepository(
            db_connection=mock_conn,
            config_rag=config_custom,
            qdrant_adapter=mock_qdrant,
        )

        embedding_consulta = [0.03] * 2048
        repo.buscar_contexto(embedding_consulta, id_tecnica="kimura_guardia")

        assert mock_qdrant.buscar.called
        _, kwargs = mock_qdrant.buscar.call_args
        assert kwargs["id_tecnica"] == "kimura_guardia"
        assert kwargs["umbral_similitud"] == 0.80
        assert kwargs["limite"] == 2


class TestQdrantAdapterLocal:
    """Valida la persistencia vectorial en Qdrant Local corriendo en http://localhost:6333."""

    @pytest.fixture(autouse=True)
    def verificar_qdrant(self):
        import urllib.request
        try:
            req = urllib.request.urlopen("http://localhost:6333/collections", timeout=2)
            if req.status != 200:
                pytest.skip("Qdrant local no está disponible en http://localhost:6333")
        except Exception:
            pytest.skip("Qdrant local no está disponible en http://localhost:6333")

    def test_creacion_automatica_coleccion_2048_cosine(self):
        from src.infrastructure.adapters.qdrant_adapter import QdrantAdapter
        adapter = QdrantAdapter(url="http://localhost:6333", collection_name="bjj_knowledge_test")
        adapter.asegurar_coleccion()

        # Verificar que la colección existe en Qdrant y sus parámetros son 2048 y Cosine
        info = adapter._client.get_collection("bjj_knowledge_test")
        assert info is not None
        vectors_cfg = info.config.params.vectors
        # vectors_cfg puede ser VectorParams o dict
        size = getattr(vectors_cfg, "size", None) or vectors_cfg.get("size")
        assert size == 2048

    def test_indexacion_y_busqueda_con_umbral_75_y_filtro_tecnica(self):
        from src.infrastructure.adapters.qdrant_adapter import QdrantAdapter
        adapter = QdrantAdapter(url="http://localhost:6333", collection_name="bjj_knowledge_test")
        adapter.asegurar_coleccion()

        # Insertar dos vectores de 2048d
        vec_armbar = [0.1] * 2048
        adapter.upsert(
            id_fuente="fuente_armbar_qdrant",
            vector=vec_armbar,
            payload={
                "id_fuente": "fuente_armbar_qdrant",
                "titulo": "Armbar desde la Guardia Cerrada",
                "chunk_texto": "Asegura la muñeca del rival contra tu pecho.",
                "id_tecnica": "armbar_guardia",
            },
        )

        vec_triangulo = [-0.1] * 1024 + [0.1] * 1024
        adapter.upsert(
            id_fuente="fuente_triangulo_qdrant",
            vector=vec_triangulo,
            payload={
                "id_fuente": "fuente_triangulo_qdrant",
                "titulo": "Triángulo desde la Guardia",
                "chunk_texto": "Pasa la pierna sobre el hombro y bloquea el cuello.",
                "id_tecnica": "triangulo_guardia",
            },
        )

        # 1. Búsqueda con vector similar y umbral >= 0.75
        resultados = adapter.buscar(
            consulta_embedding=vec_armbar,
            limite=3,
            umbral_similitud=0.75,
            id_tecnica="armbar_guardia",
        )

        assert len(resultados) >= 1
        mejor = resultados[0]
        assert mejor["id_fuente"] == "fuente_armbar_qdrant"
        assert mejor["titulo"] == "Armbar desde la Guardia Cerrada"
        assert mejor["similitud"] >= 0.75
        assert mejor["id_tecnica"] == "armbar_guardia"

        # 2. Filtrado por otra técnica no debe devolver el armbar
        res_tri = adapter.buscar(
            consulta_embedding=vec_armbar,
            limite=3,
            umbral_similitud=0.75,
            id_tecnica="triangulo_guardia",
        )
        assert len(res_tri) == 0

    def test_rechaza_vector_dimension_incorrecta(self):
        from src.infrastructure.adapters.qdrant_adapter import QdrantAdapter
        adapter = QdrantAdapter(url="http://localhost:6333", collection_name="bjj_knowledge_test")

        vector_invalido = [0.05] * 768
        with pytest.raises(ValueError, match="Dimensión incorrecta"):
            adapter.upsert("f_invalida", vector_invalido, {})

        with pytest.raises(ValueError, match="Dimensión incorrecta"):
            adapter.buscar(vector_invalido)



class TestPipelineIngestaRAG:
    """Valida la integración de extremo a extremo de chunking e ingesta."""

    def test_pipeline_ingesta_coordina_chunker_y_embedding(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_embed_svc = MagicMock()
        mock_embed_svc.generar_embeddings_batch.return_value = [[0.05] * 2048, [0.05] * 2048]

        pipeline = PipelineIngestaRAG(
            db_connection=mock_conn,
            embedding_service=mock_embed_svc,
        )

        texto_tecnico = (
            "Capítulo 1: Fundamentos de la Guardia Cerrada.\n\n"
            + ("Control de postura mediante presión de aductores y agarres cruzados. " * 30)
            + "\n\nCapítulo 2: Transición a la Palanca de Brazo.\n\n"
            + ("Aislar el codo del oponente cruzando la línea media del pecho. " * 30)
        )

        ids = pipeline.indexar_manual(
            id_tecnica="guardia_cerrada",
            titulo="Manual de Control Postural",
            texto_completo=texto_tecnico,
        )

        assert len(ids) >= 2
        assert mock_embed_svc.generar_embeddings_batch.called
        assert mock_cursor.execute.call_count == len(ids)
        args, _ = mock_cursor.execute.call_args
        assert "INSERT INTO fuentes_conocimiento" in args[0]

    def test_indexar_manual_texto_vacio_retorna_lista_vacia(self):
        pipeline = PipelineIngestaRAG(db_connection="mock_db")
        assert pipeline.indexar_manual("tecnica_1", "Titulo", "") == []

    def test_indexar_manual_con_servicio_embedding_unitario_y_retry(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        class ServicioEmbeddingUnitario:
            def __init__(self):
                self.intentos = 0

            def generar_embedding(self, texto: str):
                self.intentos += 1
                if self.intentos == 1:
                    raise Exception("429 Rate limit exceeded")
                return [0.05] * 2048

        svc = ServicioEmbeddingUnitario()
        pipeline = PipelineIngestaRAG(db_connection=mock_conn, embedding_service=svc)

        with patch("time.sleep"):
            ids = pipeline.indexar_manual("kimura", "Manual Kimura", "Texto de prueba para kimura.")

        assert len(ids) == 1
        assert svc.intentos == 2

    def test_indexar_manual_rechaza_vector_dimension_incorrecta(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_embed_svc = MagicMock()
        mock_embed_svc.generar_embeddings_batch.return_value = [[0.05] * 512]

        pipeline = PipelineIngestaRAG(db_connection=mock_conn, embedding_service=mock_embed_svc)

        with pytest.raises(ValueError, match="Dimensión incorrecta del embedding"):
            pipeline.indexar_manual("guillotina", "Guillotina", "Apretar el cuello.")

