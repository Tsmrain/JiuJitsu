import pytest
from src.domain.services.rule_engine import RuleEngine
from src.domain.entities import TecnicaMaestra, ReglaBiomecanica


class TestRuleEngine:
    """Pruebas unitarias para el motor de reglas deterministas (RF-10 - TDD)."""

    def test_es_critico_umbral_defecto(self):
        """Prueba: evaluación de umbral de 15 grados."""
        assert not RuleEngine.es_critico(14.9)
        assert RuleEngine.es_critico(15.1)

    def test_generar_diagnostico_plantilla_defecto(self):
        """Prueba: generación de mensaje pedagógico por defecto."""
        msg = RuleEngine.generar_diagnostico("rodilla_izq", 45.2)
        assert "Rodilla izquierda desviada 45.2°" in msg

    def test_generar_diagnostico_regla_personalizada(self):
        """Prueba: generación de mensaje a partir de regla registrada en TecnicaMaestra."""
        regla = ReglaBiomecanica(
            articulacion_clave="codo_izq",
            umbral_angular_tolerado=20.0,
            descripcion_error="Falta de presión en palanca de codo"
        )
        tecnica = TecnicaMaestra(
            nombre="Armbar Clásico",
            reglas=[regla]
        )

        msg = RuleEngine.generar_diagnostico("codo_izq", 25.0, tecnica=tecnica)
        assert "Falta de presión en palanca de codo" in msg
        assert "25.0°" in msg
