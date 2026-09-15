# tests/test_e2e_rag.py
"""Pruebas de Integración End-to-End (E2E) para el Pipeline RAG con Qdrant Local + PostgreSQL (BCNF).

Ejecuta el ciclo de vida completo contra los contenedores Docker bjj_qdrant y bjj_postgres:
1. Fragmentación semántica con ChunkerSemanticoBJJ (LangChain).
2. Generación de vectores densos 2048d con QwenEmbeddingAdapter y persistencia en Qdrant (colección bjj_knowledge).
3. Verificación de dimensión vectorial de 2048 en Qdrant.
4. Búsqueda vectorial KNN usando similitud coseno en Qdrant con filtro de técnica.
5. Verificación de que los resultados devueltos superan el umbral semántico de 0.75.
6. Filtrado estricto por umbral alto ante vectores divergentes.
"""

import os
import pytest
import psycopg2
from src.domain.models import ConfiguracionRAG, FuenteConocimiento
from src.services.chunker_semantico import ChunkerSemanticoBJJ
from src.infrastructure.adapters.qwen_embedding_adapter import QwenEmbeddingAdapter
from src.infrastructure.adapters.qdrant_adapter import QdrantAdapter
from src.infrastructure.persistence import PostgresFuenteConocimientoRepository
from src.infrastructure.persistence.rag_ingestion import PipelineIngestaRAG

# URL de conexión al contenedor Docker en desarrollo
DOCKER_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgrespassword@localhost:5433/bjj_biomechanics",
)
QDRANT_TEST_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


def _verificar_docker_db_disponible() -> bool:
    """Comprueba si el contenedor Docker bjj_postgres está escuchando."""
    try:
        conn = psycopg2.connect(DOCKER_DB_URL)
        conn.close()
        return True
    except Exception:
        return False


def _verificar_qdrant_disponible() -> bool:
    """Comprueba si el contenedor Docker bjj_qdrant está escuchando."""
    import urllib.request
    try:
        req = urllib.request.urlopen(f"{QDRANT_TEST_URL}/collections", timeout=2)
        return req.status == 200
    except Exception:
        return False


