# src/application/profesor_controller.py
"""Controlador de Aplicación / Fachada de Sesión para Profesores (Larman GRASP).

Orquesta el flujo: Validación de Entrada -> Repositorio -> Retorno DTO limpio.
No contiene SQL directo ni dependencias de frameworks web.
"""

import uuid
from typing import Any, Dict, List, Optional
from src.domain.interfaces import IProfesorRepository, ITecnicaRepository
from src.domain.models import Profesor


class ProfesorController:
    """Session Facade para la administración del maestro de Profesores."""

    def __init__(
        self,
        repository: IProfesorRepository,
        tecnica_repository: Optional[ITecnicaRepository] = None,
    ):
        self._repository = repository
        self._tecnica_repo = tecnica_repository

    def registrar(self, nombre: str, email: str, id_profesor: Optional[str] = None) -> str:
        """Registra un nuevo profesor validando unicidad de correo y retorna su ID."""
        clean_email = email.strip()
        # Validación de unicidad de correo electrónico (BCNF / Integridad)
        existentes = self._repository.listar_todos()
        for p in existentes:
            if p.email.lower() == clean_email.lower():
                raise ValueError(f"El email '{email}' ya se encuentra registrado.")

        pid = id_profesor or f"prof_{uuid.uuid4().hex[:8]}"
        profesor = Profesor(id_profesor=pid, nombre=nombre, email=clean_email)
        self._repository.guardar(profesor)
        return profesor.id_profesor

    def crear_profesor(self, id_profesor: str, nombre: str, email: str) -> Dict[str, Any]:
        """Crea y persiste un nuevo profesor retornando el DTO completo."""
        self.registrar(nombre=nombre, email=email, id_profesor=id_profesor)
        profesor = self._repository.obtener_por_id(id_profesor)
        return {
            "id_profesor": profesor.id_profesor,
            "nombre": profesor.nombre,
            "email": profesor.email,
            "fecha_registro": profesor.fecha_registro.isoformat() if profesor.fecha_registro else None,
        }

    def obtener_profesor(self, id_profesor: str) -> Optional[Dict[str, Any]]:
        """Recupera un profesor por identificador."""
        profesor = self._repository.obtener_por_id(id_profesor)
        if not profesor:
            return None
        return {
            "id_profesor": profesor.id_profesor,
            "nombre": profesor.nombre,
            "email": profesor.email,
            "fecha_registro": profesor.fecha_registro.isoformat() if profesor.fecha_registro else None,
        }

    def listar_profesores(self) -> List[Dict[str, Any]]:
        """Lista todos los profesores registrados ordenados alfabéticamente."""
        profesores = self._repository.listar_todos()
        return [
            {
                "id_profesor": p.id_profesor,
                "nombre": p.nombre,
                "email": p.email,
                "fecha_registro": p.fecha_registro.isoformat() if p.fecha_registro else None,
            }
            for p in profesores
        ]

    def eliminar(self, id_profesor: str) -> bool:
        """Elimina un profesor y propaga cascada a técnicas vinculadas (ON DELETE CASCADE)."""
        if self._tecnica_repo:
            if hasattr(self._tecnica_repo, "eliminar_por_instructor"):
                self._tecnica_repo.eliminar_por_instructor(id_profesor)
            else:
                tecnicas = self._tecnica_repo.listar_por_instructor(id_profesor)
                for t in tecnicas:
                    if hasattr(self._tecnica_repo, "eliminar"):
                        self._tecnica_repo.eliminar(t.id_tecnica)
        return self._repository.eliminar(id_profesor)

    def eliminar_profesor(self, id_profesor: str) -> bool:
        """Alias retrocompatible para eliminar."""
        return self.eliminar(id_profesor)
