# tests/test_rag_documentos_consolidados.py
"""Pruebas de Integración End-to-End para el subsistema RAG con documentos consolidados.

Valida:
1. Recuperación semántica en Qdrant filtrada por técnica desde documentos consolidados (BOOKS).
2. Síntesis pedagógica estructurada (4 claves JSONB) mediante Gemini con inyección del acervo pedagógico.
"""

import os
from typing import Any
import pytest
import psycopg2
from dotenv import load_dotenv

load_dotenv()

from src.domain.models import ConfiguracionRAG, DesviacionArticular
from src.infrastructure.adapters.qdrant_adapter import QdrantAdapter
from src.infrastructure.adapters.gemini_adapter import GeminiServiceAdapter
from src.infrastructure.persistence.postgres_repository import PostgresFuenteConocimientoRepository
from src.services.sintesis_pedagogica_service import SintesisPedagogicaService
from src.application.controllers import EvaluacionController


def obtener_db_url():
    return os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5433/bjj_biomechanics")


from src.infrastructure.mocks import MockYOLOEngine, MockTecnicaRepository


class MockYOLOEngineCodo(MockYOLOEngine):
    """Simula detección de YOLO con desviación angular pronunciada en la articulación del Codo."""
    def __init__(self, desviacion: float = 30.0):
        super().__init__(desviacion_grados=desviacion)

    def evaluar_desviacion(self, video_path: str, tecnica_patron: Any = None):
        return [
            DesviacionArticular(
                nombre_articulacion="Codo",
                angulo_esperado=90.0,
                angulo_real=60.0,
                desviacion_grados=self._desviacion,
            )
        ]




def test_recuperar_contexto_de_libro_books():
    """PASO 1: Valida que buscar_contexto recupere fragmentos relevantes de BOOKS con id_documento."""
    db_url = obtener_db_url()
    conn = psycopg2.connect(db_url)
    qdrant = QdrantAdapter()

    # Configuramos umbral adecuado para búsqueda semántica con vector de consulta representativo
    config = ConfiguracionRAG(umbral_similitud_minima=0.5, top_k_resultados=3)
    repo = PostgresFuenteConocimientoRepository(
        db_connection=conn,
        config_rag=config,
        qdrant_adapter=qdrant,
    )

    # Vector de consulta de 2048 dimensiones correspondiente al espacio de embedding
    embedding_consulta = [0.05] * 2048

    chunks_recuperados = repo.buscar_contexto(
        consulta_embedding=embedding_consulta,
        limite=3,
        id_tecnica="armbar_guardia",
    )

    conn.close()

    assert len(chunks_recuperados) > 0, "Debe retornar al menos un chunk relevante para armbar_guardia"
    
    # Assert: Debe retornar chunks cuyo título contenga 'BOOKS' y texto relevante
    titulos = [c.titulo for c in chunks_recuperados]
    assert any("BOOKS" in t for t in titulos), f"Debe recuperar chunks de BOOKS, obtenidos: {titulos}"
    
    mejor_chunk = chunks_recuperados[0]
    texto = mejor_chunk.chunk_texto.lower()
    assert ("bloqueo" in texto or "tríceps" in texto or "codo" in texto or "armbar" in texto), (
        f"El chunk debe contener terminología técnica relevante, obtenido: {mejor_chunk.chunk_texto}"
    )

    # Assert: Verificar que los chunks retornados tienen id_documento válido
    assert mejor_chunk.id_documento is not None, "El chunk debe tener id_documento asociado"
    assert mejor_chunk.id_documento.startswith("doc_"), f"id_documento inválido: {mejor_chunk.id_documento}"


def test_sintesis_pedagogica_con_contexto_real():
    """PASO 2: Valida la orquestación RAG + Gemini generando las 4 claves JSONB con conceptos del manual."""
    db_url = obtener_db_url()
    conn = psycopg2.connect(db_url)
    qdrant = QdrantAdapter()
    config = ConfiguracionRAG(umbral_similitud_minima=0.5, top_k_resultados=3)

    repo = PostgresFuenteConocimientoRepository(
        db_connection=conn,
        config_rag=config,
        qdrant_adapter=qdrant,
    )

    sintesis_service = SintesisPedagogicaService(repo=repo, config=config)
    gemini_adapter = GeminiServiceAdapter()

    # EvaluacionController con motor YOLO simulando falla en Codo
    controller = EvaluacionController(
        inference_engine=MockYOLOEngineCodo(desviacion=30.0),
        generation_service=gemini_adapter,
        tecnica_repository=MockTecnicaRepository(),
        sintesis_service=sintesis_service,
    )

    # Ejecutar evaluación con vector de consulta de 2048d
    resultado = controller.evaluar_ejecucion(
        video_path="dummy.mp4",
        id_tecnica="armbar_guardia",
        embedding_desviacion=[0.05] * 2048,
    )

    conn.close()

    # Assert 1: Estructura y 4 claves de respuesta pedagógica
    assert "consejo_estructurado" in resultado, "El resultado debe incluir consejo_estructurado"
    estructurado = resultado["consejo_estructurado"]
    for clave in ["analisis_postural", "riesgo_lesion", "paso_a_paso", "resumen_ejecutivo"]:
        assert clave in estructurado, f"Falta clave '{clave}' en consejo_estructurado"
        assert len(estructurado[clave].strip()) > 0, f"La clave '{clave}' no puede estar vacía"

    # Assert 2: El contenido debe hacer referencia a la articulación y conceptos técnicos
    texto_total = (
        estructurado["analisis_postural"] + " " +
        estructurado["paso_a_paso"] + " " +
        estructurado["resumen_ejecutivo"]
    ).lower()

    assert "codo" in texto_total or "brazo" in texto_total, "Debe mencionar la articulación evaluada (Codo/Brazo)"
    assert resultado["score_similitud_rag"] >= 0.5, f"Debe usar contexto RAG válido, score: {resultado['score_similitud_rag']}"
    assert resultado["usó_fallback_rag"] is False, "No debe activar fallback pedagógico cuando hay manual disponible"
