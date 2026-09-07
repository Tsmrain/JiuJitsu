import unittest
import numpy as np
from uuid import UUID

from src.domain.value_objects import Keypoint, Frame, AnguloArticular, ErrorBiomecanico
from src.domain.entities import TecnicaMaestra, ReglaBiomecanica, AnalisisBiomecanico, FotogramaAnotado


class TestDomainEntities(unittest.TestCase):
    def test_keypoint_inmutable(self):
        """Verifica que Keypoint sea un objeto de valor inmutable con coordenadas float."""
        kp = Keypoint(x=150.5, y=200.0, confianza=0.95)
        self.assertEqual(kp.x, 150.5)
        self.assertEqual(kp.y, 200.0)
        self.assertEqual(kp.confianza, 0.95)

        arr = kp.to_array()
        self.assertIsInstance(arr, np.ndarray)
        self.assertEqual(arr.shape, (2,))

        # Inmutabilidad (frozen dataclass)
        with self.assertRaises((AttributeError, TypeError)):
            kp.x = 300.0

    def test_frame_value_object(self):
        """Verifica el objeto de valor Frame y su colección de puntos clave."""
        kp1 = Keypoint(x=10.0, y=20.0)
        kp2 = Keypoint(x=30.0, y=40.0)
        frame = Frame(index=5, keypoints=[kp1, kp2])

        self.assertEqual(frame.index, 5)
        self.assertEqual(len(frame.keypoints), 2)
        self.assertEqual(frame.get_keypoint_by_index(0), kp1)
        self.assertIsNone(frame.get_keypoint_by_index(99))

    def test_angulo_articular_validacion(self):
        """Verifica validación y cálculo de diferencia de AnguloArticular."""
        ang1 = AnguloArticular(articulacion="codo_izq", valor=90.0, frame=10)
        ang2 = AnguloArticular(articulacion="codo_izq", valor=115.5, frame=10)

        self.assertTrue(ang1.es_valido(0.0, 180.0))
        ang_invalido = AnguloArticular(articulacion="rodilla_der", valor=220.0, frame=1)
        self.assertFalse(ang_invalido.es_valido(0.0, 180.0))

        diff = ang1.diferencia(ang2)
        self.assertAlmostEqual(diff, 25.5, places=2)

    def test_error_biomecanico_critico(self):
        """Verifica el cálculo de error crítico en base a umbrales configurables."""
        error_leve = ErrorBiomecanico(
            articulacion="cadera", angulo_alumno=80.0, angulo_maestro=70.0,
            diferencia=10.0, frame=25
        )
        self.assertFalse(error_leve.es_critico(umbral=15.0))

        error_grave = ErrorBiomecanico(
            articulacion="rodilla_izq", angulo_alumno=180.0, angulo_maestro=90.0,
            diferencia=90.0, frame=51, mensaje="Extensión excesiva"
        )
        self.assertTrue(error_grave.es_critico(umbral=15.0))

    def test_regla_biomecanica_evaluacion(self):
        """Verifica la evaluación lógica de reglas de negocio biomecánicas."""
        regla = ReglaBiomecanica(
            articulacion_clave="rodilla_izq",
            umbral_angular_tolerado=15.0,
            descripcion_error="Desviación mayor a 15 grados tolerados"
        )
        self.assertFalse(regla.evaluar(10.0))
        self.assertTrue(regla.evaluar(15.5))

    def test_tecnica_maestra_entidad(self):
        """Verifica la entidad TecnicaMaestra y su identidad unívoca UUID."""
        tecnica = TecnicaMaestra(
            nombre="Armbar desde Guardia Cerrada",
            categoria="Finalización",
            posicion_origen="Guardia Cerrada"
        )
        self.assertIsInstance(tecnica.id, UUID)
        self.assertEqual(tecnica.ventana_sakoe_chiba, 0.15)
        self.assertEqual(len(tecnica.reglas), 0)

    def test_analisis_biomecanico_entidad(self):
        """Verifica la entidad AnalisisBiomecanico consolidando fotograma y errores."""
        fotograma = FotogramaAnotado(
            imagen_url="resultados/fotogramas/error.jpg",
            coordenada_error_x=320,
            coordenada_error_y=240,
            explicacion_causa="Desviación crítica en rodilla izquierda"
        )
        analisis = AnalisisBiomecanico(
            desviacion_angular_maxima=35.5,
            articulacion_afectada="rodilla_izq",
            fotograma_anotado=fotograma
        )
        self.assertIsInstance(analisis.id, UUID)
        self.assertEqual(analisis.estado_computo, "completado")
        self.assertEqual(analisis.fotograma_anotado.coordenada_error_x, 320)


if __name__ == '__main__':
    unittest.main()
