"""
Vista del Panel del Head Coach / Profesor (Craig Larman / CU-01, RF-01).
Diseño ultra-simplificado para el tatami:
El profesor únicamente ingresa el nombre o tema de la clase y sube su video demostrativo.
Sin formularios burocráticos ni campos innecesarios.
"""

from pathlib import Path
import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def render_coach_view(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza el panel del profesor adaptado a la dinámica real del tatami:
    Nombre de lo que va a enseñar + Video demostrativo -> Publicar.
    """
    col_t, col_b = st.columns([3, 1])
    with col_t:
        st.markdown(
            """
            <div>
                <div style="color: #D90429; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                    Academia Corpo e Mente &middot; Humberto Tavares
                </div>
                <div style="color: #FFFFFF; font-size: 1.4rem; font-weight: 800; text-transform: uppercase;">
                    Panel del Profesor: Publicar Técnica de la Clase
                </div>
                <div style="color: #8B949E; font-size: 0.85rem; margin-top: 2px;">
                    Escribe lo que vas a enseñar hoy y sube tu video demostrativo. Tus alumnos se auditarán directamente contra tu ejecución.
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

    col_izq, col_der = st.columns([1.3, 1], gap="large")

    with col_izq:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-bottom: 14px; border-bottom: 2px solid #D90429; padding-bottom: 6px;">
                    ¿Qué técnica les vas a enseñar a tus alumnos hoy?
                </div>
                """,
                unsafe_allow_html=True,
            )

            nombre_tecnica = st.text_input(
                "Nombre o Tema de la Clase",
                placeholder="Ej. Cómo finalizar desde la montada y hacer una americana",
                help="Escribe la lección tal como se la anuncias a tus alumnos en el tatami.",
            )

            # Subida directa del video de la demostración del profesor
            video_patron = st.file_uploader(
                "Video de la Demostración del Profesor",
                type=["mp4", "mov"],
                help="Sube tu video en el tatami ejecutando el movimiento paso a paso.",
            )

            if video_patron is not None:
                st.video(video_patron)

            st.write("")
            boton_guardar = st.button(
                "Publicar Técnica para la Clase",
                disabled=video_patron is None or not nombre_tecnica.strip(),
                width="stretch",
            )

    with col_der:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-bottom: 14px; border-bottom: 2px solid #D90429; padding-bottom: 6px;">
                    Técnicas Enseñadas por el Profesor
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
                            <div style="color: #3FB950; font-size: 0.75rem; margin-top: 6px; font-weight: 600;">
                                DISPONIBLE PARA EVALUACIÓN EN CLASE
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No hay técnicas registradas todavía.")

    # Al presionar guardar, se persiste de forma automática
    if boton_guardar and video_patron is not None:
        video_bytes = video_patron.read()

        # Inferencia automática de posición y categoría según las palabras del profesor
        nombre_clean = nombre_tecnica.strip()
        nombre_lower = nombre_clean.lower()

        posicion_auto = "Tatami"
        for p in ["Montada", "Guardia Cerrada", "Media Guardia", "Side Control", "De Pie", "Espalda", "Norte Sur"]:
            if p.lower() in nombre_lower:
                posicion_auto = p
                break

        categoria_auto = "Técnica de Clase"
        if any(w in nombre_lower for w in ["escapar", "escape", "defensa", "defender"]):
            categoria_auto = "Escape / Defensa"
        elif any(w in nombre_lower for w in ["finalizar", "americana", "armbar", "kimura", "triangulo", "mata-leon", "llave", "estrangulacion"]):
            categoria_auto = "Sumisión / Finalización"
        elif any(w in nombre_lower for w in ["pasar", "pasaje"]):
            categoria_auto = "Pasaje de Guardia"
        elif any(w in nombre_lower for w in ["raspar", "raspado"]):
            categoria_auto = "Raspado"

        reglas_datos = [
            {
                "articulacion_clave": "codo_derecho",
                "umbral_angular_tolerado": 15.0,
                "descripcion_error": f"Desviación postural respecto a la técnica demostrada por el profesor para: {nombre_clean}.",
            }
        ]

        with st.spinner("Publicando técnica para los alumnos..."):
            try:
                tecnica_creada = controller.registrar_tecnica_maestra(
                    nombre=nombre_clean,
                    categoria=categoria_auto,
                    posicion=posicion_auto,
                    ventana_sakoe=0.15,
                    video_bytes=video_bytes,
                    reglas_datos=reglas_datos,
                )

                st.success(
                    f"¡Técnica '{tecnica_creada.nombre}' publicada con éxito! "
                    "Tus alumnos ya pueden seleccionarla y evaluarse con tu video."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar la técnica: {str(e)}")
