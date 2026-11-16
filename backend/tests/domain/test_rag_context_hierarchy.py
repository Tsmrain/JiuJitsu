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

    def test_spanish_strategy_with_rag_context(self):
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Armbar",
            discrepancias=["Cadera baja"],
            mensaje_profesor="Instrucción que debe ignorarse",
            tiene_contexto_rag=True,
        )
        assert "REGLA ESTRICTA: Responde basándote ÚNICAMENTE en el contexto del manual adjunto." in prompt
        assert "EL CONTEXTO PUEDE ESTAR EN OTRO IDIOMA, TRADÚCELO Y RESPONDE EN ESPAÑOL." in prompt
        assert "Instrucción que debe ignorarse" not in prompt
        assert "(p. X)" in prompt

    def test_spanish_strategy_with_instructor_message_only(self):
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Armbar",
            discrepancias=["Cadera baja"],
            mensaje_profesor="Apretar rodillas firmemente",
            tiene_contexto_rag=False,
        )
        assert "REGLA ESTRICTA: Basa tu corrección únicamente en las instrucciones directas del profesor." in prompt
        assert "Apretar rodillas firmemente" in prompt
        assert "EL CONTEXTO PUEDE ESTAR EN OTRO IDIOMA" not in prompt

    def test_english_strategy_with_rag_context(self):
        strategy = EnglishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Triangle Choke",
            discrepancias=["Loose leg clamp"],
            mensaje_profesor="Should be ignored",
            tiene_contexto_rag=True,
        )
        assert "STRICT RULE: Base your response SOLELY on the attached manual context." in prompt
        assert "THE CONTEXT MAY BE IN ANOTHER LANGUAGE, TRANSLATE IT AND RESPOND IN ENGLISH." in prompt
        assert "Should be ignored" not in prompt
        assert "(p. X)" in prompt

    def test_english_strategy_with_instructor_message_only(self):
        strategy = EnglishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Triangle Choke",
            discrepancias=["Loose leg clamp"],
            mensaje_profesor="Cut angle to 90 degrees",
            tiene_contexto_rag=False,
        )
        assert "STRICT RULE: Base your correction solely on the direct instructions from the instructor." in prompt
        assert "Cut angle to 90 degrees" in prompt
        assert "THE CONTEXT MAY BE IN ANOTHER LANGUAGE" not in prompt

    def test_portuguese_strategy_with_rag_context(self):
        strategy = PortuguesePromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Mata-Leão",
            discrepancias=["Cotovelo aberto"],
            mensaje_profesor="Deve ser ignorado",
            tiene_contexto_rag=True,
        )
        assert "REGRA ESTRITA: Responda baseando-se UNICAMENTE no contexto do manual anexo." in prompt
        assert "O CONTEXTO PODE ESTAR EM OUTRO IDIOMA, TRADUZA-O E RESPONDA EM PORTUGUÊS." in prompt
        assert "Deve ser ignorado" not in prompt
        assert "(p. X)" in prompt

    def test_portuguese_strategy_with_instructor_message_only(self):
        strategy = PortuguesePromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            tecnica_nombre="Mata-Leão",
            discrepancias=["Cotovelo aberto"],
            mensaje_profesor="Esconda a mão atrás da cabeça",
            tiene_contexto_rag=False,
        )
        assert "REGRA ESTRITA: Baseie sua correção unicamente nas instruções diretas do professor." in prompt
        assert "Esconda a mão atrás da cabeça" in prompt
        assert "O CONTEXTO PODE ESTAR EM OUTRO IDIOMA" not in prompt

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

    def test_prioridad_1_rag_manual_supera_umbral_y_ignora_mensaje_profesor(self):
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
            "correction": "Baja el hombro como indica el manual (p. 142).",
        }

        with patch("os.path.exists", return_value=True):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=uuid4(),
                tecnica_nombre="Americana",
                mensaje_profesor="Instrucción del instructor que debe ser descartada por P1",
                idioma="es",
            )

        # Gemini debe haber sido llamado
        mock_gemini.generar_texto_feedback.assert_called_once()
        call_prompt = mock_gemini.generar_texto_feedback.call_args.args[0]
        evidencias_visuales = mock_gemini.generar_texto_feedback.call_args.kwargs.get("evidencias_visuales")

        # Debe contener la regla estricta de manual y cita cross-lingual
        assert "REGLA ESTRICTA: Responde basándote ÚNICAMENTE en el contexto del manual adjunto." in call_prompt
        assert "EL CONTEXTO PUEDE ESTAR EN OTRO IDIOMA, TRADÚCELO Y RESPONDE EN ESPAÑOL." in call_prompt
        assert "Underhook the arm and drive shoulder pressure" in call_prompt
        # El mensaje del profesor NO debe estar en el prompt
        assert "Instrucción del instructor que debe ser descartada" not in call_prompt
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

        assert "REGLA ESTRICTA: Basa tu corrección únicamente en las instrucciones directas del profesor." in call_prompt
        assert "Fija la muñeca al suelo y desliza el codo como un pincel." in call_prompt
        # El contenido irrelevante del manual NO debe ser inyectado
        assert "Conceptos no relacionados con Americana" not in call_prompt
        # Evidencias visuales vacías para no distraer al VLM con manuales no relevantes
        assert len(evidencias_visuales) == 0

    def test_prioridad_3_sin_manuales_ni_mensaje_omite_gemini_y_retorna_fallback_es(self):
        facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen = self._setup_facade()

        # Sin manuales
        mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = []

        with patch("os.path.exists", return_value=True):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=uuid4(),
                tecnica_nombre="Americana",
                mensaje_profesor="",  # Vacío
                idioma="es",
            )

        # Gemini NO debe haber sido invocado para evitar alucinaciones
        mock_gemini.generar_texto_feedback.assert_not_called()
        assert res.feedback_summary == "Información insuficiente"
        assert res.feedback == "No hay información suficiente en los manuales ni en las instrucciones del instructor para evaluar esta técnica."

    def test_prioridad_3_sin_manuales_ni_mensaje_omite_gemini_y_retorna_fallback_en(self):
        facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen = self._setup_facade()
        mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = []

        with patch("os.path.exists", return_value=True):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=uuid4(),
                tecnica_nombre="Kimura",
                mensaje_profesor="   ",  # Solo espacios
                idioma="en",
            )

        mock_gemini.generar_texto_feedback.assert_not_called()
        assert res.feedback_summary == "Insufficient information"
        assert res.feedback == "There is not enough information in the manuals or instructor instructions to evaluate this technique."

    def test_prioridad_3_sin_manuales_ni_mensaje_omite_gemini_y_retorna_fallback_pt(self):
        facade, mock_yolo, mock_qdrant, mock_gemini, mock_qwen = self._setup_facade()
        mock_qdrant.recuperar_evidencias_rag_multimodal.return_value = []

        with patch("os.path.exists", return_value=True):
            res = facade.ejecutar_analisis_completo(
                video_path="/tmp/video.mp4",
                tecnica_id=uuid4(),
                tecnica_nombre="Raspagem",
                mensaje_profesor="",
                idioma="pt",
            )

        mock_gemini.generar_texto_feedback.assert_not_called()
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
        assert "p. 56" in res.feedback
