"""
Handler de Invocación Serverless para Huawei Cloud FunctionGraph.

Traduce la invocación proveniente de Huawei Cloud API Gateway (APIG) o invocaciones
directas hacia el Controlador GRASP de caso de uso (AnalisisBiomecanicoController).

Formato de Respuesta de Huawei Cloud API Gateway:
{
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps({...}),
    "isBase64Encoded": False
}

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.models import Base
from src.infrastructure.repositories.analisis_repository import AnalisisBiomecanicoRepository
from src.infrastructure.repositories.tecnica_repository import TecnicaMaestraRepository
from src.infrastructure.repositories.video_repository import VideoEjecucionRepository
from src.infrastructure.storage.obs_adapter import HuaweiOBSStorageAdapter
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController
from src.services.dtw_comparator import DTWComparator
from src.services.landmark_adapter import LandmarkAdapter
from src.services.pipeline_engine import PipelineBiomecanicoEngine


def _crear_controlador_por_defecto() -> AnalisisBiomecanicoController:
    """Crea una instancia de AnalisisBiomecanicoController con infraestructura real/por defecto."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    tecnica_repo = TecnicaMaestraRepository(session)
    analisis_repo = AnalisisBiomecanicoRepository(session)
    video_repo = VideoEjecucionRepository(session)
    obs_adapter = HuaweiOBSStorageAdapter()

    pipeline_engine = PipelineBiomecanicoEngine(
        landmark_adapter=LandmarkAdapter(),
        dtw_comparator=DTWComparator(),
    )

    return AnalisisBiomecanicoController(
        pipeline_engine=pipeline_engine,
        tecnica_repository=tecnica_repo,
        analisis_repository=analisis_repo,
        video_repository=video_repo,
        obs_adapter=obs_adapter,
    )


def handler(
    event: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    controller: Optional[Any] = None,
) -> Dict[str, Any]:
    """Punto de entrada serverless para Huawei Cloud FunctionGraph.

    Maneja eventos provenientes de API Gateway (APIG) con o sin base64,
    así como eventos de invocación directa.

    Args:
        event: Diccionario del evento APIG / FunctionGraph.
        context: Contexto serverless provisto por el runtime de Huawei Cloud.
        controller: Controlador de caso de uso inyectable (para pruebas / testing).

    Returns:
        Diccionario con la respuesta serializada para API Gateway:
        - statusCode: 200 (éxito), 400 (error cliente/validación), 500 (error servidor)
        - headers: Diccionario con headers HTTP
        - body: String JSON con el resultado o mensaje de error
        - isBase64Encoded: False
    """
    try:
        if not isinstance(event, dict):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "estado_computo": "ERROR_VALIDACION",
                    "error": "El evento recibido debe ser un diccionario válido.",
                }),
                "isBase64Encoded": False,
            }

        # 1. Parsear el body del evento
        if "body" not in event or event["body"] is None:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "estado_computo": "ERROR_VALIDACION",
                    "error": "El cuerpo de la solicitud (body) es obligatorio.",
                }),
                "isBase64Encoded": False,
            }

        raw_body = event["body"]
        is_b64 = event.get("isBase64Encoded", False)

        # Si viene codificado en Base64 por API Gateway
        if is_b64:
            if isinstance(raw_body, str):
                video_bytes = base64.b64decode(raw_body)
            elif isinstance(raw_body, bytes):
                video_bytes = raw_body
            else:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "estado_computo": "ERROR_VALIDACION",
                        "error": "El body en base64 debe ser una cadena o bytes.",
                    }),
                    "isBase64Encoded": False,
                }
        else:
            # Si no es isBase64Encoded, puede ser un JSON string o un diccionario
            if isinstance(raw_body, str):
                try:
                    parsed_json = json.loads(raw_body)
                    if isinstance(parsed_json, dict) and "video_base64" in parsed_json:
                        video_bytes = base64.b64decode(parsed_json["video_base64"])
                    else:
                        video_bytes = raw_body.encode("utf-8")
                except Exception:
                    video_bytes = raw_body.encode("utf-8")
            elif isinstance(raw_body, dict):
                if "video_base64" in raw_body:
                    video_bytes = base64.b64decode(raw_body["video_base64"])
                else:
                    video_bytes = json.dumps(raw_body).encode("utf-8")
            elif isinstance(raw_body, bytes):
                video_bytes = raw_body
            else:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "estado_computo": "ERROR_VALIDACION",
                        "error": "Formato de body no soportado.",
                    }),
                    "isBase64Encoded": False,
                }

        # 2. Extraer parámetros (tecnica_id de queryStringParameters o del body)
        query_params = event.get("queryStringParameters") or {}
        tecnica_id = query_params.get("tecnica_id")

        if not tecnica_id and isinstance(event.get("body"), dict):
            tecnica_id = event["body"].get("tecnica_id")

        if not tecnica_id:
            tecnica_id = "default"

        # 3. Obtener o instanciar controlador de caso de uso
        ctrl = controller if controller is not None else _crear_controlador_por_defecto()

        # 4. Ejecutar análisis biomecánico a través del controlador
        # Suposición operativa estándar para video APIG: 5.0 segundos si no viene especificada
        duracion_segundos = 5.0
        nombre_archivo = f"ejecucion_{tecnica_id}.mp4"

        diagnostico = ctrl.ejecutar_analisis(
            video_bytes=video_bytes,
            id_tecnica=str(tecnica_id),
            duracion_segundos=duracion_segundos,
            nombre_archivo=nombre_archivo,
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(diagnostico),
            "isBase64Encoded": False,
        }

    except ValueError as val_err:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "estado_computo": "ERROR_VALIDACION",
                "error": str(val_err),
            }),
            "isBase64Encoded": False,
        }
    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "estado_computo": "ERROR_SERVIDOR",
                "error": f"Error interno en FunctionGraph: {str(exc)}",
            }),
            "isBase64Encoded": False,
        }
