"""
Pruebas Unitarias para la Capa de Presentación (Streamlit / Craig Larman / TDD).
"""

import unittest
import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController
from src.ui.app import inicializar_estado_sesion, obtener_controlador


class TestUIApp(unittest.TestCase):

    def setUp(self) -> None:
        # Limpiar session_state antes de cada prueba
        for key in list(st.session_state.keys()):
            del st.session_state[key]

    def test_inicializar_estado_sesion(self) -> None:
        """Prueba 1: Verifica que las variables reactivas de sesión se inicialicen con valores por defecto."""
        inicializar_estado_sesion()

        self.assertIn("authenticated", st.session_state)
        self.assertFalse(st.session_state["authenticated"])
        self.assertIn("current_view", st.session_state)
        self.assertEqual(st.session_state["current_view"], "token")
        self.assertIn("token", st.session_state)
        self.assertIsNone(st.session_state["token"])
        self.assertIn("diagnostico", st.session_state)
        self.assertIsNone(st.session_state["diagnostico"])

    def test_obtener_controlador_inyeccion_correcta(self) -> None:
        """Prueba 2: Verifica que obtener_controlador retorne una instancia configurada de AnalisisBiomecanicoController."""
        controller = obtener_controlador()

        self.assertIsInstance(controller, AnalisisBiomecanicoController)
        self.assertIsNotNone(controller.token_repo)
        self.assertIsNotNone(controller.tecnica_repo)
        self.assertIsNotNone(controller.analisis_repo)
        self.assertIsNotNone(controller.storage_adapter)
        self.assertIsNotNone(controller.pipeline_engine)


if __name__ == "__main__":
    unittest.main()
