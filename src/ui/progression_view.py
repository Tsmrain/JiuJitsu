"""
Vista de Historial Longitudinal y Métricas de Progresión (Craig Larman / RF-12, CU-04).
"""

import pandas as pd
import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController


def render_progression_view(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza el panel de progresión técnica del atleta con visualización de series temporales (RF-12).
    """
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h2 style="color: #1D3557; margin-bottom: 0;">📈 Historial Longitudinal de Progresión Técnica</h2>
            <p style="color: #666; font-size: 0.95rem;">
                Trazabilidad cinemática continua del practicante en el currículo oficial de Corpo & Mente (RF-12).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Métricas clave en tarjetas ejecutivas
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(
            label="Puntuación Global Canónica",
            value="89.5 / 100",
            delta="+6.5 pts vs mes anterior",
            delta_color="normal",
        )
    with col_m2:
        st.metric(
            label="Evaluaciones Completadas",
            value="14 sesiones",
            delta="+3 esta semana",
        )
    with col_m3:
        st.metric(
            label="Frecuencia de Errores",
            value="1.2 por técnica",
            delta="-0.8 (Mejora motriz)",
            delta_color="normal",
        )

    st.divider()

    st.markdown("### 📉 Curva de Desviación Angular Promedio (°)")
    st.caption("Evolución de la discrepancia angular respecto a las técnicas maestras (a menor desviación, mayor precisión canónica).")

    # Datos temporales de progresión técnica
    datos_historicos = {
        "Fecha": [
            "2026-07-05", "2026-07-12", "2026-07-19", "2026-07-26",
            "2026-08-02", "2026-08-09", "2026-08-16", "2026-08-23"
        ],
        "Desviación Angular Promedio (°)": [38.2, 34.0, 29.5, 27.1, 22.8, 19.4, 16.2, 12.8],
        "Puntuación Técnica (%)": [62.0, 66.5, 71.0, 74.0, 78.5, 82.0, 85.5, 89.5],
    }
    df_progreso = pd.DataFrame(datos_historicos).set_index("Fecha")

    st.line_chart(df_progreso["Desviación Angular Promedio (°)"], color="#E63946")

    # Tabla de últimas evaluaciones registradas
    with st.expander("📋 Desglose de Evaluaciones Recientes", expanded=True):
        tabla_sesiones = pd.DataFrame({
            "Fecha": ["2026-08-23", "2026-08-16", "2026-08-09", "2026-08-02"],
            "Técnica Evaluada": [
                "Armbar desde Guardia Cerrada",
                "Knee Slice Pass",
                "Triángulo desde Guardia",
                "Armbar desde Guardia Cerrada",
            ],
            "Articulación Evaluada": ["Codo Derecho", "Rodilla Izquierda", "Cuello / Hombro", "Codo Derecho"],
            "Desviación": ["12.8°", "16.2°", "19.4°", "22.8°"],
            "Veredicto": ["✅ Cumple Norma", "⚠️ Falla Leve", "⚠️ Falla Moderada", "⚠️ Falla"],
        })
        st.dataframe(tabla_sesiones, use_container_width=True, hide_index=True)

    st.write("")
    if st.button("⬅️ Volver al Módulo de Carga", type="primary"):
        st.session_state["current_view"] = "upload"
        st.rerun()
