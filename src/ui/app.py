"""
Punto de Entrada Principal de la Interfaz Gráfica (Streamlit / Craig Larman).
Diseño Full-Width, responsivo y adaptado a la identidad visual oficial de Corpo e Mente.
"""

import os
import sys
from pathlib import Path

# Garantizar que la raíz del proyecto esté en sys.path al invocar streamlit run
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from unittest.mock import MagicMock
import streamlit as st

from src.infrastructure.repositories.analisis_repository import AnalisisBiomecanicoRepository
from src.infrastructure.repositories.tecnica_repository import TecnicaMaestraRepository
from src.infrastructure.repositories.token_repository import TokenRepository
from src.infrastructure.storage.obs_adapter import HuaweiOBSStorageAdapter
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController
from src.services.pipeline_engine import PipelineBiomecanicoEngine
from src.ui.feedback_view import render_feedback_view
from src.ui.progression_view import render_progression_view
from src.ui.token_view import render_token_gate
from src.ui.upload_view import render_upload_view

RUTA_LOGO = str(ROOT_DIR / "assets" / "corpo_e_mente_logo.png")

# Configuración formal con diseño extendido (Full Width / Pantalla Completa)
st.set_page_config(
    page_title="CORPO E MENTE - Auditoría Biomecánica",
    page_icon=RUTA_LOGO if os.path.exists(RUTA_LOGO) else None,
    layout="wide",
    initial_sidebar_state="collapsed",
)


def aplicar_estilos_oficiales() -> None:
    """Inyecta el sistema de diseño CSS oficial con la paleta de colores del logo y responsividad total."""
    st.markdown(
        """
        <style>
            /* Reset y aprovechamiento de toda la pantalla */
            .main .block-container {
                max-width: 96% !important;
                padding-top: 1.2rem !important;
                padding-bottom: 2rem !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }

            /* Tipografía corporativa limpia */
            body, h1, h2, h3, h4, h5, p, span, label, div {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
            }

            /* Encabezado de aplicación */
            .app-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: linear-gradient(90deg, #101216 0%, #181B22 100%);
                border: 1px solid #282C34;
                border-left: 6px solid #D90429;
                border-radius: 8px;
                padding: 16px 24px;
                margin-bottom: 24px;
            }

            .app-header h1 {
                color: #FFFFFF !important;
                font-size: 1.6rem !important;
                font-weight: 800 !important;
                letter-spacing: 1px !important;
                margin: 0 !important;
                text-transform: uppercase;
            }

            .app-header p {
                color: #8B949E !important;
                font-size: 0.9rem !important;
                margin: 4px 0 0 0 !important;
            }

            /* Contenedor tipo tarjeta */
            .bjj-card {
                background-color: #14171E;
                border: 1px solid #262A34;
                border-radius: 8px;
                padding: 24px;
                margin-bottom: 20px;
            }

            /* Botones primarios en rojo oficial del logo */
            div.stButton > button {
                background-color: #D90429 !important;
                color: #FFFFFF !important;
                border: 1px solid #D90429 !important;
                border-radius: 6px !important;
                font-weight: 600 !important;
                font-size: 0.95rem !important;
                padding: 8px 18px !important;
                letter-spacing: 0.4px !important;
                transition: all 0.2s ease-in-out !important;
            }

            div.stButton > button:hover {
                background-color: #EF233C !important;
                border-color: #EF233C !important;
                box-shadow: 0 4px 14px rgba(217, 4, 41, 0.4) !important;
            }

            div.stButton > button:focus {
                box-shadow: 0 0 0 2px #FFFFFF, 0 0 0 4px #D90429 !important;
            }

            /* Personalización de entradas y cajas de selección */
            div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
                background-color: #161922 !important;
                border-color: #2D323E !important;
                color: #FFFFFF !important;
            }

            div[data-baseweb="select"] > div:focus-within, div[data-baseweb="input"] > div:focus-within {
                border-color: #D90429 !important;
            }

            /* Notificaciones de advertencia y error adaptadas */
            div[data-testid="stAlert"] {
                border-radius: 6px !important;
                border-left-width: 6px !important;
            }

            /* Adaptabilidad para dispositivos móviles y tabletas */
            @media (max-width: 900px) {
                .main .block-container {
                    max-width: 100% !important;
                    padding-left: 0.8rem !important;
                    padding-right: 0.8rem !important;
                }
                .app-header {
                    flex-direction: column;
                    text-align: center;
                    gap: 12px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def obtener_controlador() -> AnalisisBiomecanicoController:
    """Inicializa e inyecta dependencias al controlador."""
    token_repo = TokenRepository(session=None)
    tecnica_repo = TecnicaMaestraRepository(session=None)
    analisis_repo = AnalisisBiomecanicoRepository(session=None)

    ak = os.getenv("HUAWEI_OBS_AK", "")
    sk = os.getenv("HUAWEI_OBS_SK", "")
    server = os.getenv("HUAWEI_OBS_SERVER", "obs.la-south-2.myhuaweicloud.com")

    if ak and sk:
        storage_adapter = HuaweiOBSStorageAdapter(
            ak=ak,
            sk=sk,
            server=server,
            bucket_input="bjj-videos-input",
            bucket_output="bjj-reports-output",
        )
    else:
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_client.putObject.return_value = mock_resp
        mock_client.getObject.return_value = mock_resp
        storage_adapter = HuaweiOBSStorageAdapter(
            server=server,
            bucket_input="bjj-videos-input",
            bucket_output="bjj-reports-output",
            client=mock_client,
        )

    pipeline_engine = PipelineBiomecanicoEngine(ventana_sakoe_chiba_default=0.15, calidad_jpeg=85)

    return AnalisisBiomecanicoController(
        token_repo=token_repo,
        tecnica_repo=tecnica_repo,
        analisis_repo=analisis_repo,
        storage_adapter=storage_adapter,
        pipeline_engine=pipeline_engine,
    )


def inicializar_estado_sesion() -> None:
    """Inicializa las variables de estado reactivo."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "current_view" not in st.session_state:
        st.session_state["current_view"] = "token"
    if "diagnostico" not in st.session_state:
        st.session_state["diagnostico"] = None
    if "video_bytes" not in st.session_state:
        st.session_state["video_bytes"] = None


def main() -> None:
    """Punto de entrada y enrutamiento."""
    inicializar_estado_sesion()
    aplicar_estilos_oficiales()
    controller = obtener_controlador()

    if not st.session_state.get("authenticated"):
        render_token_gate(controller)
    else:
        vista_actual = st.session_state.get("current_view", "upload")

        if vista_actual == "upload":
            render_upload_view(controller)
        elif vista_actual == "feedback":
            render_feedback_view()
        elif vista_actual == "progression":
            render_progression_view(controller)
        else:
            render_upload_view(controller)

    # Pie institucional limpio y formal
    st.write("")
    st.markdown(
        """
        <div style="text-align: center; margin-top: 50px; border-top: 1px solid #262A34; padding-top: 16px; color: #6E7681; font-size: 0.8rem; letter-spacing: 0.5px;">
            CORPO E MENTE JIU JITSU - JUDO | HUMBERTO TAVARES<br/>
            PLATAFORMA DE AUDITORÍA BIOMECÁNICA SERVERLESS &middot; ARQUITECTURA DISTRIBUIDA
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
