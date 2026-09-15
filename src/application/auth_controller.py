"""Controlador de Sesión (Session Facade) para la Autenticación.

Aplica el patrón GRASP de Controlador para delegar el hashing al dominio
y la persistencia a la infraestructura, manteniendo la capa de aplicación
libre de acoplamiento fuerte.
"""

import uuid
from typing import Optional, Dict, Any
from src.domain.models import Usuario
from src.domain.interfaces import IUsuarioRepository
from src.domain.security import hash_password, verify_password

class AuthController:
    """Session Facade (Larman) para orquestar registro y login."""

    def __init__(self, usuario_repo: IUsuarioRepository):
        self._usuario_repo = usuario_repo

    def registrar_usuario(self, email: str, nombre_completo: str, password: str, rol: str) -> Dict[str, Any]:
        # Validar si ya existe
        if self._usuario_repo.obtener_por_email(email):
            raise ValueError(f"El email '{email}' ya se encuentra registrado.")
        
        # Validar password mínimo
        if len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
            
        hashed = hash_password(password)
        id_usuario = f"usr_{uuid.uuid4().hex[:12]}"
        
        usuario = Usuario(
            id_usuario=id_usuario,
            email=email,
            nombre_completo=nombre_completo,
            rol=rol,
            password_hash=hashed
        )
        self._usuario_repo.guardar(usuario)
        
        return {
            "id_usuario": usuario.id_usuario,
            "email": usuario.email,
            "nombre_completo": usuario.nombre_completo,
            "rol": usuario.rol,
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        usuario = self._usuario_repo.obtener_por_email(email)
        if not usuario:
            raise ValueError("Credenciales inválidas (email no encontrado).")
            
        if not verify_password(password, usuario.password_hash):
            raise ValueError("Credenciales inválidas (contraseña incorrecta).")
            
        return {
            "id_usuario": usuario.id_usuario,
            "email": usuario.email,
            "nombre_completo": usuario.nombre_completo,
            "rol": usuario.rol,
        }

    def obtener_usuario(self, id_usuario: str) -> Optional[Dict[str, Any]]:
        usuario = self._usuario_repo.obtener_por_id(id_usuario)
        if not usuario:
            return None
        return {
            "id_usuario": usuario.id_usuario,
            "email": usuario.email,
            "nombre_completo": usuario.nombre_completo,
            "rol": usuario.rol,
        }
