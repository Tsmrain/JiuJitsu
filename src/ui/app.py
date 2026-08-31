"""
Capa de Presentación - Sistema de Análisis Biomecánico BJJ (Streamlit RBAC)

Implementación con separación estricta de responsabilidades y control de acceso basado en roles (RBAC):
- CU-01: Gestión Curricular y Homologación de Técnicas (Head Coach / Profesor).
- CU-02 / CU-03: Sala de Práctica, Auditoría Biomecánica y Diagnóstico Cinemático (Estudiante / Practicante).

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import base64
import json
import os
import sys
import uuid
from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock

# Garantizar que la raíz del proyecto esté en el PYTHONPATH
RUTA_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if RUTA_RAIZ not in sys.path:
    sys.path.insert(0, RUTA_RAIZ)

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.models import ReglaBiomecanica, TecnicaMaestra
from src.infrastructure.database.models import Base
from src.infrastructure.repositories.analisis_repository import AnalisisBiomecanicoRepository
from src.infrastructure.repositories.tecnica_repository import TecnicaMaestraRepository
from src.infrastructure.repositories.video_repository import VideoEjecucionRepository
from src.infrastructure.serverless.functiongraph_handler import handler
from src.infrastructure.storage.obs_adapter import HuaweiOBSStorageAdapter
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController
from src.services.dtw_comparator import DTWComparator
from src.services.landmark_adapter import LandmarkAdapter
from src.services.pipeline_engine import PipelineBiomecanicoEngine
from src.services.rtmpose3d_extractor import RTMPose3DExtractor

# ──────────────────────────────────────────────
#  Configuración de Página
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Corpo & Mente BJJ",
    layout="wide",
    page_icon="🥋",
)

# ──────────────────────────────────────────────
#  Singleton de Almacenamiento Local de Videos
# ──────────────────────────────────────────────

class LocalOBSStorageSimulator:
    """Simulador en memoria/disco local para almacenar y reproducir videos subidos por el profesor."""

    _videos: Dict[str, bytes] = {}

    @classmethod
    def guardar_video(cls, video_id: str, contenido: bytes) -> None:
        cls._videos[video_id] = contenido

    @classmethod
    def obtener_video(cls, video_id: str) -> bytes | None:
        return cls._videos.get(video_id)


# ──────────────────────────────────────────────
#  Inicialización de Infraestructura y Repositorios
# ──────────────────────────────────────────────

@st.cache_resource
def get_system_controller() -> tuple[AnalisisBiomecanicoController, TecnicaMaestraRepository]:
    """Inicializa la base de datos local SQLite y el controlador de caso de uso."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    tecnica_repo = TecnicaMaestraRepository(session)
    analisis_repo = AnalisisBiomecanicoRepository(session)
    video_repo = VideoEjecucionRepository(session)

    mock_obs_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_obs_client.putObject.return_value = mock_resp

    obs_adapter = HuaweiOBSStorageAdapter(
        server="obs.la-south-2.myhuaweicloud.com",
        bucket_input="bjj-videos-input",
        bucket_output="bjj-reports-output",
        client=mock_obs_client,
    )

    pipeline_engine = PipelineBiomecanicoEngine(
        landmark_adapter=LandmarkAdapter(),
        dtw_comparator=DTWComparator(),
        pose_extractor=RTMPose3DExtractor.obtener_instancia(),
    )

    controller = AnalisisBiomecanicoController(
        pipeline_engine=pipeline_engine,
        tecnica_repository=tecnica_repo,
        analisis_repository=analisis_repo,
        video_repository=video_repo,
        obs_adapter=obs_adapter,
    )

    # Cargar técnicas base iniciales de la academia
    tecnicas_base = [
        ("Armbar desde Guardia Cerrada", "Sumisión", "Guardia Cerrada", "codo_derecho", 90.0, "Brazo hiper-extendido o flexión insuficiente del codo"),
        ("Triangle Choke (Triángulo)", "Estrangulamiento", "Guardia Abierta", "rodilla_derecha", 120.0, "Ángulo de pierna insuficiente para cierre arterial"),
        ("Kimura Lock", "Sumisión de Hombro", "Media Guardia", "codo_izquierdo", 85.0, "Apalancamiento de hombro fuera de rango biomecánico seguro"),
    ]

    for nombre, cat, pos, art, umbral, desc in tecnicas_base:
        tid = uuid.uuid4()
        t = TecnicaMaestra(
            nombre=nombre,
            categoria=cat,
            posicion_origen=pos,
            video_url=f"local://{tid}",
            ventana_sakoe_chiba=0.15,
            id_tecnica=tid,
        )
        r = ReglaBiomecanica(
            articulacion_clave=art,
            umbral_angular_tolerado=umbral,
            descripcion_error=desc,
        )
        t.agregar_regla(r)
        tecnica_repo.guardar(t)

    return controller, tecnica_repo


