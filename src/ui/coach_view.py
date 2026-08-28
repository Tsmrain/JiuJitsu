"""
Vista del Panel del Head Coach / Profesor (Craig Larman / CU-01, RF-01).
Permite al profesor registrarse grabando el video patrón maestro y parametrizar las tolerancias biomecánicas.
"""

from pathlib import Path
import streamlit as st
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def render_coach_view(controller: AnalisisBiomecanicoController) -> None:
    """
    Renderiza el panel de gestión del Head Coach para homologar nuevas técnicas maestras
    y cargar los videos patrón de referencia cinemática (CU-01 / RF-01).
    """
    col_t, col_b = st.columns([3, 1])
    with col_t:
        st.markdown(
            """
            <div>
                <div style="color: #D90429; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                    Panel del Head Coach &middot; Gestión Curricular (CU-01)
                </div>
                <div style="color: #FFFFFF; font-size: 1.4rem; font-weight: 800; text-transform: uppercase;">
                    Homologación de Técnicas Maestras y Videos Patrón
                </div>
                <div style="color: #8B949E; font-size: 0.85rem; margin-top: 2px;">
                    Sube tu propia grabación ejecutando la técnica canónica. El sistema usará este video para evaluar a tus alumnos.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        if st.button("Sala de Evaluación", use_container_width=True):
            st.session_state["current_view"] = "upload"
            st.rerun()

    st.divider()

    # Formulario en dos columnas anchas
    col_izq, col_der = st.columns([1.2, 1], gap="large")

    with col_izq:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-bottom: 12px; border-bottom: 2px solid #D90429; padding-bottom: 6px;">
                    1. Datos de la Técnica y Grabación del Profesor
                </div>
                """,
                unsafe_allow_html=True,
            )

            nombre_tecnica = st.text_input(
                "Nombre Oficial de la Técnica",
                placeholder="Ej. Armbar desde Guardia Cerrada",
                help="Nombre pedagógico con el que los alumnos identificarán el fundamento.",
            )

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                categoria = st.selectbox(
                    "Categoría Curricular",
                    options=["Llave de Brazo", "Pasaje de Guardia", "Estrangulación", "Derribo", "Raspado"],
                    index=0,
                )
            with col_c2:
                posicion = st.selectbox(
                    "Posición de Origen",
                    options=["Guardia Cerrada", "Montada", "Side Control", "Media Guardia", "De Pie", "Espalda"],
                    index=0,
                )

            # Carga del video patrón grabado por el profesor
            video_patron = st.file_uploader(
                "Subir Video Patrón del Profesor (Grabación Oficial)",
                type=["mp4", "mov"],
                help="Video de referencia canónica ejecutado por el profesor. Servirá como molde de comparación DTW.",
            )

            if video_patron is not None:
                st.video(video_patron)

    with col_der:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; margin-bottom: 12px; border-bottom: 2px solid #D90429; padding-bottom: 6px;">
                    2. Tolerancias Biomecánicas y Reglas de Error (RF-01)
                </div>
                """,
                unsafe_allow_html=True,
            )

            ventana_sakoe = st.slider(
                "Ventana de Tolerancia Temporal Sakoe-Chiba (%)",
                min_value=5,
                max_value=30,
                value=15,
                step=1,
                help="Holgura porcentual de desalineación temporal permitida entre el alumno y el profesor.",
            )

            articulacion_clave = st.selectbox(
                "Articulación Clave a Auditar",
                options=[
                    "codo_derecho",
                    "codo_izquierdo",
                    "rodilla_derecha",
                    "rodilla_izquierda",
                    "hombro_derecho",
                    "hombro_izquierdo",
                ],
                format_func=lambda x: x.replace("_", " ").title(),
                help="Punto anatómico crítico donde reside la efectividad del movimiento.",
            )

            umbral_angular = st.slider(
                "Umbral Angular de Tolerancia (Grados °)",
                min_value=5.0,
                max_value=30.0,
                value=15.0,
                step=0.5,
                help="Desviación angular máxima tolerada antes de declarar falla biomecánica.",
            )

            descripcion_error = st.text_area(
                "Explicación Pedagógica en caso de Falla",
                value="El brazo se encuentra hiperextendido sin fijación de la muñeca contra el pecho del ejecutante.",
                help="Mensaje determinista que el alumno leerá en su reporte si supera el umbral tolerado.",
            )

            st.write("")
            boton_registrar = st.button(
                "Homologar Técnica Maestra",
                disabled=video_patron is None or not nombre_tecnica.strip(),
                use_container_width=True,
            )

    # Procesar registro de técnica maestra
    if boton_registrar and video_patron is not None:
        video_bytes = video_patron.read()
        reglas_datos = [
            {
                "articulacion_clave": articulacion_clave,
                "umbral_angular_tolerado": float(umbral_angular),
                "descripcion_error": descripcion_error.strip(),
            }
        ]

        with st.spinner("Almacenando video del profesor en Huawei Cloud OBS y registrando técnica en base de datos..."):
            try:
                tecnica_creada = controller.registrar_tecnica_maestra(
                    nombre=nombre_tecnica.strip(),
                    categoria=categoria,
                    posicion=posicion,
                    ventana_sakoe=float(ventana_sakoe) / 100.0,
                    video_bytes=video_bytes,
                    reglas_datos=reglas_datos,
                )

                st.success(
                    f"Técnica Maestra '{tecnica_creada.nombre}' homologada exitosamente. "
                    "A partir de este momento, todos los videos de los alumnos para este movimiento "
                    "se compararán automáticamente contra tu video patrón."
                )
                st.session_state["tecnica_seleccionada_id"] = tecnica_creada.id

            except Exception as e:
                st.error(f"Error al registrar técnica maestra: {str(e)}")

    st.write("")

    # Listado de técnicas actualmente disponibles en el currículo
    with st.container(border=True):
        st.markdown(
            """
            <div style="color: #FFFFFF; font-weight: 700; font-size: 1rem; margin-bottom: 12px;">
                Catálogo Curricular Vigente de la Academia
            </div>
            """,
            unsafe_allow_html=True,
        )

        tecnicas_actuales = controller.listar_tecnicas()
        if tecnicas_actuales:
            for t in tecnicas_actuales:
                with st.expander(f"{t.nombre} ({t.categoria_tecnica} &mdash; {t.posicion_origen})"):
                    st.write(f"**Identificador:** `{t.id}`")
                    st.write(f"**Ventana Sakoe-Chiba:** `{int(t.ventana_sakoe_chiba * 100)}%`")
                    st.write(f"**URL de Video Patrón:** `{t.video_url}`")
                    st.write("**Reglas Biomecánicas:**")
                    for reg in t.reglas:
                        st.markdown(
                            f"- Articulación: `{reg.articulacion_clave}` | Tolerancia: `{reg.umbral_angular_tolerado}°` | Error: *{reg.descripcion_error}*"
                        )
        else:
            st.info("No hay técnicas registradas en el catálogo.")
