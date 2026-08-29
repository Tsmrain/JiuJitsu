"""
Servicio de Métricas Cinemáticas Avanzadas de Similitud de Posición 3D y Ángulos (RF-13, RF-14, RF-15).
Calcula distancia euclidiana 3D para 33 landmarks, similitud coseno de 28 grupos articulares,
exporta reportes tabulares en CSV y genera visualizaciones temporales con Matplotlib GridSpec.
"""

import csv
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # Backend sin interfaz gráfica para ejecución serverless/headless
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np

# 28 grupos anatómicos clave de MediaPipe Pose (miembros superiores, manos, inferiores, pies y faciales)
GRUPOS_PUNTOS_CLAVE_28 = [
    (11, 13, 15),  # 1. Hombro Izq - Codo Izq - Muñeca Izq
    (12, 14, 16),  # 2. Hombro Der - Codo Der - Muñeca Der
    (13, 11, 23),  # 3. Codo Izq - Hombro Izq - Cadera Izq
    (14, 12, 24),  # 4. Codo Der - Hombro Der - Cadera Der
    (23, 25, 27),  # 5. Cadera Izq - Rodilla Izq - Tobillo Izq
    (24, 26, 28),  # 6. Cadera Der - Rodilla Der - Tobillo Der
    (11, 23, 25),  # 7. Hombro Izq - Cadera Izq - Rodilla Izq
    (12, 24, 26),  # 8. Hombro Der - Cadera Der - Rodilla Der
    (13, 15, 21),  # 9. Codo Izq - Muñeca Izq - Pulgar Izq
    (14, 16, 22),  # 10. Codo Der - Muñeca Der - Pulgar Der
    (19, 15, 17),  # 11. Mano/Índice Izq - Muñeca Izq - Meñique Izq
    (20, 16, 18),  # 12. Mano/Índice Der - Muñeca Der - Meñique Der
    (15, 17, 19),  # 13. Muñeca Izq - Meñique Izq - Índice Izq
    (16, 18, 20),  # 14. Muñeca Der - Meñique Der - Índice Der
    (15, 19, 17),  # 15. Muñeca Izq - Índice Izq - Meñique Izq
    (16, 20, 18),  # 16. Muñeca Der - Índice Der - Meñique Der
    (25, 27, 29),  # 17. Rodilla Izq - Tobillo Izq - Talón Izq
    (26, 28, 30),  # 18. Rodilla Der - Tobillo Der - Talón Der
    (27, 29, 31),  # 19. Tobillo Izq - Talón Izq - Dedo Pie Izq
    (28, 30, 32),  # 20. Tobillo Der - Talón Der - Dedo Pie Der
    (27, 31, 29),  # 21. Tobillo Izq - Dedo Pie Izq - Talón Izq
    (28, 32, 30),  # 22. Tobillo Der - Dedo Pie Der - Talón Der
    (7, 3, 2),     # 23. Oreja Izq - Ojo Ext Izq - Ojo Izq
    (8, 6, 5),     # 24. Oreja Der - Ojo Ext Der - Ojo Der
    (2, 1, 0),     # 25. Ojo Izq - Ojo Int Izq - Nariz
    (5, 4, 0),     # 26. Ojo Der - Ojo Int Der - Nariz
    (1, 0, 4),     # 27. Ojo Int Izq - Nariz - Ojo Int Der
    (10, 0, 9),    # 28. Boca Der - Nariz - Boca Izq
]


