"""
Vista de Entrega y Retroalimentación Visual Biomecánica (Craig Larman / RF-05, RF-10).
Diseño Full-Width, sobrio, sin emojis y orientado a visualización técnica de alto impacto.
"""

import os
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
                foto_a_mostrar = None
                if getattr(diagnostico, "imagen_bytes", None):
                    foto_a_mostrar = diagnostico.imagen_bytes
                elif diagnostico.imagen_url:
                    foto_a_mostrar = diagnostico.imagen_url

                if foto_a_mostrar is not None:
                    st.image(
                        foto_a_mostrar,
                        caption="Segmento articular en falla resaltado en rojo (Compresión JPEG < 100 KB / RP-02)",
                        use_container_width=True,
                    )
                else:
                    st.info("Fotograma clave generado y registrado.")

                # Cálculo de exceso angular y severidad técnica
                tolerancia_base = 15.0
                exceso_angular = max(0.0, diagnostico.desviacion_maxima - tolerancia_base)

                if diagnostico.desviacion_maxima <= 25.0:
                    badge_severidad = "Ajuste Angular Leve"
                    color_severidad = "#FFB703"
                elif diagnostico.desviacion_maxima <= 45.0:
                    badge_severidad = "Corrección Postural Moderada"
                    color_severidad = "#FB8500"
                else:
                    badge_severidad = "Desalineación Severa / Pérdida de Control en Tatami"
                    color_severidad = "#D90429"

                # Panel de diagnóstico técnico detallado
                st.markdown(
                    f"""
                    <div style="background-color: #1A1518; border: 1px solid rgba(217, 4, 41, 0.5); border-left: 5px solid #D90429; border-radius: 6px; padding: 18px; margin-top: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="color: #D90429; font-weight: 700; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;">
                                Falla Biomecánica Identificada
                            </span>
                            <span style="background-color: {color_severidad}22; color: {color_severidad}; border: 1px solid {color_severidad}; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase;">
                                {badge_severidad}
                            </span>
                        </div>
                        <div style="color: #FFFFFF; font-size: 1.1rem; font-weight: 700;">
                            Articulación: {diagnostico.articulacion_afectada.replace('_', ' ').title()}
                        </div>
                        <div style="display: flex; gap: 24px; margin-top: 10px; margin-bottom: 12px; background: rgba(0,0,0,0.3); padding: 10px 14px; border-radius: 4px;">
                            <div>
                                <div style="color: #8B949E; font-size: 0.75rem; text-transform: uppercase;">Desviación Registrada</div>
                                <div style="color: #EF233C; font-size: 1.15rem; font-weight: 800;">{diagnostico.desviacion_maxima:.1f}&deg;</div>
                            </div>
                            <div>
                                <div style="color: #8B949E; font-size: 0.75rem; text-transform: uppercase;">Tolerancia Homologada</div>
                                <div style="color: #FFFFFF; font-size: 1.15rem; font-weight: 800;">{tolerancia_base:.1f}&deg;</div>
                            </div>
                            <div>
                                <div style="color: #8B949E; font-size: 0.75rem; text-transform: uppercase;">Exceso Angular</div>
                                <div style="color: {color_severidad}; font-size: 1.15rem; font-weight: 800;">+{exceso_angular:.1f}&deg;</div>
                            </div>
                        </div>
                        <div style="color: #C9D1D9; font-size: 0.9rem; line-height: 1.45; border-top: 1px solid #2D323E; padding-top: 10px;">
                            <strong style="color: #FFFFFF;">Directiva Pedagógica:</strong> {diagnostico.explicacion_error}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Sección de Evolución Temporal y Similitud Global del Movimiento (RF-13, RF-14, RF-15)
    st.markdown(
        """
        <div style="margin-top: 25px; margin-bottom: 15px;">
            <h4 style="color: #FFFFFF; font-weight: 700; margin-bottom: 2px;">
                Evolución Temporal y Similitud Global del Movimiento
            </h4>
            <p style="color: #8B949E; font-size: 0.85rem;">
                Métricas multimodales: Similitud Coseno de 28 grupos articulares y Distancia Euclidiana 3D (33 landmarks).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(
            label="Similitud Angular Global",
            value=f"{getattr(diagnostico, 'angle_similarity_percentage', 0.0):.1f} %",
            help="Similaridad coseno promedio entre los vectores de 28 ángulos clave durante la ejecución.",
        )
    with col_m2:
        st.metric(
            label="Similitud de Posición 3D",
            value=f"{getattr(diagnostico, 'position_similarity_percentage', 0.0):.1f} %",
            help="Proximidad espacial euclidiana normalizada de los 33 puntos esqueléticos respecto al patrón.",
        )
    with col_m3:
        st.metric(
            label="Coincidencia Biomecánica Combinada",
            value=f"{getattr(diagnostico, 'combined_similarity_percentage', 0.0):.1f} %",
            delta="Score Integral",
            delta_color="normal",
            help="Índice balanceado de conformidad técnica global.",
        )

    # Gráfico temporal de Matplotlib
    chart_path = getattr(diagnostico, "chart_image_path", "")
    if chart_path and os.path.exists(chart_path):
        st.image(
            chart_path,
            caption="Evolución temporal de la similitud cinemática (Ángulos, Posición y Promedio por Fotograma / RF-15)",
            use_container_width=True,
        )

    # Descarga de reportes tabulares CSV (RF-14)
    csv_paths = getattr(diagnostico, "csv_files_paths", [])
    if csv_paths:
        st.markdown(
            "<div style='margin-top: 15px; margin-bottom: 8px; color: #C9D1D9; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>"
            "Descarga de Datos Tabulares por Fotograma (RF-14):"
            "</div>",
            unsafe_allow_html=True,
        )
        col_c1, col_c2, col_c3 = st.columns(3)
        cols = [col_c1, col_c2, col_c3]
        for i, c_path in enumerate(csv_paths):
            col_target = cols[i % 3]
            if os.path.exists(c_path):
                file_name = Path(c_path).name
                with open(c_path, "rb") as fp:
                    btn_data = fp.read()
                label_btn = (
                    "CSV Ángulos Articulares"
                    if "angle" in file_name
                    else ("CSV Coordenadas 3D" if "position" in file_name else "CSV Similitud por Frame")
                )
                with col_target:
                    st.download_button(
                        label=label_btn,
                        data=btn_data,
                        file_name=file_name,
                        mime="text/csv",
                        key=f"dl_csv_{i}_{file_name}",
                        use_container_width=True,
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
