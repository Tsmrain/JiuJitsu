"""
Punto de Entrada Principal de la Interfaz Gráfica (Streamlit / Craig Larman).
Orquesta la navegación reactiva y conecta las vistas con AnalisisBiomecanicoController.
"""

import os
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


# Configuración formal de la aplicación
st.set_page_config(
    page_title="Corpo & Mente - Auditoría Biomecánica",
    page_icon="🥋",
    layout="centered",
    initial_sidebar_state="collapsed",
)


@st.cache_resource
def obtener_controlador() -> AnalisisBiomecanicoController:
    """
    Inicializa e inyecta las dependencias del AnalisisBiomecanicoController.
    Si no existen variables de entorno de producción de Huawei Cloud / PostgreSQL,
    configura un entorno de desarrollo local controlado.
    """
    # 1. Repositorios de base de datos
    token_repo = TokenRepository(session=None)
    tecnica_repo = TecnicaMaestraRepository(session=None)
    analisis_repo = AnalisisBiomecanicoRepository(session=None)

    # 2. Adaptador de almacenamiento Huawei Cloud OBS (con fallback simulado si no hay credenciales)
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
        # Modo Demostración Local: cliente simulado para evitar caídas de red en desarrollo
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

    # 3. Motor del pipeline biomecánico
    pipeline_engine = PipelineBiomecanicoEngine(ventana_sakoe_chiba_default=0.15, calidad_jpeg=85)

    return AnalisisBiomecanicoController(
        token_repo=token_repo,
        tecnica_repo=tecnica_repo,
        analisis_repo=analisis_repo,
        storage_adapter=storage_adapter,
        pipeline_engine=pipeline_engine,
    )


def inicializar_estado_sesion() -> None:
    """Inicializa las variables de estado reactivo en st.session_state."""
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
    """Función de enrutamiento principal de vistas."""
    inicializar_estado_sesion()
    controller = obtener_controlador()

    # Enrutador de estados de navegación (Figura 5.7 del Capítulo V)
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

    # Pie de página institucional
    st.write("")
    st.markdown(
        """
        <div style="text-align: center; margin-top: 40px; border-top: 1px solid #E0E0E0; padding-top: 15px; color: #888; font-size: 0.8rem;">
            🥋 <strong>Corpo & Mente Brazilian Jiu-Jitsu Bolivia</strong> — Sistema de Auditoría Biomecánica Serverless<br/>
            Arquitectura Orientada a Objetos (Craig Larman) & Persistencia Relacional (Michael V. Mannino)
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
