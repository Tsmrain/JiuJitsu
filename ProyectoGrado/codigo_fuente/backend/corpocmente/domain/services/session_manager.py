"""
Gestor del ciclo de vida de sesiones de video en CorpocMente.

Estados válidos:
  • CREATED: video subido, primer frame analizado, en espera de selección de persona.
  • PERSONA_SELECTED: persona confirmada por el usuario (profesor o alumno).
  • IN_USE: análisis DTW o registro de patrón en ejecución.
  • COMPLETED: operación finalizada con éxito.
  • FAILED: operación fallida (con período de gracia para diagnóstico).
"""

import os
import json
import time
from typing import Optional, Dict, Any

SESSIONS_DIR = "/tmp/corpocmente_sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

class SessionState:
    CREATED = "CREATED"
    PERSONA_SELECTED = "PERSONA_SELECTED"
    IN_USE = "IN_USE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    TRANSICIONES_VALIDAS = {
        CREATED: {PERSONA_SELECTED, FAILED},
        PERSONA_SELECTED: {IN_USE, FAILED},
        IN_USE: {COMPLETED, FAILED},
        COMPLETED: set(),
        FAILED: set(),
    }

class SessionError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code

class SessionConflictError(SessionError):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)

class SessionNotFoundError(SessionError):
    def __init__(self, message: str = "Sesión no encontrada o expirada."):
        super().__init__(message, status_code=404)

class SessionExpiredError(SessionError):
    def __init__(self, message: str = "La sesión ha expirado por inactividad."):
        super().__init__(message, status_code=410)

class SessionStateManager:
    @staticmethod
    def _session_path(session_id: str) -> str:
        return os.path.join(SESSIONS_DIR, f"{session_id}.json")

    @classmethod
    def crear_sesion(cls, session_id: str, video_path: str, personas_detectadas: list, frame_idx: int) -> Dict[str, Any]:
        path = cls._session_path(session_id)
        if os.path.exists(path):
            raise SessionConflictError(f"La sesión {session_id} ya existe y no puede ser reusada.")

        datos = {
            "session_id": session_id,
            "video_path": video_path,
            "estado": SessionState.CREATED,
            "frame_idx_analizado": frame_idx,
            "personas_detectadas": personas_detectadas,
            "persona_idx_seleccionada": None,
            "creado_en": time.time(),
            "actualizado_en": time.time(),
            "tecnica_id": None,
            "error_detail": None,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2)
        return datos

    @classmethod
    def obtener_sesion(cls, session_id: str, max_age_seconds: int = 3600) -> Dict[str, Any]:
        path = cls._session_path(session_id)
        if not os.path.exists(path):
            raise SessionNotFoundError()

        with open(path, "r", encoding="utf-8") as f:
            datos = json.load(f)

        # Validación de expiración (1 hora sin actividad)
        ahora = time.time()
        if ahora - datos.get("actualizado_en", datos.get("creado_en", 0)) > max_age_seconds:
            if datos.get("estado") != SessionState.IN_USE:
                raise SessionExpiredError()

        return datos

    @classmethod
    def seleccionar_persona(cls, session_id: str, persona_idx: int) -> Dict[str, Any]:
        datos = cls.obtener_sesion(session_id)
        estado_actual = datos["estado"]

        if estado_actual == SessionState.IN_USE:
            raise SessionConflictError("La sesión está en uso por otra operación en curso.")

        personas = datos.get("personas_detectadas", [])
        indices_validos = [p["idx"] for p in personas]
        if persona_idx not in indices_validos:
            raise SessionError(f"persona_idx={persona_idx} no es válido para esta sesión. Válidos: {indices_validos}", status_code=422)

        if estado_actual in (SessionState.CREATED, SessionState.PERSONA_SELECTED):
            datos["persona_idx_seleccionada"] = persona_idx
            datos["estado"] = SessionState.PERSONA_SELECTED
            datos["actualizado_en"] = time.time()
            with open(cls._session_path(session_id), "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=2)
            return datos
        else:
            raise SessionConflictError(f"No se puede seleccionar persona en una sesión en estado {estado_actual}.")

    @classmethod
    def iniciar_operacion(cls, session_id: str, tecnica_id: Optional[str] = None) -> Dict[str, Any]:
        datos = cls.obtener_sesion(session_id)
        estado_actual = datos["estado"]

        if estado_actual == SessionState.IN_USE:
            raise SessionConflictError("Operación concurrente detectada: la sesión ya se encuentra en proceso.")

        if estado_actual not in (SessionState.CREATED, SessionState.PERSONA_SELECTED):
            raise SessionConflictError(f"No se puede iniciar operación sobre una sesión en estado {estado_actual}.")

        datos["estado"] = SessionState.IN_USE
        if tecnica_id:
            datos["tecnica_id"] = str(tecnica_id)
        datos["actualizado_en"] = time.time()
        with open(cls._session_path(session_id), "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2)
        return datos

    @classmethod
    def finalizar_operacion(cls, session_id: str, exito: bool, error: Optional[str] = None, eliminar_video: bool = True) -> Dict[str, Any]:
        try:
            datos = cls.obtener_sesion(session_id, max_age_seconds=86400)
        except Exception:
            return {}

        datos["estado"] = SessionState.COMPLETED if exito else SessionState.FAILED
        datos["error_detail"] = error
        datos["actualizado_en"] = time.time()

        video_path = datos.get("video_path")
        if exito and eliminar_video and video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass

        with open(cls._session_path(session_id), "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2)
        return datos

    @classmethod
    def limpiar_sesiones_antiguas(cls, max_age_seconds: int = 3600) -> int:
        """Elimina sesiones abandonadas o completadas antiguas sin tocar las que estén IN_USE."""
        eliminadas = 0
        ahora = time.time()
        if not os.path.exists(SESSIONS_DIR):
            return 0

        for arch in os.listdir(SESSIONS_DIR):
            if not arch.endswith(".json"):
                continue
            path = os.path.join(SESSIONS_DIR, arch)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                if datos.get("estado") == SessionState.IN_USE:
                    continue
                tiempo_inactivo = ahora - datos.get("actualizado_en", datos.get("creado_en", 0))
                limite = 300 if datos.get("estado") in (SessionState.COMPLETED, SessionState.FAILED) else max_age_seconds
                if tiempo_inactivo > limite:
                    video_path = datos.get("video_path")
                    if video_path and os.path.exists(video_path):
                        try:
                            os.remove(video_path)
                        except Exception:
                            pass
                    os.remove(path)
                    eliminadas += 1
            except Exception:
                pass
        return eliminadas