class PositionSimilarityService:
    """
    Servicio de cálculo de métricas cinemáticas y exportación analítica (Craig Larman / Pure Fabrication).
    Implementa la evaluación de similitud euclidiana 3D, similaridad coseno de ángulos y generación
    de entregables gráficos y CSV.
    """

    def __init__(self, key_points: Optional[List[Tuple[int, int, int]]] = None) -> None:
        self.key_points = key_points or GRUPOS_PUNTOS_CLAVE_28

    @staticmethod
    def _extraer_coords(lm: Any) -> Tuple[float, float, float]:
        """Extrae coordenadas (x, y, z) ya sea de tuplas/listas o de objetos MediaPipe Landmark."""
        if isinstance(lm, (tuple, list)):
            x = float(lm[0])
            y = float(lm[1])
            z = float(lm[2]) if len(lm) > 2 else 0.0
            return (x, y, z)
        return (float(getattr(lm, "x", 0.0)), float(getattr(lm, "y", 0.0)), float(getattr(lm, "z", 0.0)))

    def calculate_position_similarity(
        self,
        landmarks1: Sequence[Any],
        landmarks2: Sequence[Any],
    ) -> float:
        """
        Calcula la similitud de posición 3D usando la distancia Euclidiana para los 33 landmarks:
        dist = sqrt((x1 - x2)^2 + (y1 - y2)^2 + (z1 - z2)^2)
        Retorna porcentaje: (1 - avg_distance) * 100 acotado en [0.0, 100.0]
        """
        if not landmarks1 or not landmarks2:
            return 0.0

        n = min(len(landmarks1), len(landmarks2))
        if n == 0:
            return 0.0

        distances = []
        for i in range(n):
            c1 = self._extraer_coords(landmarks1[i])
            c2 = self._extraer_coords(landmarks2[i])

            dist = np.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2)
            distances.append(dist)

        avg_distance = float(np.mean(distances))
        similitud = (1.0 - avg_distance) * 100.0
        return float(np.clip(similitud, 0.0, 100.0))

    @staticmethod
    def calculate_angle_similarity_cosine(
        angles1: Sequence[float],
        angles2: Sequence[float],
    ) -> float:
        """
        Calcula la similitud coseno entre dos vectores de ángulos:
        cosine_sim = (a1 . a2) / (||a1|| * ||a2||) * 100
        """
        if not angles1 or not angles2:
            return 0.0

        a1 = np.array(angles1, dtype=np.float64)
        a2 = np.array(angles2, dtype=np.float64)

        norm_a1 = np.linalg.norm(a1)
        norm_a2 = np.linalg.norm(a2)

        if norm_a1 < 1e-6 and norm_a2 < 1e-6:
            return 100.0
        if norm_a1 < 1e-6 or norm_a2 < 1e-6:
            return 0.0

        cosine_sim = np.dot(a1, a2) / (norm_a1 * norm_a2)
        cosine_sim = np.clip(cosine_sim, -1.0, 1.0)
        return float(np.clip(cosine_sim * 100.0, 0.0, 100.0))

    @staticmethod
    def calculate_combined_similarity(angle_pct: float, pos_pct: float) -> float:
        """Calcula el promedio balanceado entre la similitud angular y la de posición 3D."""
        return float(np.clip((angle_pct + pos_pct) / 2.0, 0.0, 100.0))

    @staticmethod
    def calculate_angle_from_points(
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
    ) -> float:
        """Calcula el ángulo en el vértice p2 mediante arctan2."""
        radians = np.arctan2(p3[1] - p2[1], p3[0] - p2[0]) - np.arctan2(p1[1] - p2[1], p1[0] - p2[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360.0 - angle
        return float(angle)

    def extract_28_angles(self, landmarks: Sequence[Any]) -> List[float]:
        """Calcula los 28 ángulos clave para un conjunto de landmarks de un fotograma."""
        angles = []
        for (idx_a, idx_v, idx_c) in self.key_points:
            if idx_a < len(landmarks) and idx_v < len(landmarks) and idx_c < len(landmarks):
                c1 = self._extraer_coords(landmarks[idx_a])
                c2 = self._extraer_coords(landmarks[idx_v])
                c3 = self._extraer_coords(landmarks[idx_c])
                ang = self.calculate_angle_from_points((c1[0], c1[1]), (c2[0], c2[1]), (c3[0], c3[1]))
                angles.append(ang)
            else:
                angles.append(0.0)
        return angles

    def export_csv_results(
        self,
        output_dir: Union[str, Path],
        video_id: str,
        angle_records: List[List[Any]],
        position_records: List[List[Any]],
        frame_similarity_records: List[List[Any]],
    ) -> List[str]:
        """
        Exporta los tres archivos CSV analíticos por fotograma (RF-14):
        1. skeleton_angle_similarity_{video_id}.csv: [frame, keypoint_group, angle_student, angle_master]
        2. skeleton_position_similarity_{video_id}.csv: [frame, point_idx, x1, y1, z1, x2, y2, z2]
        3. skeleton_eachframe_similarity_{video_id}.csv: [frame, angle_sim_pct, pos_sim_pct, avg_sim_pct]
        """
        dir_path = Path(output_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        path_angles = dir_path / f"skeleton_angle_similarity_{video_id}.csv"
        path_positions = dir_path / f"skeleton_position_similarity_{video_id}.csv"
        path_similarity = dir_path / f"skeleton_eachframe_similarity_{video_id}.csv"

        # 1. CSV de ángulos articulares
        with open(path_angles, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["frame", "keypoint_group", "angle_student", "angle_master"])
            writer.writerows(angle_records)

        # 2. CSV de coordenadas de posición
        with open(path_positions, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["frame", "point_idx", "x1", "y1", "z1", "x2", "y2", "z2"])
            writer.writerows(position_records)

        # 3. CSV de similitud cuadro a cuadro
        with open(path_similarity, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "frame",
                "angle_similarity_percentage",
                "position_similarity_percentage",
                "average_similarity",
            ])
            writer.writerows(frame_similarity_records)

        return [str(path_angles), str(path_positions), str(path_similarity)]

    def plot_similarity_graphs(
        self,
        output_dir: Union[str, Path],
        video_id: str,
        angle_sim_list: List[float],
        pos_sim_list: List[float],
        avg_sim_list: List[float],
    ) -> str:
        """
        Genera un panel gráfico temporal de similitud con Matplotlib y GridSpec(2, 3) (RF-15):
        - Fila 1: 3 gráficos lineales (Ángulos en Azul, Posición en Verde, Promedio en Rojo Carmesí #D90429).
        - Fila 2: Tarjeta resumen con métricas estadísticas y número de grupos evaluados.
        """
        dir_path = Path(output_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        chart_path = dir_path / f"skeleton_similarity_{video_id}.png"

        fig = plt.figure(figsize=(12, 6), facecolor="#0E1117")
        gs = GridSpec(2, 3, height_ratios=[3, 1], figure=fig)

        # Configurar colores institucionales
        color_texto = "#F0F2F6"
        color_grid = "#282C34"
        frames = list(range(len(angle_sim_list))) if angle_sim_list else [0]

        # 1. Gráfico de Similitud de Ángulos (Azul)
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.set_facecolor("#161922")
        ax1.plot(frames, angle_sim_list, label="Similitud Ángulos", color="#1E88E5", linewidth=2.0)
        ax1.set_xlabel("Fotograma (Frame)", color=color_texto, fontsize=9)
        ax1.set_ylabel("Similitud (%)", color=color_texto, fontsize=9)
        ax1.set_title("Similitud de Ángulos (Coseno)", color="#FFFFFF", fontsize=11, fontweight="bold")
        ax1.set_ylim([0, 105])
        ax1.tick_params(colors=color_texto, labelsize=8)
        ax1.grid(True, linestyle="--", alpha=0.3, color=color_grid)
        ax1.legend(loc="lower right", fontsize=8, facecolor="#161922", edgecolor=color_grid, labelcolor=color_texto)

        # 2. Gráfico de Similitud de Posición 3D (Verde)
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.set_facecolor("#161922")
        ax2.plot(frames, pos_sim_list, label="Similitud Posición", color="#2E7D32", linewidth=2.0)
        ax2.set_xlabel("Fotograma (Frame)", color=color_texto, fontsize=9)
        ax2.set_ylabel("Similitud (%)", color=color_texto, fontsize=9)
        ax2.set_title("Similitud de Posición 3D", color="#FFFFFF", fontsize=11, fontweight="bold")
        ax2.set_ylim([0, 105])
        ax2.tick_params(colors=color_texto, labelsize=8)
        ax2.grid(True, linestyle="--", alpha=0.3, color=color_grid)
        ax2.legend(loc="lower right", fontsize=8, facecolor="#161922", edgecolor=color_grid, labelcolor=color_texto)

        # 3. Gráfico de Similitud Promedio Combinada (Rojo Carmesí Oficial #D90429)
        ax3 = fig.add_subplot(gs[0, 2])
        ax3.set_facecolor("#161922")
        ax3.plot(frames, avg_sim_list, label="Similitud Promedio", color="#D90429", linewidth=2.2)
        ax3.set_xlabel("Fotograma (Frame)", color=color_texto, fontsize=9)
        ax3.set_ylabel("Similitud (%)", color=color_texto, fontsize=9)
        ax3.set_title("Similitud Promedio Integral", color="#FFFFFF", fontsize=11, fontweight="bold")
        ax3.set_ylim([0, 105])
        ax3.tick_params(colors=color_texto, labelsize=8)
        ax3.grid(True, linestyle="--", alpha=0.3, color=color_grid)
        ax3.legend(loc="lower right", fontsize=8, facecolor="#161922", edgecolor=color_grid, labelcolor=color_texto)

        # 4. Fila inferior: Tarjeta resumen con métricas promedio
        ax_text = fig.add_subplot(gs[1, :])
        ax_text.set_facecolor("#14171E")
        ax_text.axis("off")

        media_ang = float(np.mean(angle_sim_list)) if angle_sim_list else 0.0
        media_pos = float(np.mean(pos_sim_list)) if pos_sim_list else 0.0
        media_tot = float(np.mean(avg_sim_list)) if avg_sim_list else 0.0

        resumen_texto = (
            f"Grupos Articulares Evaluados: {len(self.key_points)}  |  Total Fotogramas: {len(angle_sim_list)}\n"
            f"Similitud Angular Media: {media_ang:.2f}%   —   "
            f"Similitud Posicional 3D Media: {media_pos:.2f}%\n"
            f"COINCIDENCIA CINEMÁTICA GLOBAL PROMEDIO: {media_tot:.2f}%"
        )

        ax_text.text(
            0.5,
            0.5,
            resumen_texto,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="#FFFFFF",
            bbox={
                "facecolor": "#1A1518",
                "edgecolor": "#D90429",
                "boxstyle": "round,pad=0.8",
                "linewidth": 1.5,
            },
        )

        plt.tight_layout()
        plt.savefig(chart_path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)

        return str(chart_path)
