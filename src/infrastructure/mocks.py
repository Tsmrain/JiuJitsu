# src/infrastructure/mocks.py
"""Mocks y Repositorios en Memoria para Pruebas Unitarias Aisladas (<100ms).

Permite ejecutar pruebas del Proceso Unificado (Larman) sin requerir servicios externos,
base de datos PostgreSQL activa ni hardware GPU.
"""

import math
from typing import Dict, List, Optional
from src.domain.interfaces import (
    IInferenceEngine,
    IGenerationService,
    ITecnicaRepository,
    IProfesorRepository,
    IFuenteConocimientoRepository,
)
from src.domain.models import (
    MatrizEsqueletica,
    Punto3D,
    DesviacionArticular,
    Profesor,
    TecnicaPatron,
    FuenteConocimiento,
    ConfiguracionRAG,
)


class MockYOLOEngine(IInferenceEngine):
    """Simula la extracción de keypoints 3D de YOLO26x."""

    def __init__(self, desviacion_grados: float = 0.0):
        self._desviacion = desviacion_grados

    def inferir_esqueleto_3d(self, video_path: str) -> MatrizEsqueletica:
        rad = math.radians(90.0 + self._desviacion)
        puntos = {
            6: Punto3D(0.0, 0.0, 0.0),                             # Hombro dcho
            8: Punto3D(1.0, 0.0, 0.0),                             # Codo dcho
            10: Punto3D(1.0 + math.cos(rad), math.sin(rad), 0.0),  # Muñeca dcha
        }
        return MatrizEsqueletica(puntos_3d=puntos)


class MockGeminiService(IGenerationService):
    """Simula la respuesta pedagógica de Gemini 3.8 Flash."""

    def generar_consejo(
        self,
        tecnica: str,
        desviaciones: List[DesviacionArticular],
        contexto_manual: Optional[str] = None,
    ) -> str:
        if not desviaciones:
            return f"¡Excelente ejecución de {tecnica}! Mantienes la postura del patrón."

        falla = desviaciones[0]
        base_msg = (
            f"En {tecnica}, se detectó un desajuste en {falla.nombre_articulacion} "
            f"de {falla.desviacion_grados:.1f}°. Recuerda ajustar el ángulo."
        )
        if contexto_manual:
            return f"{base_msg} Contexto aplicado: {contexto_manual}"
        return base_msg


class MockTecnicaRepository(ITecnicaRepository):
    """Simula el repositorio con el patrón del maestro para compatibilidad legacy."""

    def __init__(self):
        self._tecnicas: Dict[str, TecnicaPatron] = {}

    def registrar_patron(self, tecnica: TecnicaPatron) -> bool:
        self._tecnicas[tecnica.id_tecnica] = tecnica
        return True

    def obtener_patron(self, id_tecnica: str) -> Optional[TecnicaPatron]:
        if id_tecnica in self._tecnicas:
            return self._tecnicas[id_tecnica]
        # Patrón por defecto para compatibilidad con pruebas preexistentes
        puntos_patron = {
            6: Punto3D(0.0, 0.0, 0.0),
            8: Punto3D(1.0, 0.0, 0.0),
            10: Punto3D(1.0, 1.0, 0.0),  # Codo a 90 grados exactos
        }
        return TecnicaPatron(
            id_tecnica=id_tecnica,
            id_profesor="inst_carlos",
            nombre=id_tecnica.replace("_", " ").title(),
            categoria="Sumisión",
            matriz_esqueletica=MatrizEsqueletica(puntos_3d=puntos_patron),
            video_url="/static/videos_patron/armbar_guardia.mp4",
        )

    def listar_por_instructor(self, id_profesor: str) -> List[TecnicaPatron]:
        return [t for t in self._tecnicas.values() if t.id_profesor == id_profesor]


class InMemoryTecnicaRepository(ITecnicaRepository):
    """Repositorio en memoria para pruebas unitarias de Técnicas Patrón (<10ms)."""

    def __init__(self):
        self._storage: Dict[str, TecnicaPatron] = {}

    def registrar_patron(self, tecnica: TecnicaPatron) -> bool:
        self._storage[tecnica.id_tecnica] = tecnica
        return True

    def obtener_patron(self, id_tecnica: str) -> Optional[TecnicaPatron]:
        return self._storage.get(id_tecnica)

    def listar_por_instructor(self, id_profesor: str) -> List[TecnicaPatron]:
        return [t for t in self._storage.values() if t.id_profesor == id_profesor]

    def eliminar(self, id_tecnica: str) -> bool:
        if id_tecnica in self._storage:
            del self._storage[id_tecnica]
            return True
        return False

    def eliminar_por_instructor(self, id_profesor: str) -> int:
        keys = [k for k, t in self._storage.items() if t.id_profesor == id_profesor]
        for k in keys:
            del self._storage[k]
        return len(keys)