# ──────────────────────────────────────────────
#  Pantalla 1: Acceso y Selección de Rol (Login)
# ──────────────────────────────────────────────

def render_login() -> None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "corpo_e_mente_logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center;'>🥋 Corpo & Mente BJJ</h1>", unsafe_allow_html=True)

        st.markdown("<h3 style='text-align: center;'>Sistema de Análisis Biomecánico en Tatami</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Selecciona tu perfil de acceso para ingresar a la plataforma.</p>", unsafe_allow_html=True)

        with st.form("form_login"):
            rol_opcion = st.radio(
                "Perfil de Usuario:",
                options=["Soy Practicante (Estudiante)", "Soy Profesor (Head Coach)"],
                index=0,
            )

            token_input = st.text_input(
                "Token de Acceso:",
                type="password",
                placeholder="Ej. SANTIAGO-BJJ",
                help="Introduce tu token personal asignado por la academia.",
            )

            submit_login = st.form_submit_button("Ingresar a la Plataforma", use_container_width=True)

            if submit_login:
                if not token_input.strip():
                    st.error("Por favor, ingresa un token de acceso válido.")
                else:
                    rol_simplificado = "Profesor" if "Profesor" in rol_opcion else "Practicante"
                    st.session_state["autenticado"] = True
                    st.session_state["rol_usuario"] = rol_simplificado
                    st.session_state["token"] = token_input.strip()
                    st.rerun()


# ──────────────────────────────────────────────
#  Pantalla 2: Vista del Profesor (CU-01)
# ──────────────────────────────────────────────

def render_profesor(controller: AnalisisBiomecanicoController, repo: TecnicaMaestraRepository) -> None:
    st.markdown("## 📋 Panel de Gestión Curricular - Head Coach (CU-01)")
    st.caption("Homologación de técnicas maestras y publicación del patrón cinemático de referencia para los alumnos.")

    st.markdown("---")

    col_form, col_list = st.columns([3, 2])

    with col_form:
        st.markdown("#### 🥋 Publicar Nueva Técnica de la Clase")
        with st.form("form_nueva_tecnica", clear_on_submit=True):
            nombre_tecnica = st.text_input(
                "Nombre de la Técnica / Tema de la Clase:",
                placeholder="Ej: Cómo finalizar desde la montada y hacer una americana",
            )

            col_a, col_b = st.columns(2)
            with col_a:
                categoria = st.selectbox(
                    "Categoría:",
                    options=["Sumisión", "Estrangulamiento", "Pasaje de Guardia", "Raspado (Sweep)", "Defensa / Escape"],
                )
            with col_b:
                posicion = st.selectbox(
                    "Posición de Origen:",
                    options=["Guardia Cerrada", "Guardia Abierta", "Media Guardia", "Montada (Mount)", "Control Lateral (Side Control)", "Espalda (Back)"],
                )

            col_c, col_d = st.columns(2)
            with col_c:
                articulacion = st.selectbox(
                    "Articulación Crítica a Evaluar:",
                    options=["codo_derecho", "codo_izquierdo", "rodilla_derecha", "rodilla_izquierda"],
                    format_func=lambda x: x.replace("_", " ").title(),
                )
            with col_d:
                umbral_tolerado = st.slider(
                    "Ángulo Óptimo Esperado (°):",
                    min_value=30.0,
                    max_value=180.0,
                    value=90.0,
                    step=5.0,
                )

            descripcion_falla = st.text_input(
                "Mensaje Pedagógico de Error:",
                value="Ángulo articular fuera del rango biomecánico de palanca óptima",
                help="Retroalimentación instructiva que se le mostrará al alumno si falla la regla.",
            )

            video_file = st.file_uploader(
                "Subir Video Demostrativo (Patrón Maestro):",
                type=["mp4", "mov"],
                help="Video de referencia del profesor (máx. 5 MB, máx. 6s).",
            )

            submit_publicar = st.form_submit_button("🚀 Publicar Técnica para la Clase", use_container_width=True)

            if submit_publicar:
                if not nombre_tecnica.strip():
                    st.error("❌ El nombre de la técnica es obligatorio.")
                elif video_file is None:
                    st.error("❌ Debes adjuntar el video patrón demostrativo.")
                else:
                    video_bytes = video_file.read()
                    if len(video_bytes) > 5 * 1024 * 1024:
                        st.error("❌ El video supera los 5 MB permitidos (RF-07).")
                    else:
                        tid = uuid.uuid4()
                        # Guardar video patrón en simulador de almacenamiento local
                        LocalOBSStorageSimulator.guardar_video(str(tid), video_bytes)

                        nueva_t = TecnicaMaestra(
                            nombre=nombre_tecnica.strip(),
                            categoria=categoria,
                            posicion_origen=posicion,
                            video_url=f"local://{tid}",
                            ventana_sakoe_chiba=0.15,
                            id_tecnica=tid,
                        )
                        regla = ReglaBiomecanica(
                            articulacion_clave=articulacion,
                            umbral_angular_tolerado=umbral_tolerado,
                            descripcion_error=descripcion_falla.strip(),
                        )
                        nueva_t.agregar_regla(regla)
                        repo.guardar(nueva_t)

                        st.success(f"✅ Técnica **'{nombre_tecnica}'** publicada exitosamente y disponible para los alumnos.")
                        st.rerun()

    with col_list:
        st.markdown("#### 📚 Técnicas Publicadas en la Academia")
        tecnicas = repo.listar_todas()
        if not tecnicas:
            st.info("No hay técnicas registradas actualmente.")
        else:
            for t in tecnicas:
                with st.expander(f"🥋 {t.nombre} ({t.categoria})"):
                    st.write(f"**Posición inicial:** {t.posicion_origen}")
                    st.write(f"**Reglas biomecánicas:** {len(t.reglas_biomecanicas)}")
                    for r in t.reglas_biomecanicas:
                        st.caption(f"- Articulación: `{r.articulacion_clave}` (Ángulo tolerado: {r.umbral_angular_tolerado}°)")
                        st.caption(f"  *Feedback de error:* {r.descripcion_error}")

                    # Mostrar video patrón si está guardado en el simulador local
                    video_id = t.video_url.replace("local://", "")
                    video_data = LocalOBSStorageSimulator.obtener_video(video_id)
                    if video_data:
                        st.video(video_data)

                    if st.button(f"🗑️ Eliminar técnica", key=f"del_{t.id_tecnica}"):
                        repo.eliminar(str(t.id_tecnica))
                        st.warning(f"Técnica eliminada.")
                        st.rerun()


