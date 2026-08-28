"""
Vista de Control de Acceso y Validación de Token de Membresía (Craig Larman / RF-09).
"""

import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController


def render_token_gate(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza la compuerta de autenticación mediante token de activación (RF-09).
    Restringe el acceso al analizador hasta validar la vigencia de la membresía.
    """
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="color: #1D3557; margin-bottom: 5px;">🥋 Corpo & Mente Jiu-Jitsu</h1>
            <h3 style="color: #E63946; font-weight: 500; margin-top: 0;">Plataforma de Auditoría Biomecánica Asistida por IA</h3>
            <p style="color: #555; font-size: 0.95rem;">
                Sistema de evaluación cinemática curricular para practicantes de Brazilian Jiu-Jitsu.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Acceso de Practicante")
        st.write(
            "Ingresa el **código de activación** suministrado por tu Head Coach para desbloquear el módulo de análisis."
        )

        with st.form(key="form_token_gate"):
            token_input = st.text_input(
                "Token de Membresía Alfanumérico",
                type="password",
                placeholder="Ej. TOKEN_VALIDO_TEST",
                help="Código alfanumérico emitido al renovar o registrar tu membresía federativa.",
            )
            submit_token = st.form_submit_button("Validar Membresía", use_container_width=True)

        st.caption("💡 *Modo Demostración / Desarrollo: Usa `TOKEN_VALIDO_TEST` para ingresar.*")

        if submit_token:
            if not token_input or not token_input.strip():
                st.error("Por favor ingresa un código de activación.")
                return

            token_limpio = token_input.strip()
            # Validación a través del repositorio del controlador
            if controller.token_repo.validar_token(token_limpio):
                st.session_state["authenticated"] = True
                st.session_state["token"] = token_limpio
                st.session_state["current_view"] = "upload"
                st.success("✅ Membresía verificada y vigente. Accediendo al laboratorio...")
                st.rerun()
            else:
                st.error(
                    "❌ Token inválido, expirado o revocado. Contacta al Head Coach para obtener un código vigente."
                )