class InMemoryProfesorRepository(IProfesorRepository):
    """Repositorio en memoria para pruebas unitarias de Profesores (<10ms)."""

    def __init__(self, tecnica_repository: Optional[InMemoryTecnicaRepository] = None):
        self._storage: Dict[str, Profesor] = {}
        self._tecnica_repo = tecnica_repository

    def guardar(self, profesor: Profesor) -> None:
        self._storage[profesor.id_profesor] = profesor

    def obtener_por_id(self, id_profesor: str) -> Optional[Profesor]:
        return self._storage.get(id_profesor)

    def listar_todos(self) -> List[Profesor]:
        return sorted(list(self._storage.values()), key=lambda p: p.nombre)

    def eliminar(self, id_profesor: str) -> bool:
        if id_profesor in self._storage:
            del self._storage[id_profesor]
            if self._tecnica_repo and hasattr(self._tecnica_repo, "eliminar_por_instructor"):
                self._tecnica_repo.eliminar_por_instructor(id_profesor)
            return True
        return False

    def actualizar(self, id_profesor: str, nombre: str, email: str) -> bool:
        if id_profesor not in self._storage:
            return False
        clean_email = email.strip().lower()
        for pid, p in self._storage.items():
            if pid != id_profesor and p.email.strip().lower() == clean_email:
                raise ValueError(f"El email '{email}' ya se encuentra registrado.")
        profesor_actual = self._storage[id_profesor]
        self._storage[id_profesor] = Profesor(
            id_profesor=id_profesor,
            nombre=nombre,
            email=email.strip(),
            fecha_registro=profesor_actual.fecha_registro,
        )
        return True


class InMemoryFuenteConocimientoRepository(IFuenteConocimientoRepository):
    """Repositorio en memoria para pruebas unitarias de Fuentes de Conocimiento RAG (<10ms)."""

    def __init__(self, config_rag: Optional[ConfiguracionRAG] = None):
        self._storage: Dict[str, FuenteConocimiento] = {}
        self._config = config_rag if config_rag is not None else ConfiguracionRAG()

    def indexar_documento(self, fuente: FuenteConocimiento) -> str:
        self._storage[fuente.id_fuente] = fuente
        return fuente.id_fuente

    def buscar_contexto(
        self,
        consulta_embedding: List[float],
        limite: Optional[int] = None,
        id_tecnica: Optional[str] = None,
    ) -> List[FuenteConocimiento]:
        if len(consulta_embedding) != 768:
            raise ValueError(f"Dimensión de embedding de búsqueda incorrecta: {len(consulta_embedding)} != 768")

        if isinstance(limite, str) and id_tecnica is None:
            id_tecnica = limite
            limite = None

        k = limite if (isinstance(limite, int) and limite > 0) else self._config.top_k_resultados

        candidatos = list(self._storage.values())
        if id_tecnica:
            candidatos = [f for f in candidatos if f.id_tecnica == id_tecnica]

        def calcular_similitud(f: FuenteConocimiento) -> float:
            if not f.embedding_vector or len(f.embedding_vector) != len(consulta_embedding):
                return 1.0
            norm_a = math.sqrt(sum(a * a for a in f.embedding_vector))
            norm_b = math.sqrt(sum(b * b for b in consulta_embedding))
            if norm_a == 0 or norm_b == 0:
                return 1.0
            dot = sum(a * b for a, b in zip(f.embedding_vector, consulta_embedding))
            return dot / (norm_a * norm_b)

        filtrados = [
            f for f in candidatos
            if calcular_similitud(f) >= self._config.umbral_similitud_minima
        ]
        filtrados.sort(key=calcular_similitud, reverse=True)
        return filtrados[:k]

    def listar_fuentes(self, id_tecnica: Optional[str] = None) -> List[FuenteConocimiento]:
        if id_tecnica:
            return [f for f in self._storage.values() if f.id_tecnica == id_tecnica]
        return list(self._storage.values())
