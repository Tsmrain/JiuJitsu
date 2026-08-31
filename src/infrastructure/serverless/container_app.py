"""
Adaptador de Entrada HTTP para Custom Container (Huawei Cloud FunctionGraph).

Implementa el Patrón Adaptador (GoF Adapter) envolviendo el handler serverless existente
(functiongraph_handler) en un servidor HTTP ligero FastAPI que cumple con la especificación
de contenedores personalizados de Huawei Cloud FunctionGraph:
- Puerto 8000
- Endpoint POST /invoke: Recibe peticiones HTTP, construye el evento APIG y despacha al handler.
- Endpoint POST /init: Inicialización de runtime / precalentamiento para mitigar Cold Starts.
- Endpoint GET /health: Liveness probe y monitoreo del contenedor.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

import os

from src.infrastructure.serverless.functiongraph_handler import handler
from src.services.rtmpose3d_extractor import RTMPose3DExtractor

app = FastAPI(
    title="Corpo & Mente BJJ - FunctionGraph Custom Container Runtime",
    description="HTTP Adapter para Huawei Cloud FunctionGraph Serverless Container",
    version="1.0.0",
)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Endpoint de comprobación de salud (Liveness probe) del contenedor."""
    return {"status": "healthy"}


@app.post("/init")
async def init_runtime() -> Dict[str, Any]:
    """Endpoint de inicialización de runtime para mitigar Cold Starts.

    Precarga el modelo cinemático RTMPose3D en memoria RAM antes de recibir
    tráfico de producción de FunctionGraph.
    """
    extractor = RTMPose3DExtractor.obtener_instancia()
    repo_path = os.getenv("RTMPOSE3D_REPO_PATH", "/opt/rtmpose3d")
    extractor.inicializar_modelo(ruta_checkpoints=repo_path, device="cpu")

    return {"status": "initialized", "model_loaded": extractor.esta_inicializado}


@app.post("/invoke")
async def invoke_handler(request: Request) -> Response:
    """Endpoint principal de invocación de FunctionGraph Custom Container.

    Recibe el payload HTTP, asegura la inicialización del modelo RTMPose3D,
    construye el diccionario de evento con el formato estándar de API Gateway
    y delega la ejecución al handler existente.

    Returns:
        JSONResponse con el status_code, headers y body devueltos por el handler.
    """
    # 0. Verificación / Fallback de inicialización del modelo (Thread-Safe)
    extractor = RTMPose3DExtractor.obtener_instancia()
    if not extractor.esta_inicializado:
        repo_path = os.getenv("RTMPOSE3D_REPO_PATH", "/opt/rtmpose3d")
        extractor.inicializar_modelo(ruta_checkpoints=repo_path, device="cpu")

    # 1. Leer cuerpo crudo de la petición
    body_bytes = await request.body()


    # Intentar deserializar a string o estructura JSON
    try:
        payload_decodificado = body_bytes.decode("utf-8")
        try:
            # Si es un JSON serializado, se puede conservar estructurado o como string
            parsed_json = json.loads(payload_decodificado)
            payload_para_evento = parsed_json
        except Exception:
            payload_para_evento = payload_decodificado
    except Exception:
        # En caso de bytes binarios directos
        payload_para_evento = body_bytes

    # 2. Construir diccionario `event` en formato API Gateway
    event: Dict[str, Any] = {
        "body": payload_para_evento,
        "isBase64Encoded": False,
        "headers": dict(request.headers),
        "queryStringParameters": dict(request.query_params),
    }

    # 3. Invocar al handler de FunctionGraph
    fg_response = handler(event)

    status_code = fg_response.get("statusCode", 200)
    response_headers = fg_response.get("headers", {"Content-Type": "application/json"})
    raw_body = fg_response.get("body", "{}")

    # 4. Parsear body devuelto por el handler si es un string JSON
    if isinstance(raw_body, str):
        try:
            content_data = json.loads(raw_body)
        except Exception:
            content_data = {"raw_output": raw_body}
    elif isinstance(raw_body, dict):
        content_data = raw_body
    else:
        content_data = {"output": str(raw_body)}

    # Limpiar Content-Type de headers manuales para que FastAPI / JSONResponse lo gestione
    filtered_headers = {
        k: v for k, v in response_headers.items() if k.lower() != "content-type"
    }

    return JSONResponse(
        status_code=status_code,
        content=content_data,
        headers=filtered_headers,
    )
