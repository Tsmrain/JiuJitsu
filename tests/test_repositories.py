import unittest
import os
import shutil
import tempfile
from uuid import uuid4

from src.domain.entities import TecnicaMaestra, ReglaBiomecanica, AnalisisBiomecanico
from src.domain.value_objects import ErrorBiomecanico
from src.infrastructure.repositories import TecnicaMaestraRepository, AnalisisRepository


class TestRepositories(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.tecnicas_path = os.path.join(self.test_dir, "tecnicas.json")
        self.analisis_path = os.path.join(self.test_dir, "analisis.json")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_tecnica_maestra_crud(self):
        """Verifica las operaciones CRUD en TecnicaMaestraRepository."""
        repo = TecnicaMaestraRepository(storage_path=self.tecnicas_path)

        regla = ReglaBiomecanica(articulacion_clave="codo_izq", umbral_angular_tolerado=15.0)
        tecnica = TecnicaMaestra(
            nombre="Triángulo desde Guardia",
            categoria="Sumisión",
            posicion_origen="Guardia",
            reglas=[regla]
        )

        # Guardar
        guardada = repo.guardar(tecnica)
        self.assertEqual(guardada.nombre, "Triángulo desde Guardia")
        self.assertTrue(os.path.exists(self.tecnicas_path))

        # Obtener por ID
        recuperada = repo.obtener_por_id(tecnica.id)
        self.assertIsNotNone(recuperada)
        self.assertEqual(recuperada.id, tecnica.id)
        self.assertEqual(len(recuperada.reglas), 1)

        # Obtener todas
        todas = repo.obtener_todas()
        self.assertEqual(len(todas), 1)

        # Eliminar
        eliminada = repo.eliminar(tecnica.id)
        self.assertTrue(eliminada)
        self.assertEqual(len(repo.obtener_todas()), 0)

    def test_analisis_repository_persistencia(self):
        """Verifica la persistencia y consulta de análisis en AnalisisRepository."""
        repo = AnalisisRepository(storage_path=self.analisis_path)

        v_id = uuid4()
        analisis = AnalisisBiomecanico(
            video_id=v_id,
            desviacion_angular_maxima=42.0,
            articulacion_afectada="rodilla_izq",
            errores=[
                ErrorBiomecanico(
                    articulacion="rodilla_izq", angulo_alumno=180.0,
                    angulo_maestro=138.0, diferencia=42.0, frame=15
                )
            ]
        )

        repo.guardar(analisis)
        self.assertTrue(os.path.exists(self.analisis_path))

        # Recuperar por ID
        rec = repo.obtener_por_id(analisis.id)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.desviacion_angular_maxima, 42.0)
        self.assertEqual(len(rec.errores), 1)

        # Recuperar por Video ID
        por_video = repo.obtener_por_video(v_id)
        self.assertEqual(len(por_video), 1)
        self.assertEqual(por_video[0].id, analisis.id)


if __name__ == '__main__':
    unittest.main()
