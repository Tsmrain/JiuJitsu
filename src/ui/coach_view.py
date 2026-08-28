"""
Vista del Panel del Head Coach / Profesor (Craig Larman / CU-01, RF-01).
Diseño directo, sin campos complejos ni letras superpuestas.
El profesor únicamente asigna el nombre de la técnica y sube su video grabado.
"""

from pathlib import Path
import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def render_coach_view(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza el panel del profesor optimizado para el tatami:
    Nombre de técnica + Video grabado -> Guardar.
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

    # Formulario en dos columnas limpias
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
                    st.markdown(
                        f"""
                        <div style="background-color: #161922; border: 1px solid #2B303C; border-left: 4px solid #D90429; border-radius: 6px; padding: 12px 14px; margin-bottom: 10px;">
                            <div style="color: #FFFFFF; font-weight: 700; font-size: 0.95rem;">{t.nombre}</div>
                            <div style="color: #8B949E; font-size: 0.8rem; margin-top: 4px;">
                                Categoría: <span style="color: #F0F6FC;">{t.categoria_tecnica}</span> &bull; Posición: <span style="color: #F0F6FC;">{t.posicion_origen}</span>
                            </div>
                            <div style="color: #D90429; font-size: 0.75rem; margin-top: 4px;">
                                Molde Activo &bull; Tolerancia Angular Canónica: 15.0&deg;
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
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
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar la técnica: {str(e)}")
