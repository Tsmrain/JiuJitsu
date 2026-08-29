"""
Pruebas Unitarias TDD para el Servicio de Similitud de Posición 3D, Exportación CSV y Gráficos (RF-13, RF-14, RF-15).
"""

import csv
import os
from pathlib import Path
import tempfile
import unittest

from src.services.position_similarity import (
    GRUPOS_PUNTOS_CLAVE_28,
    PositionSimilarityService,
)


class TestPositionSimilarityService(unittest.TestCase):
    """Batería de pruebas unitarias para PositionSimilarityService según TDD estricto."""

    def setUp(self) -> None:
        self.service = PositionSimilarityService()

    def test_calculate_position_similarity_perfect_match(self) -> None:
        """Prueba 1 (RF-13): Dos esqueletos con coordenadas 3D idénticas deben arrojar 100.0% de similitud."""
        landmarks_identicos_1 = [(0.2, 0.4, -0.1) for _ in range(33)]
        landmarks_identicos_2 = [(0.2, 0.4, -0.1) for _ in range(33)]

        similitud = self.service.calculate_position_similarity(landmarks_identicos_1, landmarks_identicos_2)
        self.assertAlmostEqual(similitud, 100.0, places=2)

    def test_calculate_position_similarity_different_positions(self) -> None:
        """Prueba 2 (RF-13): Dos esqueletos con discrepancias posicionales deben arrojar similitud significativamente menor."""
        landmarks_base = [(0.2, 0.4, 0.0) for _ in range(33)]
        landmarks_desplazados = [(0.5, 0.8, 0.2) for _ in range(33)]

        similitud = self.service.calculate_position_similarity(landmarks_base, landmarks_desplazados)
        self.assertLess(similitud, 90.0)
        self.assertGreaterEqual(similitud, 0.0)

    def test_csv_export_creation(self) -> None:
        """Prueba 3 (RF-14): Verifica la creación física de los 3 archivos CSV con sus encabezados estandarizados."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_id = "test_video_123"
            angle_records = [[0, 0, 90.0, 95.0], [1, 0, 92.0, 94.0]]
            pos_records = [[0, 0, 0.1, 0.2, 0.3, 0.1, 0.2, 0.3]]
            sim_records = [[0, 98.5, 95.0, 96.75], [1, 97.0, 94.5, 95.75]]

            rutas = self.service.export_csv_results(
                output_dir=tmp_dir,
                video_id=video_id,
                angle_records=angle_records,
                position_records=pos_records,
                frame_similarity_records=sim_records,
            )

            self.assertEqual(len(rutas), 3)
            for r in rutas:
                self.assertTrue(os.path.exists(r))

            # 1. Validar encabezados de ángulos
            with open(rutas[0], mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header_ang = next(reader)
                self.assertEqual(header_ang, ["frame", "keypoint_group", "angle_student", "angle_master"])

            # 2. Validar encabezados de posiciones
            with open(rutas[1], mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header_pos = next(reader)
                self.assertEqual(header_pos, ["frame", "point_idx", "x1", "y1", "z1", "x2", "y2", "z2"])

            # 3. Validar encabezados de similitud cuadro a cuadro
            with open(rutas[2], mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header_sim = next(reader)
                self.assertEqual(header_sim, [
                    "frame",
                    "angle_similarity_percentage",
                    "position_similarity_percentage",
                    "average_similarity",
                ])

    def test_chart_generation(self) -> None:
        """Prueba 4 (RF-15): Verifica la generación del gráfico PNG temporal con GridSpec en disco."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_id = "test_chart_456"
            angle_sim = [95.0, 94.0, 93.5, 96.0]
            pos_sim = [88.0, 89.0, 87.5, 90.0]
            avg_sim = [91.5, 91.5, 90.5, 93.0]

            chart_path = self.service.plot_similarity_graphs(
                output_dir=tmp_dir,
                video_id=video_id,
                angle_sim_list=angle_sim,
                pos_sim_list=pos_sim,
                avg_sim_list=avg_sim,
            )

            self.assertTrue(os.path.exists(chart_path))
            self.assertTrue(chart_path.endswith(f"skeleton_similarity_{video_id}.png"))
            # Verificar que el archivo generado tenga peso binario real (> 1 KB y < 500 KB / RP-02)
            tamano_bytes = os.path.getsize(chart_path)
            self.assertGreater(tamano_bytes, 1000)
            self.assertLess(tamano_bytes, 500_000)

    def test_combined_similarity_calculation(self) -> None:
        """Prueba 5: Valida el cálculo determinista de la métrica combinada promedio."""
        ang_sim = 90.0
        pos_sim = 80.0
        combinada = self.service.calculate_combined_similarity(ang_sim, pos_sim)
        self.assertEqual(combinada, 85.0)

        # Prueba de saturación en bordes
        self.assertEqual(self.service.calculate_combined_similarity(100.0, 100.0), 100.0)
        self.assertEqual(self.service.calculate_combined_similarity(0.0, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
