# tests/test_rag_real.py
"""Pruebas Unitarias TDD para Subsistema RAG Real con gemini-embedding-2 y Chunker Semántico.

Verifica:
1. Prefijo oficial Google 'task: search result | query:' en GeminiEmbedding2Adapter.
2. Dimensión canónica estricta de 768 floats y validación de dimensionalidad.
3. Reintento exponencial ante excepciones de cuota HTTP 429.
4. ChunkerSemanticoBJJ encapsulando langchain_text_splitters (1000/200).
5. ConfiguracionRAG como Experto en Información inyectado en repositorios.
6. Filtrado por umbral configurable (0.65 por defecto) sin valores mágicos hardcodeados.
"""

from unittest.mock import MagicMock, patch
import pytest
from src.domain.models import ConfiguracionRAG, FuenteConocimiento
from src.services.chunker_semantico import ChunkerSemanticoBJJ
from src.infrastructure.adapters.gemini_embedding_adapter import GeminiEmbedding2Adapter
from src.infrastructure.persistence import PostgresFuenteConocimientoRepository
from src.infrastructure.persistence.rag_ingestion import PipelineIngestaRAG


class TestGeminiEmbedding2Adapter:
    """Valida el adaptador para gemini-embedding-2 bajo el SDK google-genai."""

    def test_prefijo_oficial_google_en_generar_embedding(self):
        """Verifica que el prompt se formatea con 'task: search result | query: '."""
        adapter = GeminiEmbedding2Adapter(api_key="fake-test-key")
        mock_client = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.01] * 768
        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding]
        mock_client.models.embed_content.return_value = mock_response
        adapter._client = mock_client

        texto_consulta = "escape de guardia cerrada"
        resultado = adapter.generar_embedding(texto_consulta)

        assert len(resultado) == 768
        assert mock_client.models.embed_content.called
        _, kwargs = mock_client.models.embed_content.call_args
        assert kwargs["contents"] == f"task: search result | query: {texto_consulta}"
        assert kwargs["model"] == "gemini-embedding-2"
        assert kwargs["config"].output_dimensionality == 768

    def test_rechaza_vector_dimension_distinta_de_768(self):
        """Lanza ValueError si el backend devuelve dimensión errónea (ej. 512 o 1536)."""
        adapter = GeminiEmbedding2Adapter(api_key="fake-test-key")
        mock_client = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.01] * 512  # Dimensión incorrecta
        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding]
        mock_client.models.embed_content.return_value = mock_response
        adapter._client = mock_client

        with pytest.raises(ValueError, match="Dimensión incorrecta"):
            adapter.generar_embedding("armbar biomecánica")

    def test_generar_embeddings_batch_con_prefijo_y_reintento_429(self):
        """Verifica lote con prefijo para cada elemento y reintento exponencial ante 429."""
        adapter = GeminiEmbedding2Adapter(api_key="fake-test-key")
        mock_client = MagicMock()
        adapter._client = mock_client

        mock_embedding = MagicMock()
        mock_embedding.values = [0.05] * 768
        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding, mock_embedding]

        # Simula error 429 en el primer intento y éxito en el segundo
        mock_client.models.embed_content.side_effect = [
            Exception("ResourceExhausted: 429 Quota exceeded"),
            mock_response,
        ]

        textos = ["palanca de brazo", "estrangulación cruzada"]
        with patch("time.sleep") as mock_sleep:
            vectores = adapter.generar_embeddings_batch(textos, max_retries=3, backoff_base=0.01)

        assert len(vectores) == 2
        assert mock_client.models.embed_content.call_count == 2
        assert mock_sleep.called
        # Verificar que ambos textos tienen el prefijo oficial
        _, kwargs = mock_client.models.embed_content.call_args
        assert kwargs["contents"] == [
            "task: search result | query: palanca de brazo",
            "task: search result | query: estrangulación cruzada",
        ]

    def test_adapter_sin_api_key_retorna_vector_deterministico_768(self):
        """Garantiza funcionamiento offline/test devolviendo vector normalizado 768d."""
        with patch.dict("os.environ", {}, clear=True):
            adapter = GeminiEmbedding2Adapter(api_key="")
            vector = adapter.generar_embedding("prueba sin credenciales")
            assert len(vector) == 768
            assert vector[0] == 0.05

            lote = adapter.generar_embeddings_batch(["texto 1", "texto 2"])
            assert len(lote) == 2
            assert len(lote[0]) == 768

    def test_generar_embeddings_batch_textos_vacios_retorna_vacio(self):
        adapter = GeminiEmbedding2Adapter(api_key="fake-test-key")
        assert adapter.generar_embeddings_batch([]) == []

    def test_generar_embeddings_batch_dimension_invalida_lanza_error(self):
        adapter = GeminiEmbedding2Adapter(api_key="fake-test-key")
        mock_client = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.01] * 256  # Invalida
        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding]
        mock_client.models.embed_content.return_value = mock_response
        adapter._client = mock_client

        with pytest.raises(ValueError, match="dimensión incorrecta"):
            adapter.generar_embeddings_batch(["prueba"])

    def test_generar_embeddings_batch_reintentos_agotados_lanza_excepcion(self):
        adapter = GeminiEmbedding2Adapter(api_key="fake-test-key")
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = Exception("429 Too Many Requests")
        adapter._client = mock_client

        with patch("time.sleep"):
            with pytest.raises(Exception, match="429"):
                adapter.generar_embeddings_batch(["texto"], max_retries=2, backoff_base=0.001)

    def test_generate_embedding_alias_contrato(self):
        adapter = GeminiEmbedding2Adapter(api_key="")
        vec = adapter.generate_embedding("armbar")
        assert len(vec) == 768


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
    """Valida el patrón Experto en Información para umbrales RAG e inyección en Postgres."""

    def test_configuracion_rag_valores_por_defecto_y_congelada(self):
        cfg = ConfiguracionRAG()
        assert cfg.umbral_similitud_minima == 0.65
        assert cfg.top_k_resultados == 3

        # Inmutabilidad (frozen dataclass)
        with pytest.raises(Exception):
            cfg.umbral_similitud_minima = 0.75  # type: ignore

    def test_inyeccion_configuracion_rag_en_repositorio_postgres(self):
        """Verifica que el repositorio recibe ConfiguracionRAG y la utiliza en la consulta."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        config_instructor = ConfiguracionRAG(umbral_similitud_minima=0.72, top_k_resultados=5)
        repo = PostgresFuenteConocimientoRepository(
            db_connection=mock_conn,
            config_rag=config_instructor,
        )

        mock_cursor.fetchall.return_value = [
            ("f1", "armbar", "Guía Armbar", "Manual", "Texto del armbar", None),
        ]

        embedding_consulta = [0.02] * 768
        resultados = repo.buscar_contexto(embedding_consulta)

        assert len(resultados) == 1
        assert mock_cursor.execute.called
        sql_query, sql_params = mock_cursor.execute.call_args[0]
        # Verificar que el umbral usado es 0.72 inyectado, NO 0.65 hardcodeado
        assert 0.72 in sql_params
        assert sql_params[-1] == 5  # top_k inyectado
        assert "embedding_vector <=>" in sql_query

    def test_buscar_contexto_con_filtro_id_tecnica(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        config_custom = ConfiguracionRAG(umbral_similitud_minima=0.80, top_k_resultados=2)
        repo = PostgresFuenteConocimientoRepository(db_connection=mock_conn, config_rag=config_custom)

        mock_cursor.fetchall.return_value = []
        embedding_consulta = [0.03] * 768
        repo.buscar_contexto(embedding_consulta, id_tecnica="kimura_guardia")

        sql_query, sql_params = mock_cursor.execute.call_args[0]
        assert "id_tecnica = %s" in sql_query
        assert sql_params[0] == "kimura_guardia"
        assert 0.80 in sql_params
        assert sql_params[-1] == 2


class TestPipelineIngestaRAG:
    """Valida la integración de extremo a extremo de chunking e ingesta."""

    def test_pipeline_ingesta_coordina_chunker_y_embedding(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_embed_svc = MagicMock()
        mock_embed_svc.generar_embeddings_batch.return_value = [[0.05] * 768, [0.05] * 768]

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
                return [0.05] * 768

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

    def test_ingestor_rag_legacy_con_generar_embedding(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        class AdaptadorSimpleGenerar:
            def generar_embedding(self, texto: str):
                return [0.05] * 768

        from src.infrastructure.persistence.rag_ingestion import IngestorRAG

        ingestor = IngestorRAG(db_url=mock_conn, gemini_adapter=AdaptadorSimpleGenerar())
        total = ingestor.indexar_documento("Titulo", "Texto " * 50, tamano_chunk=200)
        assert total > 0
        assert mock_cursor.execute.called
