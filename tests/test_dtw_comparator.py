import unittest
import numpy as np
from src.dtw_comparator import DTWComparator


class TestDTWComparator(unittest.TestCase):
    def test_series_identicas(self):
        """Verifica que dos series temporales idénticas arrojen distancia DTW igual a 0."""
        serie = [45.0, 50.0, 60.0, 75.0, 90.0]
        dist, path = DTWComparator.dtw_distance(serie, serie)
        self.assertAlmostEqual(dist, 0.0, places=4)
        self.assertEqual(len(path), len(serie))

    def test_desplazamiento_constante(self):
        """Verifica que un desfase constante arroje la suma exacta de las diferencias."""
        serie_a = [10.0, 20.0, 30.0, 40.0]
        serie_b = [12.0, 22.0, 32.0, 42.0]
        dist, path = DTWComparator.dtw_distance(serie_a, serie_b, window_ratio=0.5)
        self.assertAlmostEqual(dist, 8.0, places=2)

    def test_deformacion_temporal_path(self):
        """Verifica que el camino de deformación comience en (0,0) y termine en (N-1, M-1)."""
        serie_a = [10.0, 20.0, 30.0, 40.0, 50.0]
        serie_b = [10.0, 10.0, 20.0, 30.0, 50.0]
        dist, path = DTWComparator.dtw_distance(serie_a, serie_b, window_ratio=0.5)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (len(serie_a) - 1, len(serie_b) - 1))
        self.assertGreater(len(path), 0)

    def test_series_vacias(self):
        """Verifica que series vacías retornen distancia infinita y camino vacío."""
        dist, path = DTWComparator.dtw_distance([], [10.0, 20.0])
        self.assertEqual(dist, float('inf'))
        self.assertEqual(len(path), 0)

    def test_comparar_articulacion(self):
        """Verifica la comparación de una articulación presente en secuencias de diccionarios."""
        angulos_maestro = [{'rodilla_izq': 90.0}, {'rodilla_izq': 100.0}, {'rodilla_izq': 110.0}]
        angulos_alumno = [{'rodilla_izq': 85.0}, {'rodilla_izq': 95.0}, {'rodilla_izq': 105.0}]
        dist, path, sm, sa = DTWComparator.comparar_articulacion(
            angulos_maestro, angulos_alumno, 'rodilla_izq'
        )
        self.assertIsNotNone(dist)
        self.assertAlmostEqual(dist, 15.0, places=1)


if __name__ == '__main__':
    unittest.main()
