import streamlit as st
import os
import sys
import tempfile
import pandas as pd

# Asegurar disponibilidad del paquete raíz
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.infrastructure.adapters.yolo_adapter import YOLOPoseExtractor
from src.infrastructure.storage import LocalStorageProvider, DriveStorageProvider
from src.application.pipeline import BiomechanicsPipeline
from src.domain.services import AngleCalculatorImpl, DTWComparatorImpl
from src.infrastructure.frame_annotator import FrameAnnotatorImpl

st.set_page_config(
    page_title="Corpo & Mente BJJ - Análisis Biomecánico",
    page_icon="🥋",
    layout="wide"
)

st.title("🥋 Sistema de Análisis Biomecánico de Brazilian Jiu-Jitsu")
st.markdown("**Corpo & Mente Bolivia** — Evaluación cinemática con IA (YOLO26-pose) y DTW con restricción de Sakoe-Chiba.")

# Barra lateral para configuración de almacenamiento
st.sidebar.header("⚙️ Configuración del Sistema")
storage_type = st.sidebar.selectbox(
    "Proveedor de Almacenamiento",
    ["Local (Desarrollo)", "Google Drive (Google Colab)"]
)

if storage_type == "Google Drive (Google Colab)":
    try:
        from google.colab import drive
        drive.mount('/content/drive')
        storage = DriveStorageProvider()
        st.sidebar.success("✅ Google Drive conectado")
    except Exception:
        st.sidebar.warning("⚠️ No se detectó entorno Google Colab. Empleando almacenamiento local.")
        storage = LocalStorageProvider()
else:
    storage = LocalStorageProvider()


@st.cache_resource
def get_pipeline():
    """Instancia del controlador de caso de uso con inyección de dependencias."""
    pose_extractor = YOLOPoseExtractor()
    angle_calc = AngleCalculatorImpl()
    dtw_comp = DTWComparatorImpl()
    frame_annot = FrameAnnotatorImpl()

    return BiomechanicsPipeline(
        pose_extractor=pose_extractor,
        angle_calculator=angle_calc,
        dtw_comparator=dtw_comp,
        frame_annotator=frame_annot,
        storage=storage
    )


# Carga de videos de prueba
st.subheader("📹 Carga de Videos para Comparación Técnica")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎬 Video Patrón (Maestro)")
    maestro_file = st.file_uploader("Subir video del maestro (MP4)", type=['mp4', 'mov'], key='maestro')
    if maestro_file:
        st.video(maestro_file)

with col2:
    st.markdown("### 🎬 Video de Ejecución (Alumno)")
    alumno_file = st.file_uploader("Subir video del alumno (MP4)", type=['mp4', 'mov'], key='alumno')
    if alumno_file:
        st.video(alumno_file)

# Botón de ejecución
if st.button("🔬 Iniciar Análisis Biomecánico", type="primary"):
    if not maestro_file or not alumno_file:
        st.error("⚠️ Debe cargar ambos videos (Maestro y Alumno) para proceder con el análisis.")
    else:
        with st.spinner("🔄 Procesando inferencia de pose y análisis cinemático..."):
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_m:
                tmp_m.write(maestro_file.read())
                ruta_m = tmp_m.name

            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_a:
                tmp_a.write(alumno_file.read())
                ruta_a = tmp_a.name

            try:
                pipeline = get_pipeline()
                resultado = pipeline.ejecutar(ruta_m, ruta_a)

                st.success("✅ Análisis biomecánico completado exitosamente.")

                # Métricas principales
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Desviación Angular Máxima", f"{resultado.desviacion_angular_maxima:.1f}°")
                with m2:
                    st.metric("Articulación Afectada", resultado.articulacion_afectada.replace('_', ' ').upper())
                with m3:
                    st.metric("Total de Errores Detectados", len(resultado.errores))
                with m4:
                    st.metric("Estado de Cómputo", resultado.estado_computo.upper())

                # Visualización de entregable anotado
                if resultado.fotograma_anotado and os.path.exists(resultado.fotograma_anotado.imagen_url):
                    st.subheader("📷 Fotograma Clave Anotado (RF-05, RF-06)")
                    st.image(resultado.fotograma_anotado.imagen_url, caption=resultado.fotograma_anotado.explicacion_causa)

                # Tabla detallada de discrepancias
                if resultado.errores:
                    st.subheader("📊 Tabla de Discrepancias Articulares")
                    df = pd.DataFrame([
                        {
                            'Articulación': e.articulacion.replace('_', ' ').upper(),
                            'Desviación (°)': round(e.diferencia, 1),
                            'Ángulo Alumno (°)': round(e.angulo_alumno, 1),
                            'Ángulo Maestro (°)': round(e.angulo_maestro, 1),
                            'Frame': e.frame,
                            'Diagnóstico': e.mensaje
                        }
                        for e in sorted(resultado.errores, key=lambda x: x.diferencia, reverse=True)
                    ])
                    st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Error durante el procesamiento: {str(e)}")
            finally:
                if os.path.exists(ruta_m):
                    os.unlink(ruta_m)
                if os.path.exists(ruta_a):
                    os.unlink(ruta_a)
