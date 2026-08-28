"""
Vista de Entrega y Retroalimentación Visual Biomecánica (Craig Larman / RF-05, RF-10).
"""

import streamlit as st
from src.services.controllers.analisis_controller import DiagnosticoDTO


def render_feedback_view() -> None:
    """
    Renderiza el diagnóstico biomecánico interactivo: comparación entre el video original
    y el fotograma clave anotado con OpenCV con explicación motriz determinista.
    """
    diagnostico: DiagnosticoDTO = st.session_state.get("diagnostico")

    if diagnostico is None:
        st.info("No hay diagnóstico activo para mostrar. Por favor realiza una evaluación primero.")
        if st.button("Ir al Módulo de Carga"):
            st.session_state["current_view"] = "upload"
            st.rerun()
        return

    nombre_tecnica = st.session_state.get("tecnica_nombre", "Técnica Maestra")

    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h2 style="color: #1D3557; margin-bottom: 0;">📊 Diagnóstico Biomecánico Oficial</h2>
            <p style="color: #666; font-size: 0.95rem;">
                Evaluación técnica para: <strong>{nombre_tecnica}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Disposición en dos columnas simétricas
    col_video, col_anotado = st.columns([1, 1], gap="medium")

    with col_video:
        st.markdown("### 🎥 Video Original del Practicante")
        video_bytes = st.session_state.get("video_bytes")
        if video_bytes:
            st.video(video_bytes)
        else:
            st.info("Video disponible en almacenamiento local temporal.")

        st.caption(f"Archivo: `{st.session_state.get('video_nombre', 'ejecucion.mp4')}`")

    with col_anotado:
        st.markdown("### 🎯 Fotograma Clave de Falla (OpenCV)")

        if diagnostico.estado == "SIN_FALLAS":
            st.success(
                "🎉 **¡Ejecución Técnica Sobresaliente!**\n\n"
                "Todas las articulaciones evaluadas respetaron los umbrales de tolerancia canónica homologados por el Head Coach. "
                "No se detectaron discrepancias mecánicas significativas."
            )
            st.metric(
                label="Desviación Máxima Registrada",
                value=f"{diagnostico.desviacion_maxima:.1f}°",
                delta="Dentro de norma",
                delta_color="normal",
            )
        else:
            # Fotograma anotado disponible vía URL de OBS o simulación
            if diagnostico.imagen_url:
                st.image(
                    diagnostico.imagen_url,
                    caption="Fotograma Clave con Anotación Articular (OpenCV / ~80 KB)",
                    use_container_width=True,
                )
            else:
                st.info("Fotograma anotado generado y procesado.")

            # Tarjeta de retroalimentación pedagógica
            st.warning(
                f"⚠️ **Falla Biomecánica Detectada**\n\n"
                f"**Articulación:** `{diagnostico.articulacion_afectada}`\n\n"
                f"**Desviación Angular:** `{diagnostico.desviacion_maxima:.1f}°`\n\n"
                f"**Causa Motriz:** {diagnostico.explicacion_error}"
            )

    st.divider()

    # Barra inferior de acciones
    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
    with col_btn1:
        if st.button("🔄 Nueva Evaluación", type="primary", use_container_width=True):
            st.session_state["diagnostico"] = None
            st.session_state["current_view"] = "upload"
            st.rerun()

    with col_btn2:
        if st.button("📈 Ver Historial Completo", use_container_width=True):
            st.session_state["current_view"] = "progression"
            st.rerun()
