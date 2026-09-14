# tests/test_abm_fuentes.py
"""Pruebas TDD para el Caso de Uso de Administración de Fuentes Didácticas RAG.

Valida la generación de embeddings de 768 dimensiones con AdaptadorGemini,
el filtrado por técnica y la búsqueda de contexto vectorial.
"""

import pytest
from src.application.factory import (
    crear_fuente_controller,
    reiniciar_repositorios_memoria,
)


@pytest.fixture(autouse=True)
def limpiar_estado():
    reiniciar_repositorios_memoria()
    yield
    reiniciar_repositorios_memoria()


class TestCasoDeUsoFuentesConocimiento:
    """Valida la orquestación del Session Facade FuenteController."""

    def test_indexar_fuente_autogenera_embedding_768_con_gemini(self):
        controller = crear_fuente_controller(usar_db_real=False)

        resultado = controller.indexar_fuente(
            id_fuente="fuente_armbar_01",
            id_tecnica="armbar_guardia",
            titulo="Manual de Finalizaciones Gracie",
            tipo_recurso="PDF",
            chunk_texto="Para el armbar desde la guardia, bloquea el tríceps y escala las caderas sobre el hombro.",
            embedding_vector=None,  # Debe ser autogenerado por AdaptadorGemini
        )

        assert resultado["id_fuente"] == "fuente_armbar_01"
        assert resultado["dimension_embedding"] == 768
        assert resultado["longitud_chunk"] > 0

    def test_indexar_fuente_con_vector_manual_valido(self):
        controller = crear_fuente_controller(usar_db_real=False)
        vector_valido = [0.12] * 768

        resultado = controller.indexar_fuente(
            id_fuente="fuente_manual_02",
            id_tecnica="triangulo_guardia",
            titulo="Detalles del Triángulo",
            tipo_recurso="Manual",
            chunk_texto="Corta el ángulo 90 grados y jala la espinilla detrás de la rodilla.",
            embedding_vector=vector_valido,
        )

        assert resultado["id_fuente"] == "fuente_manual_02"
        assert resultado["dimension_embedding"] == 768

    def test_indexar_fuente_rechaza_vector_dimension_incorrecta(self):
        controller = crear_fuente_controller(usar_db_real=False)
        vector_invalido = [0.1] * 512  # Debe fallar según regla BCNF / gemini-embedding-2

        with pytest.raises(ValueError, match="La dimensión del embedding debe ser 768"):
            controller.indexar_fuente(
                id_fuente="fuente_erronea",
                id_tecnica="omoplata",
                titulo="Error de Vector",
                tipo_recurso="Doc",
                chunk_texto="Texto descriptivo",
                embedding_vector=vector_invalido,
            )

    def test_buscar_contexto_retorna_lista_fuentes(self):
        controller = crear_fuente_controller(usar_db_real=False)
        controller.indexar_fuente(
            id_fuente="F1",
            id_tecnica="T1",
            titulo="Guía A",
            tipo_recurso="PDF",
            chunk_texto="Contenido relevante A",
            embedding_vector=[0.05] * 768,
        )
        controller.indexar_fuente(
            id_fuente="F2",
            id_tecnica="T1",
            titulo="Guía B",
            tipo_recurso="PDF",
            chunk_texto="Contenido relevante B",
            embedding_vector=[0.05] * 768,
        )

        consulta = [0.05] * 768
        recuperados = controller.buscar_contexto(consulta_embedding=consulta, limite=2)

        assert len(recuperados) <= 2
        assert len(recuperados) > 0
        assert "titulo" in recuperados[0]
        assert "chunk_texto" in recuperados[0]

    def test_listar_fuentes_filtra_por_tecnica_y_total(self):
        controller = crear_fuente_controller(usar_db_real=False)
        controller.indexar_fuente(
            id_fuente="F1", id_tecnica="armbar", titulo="T1", tipo_recurso="PDF", chunk_texto="Txt 1"
        )
        controller.indexar_fuente(
            id_fuente="F2", id_tecnica="triangulo", titulo="T2", tipo_recurso="PDF", chunk_texto="Txt 2"
        )

        todas = controller.listar_fuentes()
        solo_armbar = controller.listar_fuentes(id_tecnica="armbar")

        assert len(todas) == 2
        assert len(solo_armbar) == 1
        assert solo_armbar[0]["id_tecnica"] == "armbar"
