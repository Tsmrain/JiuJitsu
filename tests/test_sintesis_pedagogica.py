# tests/test_sintesis_pedagogica.py
"""Pruebas TDD para el Servicio de Síntesis Pedagógica (Pure Fabrication).

Verifica la orquestación de RAG, filtrado por umbral semántico de ConfiguracionRAG
y activación del fallback cuando la similitud biomecánica es deficiente (<0.65).
"""

import pytest
from unittest.mock import MagicMock
from src.services.sintesis_pedagogica_service import SintesisPedagogicaService
from src.domain.models import ConfiguracionRAG, FuenteConocimiento


class TestSintesisPedagogicaService:
    def setup_method(self):
        self.config = ConfiguracionRAG(umbral_similitud_minima=0.65, top_k_resultados=3)
        self.mock_repo = MagicMock()
        self.service = SintesisPedagogicaService(self.mock_repo, self.config)

    def test_retorna_fallback_cuando_similitud_baja(self):
        """Umbral 0.65: chunks con 0.50 deben activar fallback."""
        self.mock_repo.buscar_contexto.return_value = [
            {"similitud": 0.50, "chunk_texto": "texto irrelevante"}
        ]

        resultado = self.service.generar_feedback_contextualizado(
            articulacion_critica="Codo Derecho", id_tecnica="T001"
        )

        assert resultado["usó_fallback"] is True
        assert "Codo Derecho" in resultado["consejo"]
        assert resultado["contexto_recuperado"] is None

    def test_retorna_contexto_cuando_similitud_alta(self):
        """Chunk con 0.82 debe ser retornado."""
        self.mock_repo.buscar_contexto.return_value = [
            {"similitud": 0.82, "chunk_texto": "Mantén el codo pegado al cuerpo...", "titulo": "Manual BJJ"}
        ]

        resultado = self.service.generar_feedback_contextualizado(
            articulacion_critica="Codo Derecho", id_tecnica="T001"
        )

        assert resultado["usó_fallback"] is False
        assert resultado["contexto_recuperado"] == "Mantén el codo pegado al cuerpo..."
        assert resultado["score_similitud"] == 0.82

    def test_filtra_por_id_tecnica(self):
        """Verifica que repo recibe id_tecnica correcto."""
        self.service.generar_feedback_contextualizado(
            articulacion_critica="Rodilla", id_tecnica="T042"
        )
        self.mock_repo.buscar_contexto.assert_called_once()
        args = self.mock_repo.buscar_contexto.call_args
        assert args[1]["id_tecnica"] == "T042"

    def test_retorna_fallback_cuando_lista_resultados_vacia(self):
        """Si no hay fuentes indexadas para la técnica, activa fallback sin error."""
        self.mock_repo.buscar_contexto.return_value = []
        resultado = self.service.generar_feedback_contextualizado(
            articulacion_critica="Hombro Izquierdo", id_tecnica="T099"
        )
        assert resultado["usó_fallback"] is True
        assert "Hombro Izquierdo" in resultado["consejo"]
        assert resultado["score_similitud"] == 0.0

    def test_soporta_objetos_fuente_conocimiento_del_dominio(self):
        """Verifica interoperabilidad con instancias tipadas de FuenteConocimiento."""
        fuente = FuenteConocimiento(
            id_fuente="f1",
            id_tecnica="T001",
            titulo="Manual Gracie",
            tipo_recurso="PDF",
            chunk_texto="Detalle técnico con 0.89 de similitud",
            similitud=0.89,
        )
        self.mock_repo.buscar_contexto.return_value = [fuente]

        resultado = self.service.generar_feedback_contextualizado(
            articulacion_critica="Codo", id_tecnica="T001"
        )

        assert resultado["usó_fallback"] is False
        assert resultado["contexto_recuperado"] == "Detalle técnico con 0.89 de similitud"
        assert resultado["score_similitud"] == 0.89

    def test_maneja_repo_con_firma_posicional_legacy(self):
        """Verifica tolerancia ante repositorios con firma solo de consulta_embedding."""
        def mock_buscar_legacy(consulta_embedding, limite=3, id_tecnica=None):
            return [{"similitud": 0.75, "chunk_texto": "Texto válido legacy"}]

        # Cuando se llama con kwargs no reconocidos, lanza TypeError y cae en fallback
        mock_legacy_repo = MagicMock()
        mock_legacy_repo.buscar_contexto.side_effect = [
            TypeError("buscar_contexto() got an unexpected keyword argument 'embedding'"),
            [{"similitud": 0.75, "chunk_texto": "Texto válido legacy"}],
        ]

        service = SintesisPedagogicaService(mock_legacy_repo, self.config)
        resultado = service.generar_feedback_contextualizado("Muñeca", "T10")

        assert resultado["usó_fallback"] is False
        assert resultado["contexto_recuperado"] == "Texto válido legacy"

    def test_fallback_con_plantilla_con_error_de_formato(self):
        """Si la plantilla de configuración tiene un placeholder incompatible, usa fallback seguro."""
        config_malformada = ConfiguracionRAG(plantilla_fallback="Error en {articulacion} y {campo_inexistente}")
        self.mock_repo.buscar_contexto.return_value = []
        service = SintesisPedagogicaService(self.mock_repo, config_malformada)

        resultado = service.generar_feedback_contextualizado("Tobillo", "T01")
        assert resultado["usó_fallback"] is True
        assert "Tobillo" in resultado["consejo"]
