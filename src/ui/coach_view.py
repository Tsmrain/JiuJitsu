"""
Vista del Panel del Head Coach / Profesor (Craig Larman / CU-01, RF-01).
Diseño ultra-simplificado y ágil para el tatami: el profesor solo ingresa el nombre de la técnica
y sube su video grabado. El sistema automatiza todas las reglas biomecánicas y tolerancias.
"""

from pathlib import Path
import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def render_coach_view(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza el panel del profesor optimizado para el uso ágil en el tatami.
    El profesor solo necesita nombrar la técnica y subir su video de ejecución.
    """
    col_t, col_b = st.columns([3, 1])
    with col_t:
        st.markdown(
            """
            <div>
                <div style="color: #D90429; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                    Panel del Head Coach &middot; Grabación de Técnicas
                </div>
                <div style="color: #FFFFFF; font-size: 1.4rem; font-weight: 800; text-transform: uppercase;">
                    Subir Nueva Técnica del Profesor
                </div>
                <div style="color: #8B949E; font-size: 0.85rem; margin-top: 2px;">
                    Graba tu técnica y súbela con su nombre. Tus alumnos se evaluarán automáticamente contra este video.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        if st.button("Volver a la Sala", width="stretch"):
            st.session_state["current_view"] = "upload"
            st.rerun()

    st.divider()

    # Formulario central limpio y directo
    col_izq, col_der = st.columns([1.3, 1], gap="large")

    with col_izq:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-bottom: 14px; border-bottom: 2px solid #D90429; padding-bottom: 6px;">
                    Grabación del Profesor
                </div>
                """,
                unsafe_allow_html=True,
            )

            nombre_tecnica = st.text_input(
                "Nombre de la Técnica",
                placeholder="Ej. Armbar desde Guardia Cerrada, Triángulo, Pasaje Torreando...",
                help="Nombre con el que tus alumnos verán y seleccionarán esta técnica.",
            )

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                categoria = st.selectbox(
                    "Categoría",
                    options=["Llave de Brazo", "Pasaje de Guardia", "Estrangulación", "Derribo", "Raspado"],
                    index=0,
                )
            with col_c2:
                posicion = st.selectbox(
                    "Posición de Origen",
                    options=["Guardia Cerrada", "Montada", "Side Control", "Media Guardia", "De Pie", "Espalda"],
                    index=0,
                )

            # Subida directa del video grabado por el profesor
            video_patron = st.file_uploader(
                "Video del Profesor (Grabado en el tatami)",
                type=["mp4", "mov"],
                help="Sube tu video ejecutando la técnica a la perfección.",
            )

            if video_patron is not None:
                st.video(video_patron)

            # Ajustes avanzados colapsados por defecto (el profesor no necesita tocarlos)
            with st.expander("Ajustes Biomecánicos Avanzados (Opcional)", expanded=False):
                st.caption("El sistema ya aplica las tolerancias óptimas por defecto (15.0° y ventana DTW del 15%).")
                articulacion_clave = st.selectbox(
                    "Articulación Clave Principal",
                    options=[
                        "codo_derecho",
                        "codo_izquierdo",
                        "rodilla_derecha",
                        "rodilla_izquierda",
                        "hombro_derecho",
                        "hombro_izquierdo",
                    ],
                    index=0,
                    format_func=lambda x: x.replace("_", " ").title(),
                )
                umbral_angular = st.slider("Tolerancia Angular (°)", 5.0, 30.0, 15.0, 0.5)

            st.write("")
            boton_guardar = st.button(
                "Guardar Técnica del Profesor",
                disabled=video_patron is None or not nombre_tecnica.strip(),
                width="stretch",
            )

    with col_der:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-bottom: 14px; border-bottom: 2px solid #D90429; padding-bottom: 6px;">
                    Técnicas Activas en el Sistema
                </div>
                """,
                unsafe_allow_html=True,
            )

            tecnicas_actuales = controller.listar_tecnicas()
            if tecnicas_actuales:
                for t in tecnicas_actuales:
                    with st.expander(f"{t.nombre} ({t.categoria_tecnica})", expanded=False):
                        st.write(f"**Posición:** {t.posicion_origen}")
                        st.write(f"**Video Patrón:** `{t.video_url.split('/')[-1]}`")
                        st.write(f"**Tolerancia:** 15.0° (Automática)")
            else:
                st.info("No hay técnicas registradas todavía.")

    # Al presionar guardar, se procesa automáticamente
    if boton_guardar and video_patron is not None:
        video_bytes = video_patron.read()

        # Generación automática de reglas biomecánicas deterministas sin complicar al profesor
        reglas_datos = [
            {
                "articulacion_clave": "codo_derecho",
                "umbral_angular_tolerado": 15.0,
                "descripcion_error": f"Desviación angular detectada respecto a la técnica grabada por el profesor para {nombre_tecnica.strip()}.",
            }
        ]

        with st.spinner("Guardando video del profesor y publicando técnica en el sistema..."):
            try:
                tecnica_creada = controller.registrar_tecnica_maestra(
                    nombre=nombre_tecnica.strip(),
                    categoria=categoria,
                    posicion=posicion,
                    ventana_sakoe=0.15,
                    video_bytes=video_bytes,
                    reglas_datos=reglas_datos,
                )

                st.success(
                    f"¡Técnica '{tecnica_creada.nombre}' guardada con éxito! "
                    "Ya está disponible en la sala para que todos los alumnos se evalúen con tu video."
                )
            except Exception as e:
                st.error(f"Error al guardar la técnica: {str(e)}")
