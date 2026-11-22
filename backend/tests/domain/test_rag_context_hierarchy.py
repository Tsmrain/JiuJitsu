import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from corpocmente.domain.services.intelligence_facade import (
    IntelligenceAnalysisFacade,
    UMBRAL_RELEVANCIA_RAG,
)
from corpocmente.domain.strategies.prompt_strategies import (
    SpanishPromptStrategy,
    EnglishPromptStrategy,
    PortuguesePromptStrategy,
    obtener_estrategia_prompt,
)
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import (
    QdrantVectorAdapter,
    VectorSearchResultDTO,
)
from corpocmente.domain.entities.models import EsqueletoBiomecanico


class TestPromptStrategiesHierarchyAndCrossLingual:
    """Verifica directivas de jerarquía y cross-lingual en todas las estrategias."""

    def test_spanish_strategy_with_rag_and_instructor_message(self):
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Armbar",
            discrepancias=["Cadera baja"],
            mensaje_profesor="Cerrar las rodillas",
            tiene_contexto_rag=True,
        )
        assert "manuales adjuntos junto con las indicaciones del profesor" in prompt
        assert "Cerrar las rodillas" in prompt
        assert "NUNCA menciones nombres propios" in prompt
        assert "NO cites páginas" in prompt

    def test_spanish_strategy_with_rag_context_only(self):
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Armbar",
            discrepancias=["Cadera baja"],
            mensaje_profesor="",
            tiene_contexto_rag=True,
        )
        assert "manuales adjuntos y lo observable en el fotograma" in prompt
        assert "entrenador en el tatami" in prompt
        assert "NO cites páginas" in prompt

    def test_spanish_strategy_with_instructor_message_only(self):
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Armbar",
            discrepancias=["Cadera baja"],
            mensaje_profesor="Apretar rodillas firmemente",
            tiene_contexto_rag=False,
        )
        assert "Apretar rodillas firmemente" in prompt
        assert "secuencia técnica del profesor" in prompt

    def test_english_strategy_with_rag_context(self):
        strategy = EnglishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Triangle Choke",
            discrepancias=["Loose leg clamp"],
            mensaje_profesor="",
            tiene_contexto_rag=True,
        )
        assert "attached manual context" in prompt
        assert "NEVER use proper names" in prompt
        assert "Do NOT cite page numbers" in prompt

    def test_english_strategy_with_instructor_message_only(self):
        strategy = EnglishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Triangle Choke",
            discrepancias=["Loose leg clamp"],
            mensaje_profesor="Cut angle to 90 degrees",
            tiene_contexto_rag=False,
        )
        assert "Ensure your correction aligns strictly with these instructions." in prompt
        assert "Cut angle to 90 degrees" in prompt

    def test_portuguese_strategy_with_rag_context(self):
        strategy = PortuguesePromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Mata-Leão",
            discrepancias=["Cotovelo aberto"],
            mensaje_profesor="",
            tiene_contexto_rag=True,
        )
        assert "manual anexo" in prompt
        assert "NUNCA mencione nomes próprios" in prompt
        assert "NÃO cite números de página" in prompt

    def test_portuguese_strategy_with_instructor_message_only(self):
        strategy = PortuguesePromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Mata-Leão",
            discrepancias=["Cotovelo aberto"],
            mensaje_profesor="Esconda a mão atrás da cabeça",
            tiene_contexto_rag=False,
        )
        assert "Esconda a mão atrás da cabeça" in prompt
        assert "treinador no tatame" in prompt

    def test_fallback_strings_by_language(self):
        fb_es = SpanishPromptStrategy().obtener_mensaje_sin_contexto()
        assert fb_es["summary"] == "Información insuficiente"
        assert fb_es["correction"] == "No hay información suficiente en los manuales ni en las instrucciones del instructor para evaluar esta técnica."

        fb_en = EnglishPromptStrategy().obtener_mensaje_sin_contexto()
        assert fb_en["summary"] == "Insufficient information"
        assert fb_en["correction"] == "There is not enough information in the manuals or instructor instructions to evaluate this technique."

        fb_pt = PortuguesePromptStrategy().obtener_mensaje_sin_contexto()
        assert fb_pt["summary"] == "Informações insuficientes"
        assert fb_pt["correction"] == "Não há informações suficientes nos manuais nem nas instruções do instrutor para avaliar esta técnica."


