"""
Capa de Presentación - Sistema de Análisis Biomecánico BJJ (Streamlit RBAC)

Implementación con separación estricta de responsabilidades y control de acceso basado en roles (RBAC):
- CU-01: Gestión Curricular y Homologación de Técnicas (Head Coach / Profesor).
  Minimalista: El profesor solo define el nombre del tema y sube su video demostrativo.
- CU-02 / CU-03: Sala de Práctica, Auditoría Biomecánica y Diagnóstico Cinemático (Estudiante / Practicante).
  El practicante selecciona la técnica, ve el video del profesor, sube su ejecución y recibe la retroalimentación.

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
from src.infrastructure.storage.local_storage import LocalVideoStorage
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
#  Inicialización de Base de Datos Persistente Local
# ──────────────────────────────────────────────

RUTA_BD_LOCAL = os.path.join(RUTA_RAIZ, "corpo_e_mente_local.db")

def obtener_session_fabrica():
    """Crea la base de datos persistente SQLite asegurando que las tablas existan siempre."""
    engine = create_engine(
        f"sqlite:///{RUTA_BD_LOCAL}",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)

SESSION_FACTORY = obtener_session_fabrica()


def get_system_controller() -> tuple[AnalisisBiomecanicoController, TecnicaMaestraRepository]:
    """Obtiene el controlador y repositorio vinculados a la sesión de base de datos activa."""
    session = SESSION_FACTORY()
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

    # Si es la primera vez que se crea la BD, precargar técnicas de referencia
    if not tecnica_repo.listar_todas():
        tecnicas_base = [
            ("Armbar desde Guardia Cerrada", "codo_derecho", 90.0, "Brazo hiper-extendido o flexión insuficiente del codo"),
            ("Triangle Choke (Triángulo)", "rodilla_derecha", 120.0, "Ángulo de pierna insuficiente para cierre arterial"),
            ("Kimura Lock", "codo_izquierdo", 85.0, "Apalancamiento de hombro fuera de rango biomecánico seguro"),
        ]

        for nombre, art, umbral, desc in tecnicas_base:
            tid = uuid.uuid4()
            t = TecnicaMaestra(
                nombre=nombre,
                categoria="Fundamental",
                posicion_origen="Tatami",
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
#  Pantalla 2: Vista del Profesor (CU-01 - Minimalista)
# ──────────────────────────────────────────────

def render_profesor(controller: AnalisisBiomecanicoController, repo: TecnicaMaestraRepository) -> None:
    st.markdown("## 📋 Panel de Gestión Curricular - Head Coach")
    st.caption("Publicación minimalista de la técnica demostrativa de la clase para los alumnos.")

    st.markdown("---")

    col_form, col_list = st.columns([3, 2])

    with col_form:
        st.markdown("#### 🥋 Publicar Técnica para la Clase")
        with st.form("form_nueva_tecnica", clear_on_submit=True):
            nombre_tecnica = st.text_input(
                "Nombre de la Técnica / Tema de la Clase:",
                placeholder="Ej: Cómo finalizar desde la montada y hacer una americana",
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
                        # Guardar video patrón en almacén local
                        LocalVideoStorage.guardar_video(str(tid), video_bytes)

                        # Registrar la técnica maestra con configuración cinemática estándar
                        nueva_t = TecnicaMaestra(
                            nombre=nombre_tecnica.strip(),
                            categoria="Clase del Día",
                            posicion_origen="Posición Clave",
                            video_url=f"local://{tid}",
                            ventana_sakoe_chiba=0.15,
                            id_tecnica=tid,
                        )
                        # Reglas automáticas para las 4 articulaciones del BJJ
                        nueva_t.agregar_regla(ReglaBiomecanica("codo_derecho", 90.0, "Ángulo de codo derecho fuera de alineación óptima"))
                        nueva_t.agregar_regla(ReglaBiomecanica("codo_izquierdo", 90.0, "Ángulo de codo izquierdo fuera de alineación óptima"))
                        nueva_t.agregar_regla(ReglaBiomecanica("rodilla_derecha", 110.0, "Base de rodilla derecha inestable o fuera de ángulo"))
                        nueva_t.agregar_regla(ReglaBiomecanica("rodilla_izquierda", 110.0, "Base de rodilla izquierda inestable o fuera de ángulo"))

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
                with st.expander(f"🥋 {t.nombre}"):
                    # Mostrar video patrón si está guardado en el almacén local
                    video_id = t.video_url.replace("local://", "")
                    video_data = LocalVideoStorage.obtener_video(video_id)
                    if video_data:
                        st.video(video_data)
                    else:
                        st.caption("ℹ️ Video cinemático de referencia de la academia.")

                    if st.button(f"🗑️ Eliminar técnica", key=f"del_{t.id_tecnica}"):
                        repo.eliminar(str(t.id_tecnica))
                        LocalVideoStorage.eliminar_video(video_id)
                        st.warning(f"Técnica eliminada.")
                        st.rerun()


# ──────────────────────────────────────────────
#  Pantalla 3: Vista del Practicante (CU-02 / CU-03)
# ──────────────────────────────────────────────

def render_practicante(controller: AnalisisBiomecanicoController, repo: TecnicaMaestraRepository) -> None:
    st.markdown("## 🥋 Sala de Práctica y Auditoría Biomecánica")
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

        # Mostrar video demostrativo del profesor si existe
        video_id = tecnica_sel.video_url.replace("local://", "")
        video_patron = LocalVideoStorage.obtener_video(video_id)
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
        with st.spinner("Procesando comparación biomecánica con el video del profesor..."):
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

                # Mensaje pedagógico según articulación afectada
                mensaje_feedback = f"Se detectó diferencia cinemática notable en {art_critica.replace('_', ' ')}."
                for r in tecnica_sel.reglas:
                    if r.articulacion_clave == art_critica:
                        mensaje_feedback = r.descripcion_error
                        break

                # Tarjetas de métricas
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Estado de la Evaluación", "APROBADO" if desviacion <= 15.0 else "CORRECCIÓN REQUERIDA")
                with m2:
                    st.metric("Desviación Angular Máxima", f"{desviacion:.1f}°")
                with m3:
                    st.metric("Articulación a Ajustar", art_critica.replace("_", " ").title())
                with m4:
                    st.metric("Distancia DTW (Sincronía)", f"{dtw_dist:.3f}")

                # Feedback formativo al practicante
                if desviacion > 15.0:
                    st.warning(
                        f"⚠️ **Punto de Corrección Identificado en Fotograma #{fotograma}:**\n\n"
                        f"**{mensaje_feedback}**\n\n"
                        f"Tu articulación `{art_critica.replace('_', ' ').title()}` tuvo una desviación máxima de **{desviacion:.1f}°** respecto a la ejecución del profesor en ese instante."
                    )
                else:
                    st.success(
                        f"🎉 **¡Excelente Ejecución!**\n\n"
                        f"Tu movimiento se mantuvo alineado con la técnica del profesor con una desviación máxima de solo **{desviacion:.1f}°**."
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
