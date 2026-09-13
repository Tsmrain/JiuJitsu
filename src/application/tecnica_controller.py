# src/application/tecnica_controller.py
"""Controlador de Aplicación / Fachada de Sesión para Técnicas Patrón (Larman GRASP).

Orquesta el registro del patrón biomecánico validando la existencia del profesor
y la consistencia anatómica de la matriz esquelética mediante AdaptadorYOLO.
"""

import uuid
from typing import Any, Dict, List, Optional
from src.domain.interfaces import ITecnicaRepository, IProfesorRepository
from src.domain.models import TecnicaPatron, MatrizEsqueletica
from src.services.adapters import AdaptadorYOLO


class TecnicaController:
    """Session Facade para la gestión de Técnicas Patrón de BJJ."""

    def __init__(
        self,
        repository: ITecnicaRepository,
        profesor_repository: Optional[IProfesorRepository] = None,
        yolo_adapter: Optional[AdaptadorYOLO] = None,
    ):
        self._repository = repository
        self._profesor_repo = profesor_repository
        self._yolo = yolo_adapter if yolo_adapter is not None else AdaptadorYOLO()

    def registrar_patron(
        self,
        id_profesor: str,
        nombre: str,
        categoria: str = "General",
        matriz: Optional[MatrizEsqueletica] = None,
        matriz_esqueletica: Optional[MatrizEsqueletica] = None,
        id_tecnica: Optional[str] = None,
        video: Optional[str] = None,
        video_url: Optional[str] = None,
        desc: Optional[str] = None,
        descripcion: Optional[str] = None,
    ) -> str:
        """Registra un patrón validando matriz con YOLO y existencia del instructor, retornando id_tecnica."""
        matriz_final = matriz or matriz_esqueletica
        if matriz_final is None:
            raise ValueError("Se requiere una matriz esquelética válida para registrar el patrón.")

        if not self._yolo.validar_matriz_esqueletica(matriz_final):
            raise ValueError("Matriz esquelética inválida según contrato YOLO26x")

        if self._profesor_repo is not None:
            profesor = self._profesor_repo.obtener_por_id(id_profesor)
            if not profesor:
                raise ValueError(f"El profesor con id '{id_profesor}' no existe en el sistema.")

        tid = id_tecnica or f"tec_{uuid.uuid4().hex[:8]}"
        url_final = video or video_url
        desc_final = desc or descripcion

        tecnica = TecnicaPatron(
            id_tecnica=tid,
            id_profesor=id_profesor,
            nombre=nombre,
            categoria=categoria,
            matriz_esqueletica=matriz_final,
            video_url=url_final,
            descripcion=desc_final,
        )

        self._repository.registrar_patron(tecnica)
        return tecnica.id_tecnica

    def registrar_tecnica(
        self,
        id_tecnica: str,
        id_profesor: str,
        nombre: str,
        categoria: str,
        matriz_esqueletica: MatrizEsqueletica,
        video_url: Optional[str] = None,
        descripcion: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Registra una técnica y retorna su DTO completo."""
        self.registrar_patron(
            id_tecnica=id_tecnica,
            id_profesor=id_profesor,
            nombre=nombre,
            categoria=categoria,
            matriz_esqueletica=matriz_esqueletica,
            video_url=video_url,
            descripcion=descripcion,
        )
        tecnica = self._repository.obtener_patron(id_tecnica)
        puntos = tecnica.matriz_esqueletica.puntos_3d if getattr(tecnica.matriz_esqueletica, "puntos_3d", None) else tecnica.matriz_esqueletica.puntos
        return {
            "id_tecnica": tecnica.id_tecnica,
            "id_profesor": tecnica.id_profesor,
            "nombre": tecnica.nombre,
            "categoria": tecnica.categoria,
            "video_url": tecnica.video_url,
            "descripcion": tecnica.descripcion,
            "total_puntos": len(puntos),
        }

    def obtener_tecnica(self, id_tecnica: str) -> Optional[Dict[str, Any]]:
        """Obtiene el patrón de una técnica."""
        tecnica = self._repository.obtener_patron(id_tecnica)
        if not tecnica:
            return None
        puntos = tecnica.matriz_esqueletica.puntos_3d if getattr(tecnica.matriz_esqueletica, "puntos_3d", None) else tecnica.matriz_esqueletica.puntos
        return {
            "id_tecnica": tecnica.id_tecnica,
            "id_profesor": tecnica.id_profesor,
            "nombre": tecnica.nombre,
            "categoria": tecnica.categoria,
            "video_url": tecnica.video_url,
            "descripcion": tecnica.descripcion,
            "total_puntos": len(puntos),
        }

    def listar_por_instructor(self, id_profesor: str) -> List[Dict[str, Any]]:
        """Lista todas las técnicas registradas por un instructor determinado."""
        tecnicas = self._repository.listar_por_instructor(id_profesor)
        resultado = []
        for t in tecnicas:
            puntos = t.matriz_esqueletica.puntos_3d if getattr(t.matriz_esqueletica, "puntos_3d", None) else t.matriz_esqueletica.puntos
            resultado.append(
                {
                    "id_tecnica": t.id_tecnica,
                    "id_profesor": t.id_profesor,
                    "nombre": t.nombre,
                    "categoria": t.categoria,
                    "video_url": t.video_url,
                    "descripcion": t.descripcion,
                    "total_puntos": len(puntos),
                }
            )
        return resultado
