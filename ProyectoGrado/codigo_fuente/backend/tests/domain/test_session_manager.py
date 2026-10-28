import pytest
import os
import time
from uuid import uuid4

from corpocmente.domain.services.session_manager import (
    SessionStateManager, SessionState, SessionConflictError,
    SessionNotFoundError, SessionExpiredError, SessionError
)

def test_session_lifecycle_transitions(tmp_path):
    session_id = str(uuid4())
    fake_video = "/tmp/test_vid.mp4"
    personas = [{"idx": 0, "bbox": [10, 10, 50, 50], "confianza": 0.9, "keypoints_validos": 15}]

    # 1. Crear sesión
    sesion = SessionStateManager.crear_sesion(session_id, fake_video, personas, 0)
    assert sesion["estado"] == SessionState.CREATED
    assert sesion["persona_idx_seleccionada"] is None

    # 2. Conflicto al reusar session_id
    with pytest.raises(SessionConflictError):
        SessionStateManager.crear_sesion(session_id, fake_video, personas, 0)

    # 3. Seleccionar persona inválida
    with pytest.raises(SessionError) as exc:
        SessionStateManager.seleccionar_persona(session_id, 99)
    assert exc.value.status_code == 422

    # 4. Seleccionar persona válida
    sesion = SessionStateManager.seleccionar_persona(session_id, 0)
    assert sesion["estado"] == SessionState.PERSONA_SELECTED
    assert sesion["persona_idx_seleccionada"] == 0

    # 5. Iniciar operación
    sesion = SessionStateManager.iniciar_operacion(session_id, "tecnica-123")
    assert sesion["estado"] == SessionState.IN_USE

    # 6. Intentar operación concurrente sobre la misma sesión
    with pytest.raises(SessionConflictError):
        SessionStateManager.iniciar_operacion(session_id, "tecnica-123")

    # 7. Intentar cambiar persona mientras está IN_USE
    with pytest.raises(SessionConflictError):
        SessionStateManager.seleccionar_persona(session_id, 0)

    # 8. Finalizar operación
    sesion = SessionStateManager.finalizar_operacion(session_id, exito=True, eliminar_video=False)
    assert sesion["estado"] == SessionState.COMPLETED

def test_session_not_found_and_expiration():
    with pytest.raises(SessionNotFoundError):
        SessionStateManager.obtener_sesion("inexistente-uuid-123")
