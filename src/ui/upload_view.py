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
                    Técnica Maestra Homologada por el Profesor
                </div>
                """,
                unsafe_allow_html=True,
            )

            if tecnicas_disponibles:
                tecnica_elegida = st.selectbox(
                    "Seleccionar Técnica del Catálogo Oficial",
                    options=tecnicas_disponibles,
                    format_func=lambda t: f"{t.nombre} ({t.categoria_tecnica} - {t.posicion_origen})",
                    help="Técnica canónica grabada y parametrizada por el Head Coach Humberto Tavares.",
                )
                id_tecnica_seleccionada = tecnica_elegida.id
                nombre_tecnica_display = tecnica_elegida.nombre
                categoria_display = tecnica_elegida.categoria_tecnica
                posicion_display = tecnica_elegida.posicion_origen
                ventana_display = int(tecnica_elegida.ventana_sakoe_chiba * 100)
                video_patron_display = tecnica_elegida.video_url
            else:
                st.warning("No hay técnicas registradas por el profesor. Ingrese al 'Panel Profesor' para homologar una.")
                id_tecnica_seleccionada = uuid4()
                nombre_tecnica_display = "Armbar desde Guardia Cerrada"
                categoria_display = "Llave de Brazo"
                posicion_display = "Guardia Cerrada"
                ventana_display = 15
                video_patron_display = "armbar_patron_oficial.mp4"

            st.markdown(
                f"""
                <div style="background-color: #1A1E26; border: 1px solid #2B303C; border-radius: 6px; padding: 12px; margin-top: 14px;">
                    <div style="color: #8B949E; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;">Molde Cinemático Activo del Profesor</div>
                    <div style="color: #FFFFFF; font-weight: 700; font-size: 0.95rem; margin-top: 2px;">{nombre_tecnica_display}</div>
                    <div style="color: #D90429; font-size: 0.8rem; margin-top: 4px;">Categoría: {categoria_display} &middot; Origen: {posicion_display}</div>
                    <div style="color: #8B949E; font-size: 0.75rem; margin-top: 4px;">Ventana DTW Sakoe-Chiba: {ventana_display}% &middot; Video Patrón: {video_patron_display.split('/')[-1]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_upload:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-bottom: 12px; border-bottom: 2px solid #D90429; padding-bottom: 6px;">
                    Grabación de Ejecución en Pareja
                </div>
                """,
                unsafe_allow_html=True,
            )

            archivo_subido = st.file_uploader(
                "Cargar archivo de video",
                type=["mp4", "mov"],
                help="Requisito contractual: archivo en formato MP4 o MOV. Tamaño máximo: 5.0 MB (RF-07). Duración recomendada: hasta 6.0 segundos (RP-01).",
            )

            archivo_valido = False
            if archivo_subido is not None:
                tamano_mb = archivo_subido.size / (1024 * 1024)
                if tamano_mb > 5.0:
                    st.error(
                        f"Rechazo de archivo: El tamaño ({tamano_mb:.2f} MB) supera el límite contractual de 5.0 MB (RF-07). "
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
                "Ejecutar Análisis Biomecánico",
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
