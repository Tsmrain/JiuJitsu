"""Modelos de Dominio Puro para el Asistente de Visión Artificial BJJ.

Diseñado rigurosamente bajo las directrices de Craig Larman (Patrones GRASP:
Experto en Información, Fabricación Pura, Alta Cohesión y Bajo Acoplamiento)
y los fundamentos de modelado de datos de Mannino.

Este módulo no contiene dependencias de frameworks externos (sin FastAPI, Pydantic ni SQLAlchemy).
"""

from __future__ import annotations
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass(frozen=True)
class Punto3D:
    """Objeto de Valor (Value Object) que representa una coordenada espacial tridimensional.

    Aplica el patrón GRASP: Experto en Información para operaciones de álgebra
    vectorial euclidiana en el espacio R^3.
    """

    x: float
    y: float
    z: float

    def restar(self, otro: Punto3D) -> Punto3D:
        """Calcula la resta vectorial self - otro."""
        return Punto3D(
            x=self.x - otro.x,
            y=self.y - otro.y,
            z=self.z - otro.z,
        )

    def __sub__(self, otro: Punto3D) -> Punto3D:
        """Sobrecarga del operador de resta vectorial (-) para mayor expresividad."""
        return self.restar(otro)

    def producto_punto(self, otro: Punto3D) -> float:
        """Calcula el producto escalar (dot product) en R^3:

        u · v = u_x * v_x + u_y * v_y + u_z * v_z
        """
        return (self.x * otro.x) + (self.y * otro.y) + (self.z * otro.z)

    def magnitud(self) -> float:
        """Calcula la norma euclidiana ||v|| = sqrt(x^2 + y^2 + z^2)."""
        return math.sqrt(self.producto_punto(self))

    def norma(self) -> float:
        """Alias semántico de magnitud para compatibilidad matemática."""
        return self.magnitud()


# Nombres canónicos de los 17 puntos anatómicos del estándar COCO
PUNTOS_COCO = (
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
)


@dataclass
class MatrizEsqueletica:
    """Entidad de Dominio que modela la estructura postural esquelética tridimensional.

    Aplica el patrón GRASP: Experto en Información al custodiar los keypoints corporales
    y encapsular la lógica del cálculo angular interarticular en el espacio R^3.
    Soporta índices enteros (COCO IDs: 6=R-Shoulder, 8=R-Elbow, 10=R-Wrist, etc.) o nombres de cadena.
    """

    puntos: Dict[Any, Punto3D] = field(default_factory=dict)
    puntos_3d: Optional[Dict[Any, Punto3D]] = None

    def __post_init__(self) -> None:
        """Asegura la inicialización flexible vía `puntos` o `puntos_3d`."""
        if self.puntos_3d is not None and not self.puntos:
            self.puntos = dict(self.puntos_3d)
        elif self.puntos is None:
            self.puntos = {}
        else:
            self.puntos = dict(self.puntos)

    def agregar_punto(self, nombre: Any, punto: Punto3D) -> None:
        """Agrega o actualiza un punto anatómico en la matriz esquelética."""
        self.puntos[nombre] = punto

    def obtener_punto(self, nombre: Any) -> Punto3D:
        """Obtiene un punto anatómico por su identificador (int o str)."""
        if nombre in self.puntos:
            return self.puntos[nombre]
        if str(nombre) in self.puntos:
            return self.puntos[str(nombre)]
        try:
            int_key = int(nombre)
            if int_key in self.puntos:
                return self.puntos[int_key]
        except (ValueError, TypeError):
            pass
        raise KeyError(f"La articulación '{nombre}' no existe en la matriz esquelética.")

    def calcular_angulo(self, punto_a_key: Any, centro_key: Any, punto_c_key: Any) -> float:
        r"""Calcula el ángulo interarticular tridimensional \theta(t) en radianes.

        Fórmula matemática implementada:
            \vec{u} = A - B
            \vec{v} = C - B
            \theta(t) = \arccos\left( \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|} \right)

        Donde B (centro_key) es el vértice articular central.
        Para evitar fallos numéricos por imprecisión en punto flotante, el argumento
        del coseno se clampa estrictamente al intervalo [-1.0, 1.0].
        Si alguno de los segmentos tiene longitud cero (degenerado), retorna 0.0 rad.
        """
        punto_a = self.obtener_punto(punto_a_key)
        centro_b = self.obtener_punto(centro_key)
        punto_c = self.obtener_punto(punto_c_key)

        vec_u = punto_a.restar(centro_b)
        vec_v = punto_c.restar(centro_b)

        mag_u = vec_u.magnitud()
        mag_v = vec_v.magnitud()

        # Manejo de segmento degenerado (longitud cero)
        if math.isclose(mag_u, 0.0, abs_tol=1e-9) or math.isclose(mag_v, 0.0, abs_tol=1e-9):
            return 0.0

        # Producto escalar dividido por el producto de las magnitudes
        cos_theta = vec_u.producto_punto(vec_v) / (mag_u * mag_v)

        # Clamping numérico estricto para prevenir domain error en math.acos
        cos_theta_clamped = max(-1.0, min(1.0, cos_theta))

        return math.acos(cos_theta_clamped)


