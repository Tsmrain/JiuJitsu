"""
Vista del Panel del Head Coach / Profesor (Craig Larman / CU-01, RF-01).
Soporte completo para operaciones CRUD en las técnicas de la academia:
- Create: Publicar nueva técnica y video de clase.
- Read: Listar técnicas vigentes del profesor.
- Update: Modificar el nombre o tema de una técnica existente.
- Delete: Eliminar una técnica del currículo oficial.
Con notificaciones persistentes de éxito o error para el usuario.
"""

from pathlib import Path
import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def render_coach_view(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza el panel de gestión técnica del profesor con CRUD completo y alertas visuales.
    """
    # Notificaciones persistentes de feedback al usuario
    if "coach_mensaje_exito" in st.session_state and st.session_state["coach_mensaje_exito"]:
        st.success(st.session_state.pop("coach_mensaje_exito"))
    if "coach_mensaje_error" in st.session_state and st.session_state["coach_mensaje_error"]:
        st.error(st.session_state.pop("coach_mensaje_error"))

    col_t, col_b = st.columns([3, 1])
    with col_t:
        st.markdown(
            """
            <div>
                <div style="color: #D90429; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                    Academia Corpo e Mente &middot; Humberto Tavares
                </div>
                <div style="color: #FFFFFF; font-size: 1.4rem; font-weight: 800; text-transform: uppercase;">
                    Panel del Profesor: Gestión de Técnicas (CRUD)
                </div>
                <div style="color: #8B949E; font-size: 0.85rem; margin-top: 2px;">
                    Publica, edita o elimina las técnicas enseñadas en clase para la evaluación de tus alumnos.
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

    col_izq, col_der = st.columns([1.2, 1.4], gap="large")

    # ==========================================
    # 1. CREATE: Publicar Nueva Técnica
    # ==========================================
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

    # ==========================================
    # 2. READ, UPDATE, DELETE: Técnicas Existentes
    # ==========================================
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
            id_en_edicion = st.session_state.get("coach_edit_id", None)

            if tecnicas_actuales:
                for t in tecnicas_actuales:
                    with st.container(border=True):
                        # Modo de edición activa para este elemento (UPDATE)
                        if id_en_edicion == t.id:
                            st.markdown(
                                "<div style='color: #D90429; font-weight: 700; font-size: 0.85rem;'>EDITANDO TÉCNICA</div>",
                                unsafe_allow_html=True,
                            )
                            nuevo_nombre = st.text_input(
                                "Modificar nombre de la técnica:",
                                value=t.nombre,
                                key=f"input_edit_{t.id}",
                            )
                            col_e1, col_e2 = st.columns(2)
                            with col_e1:
                                if st.button("Guardar Cambios", key=f"save_{t.id}", width="stretch"):
                                    if nuevo_nombre.strip():
                                        controller.actualizar_tecnica_maestra(t.id, nuevo_nombre.strip())
                                        st.session_state["coach_edit_id"] = None
                                        st.session_state["coach_mensaje_exito"] = (
                                            f"Técnica actualizada a '{nuevo_nombre.strip()}' correctamente."
                                        )
                                        st.rerun()
                                    else:
                                        st.error("El nombre no puede quedar vacío.")
                            with col_e2:
                                if st.button("Cancelar", key=f"cancel_{t.id}", width="stretch"):
                                    st.session_state["coach_edit_id"] = None
                                    st.rerun()
                        else:
                            # Modo de visualización normal (READ) con acciones (UPDATE / DELETE)
                            st.markdown(
                                f"""
                                <div style="margin-bottom: 6px;">
                                    <div style="color: #FFFFFF; font-weight: 700; font-size: 1rem;">{t.nombre}</div>
                                    <div style="color: #3FB950; font-size: 0.75rem; margin-top: 2px; font-weight: 600;">
                                        DISPONIBLE PARA EVALUACIÓN EN CLASE
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            col_act1, col_act2 = st.columns(2)
                            with col_act1:
                                if st.button("Editar", key=f"btn_edit_{t.id}", width="stretch"):
                                    st.session_state["coach_edit_id"] = t.id
                                    st.rerun()
                            with col_act2:
                                if st.button("Eliminar", key=f"btn_del_{t.id}", width="stretch"):
                                    nombre_del = t.nombre
                                    controller.eliminar_tecnica_maestra(t.id)
                                    st.session_state["coach_mensaje_exito"] = (
                                        f"Técnica '{nombre_del}' eliminada del catálogo oficial."
                                    )
                                    st.rerun()
            else:
                st.info("No hay técnicas registradas todavía. Publica una en el panel izquierdo.")

    # ==========================================
    # Procesar Publicación (CREATE)
    # ==========================================
    if boton_guardar and video_patron is not None:
        video_bytes = video_patron.read()

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

                # Notificación persistente garantizada al usuario
                st.session_state["coach_mensaje_exito"] = (
                    f"¡Técnica '{tecnica_creada.nombre}' publicada con éxito! "
                    "Ya está disponible en la sala para que todos los alumnos se evalúen con tu video."
                )
                st.rerun()
            except Exception as e:
                st.session_state["coach_mensaje_error"] = f"Falla al registrar la técnica: {str(e)}"
                st.rerun()
