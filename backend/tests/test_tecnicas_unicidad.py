from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from corpocmente.domain.entities.models import NombreTecnica
from corpocmente.ui.api.auth_routes import _sign_token


def _staff_headers(role: str = "profesor") -> dict:
    token = _sign_token({
        "uid": str(uuid4()),
        "role": role,
        "email": f"{role}@test.com",
        "sucursal_id": "b3000000-0000-0000-0000-000000000003",
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Larman (Information Expert / Value Object): NombreTecnica
# ---------------------------------------------------------------------------

def test_nombre_tecnica_equivalencia_canonica_y_legibilidad():
    v1 = NombreTecnica.crear("Montada")
    v2 = NombreTecnica.crear("  montada  ")
    v3 = NombreTecnica.crear("mONTAda")

    assert v1.visible == "Montada"
    assert v2.visible == "montada"
    assert v1.clave_canonica == "montada"
    assert v1.clave_canonica == v2.clave_canonica == v3.clave_canonica

    llave1 = NombreTecnica.crear("Llave de Brazo")
    llave2 = NombreTecnica.crear("llavedebrazo")
    llave3 = NombreTecnica.crear("  LLÁVE   de   Brázó! ")

    assert llave1.visible == "Llave de Brazo"
    assert llave3.visible == "LLÁVE de Brázó!"
    assert llave1.clave_canonica == "llavedebrazo"
    assert llave1.clave_canonica == llave2.clave_canonica == llave3.clave_canonica


def test_nombre_tecnica_permite_variantes_distintas():
    base = NombreTecnica.crear("Llave de Brazo")
    variante = NombreTecnica.crear("Llave de brazo desde la Montada")
    assert base.clave_canonica != variante.clave_canonica


@pytest.mark.parametrize("invalido", ["", "   ", "\t\n", "---", "!!!"])
def test_nombre_tecnica_rechaza_vacios_o_sin_alfanumericos(invalido: str):
    with pytest.raises(ValueError):
        NombreTecnica.crear(invalido)


# ---------------------------------------------------------------------------
# API / Mannino + Larman: Validación en POST y PUT /api/v1/tecnicas
# ---------------------------------------------------------------------------

def test_crear_tecnica_normaliza_espacios_y_rechaza_duplicados(client):
    existente_id = str(uuid4())
    nueva_id = str(uuid4())

    def rpc_side_effect(fn_name, params):
        if fn_name == "get_tecnicas_with_videos":
            return [
                {
                    "id": existente_id,
                    "nombre": "Llave de Brazo",
                    "nivel_cinturon": "Blanco",
                    "mensaje_profesor": "Controla la muñeca",
                    "tiene_patron": True,
                }
            ]
        if fn_name == "admin_create_tecnica":
            return [
                {
                    "id": nueva_id,
                    "nombre": params["p_nombre"],
                    "nivel_cinturon": params["p_nivel_cinturon"],
                    "mensaje_profesor": params["p_mensaje_profesor"],
                }
            ]
        return []

    fake_db = MagicMock()
    fake_db.rpc.side_effect = rpc_side_effect
    headers = _staff_headers("profesor")

    with (
        patch("corpocmente.ui.api.tecnicas_routes.get_db", return_value=fake_db),
        patch("corpocmente.ui.api.tecnicas_routes.sincronizar_mensaje_profesor"),
    ):
        for nombre_dup in ["llave de brazo", "LLAVEDEBRAZO", "  Llávé   de   Brazo  "]:
            resp_dup = client.post(
                "/api/v1/tecnicas",
                headers=headers,
                json={"nombre": nombre_dup, "nivel_cinturon": "Blanco", "mensaje_profesor": ""},
            )
            assert resp_dup.status_code == 409, f"Esperaba 409 para '{nombre_dup}', obtuvo {resp_dup.status_code}"
            assert "Llave de Brazo" in resp_dup.json()["detail"]

        resp_blank = client.post(
            "/api/v1/tecnicas",
            headers=headers,
            json={"nombre": "   ---   ", "nivel_cinturon": "Blanco", "mensaje_profesor": ""},
        )
        assert resp_blank.status_code == 422

        resp_variante = client.post(
            "/api/v1/tecnicas",
            headers=headers,
            json={"nombre": "  Llave   de brazo desde   la Montada  ", "nivel_cinturon": "Azul", "mensaje_profesor": "Cadera arriba"},
        )
        assert resp_variante.status_code == 201
        assert resp_variante.json()["nombre"] == "Llave de brazo desde la Montada"


def test_crear_tecnica_traduce_error_unique_violation_de_postgres_a_409(client):
    def rpc_side_effect(fn_name, params):
        if fn_name == "get_tecnicas_with_videos":
            return []
        if fn_name == "admin_create_tecnica":
            raise RuntimeError('DUPLICATE_TECHNIQUE:Montada')
        return []

    fake_db = MagicMock()
    fake_db.rpc.side_effect = rpc_side_effect

    with patch("corpocmente.ui.api.tecnicas_routes.get_db", return_value=fake_db):
        resp = client.post(
            "/api/v1/tecnicas",
            headers=_staff_headers("admin"),
            json={"nombre": "mONTAda", "nivel_cinturon": "Blanco", "mensaje_profesor": ""},
        )
    assert resp.status_code == 409
    assert "Montada" in resp.json()["detail"]


def test_actualizar_tecnica_permite_propio_nombre_y_rechaza_colision_con_otra(client):
    tec_a = str(uuid4())
    tec_b = str(uuid4())

    def rpc_side_effect(fn_name, params):
        if fn_name == "get_tecnicas_with_videos":
            return [
                {"id": tec_a, "nombre": "Montada", "nivel_cinturon": "Blanco", "mensaje_profesor": ""},
                {"id": tec_b, "nombre": "Guardia Cerrada", "nivel_cinturon": "Blanco", "mensaje_profesor": ""},
            ]
        if fn_name == "admin_update_tecnica":
            return [
                {
                    "id": params["p_tecnica_id"],
                    "nombre": params["p_nombre"],
                    "nivel_cinturon": params["p_nivel_cinturon"],
                    "mensaje_profesor": params["p_mensaje_profesor"],
                }
            ]
        return []

    fake_db = MagicMock()
    fake_db.rpc.side_effect = rpc_side_effect
    headers = _staff_headers("profesor")

    with (
        patch("corpocmente.ui.api.tecnicas_routes.get_db", return_value=fake_db),
        patch("corpocmente.ui.api.tecnicas_routes.sincronizar_mensaje_profesor"),
    ):
        # Renombrar tec_a cambiando mayúsculas/espacios a equivalente propio sí está permitido
        resp_own = client.put(
            f"/api/v1/tecnicas/{tec_a}",
            headers=headers,
            json={"nombre": "  montada  ", "nivel_cinturon": "Azul", "mensaje_profesor": "Peso abajo"},
        )
        assert resp_own.status_code == 200
        assert resp_own.json()["nombre"] == "montada"

        # Intentar renombrar tec_a al equivalente de tec_b debe fallar con 409
        resp_col = client.put(
            f"/api/v1/tecnicas/{tec_a}",
            headers=headers,
            json={"nombre": "guardiaCerrada", "nivel_cinturon": "Blanco", "mensaje_profesor": ""},
        )
        assert resp_col.status_code == 409
        assert "Guardia Cerrada" in resp_col.json()["detail"]
