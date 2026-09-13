# tests/test_abm_profesores.py
"""Pruebas TDD para el Caso de Uso de Administración de Profesores (Larman GRASP).

Valida el ciclo Red-Green-Refactor, la verificación de unicidad de correo (BCNF)
y la integridad referencial con eliminación en cascada sin requerir PostgreSQL activo.
"""

import pytest
from src.application.factory import (
    crear_profesor_controller,
    crear_tecnica_controller,
    reiniciar_repositorios_memoria,
)
from src.domain.models import MatrizEsqueletica, Punto3D


@pytest.fixture(autouse=True)
def limpiar_estado():
    """Garantiza aislamiento estricto de datos en memoria antes de cada test."""
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


class TestCasoDeUsoRegistrarProfesor:
    """Valida la orquestación del Session Facade ProfesorController."""

    def test_registrar_profesor_valido_retorna_id(self):
        controller = crear_profesor_controller(usar_db_real=False)
        resultado = controller.registrar(nombre="Carlos Ribeiro", email="carlos@bjj.bo")
        assert resultado is not None
        assert isinstance(resultado, str)
        assert len(resultado) > 0

    def test_registrar_email_duplicado_lanza_excepcion(self):
        controller = crear_profesor_controller(usar_db_real=False)
        controller.registrar(nombre="Carlos Ribeiro", email="dup@bjj.bo")
        with pytest.raises(ValueError, match="ya se encuentra registrado"):
            controller.registrar(nombre="Otro Instructor", email="dup@bjj.bo")

    def test_eliminar_profesor_cascada_tecnicas(self):
        """Verifica integridad referencial ON DELETE CASCADE según Mannino."""
        tec_ctrl = crear_tecnica_controller(usar_db_real=False)
        prof_ctrl = crear_profesor_controller(usar_db_real=False)

        pid = prof_ctrl.registrar(nombre="Prof. Helio", email="helio@bjj.bo")
        tec_ctrl.registrar_patron(
            id_profesor=pid,
            nombre="Guardia Cerrada",
            categoria="Defensa",
            matriz=matriz_valida_fixture(),
            video="/static/test.mp4",
            desc="Control fundamental",
        )

        assert len(tec_ctrl.listar_por_instructor(pid)) == 1

        prof_ctrl.eliminar(pid)
        assert len(tec_ctrl.listar_por_instructor(pid)) == 0

    def test_obtener_profesor_existente_e_inexistente(self):
        controller = crear_profesor_controller(usar_db_real=False)
        pid = controller.registrar(nombre="Santiago Morales", email="santiago@bjj.bo")

        profesor = controller.obtener_profesor(pid)
        assert profesor is not None
        assert profesor["id_profesor"] == pid
        assert profesor["nombre"] == "Santiago Morales"
        assert profesor["email"] == "santiago@bjj.bo"

        inexistente = controller.obtener_profesor("id_inexistente_999")
        assert inexistente is None

    def test_listar_profesores_ordenados_alfabeticamente(self):
        controller = crear_profesor_controller(usar_db_real=False)
        controller.registrar(nombre="Zack", email="zack@bjj.bo")
        controller.registrar(nombre="Alberto", email="alberto@bjj.bo")

        lista = controller.listar_profesores()
        assert len(lista) == 2
        assert lista[0]["nombre"] == "Alberto"
        assert lista[1]["nombre"] == "Zack"

    def test_crear_profesor_retorna_dto_completo(self):
        controller = crear_profesor_controller(usar_db_real=False)
        dto = controller.crear_profesor(id_profesor="P_EXPLICITO", nombre="Rickson", email="rickson@bjj.bo")
        assert dto["id_profesor"] == "P_EXPLICITO"
        assert dto["nombre"] == "Rickson"
        assert dto["email"] == "rickson@bjj.bo"
        assert dto["fecha_registro"] is not None

    def test_eliminar_profesor_alias_y_sin_tecnica_repo(self):
        from src.infrastructure.mocks import InMemoryProfesorRepository
        repo = InMemoryProfesorRepository()
        from src.application.profesor_controller import ProfesorController
        ctrl = ProfesorController(repository=repo, tecnica_repository=None)
        pid = ctrl.registrar(nombre="Royce", email="royce@bjj.bo")
        assert ctrl.obtener_profesor(pid) is not None
        assert ctrl.eliminar_profesor(pid) is True
        assert ctrl.obtener_profesor(pid) is None

    def test_eliminar_profesor_con_tecnica_repo_sin_eliminar_por_instructor(self):
        from unittest.mock import MagicMock
        from src.infrastructure.mocks import InMemoryProfesorRepository
        from src.application.profesor_controller import ProfesorController
        mock_tec_repo = MagicMock(spec=["listar_por_instructor", "eliminar"])
        mock_t = MagicMock()
        mock_t.id_tecnica = "T_MOCK"
        mock_tec_repo.listar_por_instructor.return_value = [mock_t]
        mock_tec_repo.eliminar.return_value = True

        repo = InMemoryProfesorRepository()
        ctrl = ProfesorController(repository=repo, tecnica_repository=mock_tec_repo)
        pid = ctrl.registrar(nombre="Kron", email="kron@bjj.bo")
        assert ctrl.eliminar(pid) is True
        mock_tec_repo.eliminar.assert_called_once_with("T_MOCK")

