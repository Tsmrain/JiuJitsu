import pytest
from src.domain.services.dtw_comparator import DTWComparatorImpl


class TestDTWComparator:
    """Pruebas unitarias para el alineador temporal DTW con ventana Sakoe-Chiba (TDD)."""

    def setup_method(self):
        self.comparator = DTWComparatorImpl()

    def test_series_identicas_distancia_cero(self):
        """Prueba: series idénticas producen distancia DTW igual a 0."""
        serie = [45.0, 50.0, 60.0, 75.0, 90.0]
        dist, path = self.comparator.comparar(serie, serie)
        assert dist == pytest.approx(0.0, 0.001)
        assert len(path) == len(serie)

    def test_desplazamiento_constante(self):
        """Prueba: desplazamiento constante entre series produce la suma de diferencias."""
        serie_a = [10.0, 20.0, 30.0, 40.0]
        serie_b = [12.0, 22.0, 32.0, 42.0]
        dist, path = self.comparator.comparar(serie_a, serie_b)
        assert dist == pytest.approx(8.0, 0.01)

    def test_camino_deformacion_fronteras(self):
        """Prueba: el camino de deformación inicia en (0,0) y termina en (N-1, M-1)."""
        serie_a = [10.0, 20.0, 30.0, 40.0, 50.0]
        serie_b = [10.0, 10.0, 20.0, 30.0, 50.0]
        dist, path = self.comparator.comparar(serie_a, serie_b)
        assert path[0] == (0, 0)
        assert path[-1] == (len(serie_a) - 1, len(serie_b) - 1)

    def test_series_vacias_retorna_infinito(self):
        """Prueba: series vacías retornan distancia infinita y camino vacío sin fallar."""
        dist, path = self.comparator.comparar([], [10.0, 20.0])
        assert dist == float('inf')
        assert path == []

    def test_comparar_articulacion_secuencias(self):
        """Prueba: extracción y comparación por articulación específica."""
        maestro = [{'rodilla_izq': 90.0}, {'rodilla_izq': 100.0}, {'rodilla_izq': 110.0}]
        alumno = [{'rodilla_izq': 85.0}, {'rodilla_izq': 95.0}, {'rodilla_izq': 105.0}]
        dist, path, sm, sa = self.comparator.comparar_articulacion(maestro, alumno, 'rodilla_izq')
        assert dist is not None
        assert dist == pytest.approx(15.0, 0.1)
        assert len(sm) == 3
        assert len(sa) == 3
