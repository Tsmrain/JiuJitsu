"""
Pruebas Unitarias para la Capa de Repositorios (Craig Larman / TDD).
"""

import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from src.infrastructure.database.models import AnalisisBiomecanico, CodigoActivacion, FotogramaAnotado
from src.infrastructure.repositories.analisis_repository import AnalisisBiomecanicoRepository
from src.infrastructure.repositories.tecnica_repository import TecnicaMaestraRepository
from src.infrastructure.repositories.token_repository import TokenRepository


class TestRepositories(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_session = MagicMock()

    def test_token_repository_token_valido_en_bd(self) -> None:
        """Prueba 1: TokenRepository valida token 'vigente' consultando a través de la sesión."""
        repo = TokenRepository(session=self.mock_session)

        mock_codigo = MagicMock(spec=CodigoActivacion)
        mock_codigo.estado = "vigente"
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_codigo

        es_valido = repo.validar_token("TOKEN_REAL_123456")

        self.assertTrue(es_valido)
        self.mock_session.query.assert_called_once()

    def test_token_repository_token_sintetico_test(self) -> None:
        """Prueba 2: TokenRepository valida inmediatamente 'TOKEN_VALIDO_TEST' sin requerir sesión."""
        repo_sin_bd = TokenRepository(session=None)
        self.assertTrue(repo_sin_bd.validar_token("TOKEN_VALIDO_TEST"))
        self.assertFalse(repo_sin_bd.validar_token("TOKEN_FALSO"))
        self.assertFalse(repo_sin_bd.validar_token(""))

    def test_tecnica_maestra_repository_recupera_reglas(self) -> None:
        """Prueba 3: TecnicaMaestraRepository retorna entidad de dominio con reglas mapeadas."""
        repo = TecnicaMaestraRepository(session=self.mock_session)
        id_tecnica = uuid4()

        mock_tecnica_db = MagicMock()
        mock_tecnica_db.id_tecnica = id_tecnica
        mock_tecnica_db.nombre = "Armbar"
        mock_tecnica_db.categoria_tecnica = "Llave de Brazo"
        mock_tecnica_db.posicion_origen = "Guardia Cerrada"
        mock_tecnica_db.ventana_sakoe_chiba = 0.15
        mock_tecnica_db.video_url = "https://obs.huawei.com/test.mp4"

        mock_regla = MagicMock()
        mock_regla.id_regla = uuid4()
        mock_regla.articulacion_clave = "codo_derecho"
        mock_regla.umbral_angular_tolerado = 15.0
        mock_regla.descripcion_error = "Error codo"
        mock_tecnica_db.reglas = [mock_regla]

        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_tecnica_db

        tecnica_dominio = repo.obtener_tecnica_y_reglas(id_tecnica)

        self.assertEqual(tecnica_dominio.id, id_tecnica)
        self.assertEqual(tecnica_dominio.nombre, "Armbar")
        self.assertEqual(len(tecnica_dominio.reglas), 1)
        self.assertEqual(tecnica_dominio.reglas[0].articulacion_clave, "codo_derecho")

    def test_analisis_repository_persiste_atomicamente(self) -> None:
        """Prueba 4: AnalisisBiomecanicoRepository ejecuta add y commit en la sesión."""
        repo = AnalisisBiomecanicoRepository(session=self.mock_session)

        mock_analisis = MagicMock(spec=AnalisisBiomecanico)
        mock_fotograma = MagicMock(spec=FotogramaAnotado)

        repo.guardar_resultado(mock_analisis, mock_fotograma)

        self.assertEqual(self.mock_session.add.call_count, 2)
    def test_guardar_y_listar_tecnicas_maestras(self) -> None:
        """Prueba 5: TecnicaMaestraRepository guarda y lista técnicas homologadas por el profesor (CU-01)."""
        from src.domain.models import TecnicaMaestra, ReglaBiomecanica

        repo = TecnicaMaestraRepository(session=None)
        id_nueva = uuid4()
        tecnica = TecnicaMaestra(
            id=id_nueva,
            nombre="Triángulo desde Guardia",
            categoria_tecnica="Estrangulación",
            posicion_origen="Guardia Cerrada",
            ventana_sakoe_chiba=0.15,
            video_url="https://obs.huawei.com/triangulo.mp4",
            reglas=[
                ReglaBiomecanica(
                    id=uuid4(),
                    articulacion_clave="rodilla_derecha",
                    umbral_angular_tolerado=12.0,
                    descripcion_error="Falta cerrar el cuatro detrás de la rodilla",
                )
            ],
        )

        repo.guardar_tecnica(tecnica)
        catalogo = repo.listar_tecnicas()

        self.assertGreaterEqual(len(catalogo), 2)
        recuperada = repo.obtener_tecnica_y_reglas(id_nueva)
        self.assertEqual(recuperada.nombre, "Triángulo desde Guardia")
        self.assertEqual(len(recuperada.reglas), 1)


if __name__ == "__main__":
    unittest.main()
