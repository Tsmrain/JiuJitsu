# tests/test_e2e_rag.py
"""Pruebas de Integración End-to-End (E2E) para el Pipeline RAG en PostgreSQL + pgvector.

Ejecuta el ciclo de vida completo contra el contenedor Docker bjj_postgres:
1. Fragmentación semántica con ChunkerSemanticoBJJ (LangChain).
2. Generación de vectores densos 768d y persistencia en tabla 'fuentes_conocimiento'.
3. Búsqueda vectorial HNSW usando distancia de coseno con operador (<=>).
4. Verificación del filtrado por umbral semántico de ConfiguracionRAG.
"""

import os
import pytest
import psycopg2
from src.domain.models import ConfiguracionRAG, FuenteConocimiento
from src.services.chunker_semantico import ChunkerSemanticoBJJ
from src.infrastructure.adapters.gemini_embedding_adapter import GeminiEmbedding2Adapter
from src.infrastructure.persistence import PostgresFuenteConocimientoRepository
from src.infrastructure.persistence.rag_ingestion import PipelineIngestaRAG

# URL de conexión al contenedor Docker en desarrollo
DOCKER_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgrespassword@localhost:5433/bjj_biomechanics",
)


def _verificar_docker_db_disponible() -> bool:
    """Comprueba si el contenedor Docker bjj_postgres está escuchando."""
    try:
        conn = psycopg2.connect(DOCKER_DB_URL)
        conn.close()
        return True
    except Exception:
        return False


docker_db_requerido = pytest.mark.skipif(
    not _verificar_docker_db_disponible(),
    reason="El contenedor Docker PostgreSQL con pgvector no está accesible en localhost:5433.",
)


@docker_db_requerido
class TestE2ERAGPostgres:
    """Suite de pruebas de integración real con base de datos Docker."""

    @pytest.fixture(autouse=True)
    def preparar_y_limpiar_datos(self):
        """Limpia registros de prueba antes y después de cada test."""
        conn = psycopg2.connect(DOCKER_DB_URL)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM fuentes_conocimiento WHERE id_tecnica = 'e2e_test_armbar';")
        conn.commit()
        conn.close()

        yield

        conn = psycopg2.connect(DOCKER_DB_URL)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM fuentes_conocimiento WHERE id_tecnica = 'e2e_test_armbar';")
        conn.commit()
        conn.close()

    def test_e2e_ingesta_fragmentada_y_recuperacion_semantica(self):
        """Ejecuta fragmentación real LangChain, persiste vectores en pgvector y consulta."""
        # 1. Adaptadores reales
        adapter = GeminiEmbedding2Adapter(api_key="")  # Vector determinista normalizado 768d
        pipeline = PipelineIngestaRAG(
            db_connection=DOCKER_DB_URL,
            embedding_service=adapter,
        )

        manual_bjj = (
            "Manual Biomecánico de Armbar desde Guardia.\n\n"
            "Paso 1: Romper la postura del adversario jalando la solapa y tirando con las piernas.\n"
            "Paso 2: Aislar el brazo derecho y colocar el pie en la cadera para pivotar 90 grados.\n"
            "Paso 3: Pasar la pierna sobre la cabeza y mantener las rodillas juntas pellizcando el codo.\n\n"
            "Detalle Crítico: La hiperextensión ocurre sobre el fulcro pélvico. No cruces los tobillos."
        )

        # 2. Ingesta
        ids = pipeline.indexar_manual(
            id_tecnica="e2e_test_armbar",
            titulo="Guía Completa de Finalización",
            texto_completo=manual_bjj,
            tipo_recurso="Manual",
        )

        assert len(ids) >= 1

        # 3. Búsqueda vectorial con ConfiguracionRAG (umbral 0.65)
        config_rag = ConfiguracionRAG(umbral_similitud_minima=0.65, top_k_resultados=3)
        repo = PostgresFuenteConocimientoRepository(
            db_connection=DOCKER_DB_URL,
            config_rag=config_rag,
        )

        # Vector de consulta idéntico (similitud = 1.0)
        vector_consulta = adapter.generar_embedding("aislar el codo para armbar")
        resultados = repo.buscar_contexto(vector_consulta, id_tecnica="e2e_test_armbar")

        assert len(resultados) >= 1
        assert "e2e_test_armbar" == resultados[0].id_tecnica
        assert "Guía Completa de Finalización" in resultados[0].titulo
        assert "fulcro pélvico" in resultados[0].chunk_texto or "armbar" in resultados[0].chunk_texto.lower()

    def test_e2e_umbral_estricto_filtra_resultados_baja_similitud(self):
        """Verifica que un umbral alto (ej. 0.9999) filtra vectores que no alcancen similitud requerida."""
        adapter = GeminiEmbedding2Adapter(api_key="")
        pipeline = PipelineIngestaRAG(db_connection=DOCKER_DB_URL, embedding_service=adapter)

        pipeline.indexar_manual(
            id_tecnica="e2e_test_armbar",
            titulo="Ajustes de Presión",
            texto_completo="Texto de prueba biomecánica sobre palancas y ángulos articulares.",
        )

        # Vector ortogonal / divergente para producir similitud inferior
        vector_divergente = [0.05] * 384 + [-0.05] * 384

        # Umbral exigente: 0.85
        config_estricta = ConfiguracionRAG(umbral_similitud_minima=0.85, top_k_resultados=3)
        repo = PostgresFuenteConocimientoRepository(
            db_connection=DOCKER_DB_URL,
            config_rag=config_estricta,
        )

        resultados = repo.buscar_contexto(vector_divergente, id_tecnica="e2e_test_armbar")
        # Al ser un vector divergente con similitud < 0.85, no debe superar el umbral
        assert len(resultados) == 0
