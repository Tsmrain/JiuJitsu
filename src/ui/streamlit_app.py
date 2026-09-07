import streamlit as st
import pandas as pd
from pathlib import Path
import os
import sys

# Asegurar disponibilidad del paquete raíz
project_root = Path(__file__).parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.infrastructure.storage import LocalStorageAdapter
from src.application.pipeline import AnalysisPipeline


def main():
    st.set_page_config(page_title="BJJ Biomechanics Edge", layout="wide")
    st.title("🥋 Sistema Híbrido de Análisis BJJ (Edge-Colab)")

    tab1, tab2 = st.tabs(["📹 Nueva Evaluación", "📊 Historial de Progresión"])

    with tab1:
        st.header("Paso 1: Carga de Video (Local)")
        uploaded_file = st.file_uploader("Sube el video de tu ejecución (.mp4)", type=['mp4'], key='video_uploader')

        if uploaded_file is not None:
            # Guardar localmente usando el Adapter
            storage = LocalStorageAdapter()
            file_path = storage.guardar_video_subido(uploaded_file.name, uploaded_file.read())
            st.success(f"✅ Video guardado en: `{file_path}`")

            st.info("🚀 **Siguiente paso:** Sube este video a Google Colab (`notebooks/jiujiutsu_ai_engine.ipynb`), ejecuta el análisis y descarga el archivo `colab_analysis_results.json`.")

            st.divider()
            st.header("Paso 2: Importación de Resultados IA")
            json_file = st.file_uploader("Carga el JSON generado por Colab", type=['json'], key='json_uploader')

            if json_file is not None:
                pipeline = AnalysisPipeline()

                # Simulación de IDs para la tesis (en producción provienen de la sesión del practicante)
                video_id = "550e8400-e29b-41d4-a716-446655440000"
                tecnica_id = "123e4567-e89b-12d3-a456-426614174000"

                # Guardar JSON temporalmente para procesamiento
                temp_json_path = Path("temp_analysis.json")
                with open(temp_json_path, 'wb') as f:
                    f.write(json_file.getbuffer())

                if st.button("Procesar y Guardar en Base de Datos", type="primary"):
                    try:
                        analisis = pipeline.procesar_resultado_colab(str(temp_json_path), video_id, tecnica_id)
                        st.success(f"✅ Análisis persistido en SQLite (Mannino). ID: `{analisis.id}`")

                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.metric("Desviación Máxima", f"{analisis.desviacion_angular_maxima:.2f}°")
                        with c2:
                            st.metric("Articulación Crítica", analisis.articulacion_afectada.replace('_', ' ').upper() if analisis.articulacion_afectada else "NINGUNA")
                        with c3:
                            st.metric("Total de Errores", len(analisis.errores))

                        if analisis.errores:
                            st.subheader("📋 Detalle de Errores Biomecánicos")
                            df_err = pd.DataFrame([
                                {
                                    'Articulación': e.articulacion.replace('_', ' ').upper(),
                                    'Diferencia (°)': round(e.diferencia, 1),
                                    'Ángulo Alumno (°)': round(e.angulo_alumno, 1),
                                    'Ángulo Maestro (°)': round(e.angulo_maestro, 1),
                                    'Frame': e.frame,
                                    'Diagnóstico': e.mensaje
                                }
                                for e in sorted(analisis.errores, key=lambda x: x.diferencia, reverse=True)
                            ])
                            st.dataframe(df_err, use_container_width=True)

                    except Exception as e:
                        st.error(f"Error al procesar: {e}")
                    finally:
                        if temp_json_path.exists():
                            temp_json_path.unlink()

    with tab2:
        st.header("Dashboard Longitudinal")
        pipeline = AnalysisPipeline()
        historial = pipeline.obtener_historial_estudiante("estudiante_demo_id")

        if historial:
            df = pd.DataFrame(historial)
            if 'fecha_procesamiento' in df.columns and 'puntuacion_global' in df.columns:
                st.line_chart(df.set_index('fecha_procesamiento')['puntuacion_global'])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("ℹ️ No hay datos históricos disponibles aún para este estudiante en SQLite.")


if __name__ == "__main__":
    main()
