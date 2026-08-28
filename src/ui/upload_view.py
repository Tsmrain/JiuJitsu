"""
Vista de Carga de Video y Configuración del Análisis Biomecánico (Craig Larman / RF-07, CU-02).
Diseño Full-Width, responsivo, sobrio y sin emojis.
"""

import os
from pathlib import Path
from uuid import uuid4
import streamlit as st
from src.services.controllers.analisis_controller import (
    AnalisisBiomecanicoController,
    TokenInvalidoError,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
RUTA_LOGO = str(ROOT_DIR / "assets" / "corpo_e_mente_logo.png")


def render_upload_view(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza el panel de evaluación técnica y subida de video utilizando todo el ancho disponible.
    """
    # Barra superior con marca oficial y acciones de navegación
    col_marca, col_acciones = st.columns([3, 1.2])

    with col_marca:
        col_img, col_txt = st.columns([0.15, 0.85])
        with col_img:
            if os.path.exists(RUTA_LOGO):
                st.image(RUTA_LOGO, width=65)
        with col_txt:
            st.markdown(
                """
                <div style="padding-top: 2px;">
                    <div style="color: #FFFFFF; font-weight: 800; font-size: 1.25rem; letter-spacing: 0.8px; text-transform: uppercase;">
                        Corpo e Mente Jiu Jitsu - Judo
                    </div>
                    <div style="color: #8B949E; font-size: 0.85rem;">
                        Sala de Auditoría Cinemática &middot; Patrones Técnicos Homologados
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_acciones:
        col_a1, col_a2, col_a3 = st.columns([1, 1.3, 1])
        with col_a1:
            if st.button("Mi Progreso", width="stretch"):
                st.session_state["current_view"] = "progression"
                st.rerun()
        with col_a2:
            if st.button("Panel Profesor", width="stretch"):
                st.session_state["current_view"] = "coach"
                st.rerun()
        with col_a3:
            if st.button("Cerrar Sesión", width="stretch"):
                st.session_state["authenticated"] = False
                st.session_state["token"] = None
                st.session_state["diagnostico"] = None
                st.session_state["current_view"] = "token"
                st.rerun()

    st.divider()

    # Contenedor principal en dos paneles anchos
    col_config, col_upload = st.columns([1.1, 1.4], gap="large")

    tecnicas_disponibles = controller.listar_tecnicas()

    with col_config:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-bottom: 12px; border-bottom: 2px solid #D90429; padding-bottom: 6px;">
                    Técnica que Enseñó el Profesor Hoy
                </div>
                """,
                unsafe_allow_html=True,
            )

            if tecnicas_disponibles:
                tecnica_elegida = st.selectbox(
                    "Selecciona la técnica que enseñó el profesor",
                    options=tecnicas_disponibles,
                    format_func=lambda t: t.nombre,
                    help="Técnica canónica grabada por el Head Coach Humberto Tavares para la clase.",
                )
                id_tecnica_seleccionada = tecnica_elegida.id
                nombre_tecnica_display = tecnica_elegida.nombre
                video_patron_display = tecnica_elegida.video_url
            else:
                st.warning("No hay técnicas registradas por el profesor. Ingrese al 'Panel Profesor' para publicar una.")
                id_tecnica_seleccionada = uuid4()
                nombre_tecnica_display = "Cómo finalizar desde la montada y hacer una americana"
                video_patron_display = "americana_montada_profesor.mp4"

            st.markdown(
                f"""
                <div style="background-color: #1A1E26; border: 1px solid #2B303C; border-left: 3px solid #D90429; border-radius: 6px; padding: 14px; margin-top: 14px;">
                    <div style="color: #8B949E; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;">Demostración del Profesor Humberto Tavares</div>
                    <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-top: 2px;">{nombre_tecnica_display}</div>
                    <div style="color: #C9D1D9; font-size: 0.82rem; margin-top: 8px; line-height: 1.4;">
                        El profesor demostró esta técnica en el tatami. Tu intento será evaluado comparando tus ángulos articulares directamente contra la ejecución del profesor.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_upload:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-bottom: 12px; border-bottom: 2px solid #D90429; padding-bottom: 6px;">
                    Tu Turno: Sube tu Video en Pareja
                </div>
                """,
                unsafe_allow_html=True,
            )

            archivo_subido = st.file_uploader(
                "Video de tu intento con tu compañero de tatami",
                type=["mp4", "mov"],
                help="Sube la grabación de tu intento con tu compañero (formato MP4 o MOV, máximo 5 MB).",
            )

            archivo_valido = False
            if archivo_subido is not None:
                tamano_mb = archivo_subido.size / (1024 * 1024)
                if tamano_mb > 5.0:
                    st.error(
                        f"Rechazo de archivo: El tamaño ({tamano_mb:.2f} MB) supera el límite de 5.0 MB (RF-07). "
                        f"Reduzca la resolución o comprima la grabación antes de reintentar."
                    )
                    archivo_valido = False
                else:
                    st.info(
                        f"Archivo cargado correctamente: {archivo_subido.name} ({tamano_mb:.2f} MB)"
                    )
                    archivo_valido = True

            st.write("")
            boton_analizar = st.button(
                "Auditar Mi Técnica contra la del Profesor",
                disabled=not archivo_valido,
                width="stretch",
            )

    if boton_analizar and archivo_subido is not None:
        token_sesion = st.session_state.get("token", "")
        video_bytes = archivo_subido.read()

        with st.spinner("Procesando cinemática articular en Huawei Cloud Serverless..."):
            try:
                diagnostico = controller.ejecutar_analisis(
                    token=token_sesion,
                    video_bytes=video_bytes,
                    id_tecnica=id_tecnica_seleccionada,
                )

                if diagnostico.estado == "ABORTADO_OCLUSION":
                    st.warning(
                        "Evaluación Interrumpida: Política Zero-Persistence por Oclusión Visual (RF-11).\n\n"
                        f"{diagnostico.explicacion_error}\n\n"
                        "Directiva de captura: Sitúe la cámara en ángulo oblicuo a 45 grados para asegurar que el cuerpo del oponente "
                        "no oculte los segmentos articulares durante más de 1.5 segundos consecutivos."
                    )
                else:
                    st.session_state["diagnostico"] = diagnostico
                    st.session_state["video_bytes"] = video_bytes
                    st.session_state["video_nombre"] = archivo_subido.name
                    st.session_state["tecnica_nombre"] = nombre_tecnica_display
                    st.session_state["current_view"] = "feedback"
                    st.rerun()

            except TokenInvalidoError as err:
                st.error(f"Fallo de autorización: {str(err)}")
                st.session_state["authenticated"] = False
                st.session_state["current_view"] = "token"
                st.rerun()
            except Exception as err:
                st.error(f"Error de procesamiento del sistema: {str(err)}")