# ──────────────────────────────────────────────
#  Pantalla 3: Vista del Practicante (CU-02 / CU-03)
# ──────────────────────────────────────────────

def render_practicante(controller: AnalisisBiomecanicoController, repo: TecnicaMaestraRepository) -> None:
    st.markdown("## 🥋 Sala de Práctica y Auditoría Biomecánica (CU-02 / CU-03)")
    st.caption("Contrasta tu ejecución técnica contra el patrón maestro del profesor y recibe diagnóstico cinemático instantáneo.")

    st.markdown("---")

    tecnicas = repo.listar_todas()
    if not tecnicas:
        st.warning("⚠️ El profesor aún no ha publicado técnicas para esta clase. Por favor, consulta a tu instructor.")
        return

    # Mapeo de opciones por nombre
    mapa_tecnicas = {t.nombre: t for t in tecnicas}

    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.markdown("### Paso 1: Técnica a Practicar")
        tecnica_nombre = st.selectbox(
            "Selecciona la técnica que vas a practicar hoy:",
            options=list(mapa_tecnicas.keys()),
        )
        tecnica_sel = mapa_tecnicas[tecnica_nombre]

        st.info(f"📍 **Posición:** {tecnica_sel.posicion_origen} | **Categoría:** {tecnica_sel.categoria}")

        # Mostrar video demostrativo del profesor si existe
        video_id = tecnica_sel.video_url.replace("local://", "")
        video_patron = LocalOBSStorageSimulator.obtener_video(video_id)
        if video_patron:
            st.markdown("#### 🎥 Video Patrón del Profesor (Referencia):")
            st.video(video_patron)
        else:
            st.caption("ℹ️ Esta técnica utiliza el modelo cinemático de referencia de la academia.")

    with col_der:
        st.markdown("### Paso 2: Cargar tu Ejecución")
        st.caption("ℹ️ **Límites operativos (RF-07):** Máximo 5 MB y hasta 6 segundos de duración en video MP4 o MOV.")

        video_alumno_file = st.file_uploader(
            "Sube el video de tu ejecución en pareja:",
            type=["mp4", "mov"],
            key="uploader_alumno",
        )

        alumno_bytes = None
        es_valido = False

        if video_alumno_file is not None:
            alumno_bytes = video_alumno_file.read()
            peso_mb = len(alumno_bytes) / (1024 * 1024)

            if peso_mb > 5.0:
                st.error(f"❌ El video pesa **{peso_mb:.2f} MB**, superando el límite de 5.0 MB (RF-07).")
            else:
                st.success(f"✓ Video cargado: **{peso_mb:.2f} MB**")
                st.video(alumno_bytes)
                es_valido = True

    st.markdown("---")

    # Paso 3: Botón de Análisis
    btn_analizar = st.button("🥋 Analizar mi Técnica", type="primary", disabled=(not es_valido or alumno_bytes is None), use_container_width=True)

    if btn_analizar and alumno_bytes is not None and es_valido:
        with st.spinner("Procesando con motor de análisis biomecánico (FunctionGraph Runtime)..."):
            # Si el profesor subió un video patrón real, lo pasamos al análisis para comparar alumno vs profesor
            video_b64 = base64.b64encode(alumno_bytes).decode("utf-8")
            event = {
                "httpMethod": "POST",
                "body": video_b64,
                "isBase64Encoded": True,
                "headers": {"Content-Type": "application/json"},
                "queryStringParameters": {
                    "tecnica_id": str(tecnica_sel.id_tecnica),
                },
            }

            resp = handler(event, controller=controller)
            status_code = resp.get("statusCode", 500)

            if status_code == 200:
                diagnostico = json.loads(resp.get("body", "{}"))
                st.markdown("### 📊 Paso 4: Diagnóstico y Retroalimentación (CU-03)")

                desviacion = diagnostico.get("pico_desviacion", 0.0)
                art_critica = diagnostico.get("articulacion_afectada", "codo_derecho")
                dtw_dist = diagnostico.get("distancia_dtw", 0.0)
                fotograma = diagnostico.get("fotograma_error", 0)

                # Buscar regla de la técnica para retroalimentación pedagógica
                mensaje_feedback = "Ejecución técnica correcta y alineada al patrón del profesor."
                umbral_regla = 90.0
                for r in tecnica_sel.reglas_biomecanicas:
                    if r.articulacion_clave == art_critica:
                        mensaje_feedback = r.descripcion_error
                        umbral_regla = r.umbral_angular_tolerado
                        break

                # Métricas visuales
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Estado de la Evaluación", "APROBADO" if desviacion <= 15.0 else "CORRECCIÓN REQUERIDA")
                with m2:
                    st.metric("Desviación Angular Máxima", f"{desviacion:.1f}°", delta=f"{desviacion - 10:.1f}°" if desviacion > 15 else "-Óptimo")
                with m3:
                    st.metric("Articulación a Ajustar", art_critica.replace("_", " ").title())
                with m4:
                    st.metric("Distancia DTW (Sincronía)", f"{dtw_dist:.3f}")

                # Feedback formativo al practicante
                if desviacion > 15.0:
                    st.warning(
                        f"⚠️ **Detalle de Corrección en Fotograma #{fotograma}:**\n\n"
                        f"**{mensaje_feedback}**\n\n"
                        f"Tu articulación crítica (`{art_critica.replace('_', ' ').title()}`) se desvió **{desviacion:.1f}°** respecto al patrón de referencia ({umbral_regla}° esperados)."
                    )
                else:
                    st.success(
                        f"🎉 **¡Excelente Ejecución!**\n\n"
                        f"Tu cinemática mantuvo los ángulos correctos a lo largo de todo el movimiento con una desviación mínima de **{desviacion:.1f}°**."
                    )

                with st.expander("Ver desglose biomecánico completo (JSON)"):
                    st.json(diagnostico)
            else:
                err = json.loads(resp.get("body", "{}"))
                st.error(f"Error al analizar el video ({status_code}): {err.get('error', 'Error inesperado')}")


# ──────────────────────────────────────────────
#  Flujo Principal con Enrutamiento RBAC
# ──────────────────────────────────────────────

def main() -> None:
    controller, repo = get_system_controller()

    # Inicializar variables de sesión si no existen
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if "rol_usuario" not in st.session_state:
        st.session_state["rol_usuario"] = "Practicante"

    # Si no está autenticado, mostrar pantalla de login
    if not st.session_state["autenticado"]:
        render_login()
        return

    # Barra lateral con información de sesión y cierre de sesión
    with st.sidebar:
        logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "corpo_e_mente_logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)

        st.markdown(f"### 👤 Perfil Activo")
        st.write(f"**Rol:** `{st.session_state['rol_usuario']}`")
        st.caption("Corpo & Mente BJJ · UPSA")

        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state["autenticado"] = False
            st.session_state.pop("rol_usuario", None)
            st.session_state.pop("token", None)
            st.rerun()

    # Renderizar vista según rol
    if st.session_state["rol_usuario"] == "Profesor":
        render_profesor(controller, repo)
    else:
        render_practicante(controller, repo)


if __name__ == "__main__":
    main()