@dataclass(frozen=True)
class DesviacionArticular:
    """Objeto de Valor (Value Object / DTO de Dominio) que encapsula la discrepancia articular.

    Mantiene Alta Cohesión al encapsular la articulación evaluada y los ángulos contrastados.
    """

    nombre_articulacion: str
    angulo_esperado: float
    angulo_real: float
    desviacion_grados: float


# Tripletes articulares estándar para evaluación biomecánica en BJJ:
# (nombre_articulacion, punto_a, centro, punto_c)
ARTICULACIONES_BJJ_DEFECTO: Tuple[Tuple[str, str, str, str], ...] = (
    ("left_elbow", "left_shoulder", "left_elbow", "left_wrist"),
    ("right_elbow", "right_shoulder", "right_elbow", "right_wrist"),
    ("left_knee", "left_hip", "left_knee", "left_ankle"),
    ("right_knee", "right_hip", "right_knee", "right_ankle"),
    ("left_shoulder", "left_hip", "left_shoulder", "left_elbow"),
    ("right_shoulder", "right_hip", "right_shoulder", "right_elbow"),
    ("left_hip", "left_shoulder", "left_hip", "left_knee"),
    ("right_hip", "right_shoulder", "right_hip", "right_knee"),
)


class CalculadoraBiomecanica:
    """Clase de Servicio de Dominio (Patrón GRASP: Fabricación Pura / Pure Fabrication).

    No representa una entidad del mundo físico en el tatami, sino un artefacto de diseño
    creado para lograr Alta Cohesión y Bajo Acoplamiento, orquestando la comparación
    cinemática entre el esqueleto patrón y el del practicante.
    """

    def __init__(
        self,
        articulaciones: Optional[List[Tuple[Any, ...]]] = None,
    ) -> None:
        """Inicializa la calculadora con los tripletes articulares a monitorear."""
        self.articulaciones = articulaciones if articulaciones is not None else list(ARTICULACIONES_BJJ_DEFECTO)

    def evaluar_desviaciones(
        self,
        esqueleto_alumno: MatrizEsqueletica,
        esqueleto_patron: MatrizEsqueletica,
        articulaciones: Optional[List[Tuple[Any, ...]]] = None,
        umbral_tolerancia_grados: float = 0.0,
    ) -> List[DesviacionArticular]:
        """Evalúa las discrepancias angulares entre el esqueleto del alumno y el patrón.

        Acepta tuplas en formato:
            (punto_a, centro, punto_c, nombre_articulacion)
        o
            (nombre_articulacion, punto_a, centro, punto_c)
        """
        items_a_evaluar = articulaciones if articulaciones is not None else self.articulaciones
        desviaciones: List[DesviacionArticular] = []

        for item in items_a_evaluar:
            if len(item) == 4:
                # Si los tres primeros están en el esqueleto y el cuarto es un nombre descriptivo no presente en puntos
                es_formato_puntos_primero = (
                    (item[0] in esqueleto_patron.puntos or str(item[0]) in esqueleto_patron.puntos)
                    and (item[1] in esqueleto_patron.puntos or str(item[1]) in esqueleto_patron.puntos)
                    and (item[2] in esqueleto_patron.puntos or str(item[2]) in esqueleto_patron.puntos)
                    and (item[3] not in esqueleto_patron.puntos and str(item[3]) not in esqueleto_patron.puntos)
                )
                if es_formato_puntos_primero:
                    punto_a, centro, punto_c, nombre_art = item[0], item[1], item[2], item[3]
                else:
                    nombre_art, punto_a, centro, punto_c = item[0], item[1], item[2], item[3]
            else:
                continue

            try:
                ang_esperado_rad = esqueleto_patron.calcular_angulo(punto_a, centro, punto_c)
                ang_real_rad = esqueleto_alumno.calcular_angulo(punto_a, centro, punto_c)
            except KeyError:
                continue

            angulo_esperado_deg = math.degrees(ang_esperado_rad)
            angulo_real_deg = math.degrees(ang_real_rad)
            desviacion_grados = abs(angulo_esperado_deg - angulo_real_deg)

            condicion_umbral = (
                (umbral_tolerancia_grados == 0.0 and desviacion_grados > 1e-5)
                or (umbral_tolerancia_grados > 0.0 and desviacion_grados >= umbral_tolerancia_grados)
            )

            if condicion_umbral:
                desviaciones.append(
                    DesviacionArticular(
                        nombre_articulacion=str(nombre_art),
                        angulo_esperado=round(angulo_esperado_deg, 2),
                        angulo_real=round(angulo_real_deg, 2),
                        desviacion_grados=round(desviacion_grados, 2),
                    )
                )

        return desviaciones

    def evaluar(
        self,
        esqueleto_alumno: MatrizEsqueletica,
        esqueleto_patron: MatrizEsqueletica,
        umbral: float = 0.0,
    ) -> List[DesviacionArticular]:
        """Alias retrocompatible para evaluar según la lista por defecto configurada."""
        return self.evaluar_desviaciones(
            esqueleto_alumno=esqueleto_alumno,
            esqueleto_patron=esqueleto_patron,
            articulaciones=self.articulaciones,
            umbral_tolerancia_grados=umbral,
        )
