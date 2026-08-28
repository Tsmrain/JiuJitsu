"""
Vista de Carga de Video y Configuración del Análisis Biomecánico (Craig Larman / RF-07, CU-02).
"""

from uuid import uuid4
import streamlit as st
from src.services.controllers.analisis_controller import (
    AnalisisBiomecanicoController,
    TokenInvalidoError,
)


def render_upload_view(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza el formulario de selección curricular, subida de video y disparo del análisis serverless.
    """
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
                <h2 style="color: #1D3557; margin-bottom: 0;">📤 Módulo de Evaluación Biomecánica</h2>
                <p style="color: #666; font-size: 0.9rem; margin-top: 2px;">
                    Sube una grabación en pareja de hasta 6 segundos (máximo 5 MB) para contrastarla con el patrón oficial.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navegación superior rápida
    col_nav1, col_nav2, col_nav3 = st.columns([2, 1, 1])
    with col_nav2:
        if st.button("📈 Mi Progreso", use_container_width=True):
            st.session_state["current_view"] = "progression"
            st.rerun()
    with col_nav3:
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["token"] = None
            st.session_state["diagnostico"] = None
            st.session_state["current_view"] = "token"
            st.rerun()

    st.divider()

    # Selección Curricular en Cascada
    col_cat, col_pos = st.columns(2)
    with col_cat:
        categoria = st.selectbox(
            "Categoría Técnica Curricular",
            options=["Llave de Brazo", "Pasaje de Guardia", "Estrangulación"],
            index=0,
            help="Selecciona el fundamento técnico que estás practicando.",
        )

    with col_pos:
        posiciones_disponibles = {
            "Llave de Brazo": ["Guardia Cerrada", "Montada", "De Pie"],
            "Pasaje de Guardia": ["Torreando", "Knee Slice", "Over-Under"],
            "Estrangulación": ["Triángulo", "Mata-León", "Guillotina"],
        }
        opciones_posicion = posiciones_disponibles.get(categoria, ["Guardia Cerrada"])
        posicion = st.selectbox(
            "Posición de Origen",
            options=opciones_posicion,
            index=0,
            help="Posición de inicio donde se ejecuta la técnica canónica.",
        )

    st.markdown(
        f"**Técnica seleccionada:** *{categoria} desde {posicion}* `(Patrón Maestro Homologado)`"
    )

    # Componente de Carga de Archivo Audiovisual
    archivo_subido = st.file_uploader(
        "Selecciona o arrastra el video de tu ejecución técnica",
        type=["mp4", "mov"],
        help="Límite estricto de tamaño: 5.0 MB. Duración máxima recomendada: 6.0 segundos (RP-01).",
    )

    # Validación visual contractual (RF-07)
    archivo_valido = False
    if archivo_subido is not None:
        tamano_mb = archivo_subido.size / (1024 * 1024)
        if tamano_mb > 5.0:
            st.error(
                f"❌ El archivo pesa **{tamano_mb:.2f} MB**, excediendo el límite contractual permitido de **5.0 MB** (RF-07). "
                f"Por favor comprime el video o recorta la duración."
            )
            archivo_valido = False
        else:
            st.success(f"✅ Archivo válido: **{archivo_subido.name}** ({tamano_mb:.2f} MB)")
            archivo_valido = True

    # Botón de disparo del análisis cinemático
    st.write("")
    boton_analizar = st.button(
        "🚀 Analizar Técnica con IA",
        type="primary",
        disabled=not archivo_valido,
        use_container_width=True,
    )

    if boton_analizar and archivo_subido is not None:
        token_sesion = st.session_state.get("token", "")
        id_tecnica_seleccionada = uuid4()  # Identificador para la técnica evaluada
        video_bytes = archivo_subido.read()

        with st.spinner("⏳ Procesando cinemática con MediaPipe, Kalman y DTW en FunctionGraph..."):
            try:
                diagnostico = controller.ejecutar_analisis(
                    token=token_sesion,
                    video_bytes=video_bytes,
                    id_tecnica=id_tecnica_seleccionada,
                )

                # Manejo de política Zero-Persistence ante oclusión prolongada (RF-11)
                if diagnostico.estado == "ABORTADO_OCLUSION":
                    st.warning(
                        "⚠️ **Evaluación Abortada por Oclusión Prolongada (RF-11)**\n\n"
                        f"{diagnostico.explicacion_error}\n\n"
                        "💡 **Recomendación Pedagógica:** Posiciona la cámara en un ángulo de 45° libre de obstáculos "
                        "para que las articulaciones no queden ocultas detrás del cuerpo de tu compañero de tatami durante más de 1.5 segundos."
                    )
                else:
                    # Cómputo exitoso o limpio: transicionar a vista de feedback
                    st.session_state["diagnostico"] = diagnostico
                    st.session_state["video_bytes"] = video_bytes
                    st.session_state["video_nombre"] = archivo_subido.name
                    st.session_state["tecnica_nombre"] = f"{categoria} desde {posicion}"
                    st.session_state["current_view"] = "feedback"
                    st.rerun()

            except TokenInvalidoError as err:
                st.error(f"❌ Error de autenticación: {str(err)}")
                st.session_state["authenticated"] = False
                st.session_state["current_view"] = "token"
                st.rerun()
            except Exception as err:
                st.error(f"❌ Error durante el procesamiento serverless: {str(err)}")
