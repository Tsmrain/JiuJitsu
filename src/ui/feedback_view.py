"""
Vista de Entrega y Retroalimentación Visual Biomecánica (Craig Larman / RF-05, RF-10).
Diseño Full-Width, sobrio, sin emojis y orientado a visualización técnica de alto impacto.
"""

from pathlib import Path
import streamlit as st
from src.services.controllers.analisis_controller import DiagnosticoDTO

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def render_feedback_view() -> None:
    """
    Renderiza la retroalimentación cinemática oficial contrastando el video de ejecución
    con el fotograma clave anotado por OpenCV y el diagnóstico biomecánico determinista.
    """
    diagnostico: DiagnosticoDTO = st.session_state.get("diagnostico")

    if diagnostico is None:
        st.info("No hay diagnóstico activo en sesión. Realice una evaluación previa.")
        if st.button("Ir al Módulo de Carga"):
            st.session_state["current_view"] = "upload"
            st.rerun()
        return

    nombre_tecnica = st.session_state.get("tecnica_nombre", "Técnica Maestra")

    # Encabezado del reporte oficial
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; border-bottom: 1px solid #282C34; padding-bottom: 12px;">
            <div>
                <div style="color: #D90429; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                    Reporte de Auditoría Técnica
                </div>
                <div style="color: #FFFFFF; font-size: 1.4rem; font-weight: 800; text-transform: uppercase;">
                    {nombre_tecnica}
                </div>
            </div>
            <div style="color: #8B949E; font-size: 0.85rem;">
                Motor Cinemático: MediaPipe + Filtro Kalman + DTW (Sakoe-Chiba)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Disposición en dos columnas anchas ocupando toda la pantalla
    col_video, col_anotado = st.columns([1, 1], gap="large")

    with col_video:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1rem; margin-bottom: 10px; border-bottom: 2px solid #2D323E; padding-bottom: 6px;">
                    Registro de Video del Practicante
                </div>
                """,
                unsafe_allow_html=True,
            )

            video_bytes = st.session_state.get("video_bytes")
            if video_bytes:
                st.video(video_bytes)
            else:
                st.info("Video almacenado en búfer de sesión.")

            st.caption(f"Archivo de origen: {st.session_state.get('video_nombre', 'ejecucion.mp4')}")

    with col_anotado:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1rem; margin-bottom: 10px; border-bottom: 2px solid #D90429; padding-bottom: 6px;">
                    Fotograma Clave Anotado (OpenCV)
                </div>
                """,
                unsafe_allow_html=True,
            )

            if diagnostico.estado == "SIN_FALLAS":
                st.success(
                    "Ejecución Técnica Conforme: La trayectoria articular respetó los márgenes de tolerancia "
                    "homologados para el currículo oficial. No se detectaron quiebres de postura significativos."
                )
                st.metric(
                    label="Desviación Angular Máxima",
                    value=f"{diagnostico.desviacion_maxima:.1f} grados",
                    delta="Dentro de Norma Homologada",
                    delta_color="normal",
                )
            else:
                if diagnostico.imagen_url:
                    st.image(
                        diagnostico.imagen_url,
                        caption="Segmento articular en falla resaltado en rojo (Compresión JPEG < 100 KB / RP-02)",
                        width="stretch",
                    )
                else:
                    st.info("Fotograma clave generado y registrado.")

                # Panel de diagnóstico detallado
                st.markdown(
                    f"""
                    <div style="background-color: #1A1518; border: 1px solid rgba(217, 4, 41, 0.5); border-left: 5px solid #D90429; border-radius: 6px; padding: 16px; margin-top: 14px;">
                        <div style="color: #D90429; font-weight: 700; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;">Falla Biomecánica Identificada</div>
                        <div style="color: #FFFFFF; font-size: 1.05rem; font-weight: 700; margin-top: 4px;">Articulación: {diagnostico.articulacion_afectada.replace('_', ' ').title()}</div>
                        <div style="color: #E63946; font-size: 0.95rem; font-weight: 600; margin-top: 2px;">Desviación angular: {diagnostico.desviacion_maxima:.1f}&deg;</div>
                        <div style="color: #C9D1D9; font-size: 0.9rem; margin-top: 8px; line-height: 1.4;">
                            <strong>Causa Motriz:</strong> {diagnostico.explicacion_error}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.divider()

    # Barra inferior de acciones
    col_btn1, col_btn2, _ = st.columns([1, 1.2, 2.5])
    with col_btn1:
        if st.button("Nueva Evaluación", width="stretch"):
            st.session_state["diagnostico"] = None
            st.session_state["current_view"] = "upload"
            st.rerun()

    with col_btn2:
        if st.button("Historial de Progresión", width="stretch"):
            st.session_state["current_view"] = "progression"
            st.rerun()