@pytest.mark.skipif(
    not (_verificar_docker_db_disponible() and _verificar_qdrant_disponible()),
    reason="Contenedores Docker bjj_postgres (5433) o bjj_qdrant (6333) no disponibles",
)
class TestE2ERAGPostgres:
    """Ejecuta el pipeline de ingesta y consulta vectorial contra Qdrant Local y PostgreSQL real."""

    @pytest.fixture(autouse=True)
    def limpiar_tabla_fuentes(self):
        """Limpia y prepara la técnica de prueba antes y después de cada test."""
        conn = psycopg2.connect(DOCKER_DB_URL)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM fuentes_conocimiento WHERE id_tecnica = 'e2e_test_armbar';")
            cur.execute("""
                INSERT INTO profesores (id_profesor, nombre, email)
                VALUES ('prof_admin', 'Profesor Admin', 'admin@jiujitsu.com')
                ON CONFLICT (id_profesor) DO NOTHING;
            """)
            cur.execute("""
                INSERT INTO tecnicas_patron (id_tecnica, id_profesor, nombre, categoria, matriz_esqueletica)
                VALUES ('e2e_test_armbar', 'prof_admin', 'Armbar Test E2E', 'Guardia', '{"puntos": {}}')
                ON CONFLICT (id_tecnica) DO NOTHING;
            """)
        conn.commit()
        conn.close()

        # Limpiar puntos en Qdrant para aislamiento
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            q_clean = QdrantAdapter(url=QDRANT_TEST_URL)
            if q_clean._client and q_clean._client.collection_exists("bjj_knowledge"):
                q_clean._client.delete(
                    collection_name="bjj_knowledge",
                    points_selector=Filter(must=[FieldCondition(key="id_tecnica", match=MatchValue(value="e2e_test_armbar"))])
                )
        except Exception:
            pass

        yield

        conn = psycopg2.connect(DOCKER_DB_URL)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM fuentes_conocimiento WHERE id_tecnica = 'e2e_test_armbar';")
            cur.execute("DELETE FROM tecnicas_patron WHERE id_tecnica = 'e2e_test_armbar';")
        conn.commit()
        conn.close()

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            q_clean = QdrantAdapter(url=QDRANT_TEST_URL)
            if q_clean._client and q_clean._client.collection_exists("bjj_knowledge"):
                q_clean._client.delete(
                    collection_name="bjj_knowledge",
                    points_selector=Filter(must=[FieldCondition(key="id_tecnica", match=MatchValue(value="e2e_test_armbar"))])
                )
        except Exception:
            pass


    def test_e2e_ingesta_fragmentada_y_recuperacion_semantica(self):
        """Ejecuta fragmentación real LangChain, persiste vectores en Qdrant y consulta con umbral > 0.75."""
        # 1. Adaptadores reales
        adapter = QwenEmbeddingAdapter()  # Vector determinista normalizado 2048d
        qdrant = QdrantAdapter(url="http://localhost:6333")

        # 2. Verificar que la colección bjj_knowledge tenga dimensión 2048
        qdrant.asegurar_coleccion()
        info_col = qdrant._client.get_collection("bjj_knowledge")
        vectors_cfg = info_col.config.params.vectors
        dimension = getattr(vectors_cfg, "size", None) or vectors_cfg.get("size")
        assert dimension == 2048

        pipeline = PipelineIngestaRAG(
            db_connection=DOCKER_DB_URL,
            embedding_service=adapter,
            qdrant_adapter=qdrant,
        )

        manual_bjj = (
            "Manual Biomecánico de Armbar desde Guardia.\n\n"
            "Paso 1: Romper la postura del adversario jalando la solapa y tirando con las piernas.\n"
            "Paso 2: Aislar el brazo derecho y colocar el pie en la cadera para pivotar 90 grados.\n"
            "Paso 3: Pasar la pierna sobre la cabeza y mantener las rodillas juntas pellizcando el codo.\n\n"
            "Detalle Crítico: La hiperextensión ocurre sobre el fulcro pélvico. No cruces los tobillos."
        )

        # 3. Ingesta
        ids = pipeline.indexar_manual(
            id_tecnica="e2e_test_armbar",
            titulo="Guía Completa de Finalización",
            texto_completo=manual_bjj,
            tipo_recurso="Manual",
        )

        assert len(ids) >= 1

        # 4. Búsqueda vectorial con ConfiguracionRAG (umbral 0.75)
        config_rag = ConfiguracionRAG(umbral_similitud_minima=0.75, top_k_resultados=3)
        repo = PostgresFuenteConocimientoRepository(
            db_connection=DOCKER_DB_URL,
            config_rag=config_rag,
            qdrant_adapter=qdrant,
        )

        # Vector de consulta
        vector_consulta = adapter.generar_embedding("aislar el codo para armbar")
        resultados = repo.buscar_contexto(vector_consulta, id_tecnica="e2e_test_armbar")

        # 5. Validar que la búsqueda devuelve resultados con similitud > 0.75
        assert len(resultados) >= 1
        for r in resultados:
            assert r.similitud is not None
            assert r.similitud > 0.75
        assert "e2e_test_armbar" == resultados[0].id_tecnica
        assert "Guía Completa de Finalización" in resultados[0].titulo
        assert "fulcro pélvico" in resultados[0].chunk_texto or "armbar" in resultados[0].chunk_texto.lower()

    def test_e2e_umbral_estricto_filtra_resultados_baja_similitud(self):
        """Verifica que un umbral alto (ej. 0.85) filtra vectores que no alcancen similitud requerida."""
        adapter = QwenEmbeddingAdapter()
        qdrant = QdrantAdapter(url="http://localhost:6333")
        pipeline = PipelineIngestaRAG(
            db_connection=DOCKER_DB_URL,
            embedding_service=adapter,
            qdrant_adapter=qdrant,
        )

        pipeline.indexar_manual(
            id_tecnica="e2e_test_armbar",
            titulo="Ajustes de Presión",
            texto_completo="Texto de prueba biomecánica sobre palancas y ángulos articulares.",
        )

        # Vector ortogonal / divergente para producir similitud inferior
        vector_divergente = [0.05] * 1024 + [-0.05] * 1024

        # Umbral exigente: 0.85
        config_estricta = ConfiguracionRAG(umbral_similitud_minima=0.85, top_k_resultados=3)
        repo = PostgresFuenteConocimientoRepository(
            db_connection=DOCKER_DB_URL,
            config_rag=config_estricta,
            qdrant_adapter=qdrant,
        )

        resultados = repo.buscar_contexto(vector_divergente, id_tecnica="e2e_test_armbar")
        # Al ser un vector divergente con similitud < 0.85, no debe superar el umbral
        assert len(resultados) == 0