class TestIntelligenceFacadeContextHierarchy:
    """Verifica las 3 prioridades deterministas en IntelligenceAnalysisFacade."""

    def _setup_facade(self):
        mock_yolo = Mock(spec=YOLOPoseAdapter)
        mock_qdrant = Mock(spec=QdrantVectorAdapter)
        mock_gemini = Mock(spec=LocalVLMAdapter)
        mock_qwen = Mock(spec=QwenEmbeddingAdapter)

        mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
        mock_esqueleto.to_vector_array.return_value = [0.1] * 133
        mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]
        mock_yolo.extraer_frame_y_dibujar_error.return_value = "/tmp/critico_test.jpg"

        mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
            score=0.60,
            frame_path="/tmp/frame_test.jpg",
            discrepancias=["Desviación articular en codo"],
        )

        mock_qwen.generar_embedding_texto.return_value = [0.05] * 2048
        mock_qwen.generar_embedding.return_value = [0.05] * 2048

        facade = IntelligenceAnalysisFacade(
            yolo_adapter=mock_yolo,
            qdrant_adapter=mock_qdrant,
            gemini_adapter=mock_gemini,
            qwen_adapter=mock_qwen,
        )
        return facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen

    def test_prioridad_1_combina_manual_y_mensaje_profesor_cuando_ambos_existen(self):
        facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen = self._setup_facade()

        # Simular manual con score 0.82 (>= UMBRAL_RELEVANCIA_RAG = 0.65)
        mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = [
            {
                "id": "chunk_manual_1",
                "score": 0.82,
                "fuente_tipo": "manual_pdf",
                "fuente_nombre": "Jiu-Jitsu University",
                "pagina": 142,
                "contenido_texto": "Underhook the arm and drive shoulder pressure downwards.",
            }
        ]

        mock_gemini.generar_texto_feedback.return_value = {
            "summary": "Presión incorrecta",
            "correction": "Baja el hombro como indica el manual (p. 142) y bloquea la muñeca.",
        }

        with patch("os.path.exists", return_value=True):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=uuid4(),
                tecnica_nombre="Americana",
                mensaje_profesor="Bloquea la muñeca pegada al tatami",
                idioma="es",
            )

        # Gemini debe haber sido llamado combinando AMBAS fuentes
        mock_gemini.generar_texto_feedback.assert_called_once()
        call_prompt = mock_gemini.generar_texto_feedback.call_args.args[0]
        evidencias_visuales = mock_gemini.generar_texto_feedback.call_args.kwargs.get("evidencias_visuales")

        assert "Underhook the arm and drive shoulder pressure" in call_prompt
        assert "Bloquea la muñeca pegada al tatami" in call_prompt
        assert len(evidencias_visuales) == 1
        assert res.feedback_summary == "Presión incorrecta"

    def test_prioridad_2_rag_manual_bajo_umbral_usa_mensaje_profesor(self):
        facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen = self._setup_facade()

        # Simular manual con score 0.40 (< UMBRAL_RELEVANCIA_RAG = 0.65)
        mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = [
            {
                "id": "chunk_manual_irrelevante",
                "score": 0.40,
                "fuente_tipo": "manual_pdf",
                "fuente_nombre": "Manual General",
                "contenido_texto": "Conceptos no relacionados con Americana.",
            }
        ]

        mock_gemini.generar_texto_feedback.return_value = {
            "summary": "Ángulo de muñeca",
            "correction": "Mantén la muñeca firme contra el tatami como indicó el profesor.",
        }

        with patch("os.path.exists", return_value=True):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=uuid4(),
                tecnica_nombre="Americana",
                mensaje_profesor="Fija la muñeca al suelo y desliza el codo como un pincel.",
                idioma="es",
            )

        # Gemini debe haber sido llamado con las instrucciones del profesor
        mock_gemini.generar_texto_feedback.assert_called_once()
        call_prompt = mock_gemini.generar_texto_feedback.call_args.args[0]
        evidencias_visuales = mock_gemini.generar_texto_feedback.call_args.kwargs.get("evidencias_visuales")

        assert "Fija la muñeca al suelo y desliza el codo como un pincel." in call_prompt
        assert "secuencia técnica del profesor" in call_prompt
        # El contenido irrelevante del manual NO debe ser inyectado
        assert "Conceptos no relacionados con Americana" not in call_prompt
        # Evidencias visuales vacías para no distraer al VLM con manuales no relevantes
        assert len(evidencias_visuales) == 0

    def test_prioridad_3_sin_manuales_ni_mensaje_analiza_frame_y_tecnica_en_vlm_es(self):
        facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen = self._setup_facade()
        mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = []
        mock_gemini.generar_texto_feedback.return_value = {
            "summary": "Control de codo abierto",
            "correction": "Acerca la muñeca y presiona la cadera en la Americana.",
        }

        with patch("os.path.exists", return_value=True):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=uuid4(),
                tecnica_nombre="Americana",
                mensaje_profesor="",
                idioma="es",
            )

        mock_gemini.generar_texto_feedback.assert_called_once()
        call_prompt = mock_gemini.generar_texto_feedback.call_args.args[0]
        assert "Americana" in call_prompt
        assert "No hay manuales ni instrucciones escritas del profesor" in call_prompt
        mock_gemini.evaluar_fidelidad_grounding.assert_not_called()
        assert res.feedback_summary == "Control de codo abierto"

    def test_prioridad_3_sin_manuales_ni_mensaje_analiza_frame_y_tecnica_en_vlm_en(self):
        facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen = self._setup_facade()
        mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = []
        mock_gemini.generar_texto_feedback.return_value = {
            "summary": "Loose shoulder lock",
            "correction": "Keep the opponent's wrist pinned to the mat during Kimura.",
        }

        with patch("os.path.exists", return_value=True):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=uuid4(),
                tecnica_nombre="Kimura",
                mensaje_profesor="   ",
                idioma="en",
            )

        mock_gemini.generar_texto_feedback.assert_called_once()
        assert res.feedback_summary == "Loose shoulder lock"

    def test_prioridad_3_sin_manuales_ni_mensaje_si_vlm_falla_retorna_fallback_pt(self):
        facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen = self._setup_facade()
        mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = []
        mock_gemini.generar_texto_feedback.side_effect = RuntimeError("VLM offline")

        with patch("os.path.exists", return_value=True):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=uuid4(),
                tecnica_nombre="Raspagem",
                mensaje_profesor="",
                idioma="pt",
            )

        mock_gemini.generar_texto_feedback.assert_called_once()
        assert res.feedback_summary == "Informações insuficientes"
        assert res.feedback == "Não há informações suficientes nos manuais nem nas instruções do instrutor para avaliar esta técnica."

    def test_prioridad_2_mensaje_profesor_no_cae_en_informacion_insuficiente_si_judge_rechaza(self):
        facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen = self._setup_facade()
        mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = []
        mock_gemini.generar_texto_feedback.return_value = {
            "summary": "Base elevada",
            "correction": "Baja la cadera y controla las solapas como indicó tu profesor.",
        }
        mock_gemini.evaluar_fidelidad_grounding.return_value = {
            "faithfulness_score": 0.4,
            "unsupported_claims": ["Observación adicional"],
            "reasoning": "Diferencia menor",
        }

        with patch("os.path.exists", return_value=True):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=uuid4(),
                tecnica_nombre="Pasaje de Guardia",
                mensaje_profesor="Mantén la base baja, controla las solapas y evita levantar la cadera.",
                idioma="es",
            )

        assert res.feedback_summary != "Información insuficiente"
        assert "base baja" in res.feedback.lower()
        assert "solapas" in res.feedback.lower()

    def test_fallback_global_cuando_tecnica_solo_tiene_video_y_sin_manuales_propios(self):
        facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen = self._setup_facade()
        tec_id = uuid4()

        def fake_recuperar(vectores_consulta, tecnica_id=None, limit=5, video_referencia_path=None):
            if tecnica_id is not None:
                return [
                    {
                        "id": "frame-video-1",
                        "score": 0.45,
                        "fuente_tipo": "video_referencia",
                        "fuente_nombre": "Video de referencia",
                        "contenido_texto": "Frame del video del instructor.",
                    }
                ]
            return [
                {
                    "id": "global-armbar-56",
                    "score": 0.88,
                    "alcance": "global",
                    "fuente_tipo": "manual_pdf",
                    "fuente_nombre": "BJJ-GuiaCompleto.pdf",
                    "pagina": 56,
                    "contenido_texto": "CHAVE DE BRAÇO NA MONTADA (ARMLOCK): Controlar la manga y cruzar la pierna sobre la cabeza.",
                }
            ]

        mock_qdrant.recuperar_evidencias_rag_multimodal.side_effect = fake_recuperar
        mock_gemini.generar_texto_feedback.return_value = {
            "summary": "Alineación en llave de brazo",
            "correction": "Controla la manga y pasa la pierna sobre la cabeza según el manual (p. 56).",
        }

        with patch("os.path.exists", return_value=True), \
             patch("corpocmente.domain.services.intelligence_facade.rerank_evidencias_multilingue", side_effect=lambda query_texto, evidencias, **kw: [e for e in evidencias if e.get("fuente_tipo") == "manual_pdf"]):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=tec_id,
                tecnica_nombre="Llave de brazo (Armbar)",
                mensaje_profesor="",
                idioma="es",
            )

        called_tecnica_ids = [c.kwargs.get("tecnica_id") for c in mock_qdrant.recuperar_evidencias_rag_multimodal.call_args_list]
        assert tec_id in called_tecnica_ids
        assert None in called_tecnica_ids
        assert res.feedback_summary != "Información insuficiente"
        assert "Controla la manga y pasa la pierna sobre la cabeza" in res.feedback
        assert "p. 56" not in res.feedback

    def test_reranker_encuentra_tecnica_en_chunk_largo_y_no_premia_placeholder_vacio(self):
        from corpocmente.domain.services.rag_reranker import rerank_evidencias_multilingue, Qwen3VLRerankerCrossEncoder

        texto_largo = (
            "[Página 1] Índice general de técnicas de suelo...\n" + ("Texto introductorio. " * 120) +
            "\n[Página 20]\n15 - 160 - UDE-HISHIGI-JUJI-GATAME\n"
            "Descrição I - Após estabilizar a montada, Tori agarra o kimono e passa a perna sobre a cabeça."
        )
        evidencias = [
            {
                "id": "img_placeholder",
                "score": 0.42,
                "fuente_tipo": "manual_pdf",
                "fuente_nombre": "Manual 1",
                "media_path": "/tmp/pag_20.png",
                "contenido_texto": "[Imagen: Página 20 del manual PDF]",
            },
            {
                "id": "chunk_largo_real",
                "score": 0.48,
                "fuente_tipo": "manual_pdf",
                "fuente_nombre": "Manual 1",
                "contenido_texto": texto_largo,
            },
        ]

        captured_docs = []

        def fake_rerank(query, documents, instruction=None):
            captured_docs.extend(documents)
            return [0.22 if "sin texto" in d else 0.21 for d in documents]

        with patch.object(Qwen3VLRerankerCrossEncoder, "rerank_pairs", side_effect=fake_rerank):
            ranked = rerank_evidencias_multilingue("Llave de brazo desde la Montada", evidencias, top_k=2)

        assert any("UDE-HISHIGI-JUJI-GATAME" in d for d in captured_docs)
        assert ranked[0]["id"] == "chunk_largo_real"
        assert ranked[0]["rerank_score"] >= UMBRAL_RELEVANCIA_RAG

    def test_sanitizar_respuesta_coach_elimina_paginas_y_tori_uke(self):
        from corpocmente.domain.services.intelligence_facade import _sanitizar_respuesta_coach

        raw = "Tori debe alinear el codo derecho y la rodilla sobre el hombro de Uke (p. 20)."
        limpio = _sanitizar_respuesta_coach(raw, idioma="es")
        assert "Tori" not in limpio and "tori" not in limpio
        assert "Uke" not in limpio and "uke" not in limpio
        assert "(p. 20)" not in limpio
        assert "Debes alinear el codo derecho" in limpio
        assert "tu compañero" in limpio
