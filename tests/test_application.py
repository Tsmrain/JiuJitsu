# tests/test_application.py
import pytest
from src.application.controllers import EvaluacionController
from src.infrastructure.mocks import MockYOLOEngine, MockGeminiService, MockTecnicaRepository

class TestCasoDeUsoEvaluacion:
    
    def test_evaluacion_ejecucion_correcta_sin_desviaciones(self):
        """Verifica el flujo cuando el alumno ejecuta la técnica igual al maestro."""
        controller = EvaluacionController(
            inference_engine=MockYOLOEngine(desviacion_grados=0.0),
            generation_service=MockGeminiService(),
            tecnica_repository=MockTecnicaRepository()
        )
        
        resultado = controller.evaluar_ejecucion("video_alumno.mp4", "armbar_guardia")
        
        assert resultado["es_valido"] is True
        assert resultado["total_desviaciones"] == 0
        assert "Excelente ejecución" in resultado["consejo_pedagogico"]

    def test_evaluacion_con_desviacion_biomecanica(self):
        """Verifica que detecte el error y entregue la retroalimentación de IA."""
        controller = EvaluacionController(
            inference_engine=MockYOLOEngine(desviacion_grados=25.0), # Codo desviado 25°
            generation_service=MockGeminiService(),
            tecnica_repository=MockTecnicaRepository()
        )
        
        resultado = controller.evaluar_ejecucion("video_alumno.mp4", "armbar_guardia")
        
        assert resultado["es_valido"] is False
        assert resultado["total_desviaciones"] == 1
        # Corrección: acceder al primer elemento de la lista de desviaciones
        assert resultado["desviaciones"][0]["articulacion"] == "Codo Derecho"
        assert pytest.approx(resultado["desviaciones"][0]["desviacion"], 0.1) == 25.0
        assert "desajuste en Codo Derecho de 25.0°" in resultado["consejo_pedagogico"]

    def test_evaluacion_tecnica_no_encontrada(self):
        """Verifica que lance ValueError si la técnica patrón no existe."""
        class MockRepoVacio(MockTecnicaRepository):
            def obtener_patron(self, id_tecnica: str):
                return None

        controller = EvaluacionController(
            inference_engine=MockYOLOEngine(),
            generation_service=MockGeminiService(),
            tecnica_repository=MockRepoVacio()
        )
        with pytest.raises(ValueError, match="no encontrada"):
            controller.evaluar_ejecucion("video.mp4", "tecnica_inexistente")

    def test_solicitar_evaluacion_cu02_con_sintesis_rag_fallback(self):
        """Caso de Uso CU-02: Verifica que EvaluacionController coordina RAG y retorna DTO enriquecido."""
        controller = EvaluacionController(
            inference_engine=MockYOLOEngine(desviacion_grados=20.0),
            generation_service=MockGeminiService(),
            tecnica_repository=MockTecnicaRepository(),
        )

        resultado = controller.solicitar_evaluacion("video_test.mp4", "armbar_guardia")

        assert resultado["es_valido"] is False
        assert "consejo" in resultado
        assert "score_similitud_rag" in resultado
        assert "usó_fallback_rag" in resultado
        assert resultado["usó_fallback_rag"] is True
        assert "punto_rojo" in resultado

    def test_solicitar_evaluacion_cu02_con_contexto_recuperado(self):
        """Caso de Uso CU-02: Cuando RAG provee contexto válido (>0.65), no usa fallback."""
        from unittest.mock import MagicMock
        from src.services.sintesis_pedagogica_service import SintesisPedagogicaService
        from src.domain.models import ConfiguracionRAG

        mock_sintesis = MagicMock()
        mock_sintesis.generar_feedback_contextualizado.return_value = {
            "consejo": None,
            "contexto_recuperado": "Ajuste biomecánico: presionar con los talones.",
            "score_similitud": 0.88,
            "usó_fallback": False,
            "titulo_fuente": "Manual Gracie",
        }

        controller = EvaluacionController(
            inference_engine=MockYOLOEngine(desviacion_grados=10.0),
            generation_service=MockGeminiService(),
            tecnica_repository=MockTecnicaRepository(),
            sintesis_service=mock_sintesis,
        )

        resultado = controller.solicitar_evaluacion("video_test.mp4", "armbar_guardia")

        assert resultado["usó_fallback_rag"] is False
        assert resultado["score_similitud_rag"] == 0.88
        assert "Ajuste biomecánico" in resultado["consejo"]
