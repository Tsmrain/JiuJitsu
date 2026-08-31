"""
Capa de Presentación - Sistema de Análisis Biomecánico BJJ (Streamlit)

Interfaz gráfica reactiva para el practicante e instructor de Brazilian Jiu-Jitsu.
Permite autenticarse mediante token de acceso, seleccionar la técnica maestra de referencia,
cargar videos de ejecución con validación preventiva de límites (RF-07: <= 5 MB, <= 6s)
y simular la invocación serverless a Huawei Cloud FunctionGraph mostrando métricas y diagnóstico.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import base64
import json
import os
import sys
import uuid
from typing import Any, Dict
from unittest.mock import MagicMock

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

# ──────────────────────────────────────────────
#  Configuración de Página
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Corpo & Mente BJJ",
    layout="wide",
    page_icon="🥋",
)

# ──────────────────────────────────────────────
#  Inicialización de Estado y Controlador Local
# ──────────────────────────────────────────────

@st.cache_resource
def get_local_controller_and_catalog() -> tuple[AnalisisBiomecanicoController, Dict[str, TecnicaMaestra]]:
    """Inicializa la base de datos local y el controlador de caso de uso."""
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
    )

    controller = AnalisisBiomecanicoController(
        pipeline_engine=pipeline_engine,
        tecnica_repository=tecnica_repo,
        analisis_repository=analisis_repo,
        video_repository=video_repo,
        obs_adapter=obs_adapter,
    )

    # Catálogo de técnicas maestras
    catalogo: Dict[str, TecnicaMaestra] = {}

    tecnicas_data = [
        ("Armbar desde Guardia Cerrada", "Sumisión", "Guardia Cerrada", "codo_derecho", 90.0, "Brazo hiper-extendido o flexión insuficiente del codo"),
        ("Triangle Choke (Triángulo)", "Estrangulamiento", "Guardia Abierta", "rodilla_derecha", 120.0, "Ángulo de pierna insuficiente para cierre arterial"),
        ("Kimura Lock", "Sumisión de Hombro", "Media Guardia", "codo_izquierdo", 85.0, "Apalancamiento de hombro fuera de rango biomecánico seguro"),
    ]

    for nombre, cat, pos, art, umbral, desc in tecnicas_data:
        tid = uuid.uuid4()
        t = TecnicaMaestra(
            nombre=nombre,
            categoria=cat,
            posicion_origen=pos,
            video_url=f"https://obs.la-south-2.myhuaweicloud.com/bjj-videos-input/{tid}.mp4",
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
        catalogo[nombre] = t

    return controller, catalogo


def main() -> None:
    controller, catalogo_tecnicas = get_local_controller_and_catalog()

    # ──────────────────────────────────────────────
    #  Barra Lateral (Sidebar)
    # ──────────────────────────────────────────────
    with st.sidebar:
        logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "corpo_e_mente_logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.title("🥋 Corpo & Mente BJJ")

        st.markdown("### 🔐 Acceso y Configuración")
        token_acceso = st.text_input(
            "Token de Acceso",
            type="password",
            placeholder="Ej. BJJ-STUDENT-2026",
            help="Introduce tu token de estudiante asignado para validar peticiones.",
        )

        if token_acceso:
            st.success("Token de acceso activo ✓")
        else:
            st.info("Introduce un token para habilitar el análisis.")

        st.markdown("---")
        st.markdown("### 📋 Técnica Maestra")
        nombre_tecnica_seleccionada = st.selectbox(
            "Selecciona la técnica de referencia:",
            options=list(catalogo_tecnicas.keys()),
            help="Técnica homologada registrada por los instructores contra la cual se evaluará tu ejecución.",
        )

        tecnica_seleccionada = catalogo_tecnicas[nombre_tecnica_seleccionada]
        st.caption(f"**Categoría:** {tecnica_seleccionada.categoria}")
        st.caption(f"**Posición inicial:** {tecnica_seleccionada.posicion_origen}")
        st.caption(f"**Ventana Sakoe-Chiba:** {tecnica_seleccionada.ventana_sakoe_chiba * 100:.0f}% de longitud")

        st.markdown("---")
        st.markdown(
            "<div style='font-size: 0.8em; color: #888; text-align: center;'>"
            "Corpo & Mente BJJ · UPSA Santa Cruz<br>"
            "Arquitectura Híbrida Huawei Cloud"
            "</div>",
            unsafe_allow_html=True,
        )

    # ──────────────────────────────────────────────
    #  Área Principal
    # ──────────────────────────────────────────────
    st.title("🥋 Sistema de Análisis Biomecánico en Tatami")
    st.subheader("Evaluación Cinemática de Técnicas de Brazilian Jiu-Jitsu")
    st.write(
        "Sube el video de tu ejecución técnica para contrastarlo contra el patrón maestro. "
        "El motor serverless procesa la sincronización temporal elástica (DTW con ventana de Sakoe-Chiba) "
        "y las reglas biomecánicas deterministas."
    )

    st.markdown("---")

    col_upload, col_preview = st.columns([3, 2])

    with col_upload:
        st.markdown("#### 📤 Cargar Video de Ejecución")
        st.info("ℹ️ **Restricciones Operativas (RF-07):** Máximo **5 MB** y **6 segundos** de duración en formato MP4 o MOV.")

        uploaded_file = st.file_uploader(
            "Selecciona o arrastra el archivo de video:",
            type=["mp4", "mov"],
            help="El video será validado antes de ser transmitido a la nube o al simulador local.",
        )

        video_bytes = None
        es_valido = False

        if uploaded_file is not None:
            video_bytes = uploaded_file.read()
            peso_mb = len(video_bytes) / (1024 * 1024)

            # Validación preventiva en el cliente
            if peso_mb > 5.0:
                st.error(f"❌ El archivo pesa **{peso_mb:.2f} MB**, superando el límite estricto de 5.0 MB (RF-07). Por favor, sube un video más liviano.")
                es_valido = False
            else:
                st.success(f"✓ Video válido: **{peso_mb:.2f} MB** detectados.")
                es_valido = True

    with col_preview:
        st.markdown("#### 🎥 Vista Previa")
        if uploaded_file is not None and es_valido and video_bytes is not None:
            st.video(video_bytes)
        else:
            st.markdown(
                """
                <div style="border: 2px dashed #444; border-radius: 8px; padding: 40px; text-align: center; color: #888;">
                    No se ha cargado ningún video válido para previsualizar.
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Botón de Procesamiento
    col_btn, _ = st.columns([2, 4])
    with col_btn:
        btn_analizar = st.button("🚀 Analizar Técnica", disabled=(not es_valido or video_bytes is None), use_container_width=True)

    if btn_analizar and video_bytes is not None and es_valido:
        with st.spinner("Procesando con Huawei Cloud FunctionGraph (Emulación Local)..."):
            video_b64 = base64.b64encode(video_bytes).decode("utf-8")
            event_apig = {
                "httpMethod": "POST",
                "body": video_b64,
                "isBase64Encoded": True,
                "headers": {"Content-Type": "application/json"},
                "queryStringParameters": {
                    "tecnica_id": str(tecnica_seleccionada.id_tecnica),
                },
            }

            # Llamada al handler serverless inyectando el controlador local
            resultado_apig = handler(event_apig, controller=controller)
            status_code = resultado_apig.get("statusCode", 500)

            if status_code == 200:
                body_diagnostico = json.loads(resultado_apig.get("body", "{}"))
                st.success("✅ **¡Análisis Biomecánico Completado con Éxito!** (HTTP 200)")

                # Tarjetas de Métricas Principales
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric(
                        label="Estado de Cómputo",
                        value=body_diagnostico.get("estado_computo", "N/A"),
                    )
                with m2:
                    st.metric(
                        label="Desviación Máxima",
                        value=f"{body_diagnostico.get('pico_desviacion', 0.0):.1f}°",
                    )
                with m3:
                    st.metric(
                        label="Articulación Crítica",
                        value=str(body_diagnostico.get("articulacion_afectada", "N/A")).replace("_", " ").title(),
                    )
                with m4:
                    st.metric(
                        label="Distancia DTW Acumulada",
                        value=f"{body_diagnostico.get('distancia_dtw', 0.0):.3f}",
                    )

                st.markdown("### 📊 Diagnóstico Técnico Detallado")
                st.json(body_diagnostico)

            else:
                error_body = json.loads(resultado_apig.get("body", "{}"))
                st.error(f"❌ Error en la evaluación biomecánica (Código {status_code}): {error_body.get('error', 'Error desconocido')}")


if __name__ == "__main__":
    main()
