"""
Punto de Entrada Serverless para Huawei Cloud FunctionGraph (Custom Container / Runtime).
Traduce la invocación HTTP/JSON hacia el motor de cómputo biomecánico.
"""

import base64
import json
import os
import tempfile
from typing import Any, Dict
from uuid import UUID, uuid4

from src.domain.models import ReglaBiomecanica, TecnicaMaestra
from src.services.pipeline_engine import PipelineBiomecanicoEngine


def _parsear_evento(event: Any) -> Dict[str, Any]:
    """Extrae y decodifica el payload JSON del evento recibido en FunctionGraph."""
    if isinstance(event, str):
        return json.loads(event)

    if isinstance(event, dict):
        if "body" in event:
            body_val = event["body"]
            if isinstance(body_val, str):
                if event.get("isBase64Encoded", False):
                    body_val = base64.b64decode(body_val).decode("utf-8")
                return json.loads(body_val)
            elif isinstance(body_val, dict):
                return body_val
        return event

    raise ValueError("Formato de evento no reconocido por el handler de FunctionGraph.")


def handler(event: Any, context: Any = None) -> Dict[str, Any]:
    """
    Función de entrada para Huawei Cloud FunctionGraph.

    :param event: Diccionario o JSON con el evento disparado (API Gateway o llamada directa).
    :param context: Contexto de ejecución serverless provisto por Huawei Cloud.
    :return: Respuesta HTTP serializada con statusCode, headers y body JSON.
    """
    tmp_path = None
    try:
        # 1. Parsear el cuerpo de la solicitud
        payload = _parsear_evento(event)

        video_base64 = payload.get("video_base64")
        if not video_base64:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "El campo 'video_base64' es obligatorio.",
                    "estado_computo": "ERROR_SOLICITUD",
                }),
            }

        tecnica_data = payload.get("tecnica_maestra", {})

        # 2. Decodificar video y guardar en /tmp (único volumen escribible en FunctionGraph)
        video_bytes = base64.b64decode(video_base64, validate=True)
        with tempfile.NamedTemporaryFile(dir="/tmp", delete=False, suffix=".mp4") as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(video_bytes)
            tmp_file.flush()

        # 3. Reconstruir entidades de dominio puras (TecnicaMaestra y ReglaBiomecanica)
        reglas = []
        for r in tecnica_data.get("reglas", []):
            id_regla = UUID(r["id"]) if isinstance(r.get("id"), str) else (r.get("id") or uuid4())
            reglas.append(
                ReglaBiomecanica(
                    id=id_regla,
                    articulacion_clave=r.get("articulacion_clave", "codo_derecho"),
                    umbral_angular_tolerado=float(r.get("umbral_angular_tolerado", 15.0)),
                    descripcion_error=r.get("descripcion_error", "Desviación técnica angular excesiva."),
                )
            )

        id_tecnica = (
            UUID(tecnica_data["id"])
            if isinstance(tecnica_data.get("id"), str)
            else (tecnica_data.get("id") or uuid4())
        )

        tecnica = TecnicaMaestra(
            id=id_tecnica,
            nombre=tecnica_data.get("nombre", "Técnica Curricular Homologada"),
            categoria_tecnica=tecnica_data.get("categoria_tecnica", "Llave de Brazo"),
            posicion_origen=tecnica_data.get("posicion_origen", "Guardia Cerrada"),
            ventana_sakoe_chiba=float(tecnica_data.get("ventana_sakoe_chiba", 0.15)),
            video_url=tecnica_data.get("video_url", ""),
            reglas=reglas,
        )

        # 4. Instanciar motor de cómputo biomecánico y ejecutar análisis
        engine = PipelineBiomecanicoEngine(
            ventana_sakoe_chiba_default=tecnica.ventana_sakoe_chiba,
            calidad_jpeg=85,
        )

        resultado = engine.procesar_video(tmp_path, tecnica)

        # 5. Codificar el fotograma clave resultante en Base64 si existe
        fotograma_base64 = None
        if resultado.imagen_jpg_bytes is not None:
            fotograma_base64 = base64.b64encode(resultado.imagen_jpg_bytes).decode("utf-8")

        response_body = {
            "estado_computo": resultado.estado_computo,
            "desviacion_maxima": resultado.desviacion_maxima,
            "articulacion_afectada": resultado.articulacion_afectada,
            "explicacion_error": resultado.explicacion_error,
            "fotograma_base64": fotograma_base64,
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_body),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": f"Error interno en FunctionGraph: {str(e)}",
                "estado_computo": "ERROR_SERVIDOR",
            }),
        }

    finally:
        # 6. Limpieza estricta de /tmp para evitar saturación de memoria efímera
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
