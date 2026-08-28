"""
Vista de Historial Longitudinal y Métricas de Progresión (Craig Larman / RF-12, CU-04).
Diseño Full-Width, responsivo, sobrio y sin emojis.
"""

import pandas as pd
import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController


def render_progression_view(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza el panel de seguimiento de progresión técnica del atleta a través de series temporales.
    """
    # Encabezado del módulo
    col_t, col_b = st.columns([3, 1])
    with col_t:
        st.markdown(
            """
            <div>
                <div style="color: #D90429; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                    Módulo de Trazabilidad Curricular (RF-12)
                </div>
                <div style="color: #FFFFFF; font-size: 1.4rem; font-weight: 800; text-transform: uppercase;">
                    Historial Longitudinal de Progresión Técnica
                </div>
                <div style="color: #8B949E; font-size: 0.85rem; margin-top: 2px;">
                    Evolución del desempeño motriz y reducción de discrepancia angular en el tiempo.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        if st.button("Volver al Analizador", use_container_width=True):
            st.session_state["current_view"] = "upload"
            st.rerun()

    st.divider()

    # Métricas consolidadas en tarjetas de ancho completo
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(
            label="Índice de Precisión Técnica",
            value="89.5 / 100",
            delta="+6.5 puntos vs mes anterior",
            delta_color="normal",
        )
    with col_m2:
        st.metric(
            label="Sesiones de Evaluación Registradas",
            value="14 sesiones",
            delta="+3 en el ciclo actual",
            delta_color="normal",
        )
    with col_m3:
        st.metric(
            label="Tasa Promedio de Fallas",
            value="1.2 por técnica",
            delta="-0.8 (Tendencia favorable)",
            delta_color="normal",
        )

    st.write("")

    # Visualización gráfica temporal
    with st.container(border=True):
        st.markdown(
            """
            <div style="color: #FFFFFF; font-weight: 700; font-size: 1rem; margin-bottom: 4px;">
                Curva de Desviación Angular Promedio (Grados &deg;)
            </div>
            <div style="color: #8B949E; font-size: 0.85rem; margin-bottom: 12px;">
                Trayectoria de convergencia respecto al patrón maestro oficial (a menor desviación, mayor precisión técnica).
            </div>
            """,
            unsafe_allow_html=True,
        )

        datos_historicos = {
            "Fecha": [
                "2026-07-05", "2026-07-12", "2026-07-19", "2026-07-26",
                "2026-08-02", "2026-08-09", "2026-08-16", "2026-08-23"
            ],
            "Desviación Angular Promedio (°)": [38.2, 34.0, 29.5, 27.1, 22.8, 19.4, 16.2, 12.8],
        }
        df_progreso = pd.DataFrame(datos_historicos).set_index("Fecha")

        st.line_chart(df_progreso["Desviación Angular Promedio (°)"], color="#D90429")

    st.write("")

    # Tabla detallada de auditorías recientes
    with st.container(border=True):
        st.markdown(
            """
            <div style="color: #FFFFFF; font-weight: 700; font-size: 1rem; margin-bottom: 12px;">
                Registro de Evaluaciones Recientes
            </div>
            """,
            unsafe_allow_html=True,
        )

        tabla_sesiones = pd.DataFrame({
            "Fecha": ["2026-08-23", "2026-08-16", "2026-08-09", "2026-08-02"],
            "Técnica Evaluada": [
                "Armbar desde Guardia Cerrada",
                "Knee Slice Pass",
                "Triángulo desde Guardia",
                "Armbar desde Guardia Cerrada",
            ],
            "Articulación Evaluada": ["Codo Derecho", "Rodilla Izquierda", "Hombro / Cuello", "Codo Derecho"],
            "Desviación Registrada": ["12.8°", "16.2°", "19.4°", "22.8°"],
            "Veredicto Oficial": ["CUMPLE NORMA", "FALLA LEVE", "FALLA MODERADA", "FALLA SEVERA"],
        })
        st.dataframe(tabla_sesiones, use_container_width=True, hide_index=True)
