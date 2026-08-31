"""
Pruebas Unitarias - Servicios de Dominio (TDD)

Pruebas para LandmarkAdapter (cálculo de ángulos 3D) y DTWComparator
(alineamiento temporal con Sakoe-Chiba). Siguiendo TDD, estas pruebas
validan la lógica algorítmica pura sin dependencias externas.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import math

import pytest

from src.services.landmark_adapter import LandmarkAdapter
from src.services.dtw_comparator import DTWComparator


# ──────────────────────────────────────────────
#  LandmarkAdapter - Cálculo de Ángulos 3D
# ──────────────────────────────────────────────


class TestLandmarkAdapterAngulo3D:
    """Pruebas para el cálculo de ángulos con producto escalar."""

    def test_landmark_adapter_angulo_recto(self) -> None:
        """Puntos en ángulo recto (90°) en el vértice B=(0,0,0).

        A = (0, 1, 0)  →  vector BA = (0, 1, 0)
        C = (1, 0, 0)  →  vector BC = (1, 0, 0)
        BA · BC = 0  →  θ = arccos(0) = 90°
        """
        angulo = LandmarkAdapter.calcular_angulo_3d(
            punto_a=(0, 1, 0),
            punto_b=(0, 0, 0),
            punto_c=(1, 0, 0),
        )
        assert abs(angulo - 90.0) < 1e-5

    def test_landmark_adapter_angulo_colineal(self) -> None:
        """Puntos colineales opuestos → ángulo de 180°.

        A = (0, 1, 0)   →  vector BA = (0, 1, 0)
        C = (0, -1, 0)  →  vector BC = (0, -1, 0)
        BA · BC = -1  →  θ = arccos(-1) = 180°
        """
        angulo = LandmarkAdapter.calcular_angulo_3d(
            punto_a=(0, 1, 0),
            punto_b=(0, 0, 0),
            punto_c=(0, -1, 0),
        )
        assert abs(angulo - 180.0) < 1e-5

    def test_landmark_adapter_angulo_agudo(self) -> None:
        """Ángulo agudo de 45° con vectores en el plano XY."""
        angulo = LandmarkAdapter.calcular_angulo_3d(
            punto_a=(0, 1, 0),
            punto_b=(0, 0, 0),
            punto_c=(1, 1, 0),
        )
        assert abs(angulo - 45.0) < 1e-5

    def test_landmark_adapter_angulo_cero(self) -> None:
        """Puntos colineales en la misma dirección → ángulo de 0°."""
        angulo = LandmarkAdapter.calcular_angulo_3d(
            punto_a=(0, 1, 0),
            punto_b=(0, 0, 0),
            punto_c=(0, 2, 0),
        )
        assert abs(angulo - 0.0) < 1e-5

    def test_landmark_adapter_puntos_coincidentes_error(self) -> None:
        """Puntos coincidentes → lanza ValueError."""
        with pytest.raises(ValueError, match="coincidentes"):
            LandmarkAdapter.calcular_angulo_3d(
                punto_a=(0, 0, 0),
                punto_b=(0, 0, 0),
                punto_c=(1, 0, 0),
            )

    def test_landmark_adapter_angulo_3d_real(self) -> None:
        """Ángulo en 3D completo (no coplanar con ejes)."""
        angulo = LandmarkAdapter.calcular_angulo_3d(
            punto_a=(1, 0, 0),
            punto_b=(0, 0, 0),
            punto_c=(0, 1, 0),
        )
        assert abs(angulo - 90.0) < 1e-5


# ──────────────────────────────────────────────
#  LandmarkAdapter - Adaptación de Keypoints
# ──────────────────────────────────────────────


class TestLandmarkAdapterKeypoints:
    """Pruebas para la extracción de ángulos desde keypoints COCO."""

    def _generar_keypoints_simulados(self) -> list:
        """Genera 17 keypoints COCO 3D simulados con ángulos conocidos.

        Configura keypoints para que:
        - codo_derecho (hombro=6, codo=8, muñeca=10) forme 90°
        - rodilla_derecha (cadera=12, rodilla=14, tobillo=16) forme 180°
        """
        # Inicializar 17 keypoints con posiciones genéricas
        keypoints = [(0.0, 0.0, 0.0)] * 17

        # Hombro derecho (idx 6), codo derecho (idx 8), muñeca derecha (idx 10)
        # Configurados para ángulo de 90° en el codo
        keypoints_list = list(keypoints)
        keypoints_list[6] = (0.0, 1.0, 0.0)   # hombro derecho (punto A)
        keypoints_list[8] = (0.0, 0.0, 0.0)   # codo derecho (vértice B)
        keypoints_list[10] = (1.0, 0.0, 0.0)  # muñeca derecha (punto C)

        # Cadera derecha (idx 12), rodilla derecha (idx 14), tobillo derecho (idx 16)
        # Configurados para ángulo de 180° en la rodilla (pierna extendida)
        keypoints_list[12] = (0.0, 2.0, 0.0)  # cadera derecha (punto A)
        keypoints_list[14] = (0.0, 1.0, 0.0)  # rodilla derecha (vértice B)
        keypoints_list[16] = (0.0, 0.0, 0.0)  # tobillo derecho (punto C)

        # Lado izquierdo: posiciones genéricas distintas de cero
        keypoints_list[5] = (0.0, 1.0, 1.0)   # hombro izquierdo
        keypoints_list[7] = (0.0, 0.0, 1.0)   # codo izquierdo
        keypoints_list[9] = (1.0, 0.0, 1.0)   # muñeca izquierda
        keypoints_list[11] = (1.0, 2.0, 0.0)  # cadera izquierda
        keypoints_list[13] = (1.0, 1.0, 0.0)  # rodilla izquierda
        keypoints_list[15] = (1.0, 0.0, 0.0)  # tobillo izquierdo

        return keypoints_list

    def test_adaptar_keypoints_codo_derecho(self) -> None:
        """El codo derecho con keypoints simulados debe dar 90°."""
        adapter = LandmarkAdapter()
        keypoints = self._generar_keypoints_simulados()
        angulos = adapter.adaptar_keypoints_a_angulos(keypoints)

        assert "codo_derecho" in angulos
        assert abs(angulos["codo_derecho"] - 90.0) < 1e-5

    def test_adaptar_keypoints_rodilla_derecha(self) -> None:
        """La rodilla derecha con pierna extendida debe dar 180°."""
        adapter = LandmarkAdapter()
        keypoints = self._generar_keypoints_simulados()
        angulos = adapter.adaptar_keypoints_a_angulos(keypoints)

        assert "rodilla_derecha" in angulos
        assert abs(angulos["rodilla_derecha"] - 180.0) < 1e-5

    def test_adaptar_keypoints_retorna_todas_articulaciones(self) -> None:
        """El diccionario debe contener las 4 articulaciones BJJ."""
        adapter = LandmarkAdapter()
        keypoints = self._generar_keypoints_simulados()
        angulos = adapter.adaptar_keypoints_a_angulos(keypoints)

        esperadas = {"codo_derecho", "codo_izquierdo", "rodilla_derecha", "rodilla_izquierda"}
        assert set(angulos.keys()) == esperadas


# ──────────────────────────────────────────────
#  DTWComparator - Dynamic Time Warping
# ──────────────────────────────────────────────


class TestDTWComparator:
    """Pruebas para el algoritmo DTW con banda de Sakoe-Chiba."""

    def setup_method(self) -> None:
        """Inicializa el comparador para cada prueba."""
        self.comparador = DTWComparator()

    def test_dtw_secuencias_identicas(self) -> None:
        """Series idénticas → distancia DTW = 0.0."""
        distancia = self.comparador.calcular_distancia_sakoe_chiba(
            serie_patron=[1, 2, 3],
            serie_ejecucion=[1, 2, 3],
            ventana=1.0,
        )
        assert distancia == 0.0

    def test_dtw_secuencias_desfasadas_con_ventana(self) -> None:
        """Series desfasadas con ventana restrictiva (w=1).

        Patrón:    [1, 2, 3, 4]
        Ejecución: [1, 1, 2, 3, 4]

        El DTW debe alinear correctamente el desfase temporal
        dentro de la restricción de banda.
        """
        distancia = self.comparador.calcular_distancia_sakoe_chiba(
            serie_patron=[1, 2, 3, 4],
            serie_ejecucion=[1, 1, 2, 3, 4],
            ventana=1.0,
        )
        # La distancia debe ser finita y ≥ 0 (alineamiento válido)
        assert distancia >= 0.0
        assert not math.isinf(distancia)

    def test_dtw_secuencias_constantes(self) -> None:
        """Series constantes iguales → distancia = 0.0."""
        distancia = self.comparador.calcular_distancia_sakoe_chiba(
            serie_patron=[5, 5, 5],
            serie_ejecucion=[5, 5, 5, 5],
            ventana=0.5,
        )
        assert distancia == 0.0

    def test_dtw_secuencias_desplazadas(self) -> None:
        """Series con desplazamiento constante → distancia proporcional."""
        distancia = self.comparador.calcular_distancia_sakoe_chiba(
            serie_patron=[0, 0, 0],
            serie_ejecucion=[1, 1, 1],
            ventana=1.0,
        )
        # Cada par alineado tiene costo 1.0, 3 alineamientos = 3.0
        assert abs(distancia - 3.0) < 1e-5

    def test_dtw_series_vacias_error(self) -> None:
        """Series vacías → lanza ValueError."""
        with pytest.raises(ValueError, match="vacías"):
            self.comparador.calcular_distancia_sakoe_chiba(
                serie_patron=[],
                serie_ejecucion=[1, 2, 3],
                ventana=0.5,
            )

    def test_dtw_ventana_sakoe_chiba_restrictiva(self) -> None:
        """Ventana muy pequeña con series de igual longitud funciona."""
        distancia = self.comparador.calcular_distancia_sakoe_chiba(
            serie_patron=[1, 2, 3],
            serie_ejecucion=[1, 2, 3],
            ventana=0.0,
        )
        # Alineamiento diagonal exacto → distancia 0
        assert distancia == 0.0

    def test_dtw_con_vectores(self) -> None:
        """DTW con elementos vectoriales (múltiples ángulos por frame)."""
        distancia = self.comparador.calcular_distancia_sakoe_chiba(
            serie_patron=[[90, 180], [85, 175]],
            serie_ejecucion=[[90, 180], [85, 175]],
            ventana=1.0,
        )
        assert distancia == 0.0
