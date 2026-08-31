#!/usr/bin/env python3
"""
Script de Simulación de Invocación Local (Mock Huawei Cloud API Gateway).

Emula la llamada HTTP POST enviada desde Huawei Cloud API Gateway (APIG) hacia
el Handler de FunctionGraph con el payload codificado en Base64.
Permite verificar el pipeline completo de integración de forma determinista y local:
    Video binario -> Base64 -> APIG Event -> FunctionGraph Handler
    -> AnalisisBiomecanicoController -> Motor Biomecánico DTW
    -> Persistencia SQLite en Memoria + Mock OBS Storage.

Uso:
    .venv/bin/python scripts/test_local_invocation.py

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

# Asegurar path del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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


def generar_video_dummy(tamano_kb: int = 500) -> bytes:
    """Genera un stream binario que simula un video MP4."""
    # Cabecera ISO BMFF MP4 básica seguida de bytes dummy
    header = b"\x00\x00\x00 ftypmp42\x00\x00\x00\x00isommp42"
    padding_len = max(0, (tamano_kb * 1024) - len(header))
    return header + (b"\xaa" * padding_len)


def configurar_entorno_local() -> tuple[AnalisisBiomecanicoController, TecnicaMaestra]:
    """Inicializa la infraestructura local en memoria con técnica maestra de prueba."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    tecnica_repo = TecnicaMaestraRepository(session)
    analisis_repo = AnalisisBiomecanicoRepository(session)
    video_repo = VideoEjecucionRepository(session)

    # Mock de OBS para simulación sin credenciales cloud
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

    # Registrar Técnica Maestra de referencia (Armbar)
    tecnica_id = uuid.uuid4()
    tecnica = TecnicaMaestra(
        nombre="Armbar desde Guardia Cerrada",
        categoria="Sumisión",
        posicion_origen="Guardia Cerrada",
        video_url="https://obs.la-south-2.myhuaweicloud.com/bjj-videos-input/armbar_master.mp4",
        ventana_sakoe_chiba=0.15,
        id_tecnica=tecnica_id,
    )
    regla_codo = ReglaBiomecanica(
        articulacion_clave="codo_derecho",
        umbral_angular_tolerado=90.0,
        descripcion_error="Brazo hiper-extendido o flexión insuficiente del codo",
    )
    tecnica.agregar_regla(regla_codo)
    tecnica_repo.guardar(tecnica)

    return controller, tecnica


def main() -> int:
    """Ejecuta la emulación del evento API Gateway hacia FunctionGraph."""
    print("=" * 70)
    print("🥋 SIMULACIÓN DE INVOCACIÓN LOCAL - HUAWEI CLOUD FUNCTIONGRAPH")
    print("=" * 70)

    # 1. Preparar infraestructura local y técnica
    controller, tecnica = configurar_entorno_local()
    print(f"[*] Base de datos SQLite inicializada en memoria.")
    print(f"[*] Técnica Maestra registrada: '{tecnica.nombre}' (ID: {tecnica.id_tecnica})")

    # 2. Generar video de prueba
    video_bytes = generar_video_dummy(tamano_kb=800)  # 800 KB (< 5 MB)
    video_base64 = base64.b64encode(video_bytes).decode("utf-8")
    print(f"[*] Video de prueba generado: {len(video_bytes) / 1024:.2f} KB codificado en Base64.")

    # 3. Construir evento APIG
    event: Dict[str, Any] = {
        "httpMethod": "POST",
        "body": video_base64,
        "isBase64Encoded": True,
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "HuaweiCloud-APIG-Simulator/1.0",
        },
        "queryStringParameters": {
            "tecnica_id": str(tecnica.id_tecnica),
        },
    }

    print("\n[+] Despachando evento hacia functiongraph_handler...")
    response = handler(event, controller=controller)

    # 4. Imprimir resultados
    status_code = response.get("statusCode")
    print(f"\n[HTTP Status Code]: {status_code}")
    print(f"[Headers]: {response.get('headers')}")
    print(f"[isBase64Encoded]: {response.get('isBase64Encoded')}")

    try:
        body_data = json.loads(response.get("body", "{}"))
        print("\n[Response Body (JSON Deserializado)]:")
        print(json.dumps(body_data, indent=4, ensure_ascii=False))
    except Exception:
        print(f"\n[Raw Body]: {response.get('body')}")

    if status_code == 200:
        print("\n✅ ¡ÉXITO! La invocación local emulada de APIG -> FunctionGraph finalizó con código 200.")
        return 0
    else:
        print(f"\n❌ Error en la invocación. Código recibido: {status_code}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
