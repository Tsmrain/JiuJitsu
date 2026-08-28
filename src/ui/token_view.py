"""
Vista de Control de Acceso y Validación de Token de Membresía (Craig Larman / RF-09).
Diseño sobrio, sin emojis, centrado en la identidad visual oficial de Corpo e Mente.
"""

import os
from pathlib import Path
import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
RUTA_LOGO = str(ROOT_DIR / "assets" / "corpo_e_mente_logo.png")


def render_token_gate(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza la compuerta de autenticación mediante token de activación (RF-09).
    """
    # Contenedor central adaptable
    col_izq, col_centro, col_der = st.columns([1, 1.6, 1])

    with col_centro:
        st.write("")
        # Despliegue del logotipo oficial
        if os.path.exists(RUTA_LOGO):
            col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
            with col_l2:
                st.image(RUTA_LOGO, use_container_width=True)

        st.markdown(
            """
            <div style="text-align: center; margin-top: 10px; margin-bottom: 25px;">
                <h2 style="color: #FFFFFF; font-weight: 800; letter-spacing: 1px; margin-bottom: 4px; text-transform: uppercase;">
                    CORPO E MENTE JIU JITSU - JUDO
                </h2>
                <div style="color: #D90429; font-weight: 700; font-size: 1rem; letter-spacing: 1.5px; text-transform: uppercase;">
                    Academia Humberto Tavares
                </div>
                <p style="color: #8B949E; font-size: 0.9rem; margin-top: 8px;">
                    Plataforma de Auditoría Biomecánica y Evaluación Cinemática Serverless
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown(
                """
                <div style="margin-bottom: 16px;">
                    <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-bottom: 4px;">
                        Autenticación de Practicante
                    </div>
                    <div style="color: #8B949E; font-size: 0.85rem;">
                        Ingrese el código de activación alfanumérico emitido por su Head Coach para acceder al analizador (RF-09).
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form(key="form_token_gate"):
                token_input = st.text_input(
                    "Código de Activación",
                    type="password",
                    placeholder="Ingrese su clave de membresía",
                    help="Código emitido al registrar o renovar la matrícula oficial.",
                )
                submit_token = st.form_submit_button(
                    "Validar Membresía",
                    use_container_width=True,
                )

            st.caption("Entorno de desarrollo local: Código de verificación disponible: `TOKEN_VALIDO_TEST`")

        if submit_token:
            if not token_input or not token_input.strip():
                st.error("Debe ingresar un código de activación.")
                return

            token_limpio = token_input.strip()
            if controller.token_repo.validar_token(token_limpio):
                st.session_state["authenticated"] = True
                st.session_state["token"] = token_limpio
                st.session_state["current_view"] = "upload"
                st.success("Membresía confirmada y vigente. Redirigiendo a la sala de evaluación...")
                st.rerun()
            else:
                st.error(
                    "Código de activación inválido o expirado. Contacte a la administración de la academia para renovar su credencial."
                )
