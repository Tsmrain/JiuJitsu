"""
Servicio de Dominio - LandmarkAdapter (Defensa Biomecánica)

Adaptador que transforma coordenadas 3D crudas (keypoints) del modelo
de pose estimation (RTMPose3D / COCO format) en ángulos biomecánicos
interpretables para el análisis de técnicas de Brazilian Jiu-Jitsu.

La fórmula del producto escalar implementada aquí fue defendida ante
el tribunal de grado:

    θ = arccos( (BA⃗ · BC⃗) / (‖BA⃗‖ · ‖BC⃗‖) )

Donde BA⃗ = A - B y BC⃗ = C - B.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np


# ──────────────────────────────────────────────
#  Índices COCO relevantes para BJJ
# ──────────────────────────────────────────────
# Ref: https://github.com/open-mmlab/mmpose (COCO-WholeBody)
COCO_HOMBRO_DER = 6
COCO_CODO_DER = 8
COCO_MUNECA_DER = 10
COCO_HOMBRO_IZQ = 5
COCO_CODO_IZQ = 7
COCO_MUNECA_IZQ = 9
COCO_CADERA_DER = 12
COCO_RODILLA_DER = 14
COCO_TOBILLO_DER = 16
COCO_CADERA_IZQ = 11
COCO_RODILLA_IZQ = 13
COCO_TOBILLO_IZQ = 15


class LandmarkAdapter:
    """
    Adaptador biomecánico que convierte coordenadas 3D de keypoints
    en ángulos articulares relevantes para el análisis de BJJ.

    Principio de diseño (Larman): Servicio de dominio puro. No depende
    de frameworks de visión artificial — solo recibe datos numéricos
    y retorna ángulos calculados.
    """

    # Mapeo de articulaciones BJJ a tripletas de índices COCO (A, B, C)
    # El ángulo se calcula en el punto B (vértice).
    ARTICULACIONES_BJJ: Dict[str, Tuple[int, int, int]] = {
        "codo_derecho": (COCO_HOMBRO_DER, COCO_CODO_DER, COCO_MUNECA_DER),
        "codo_izquierdo": (COCO_HOMBRO_IZQ, COCO_CODO_IZQ, COCO_MUNECA_IZQ),
        "rodilla_derecha": (COCO_CADERA_DER, COCO_RODILLA_DER, COCO_TOBILLO_DER),
        "rodilla_izquierda": (COCO_CADERA_IZQ, COCO_RODILLA_IZQ, COCO_TOBILLO_IZQ),
    }

    @staticmethod
    def calcular_angulo_3d(
        punto_a: Tuple[float, ...],
        punto_b: Tuple[float, ...],
        punto_c: Tuple[float, ...],
    ) -> float:
        """Calcula el ángulo en el vértice B formado por los puntos A-B-C.

        Implementa la fórmula del producto escalar:
            θ = arccos( (BA⃗ · BC⃗) / (‖BA⃗‖ · ‖BC⃗‖) )

        Args:
            punto_a: Coordenadas (x, y, z) del primer extremo.
            punto_b: Coordenadas (x, y, z) del vértice (donde se mide el ángulo).
            punto_c: Coordenadas (x, y, z) del segundo extremo.

        Returns:
            Ángulo en grados sexagesimales [0, 180].

        Raises:
            ValueError: Si alguno de los vectores BA o BC tiene magnitud cero
                        (puntos coincidentes).
        """
        a = np.array(punto_a, dtype=np.float64)
        b = np.array(punto_b, dtype=np.float64)
        c = np.array(punto_c, dtype=np.float64)

        # Vectores desde el vértice B hacia los extremos A y C
        vec_ba = a - b
        vec_bc = c - b

        # Magnitudes de los vectores
        norma_ba = np.linalg.norm(vec_ba)
        norma_bc = np.linalg.norm(vec_bc)

        if norma_ba < 1e-10 or norma_bc < 1e-10:
            raise ValueError(
                "No se puede calcular el ángulo: dos o más puntos son "
                "coincidentes (vector de magnitud ≈ 0)."
            )

        # Producto escalar normalizado
        coseno = np.dot(vec_ba, vec_bc) / (norma_ba * norma_bc)

        # Clamp para evitar errores numéricos de punto flotante
        # que lleven el coseno fuera de [-1, 1]
        coseno = np.clip(coseno, -1.0, 1.0)

        # Conversión a grados sexagesimales
        angulo_rad = math.acos(float(coseno))
        angulo_deg = math.degrees(angulo_rad)

        return angulo_deg

    def adaptar_keypoints_a_angulos(
        self,
        matriz_raw: List[Tuple[float, ...]],
    ) -> Dict[str, float]:
        """Extrae los ángulos articulares clave para BJJ de una matriz de keypoints.

        A partir de una lista de coordenadas 3D (formato COCO: 17+ keypoints),
        calcula los ángulos en las articulaciones relevantes para el análisis
        de técnicas de Jiu-Jitsu.

        Args:
            matriz_raw: Lista de tuplas (x, y, z) indexadas por keypoint COCO.
                        Debe contener al menos 17 keypoints.

        Returns:
            Diccionario {nombre_articulacion: ángulo_en_grados}.

        Raises:
            IndexError: Si la matriz no contiene suficientes keypoints.
        """
        angulos: Dict[str, float] = {}

        for nombre, (idx_a, idx_b, idx_c) in self.ARTICULACIONES_BJJ.items():
            punto_a = matriz_raw[idx_a]
            punto_b = matriz_raw[idx_b]
            punto_c = matriz_raw[idx_c]
            angulos[nombre] = self.calcular_angulo_3d(punto_a, punto_b, punto_c)

        return angulos
