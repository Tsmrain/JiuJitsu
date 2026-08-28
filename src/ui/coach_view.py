"""
Vista del Panel del Head Coach / Profesor (Craig Larman / CU-01, RF-01).
Experiencia de usuario natural para el tatami: el profesor define qué técnica se practica en la clase
(ej. 'Cómo escapar de la montada') y sube su video demostrativo.
"""

from pathlib import Path
import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def render_coach_view(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza el panel del profesor adaptado a la dinámica real de clase en el tatami.
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
                    Panel del Profesor: Grabación de la Clase
                </div>
                <div style="color: #8B949E; font-size: 0.85rem; margin-top: 2px;">
                    Enseña la técnica del día y sube tu video demostrativo para que tus alumnos aprendan de él y se auditen.
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
                    ¿Qué técnica vamos a practicar hoy?
                </div>
                """,
                unsafe_allow_html=True,
            )

            nombre_tecnica = st.text_input(
                "Nombre de la Técnica de la Clase",
                placeholder="Ej. Cómo escapar de la montada, Raspado de Tijera, Pasaje Torreando...",
                help="Escribe el nombre de la técnica tal como se la anuncias a tus alumnos.",
            )

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                posicion = st.selectbox(
                    "Posición de Inicio",
                    options=["Montada", "Guardia Cerrada", "Media Guardia", "Side Control", "De Pie", "Espalda"],
                    index=0,
                    help="Posición desde la que arranca la acción técnica.",
                )
            with col_c2:
                categoria = st.selectbox(
                    "Tipo de Acción",
                    options=["Escape / Defensa", "Pasaje de Guardia", "Llave / Sumisión", "Raspado / Inversión", "Derribo"],
                    index=0,
                    help="Finalidad táctica del fundamento técnico.",
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
                    Técnicas Publicadas por el Profesor
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
                                Posición: <span style="color: #F0F6FC;">{t.posicion_origen}</span> &bull; Acción: <span style="color: #F0F6FC;">{t.categoria_tecnica}</span>
                            </div>
                            <div style="color: #3FB950; font-size: 0.75rem; margin-top: 4px; font-weight: 600;">
                                DISPONIBLE PARA EVALUACIÓN DE ALUMNOS
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No hay técnicas registradas todavía.")

    # Al presionar guardar, se persiste y queda lista para los alumnos
    if boton_guardar and video_patron is not None:
        video_bytes = video_patron.read()

        # Reglas biomecánicas automáticas asignadas por el sistema
        reglas_datos = [
            {
                "articulacion_clave": "codo_derecho",
                "umbral_angular_tolerado": 15.0,
                "descripcion_error": f"Desviación postural respecto a la técnica demostrada por el profesor para {nombre_tecnica.strip()}.",
            }
        ]

        with st.spinner("Publicando técnica para los alumnos en la academia..."):
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
                    f"¡Técnica '{tecnica_creada.nombre}' publicada exitosamente! "
                    "Tus alumnos ya pueden verla y evaluar sus videos contra tu demostración."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar la técnica: {str(e)}")
