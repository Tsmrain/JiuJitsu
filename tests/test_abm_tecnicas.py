# tests/test_abm_tecnicas.py
"""Pruebas TDD para el Caso de Uso de Registro de Técnicas Patrón (Larman GRASP).

Valida el filtrado por instructor, el control de integridad referencial y la
validación obligatoria de anatomía esquelética mediante AdaptadorYOLO.
"""

import pytest
from src.application.factory import (
    crear_profesor_controller,
    crear_tecnica_controller,
    reiniciar_repositorios_memoria,
)
from src.domain.models import MatrizEsqueletica, Punto3D
from src.services.adapters import AdaptadorYOLO


@pytest.fixture(autouse=True)
def limpiar_estado():
    reiniciar_repositorios_memoria()
    yield
    reiniciar_repositorios_memoria()


def matriz_valida_fixture() -> MatrizEsqueletica:
    return MatrizEsqueletica(
        puntos_3d={
            6: Punto3D(0.0, 0.0, 0.0),
            8: Punto3D(1.0, 0.0, 0.0),
            10: Punto3D(1.0, 1.0, 0.0),
        }
    )


class TestCasoDeUsoRegistrarTecnica:
    """Valida la orquestación del Session Facade TecnicaController."""

    def test_registrar_patron_valido_exitoso(self):
        prof_ctrl = crear_profesor_controller(usar_db_real=False)
        tec_ctrl = crear_tecnica_controller(usar_db_real=False)

        pid = prof_ctrl.registrar(nombre="Carlos Ribeiro", email="carlos@bjj.bo")
        tid = tec_ctrl.registrar_patron(
            id_profesor=pid,
            nombre="Armbar Clásico",
            categoria="Sumisión",
            matriz=matriz_valida_fixture(),
            video="/static/videos/armbar.mp4",
            desc="Ataque articular de hiperextensión de codo",
        )

        assert tid is not None
        tecnica = tec_ctrl.obtener_tecnica(tid)
        assert tecnica is not None
        assert tecnica["nombre"] == "Armbar Clásico"
        assert tecnica["categoria"] == "Sumisión"
        assert tecnica["total_puntos"] == 3

    def test_registrar_patron_rechaza_matriz_vacia_o_invalida(self):
        prof_ctrl = crear_profesor_controller(usar_db_real=False)
        tec_ctrl = crear_tecnica_controller(usar_db_real=False)

        pid = prof_ctrl.registrar(nombre="Carlos Ribeiro", email="carlos@bjj.bo")
        matriz_vacia = MatrizEsqueletica(puntos_3d={})

        with pytest.raises(ValueError, match="Matriz esquelética inválida"):
            tec_ctrl.registrar_patron(
                id_profesor=pid,
                nombre="Técnica Inválida",
                matriz=matriz_vacia,
            )

    def test_registrar_patron_sin_matriz_lanza_excepcion(self):
        prof_ctrl = crear_profesor_controller(usar_db_real=False)
        tec_ctrl = crear_tecnica_controller(usar_db_real=False)
        pid = prof_ctrl.registrar(nombre="Carlos Ribeiro", email="carlos@bjj.bo")

        with pytest.raises(ValueError, match="Se requiere una matriz esquelética válida"):
            tec_ctrl.registrar_patron(
                id_profesor=pid,
                nombre="Técnica Sin Matriz",
                matriz=None,
            )

    def test_registrar_patron_profesor_inexistente_lanza_excepcion(self):
        tec_ctrl = crear_tecnica_controller(usar_db_real=False)
        with pytest.raises(ValueError, match="no existe en el sistema"):
            tec_ctrl.registrar_patron(
                id_profesor="prof_fantasma_999",
                nombre="Omoplata",
                matriz=matriz_valida_fixture(),
            )

    def test_listar_por_instructor_filtra_aislado(self):
        prof_ctrl = crear_profesor_controller(usar_db_real=False)
        tec_ctrl = crear_tecnica_controller(usar_db_real=False)

        p1 = prof_ctrl.registrar("Profesor 1", "p1@bjj.bo")
        p2 = prof_ctrl.registrar("Profesor 2", "p2@bjj.bo")

        tec_ctrl.registrar_patron(id_profesor=p1, nombre="Tecnica P1 A", matriz=matriz_valida_fixture())
        tec_ctrl.registrar_patron(id_profesor=p1, nombre="Tecnica P1 B", matriz=matriz_valida_fixture())
        tec_ctrl.registrar_patron(id_profesor=p2, nombre="Tecnica P2 Única", matriz=matriz_valida_fixture())

        lista_p1 = tec_ctrl.listar_por_instructor(p1)
        lista_p2 = tec_ctrl.listar_por_instructor(p2)

        assert len(lista_p1) == 2
        assert len(lista_p2) == 1
        assert lista_p2[0]["nombre"] == "Tecnica P2 Única"

    def test_registrar_tecnica_retorna_dto_completo(self):
        prof_ctrl = crear_profesor_controller(usar_db_real=False)
        tec_ctrl = crear_tecnica_controller(usar_db_real=False)
        pid = prof_ctrl.registrar("Instructor Pro", "pro@bjj.bo")

        dto = tec_ctrl.registrar_tecnica(
            id_tecnica="kimura_cerrada",
            id_profesor=pid,
            nombre="Kimura desde Guardia",
            categoria="Sumisión",
            matriz_esqueletica=matriz_valida_fixture(),
            video_url="/static/kimura.mp4",
            descripcion="Palanca al hombro",
        )

        assert dto["id_tecnica"] == "kimura_cerrada"
        assert dto["id_profesor"] == pid
        assert dto["total_puntos"] == 3
        assert dto["video_url"] == "/static/kimura.mp4"

    def test_obtener_tecnica_inexistente_retorna_none(self):
        tec_ctrl = crear_tecnica_controller(usar_db_real=False)
        assert tec_ctrl.obtener_tecnica("inexistente_123") is None

