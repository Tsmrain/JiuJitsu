from datetime import datetime, timedelta, timezone
import os
import shutil
import logging
from typing import List, Optional, Union, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, EmailStr, field_validator
import urllib.request
import urllib.parse
import json
import re
import jwt as pyjwt

from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Autenticación y Sucursales"])

# Modelos Pydantic DTO
class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class SignupRequest(BaseModel):
    nombre_completo: str
    username: str
    password: str
    rol: str = "alumno" # Solo 'alumno' o 'profesor'
    sucursal_id: Optional[UUID] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("El nombre de usuario solo puede contener letras, números y guiones bajos (sin espacios ni caracteres especiales)")
        return v

class LoginResponse(BaseModel):
    token: str
    user_id: UUID
    nombre_completo: str
    username: str
    email: str
    rol: str
    avatar_url: Optional[str] = None
    sucursal_id: Optional[UUID] = None
    sucursal_nombre: str
    idioma_preferido: Optional[str] = "es"
    estado_suscripcion: Optional[str] = None
    fecha_expiracion: Optional[str] = None

class AlumnoPendienteResponse(BaseModel):
    id: UUID
    nombre_completo: str
    username: str
    email: str
    sucursal_id: Optional[UUID] = None
    sucursal_nombre: str
    avatar_url: Optional[str] = None
    fecha_registro: Optional[datetime] = None
    estado_suscripcion: str
    fecha_expiracion: Optional[datetime] = None

class ActivarPaseRequest(BaseModel):
    dias: Optional[int] = 30
    notas: Optional[str] = None

class ActivarPaseResponse(BaseModel):
    success: bool
    alumno_id: UUID
    nombre_completo: Optional[str] = None
    estado_suscripcion: str
    fecha_expiracion: Optional[datetime] = None
    profesor_id: UUID

class CambiarSucursalRequest(BaseModel):
    nueva_sucursal_id: UUID
    notas: Optional[str] = None

class CambiarSucursalResponse(BaseModel):
    success: bool
    user_id: UUID
    nombre_completo: str
    username: str
    sucursal_anterior_id: Optional[UUID] = None
    sucursal_nueva_id: UUID
    sucursal_nueva_nombre: str
    mensaje: str

class SucursalCreate(BaseModel):
    nombre: str
    pais: str
    ciudad: str
    direccion: Optional[str] = None
    latitud: float
    longitud: float

class SucursalResponse(BaseModel):
    id: UUID
    nombre: str
    pais: str
    ciudad: str
    direccion: Optional[str] = None
    latitud: float
    longitud: float

class ProfesorResponse(BaseModel):
    user_id: UUID
    nombre_completo: str
    username: str
    email: str
    avatar_url: Optional[str] = None
    sucursal_id: Optional[UUID] = None
    sucursal_nombre: str

class ParseGmapsRequest(BaseModel):
    url: str

class ParseGmapsResponse(BaseModel):
    nombre: Optional[str] = None
    pais: Optional[str] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    latitud: float
    longitud: float

class UserUpdateRequest(BaseModel):
    nombre_completo: Optional[str] = None
    password: Optional[str] = None
    avatar_url: Optional[str] = None
    idioma_preferido: Optional[str] = None

class IdiomaUpdateRequest(BaseModel):
    idioma: str


def get_db():
    return PostgrestClient()

def get_user_idioma(user_id: Union[str, UUID]) -> str:
    db = get_db()
    try:
        res = db.rpc("get_user_idioma", {"p_user_id": str(user_id)})
        if res and isinstance(res, str) and res.strip():
            return res.strip().lower()
    except Exception as e:
        logger.debug(f"Error getting user idioma: {e}")
    return "es"

def set_user_idioma(user_id: Union[str, UUID], idioma: str) -> str:
    db = get_db()
    clean_lang = idioma.strip().lower() if idioma else "es"
    if clean_lang not in ["es", "pt", "en"]:
        clean_lang = "es"
    try:
        res = db.rpc("set_user_idioma", {"p_user_id": str(user_id), "p_idioma": clean_lang})
        if res:
            return res.strip().lower()
    except Exception as e:
        logger.warning(f"Error setting user idioma: {e}")
    return clean_lang

def clean_fallback_summary(feedback: Optional[str]) -> str:
    if not feedback:
        return "Technique feedback"
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", feedback.strip())
    summary = sentences[0].strip() if sentences else feedback.strip()
    if "(" in summary and ")" not in summary[summary.rfind("("):]:
        summary = summary[:summary.rfind("(")].rstrip(" ,;:")
    words = summary.split()
    if len(words) > 8:
        summary = " ".join(words[:8]) + "..."
    return summary

def _decode_jwt(authorization: Optional[str]) -> dict:
    """
    Decodifica y verifica un JWT firmado (HS256).
    Lanza HTTPException 401 si falta el header, está malformado o expiró.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required."
        )

    token_str = authorization[7:].strip()

    try:
        payload = pyjwt.decode(
            token_str,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired."
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or signature."
        )

    if not payload.get("uid") or not payload.get("role"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incomplete token."
        )

    return payload


def require_admin(authorization: Optional[str]) -> dict:
    """Verifica JWT válido + rol admin."""
    payload = _decode_jwt(authorization)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required."
        )
    return payload


def require_staff(authorization: Optional[str]) -> dict:
    """Verifica JWT válido + rol admin o profesor."""
    payload = _decode_jwt(authorization)
    if payload.get("role") not in ["admin", "profesor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff privileges required (admin or professor)."
        )
    return payload


def require_auth(authorization: Optional[str]) -> dict:
    """Verifica JWT válido (cualquier rol)."""
    return _decode_jwt(authorization)


def check_student_subscription(user_id: Union[str, UUID]) -> dict:
    """
    Verifica si un usuario (especialmente alumno) cuenta con suscripción activa ('Pase de Tatami').
    - Administradores y profesores siempre están activos.
    - Alumnos deben tener estado_suscripcion == 'activo' y fecha_expiracion > NOW().
    """
    db = get_db()
    try:
        profile_list = db.rpc("get_user_profile", {"user_id": str(user_id)})
        profile = profile_list[0] if profile_list else None
    except Exception:
        profile = None

    if not profile:
        try:
            users = db.get("usuarios", {"id": f"eq.{user_id}"})
            profile = users[0] if users else None
        except Exception:
            profile = None

    if not profile:
        return {"estado_suscripcion": "inactivo", "activo": False}

    rol = profile.get("rol", "alumno")
    if rol in ("admin", "profesor"):
        return {"estado_suscripcion": "activo", "activo": True, "rol": rol}

    estado = profile.get("estado_suscripcion", "pendiente")
    expiracion = profile.get("fecha_expiracion")

    if estado != "activo":
        return {
            "estado_suscripcion": estado or "pendiente",
            "activo": False,
            "fecha_expiracion": expiracion,
            "rol": rol
        }

    if expiracion:
        try:
            if isinstance(expiracion, str):
                exp_dt = datetime.fromisoformat(expiracion.replace("Z", "+00:00"))
            else:
                exp_dt = expiracion
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp_dt:
                return {
                    "estado_suscripcion": "expirado",
                    "activo": False,
                    "fecha_expiracion": expiracion,
                    "rol": rol
                }
        except Exception as ex:
            pass

    return {
        "estado_suscripcion": "activo",
        "activo": True,
        "fecha_expiracion": expiracion,
        "rol": rol
    }


def require_active_subscription(authorization: Optional[str] = Header(None)) -> dict:
    """
    Candado de Seguridad (Iteración 4A):
    Verifica autenticación y que los alumnos tengan su Pase de Tatami activo.
    Lanza 403 Forbidden si la suscripción del alumno está pendiente o expirada.
    """
    caller = require_auth(authorization)
    role = caller.get("role")
    if role in ("admin", "profesor"):
        return caller

    sub_info = check_student_subscription(caller.get("uid"))
    if not sub_info.get("activo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Suscripción inactiva. Solicita tu Pase de Tatami al profesor."
        )
    return caller


def _sign_token(payload: dict) -> str:
    """
    Firma un payload con HS256 y fecha de expiración.
    El payload debe contener: uid, role, email, sucursal_id.
    """
    now = datetime.now(timezone.utc)
    to_encode = {
        **payload,
        "iat": now,
        "exp": now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    }
    return pyjwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

# Endpoints
@router.post("/auth/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(req: LoginRequest):
    """
    Endpoint de Autenticación por Nombre de Usuario / Email y Contraseña.
    Utiliza RPC de PostgREST para delegar la autenticación a PostgreSQL.
    """
    db = get_db()
    
    # 1. Llamar al RPC authenticate (SECURITY DEFINER en PostgreSQL — no expone la tabla usuarios a anon)
    try:
        token_resp = db.rpc("authenticate", {
            "email": req.username_or_email.strip().lower(),
            "password": req.password
        })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password."
        )

    # PostgREST puede devolver {"token": None} si el RPC retorna NULL (credenciales inválidas)
    if not token_resp or not token_resp.get("token"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password."
        )

    try:
        legacy_payload = json.loads(token_resp["token"])
    except (KeyError, json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password."
        )

    # Firmar JWT real
    signed_token = _sign_token({
        "uid": legacy_payload["uid"],
        "role": legacy_payload.get("role", "alumno"),
        "email": legacy_payload.get("email", ""),
        "sucursal_id": legacy_payload.get("sucursal_id", "")
    })

    # Obtener perfil
    try:
        profile_list = db.rpc("get_user_profile", {"user_id": legacy_payload["uid"]})
        profile = profile_list[0] if profile_list else None
    except Exception:
        profile = None

    idioma_actual = get_user_idioma(legacy_payload["uid"])

    raw_sub = profile.get("estado_suscripcion") if profile else None
    if not raw_sub:
        raw_sub = "activo" if legacy_payload.get("role") in ("admin", "profesor") else "pendiente"
    raw_exp = str(profile.get("fecha_expiracion")) if (profile and profile.get("fecha_expiracion")) else None

    if not profile:
        return LoginResponse(
            token=signed_token,
            user_id=UUID(legacy_payload["uid"]),
            nombre_completo=legacy_payload.get("email", "").split("@")[0].replace(".", " ").title(),
            username=legacy_payload.get("email", "").split("@")[0],
            email=legacy_payload.get("email", ""),
            rol=legacy_payload.get("role", "alumno"),
            avatar_url=None,
            sucursal_id=UUID(legacy_payload["sucursal_id"]) if legacy_payload.get("sucursal_id") else None,
            sucursal_nombre="Sucursal Principal",
            idioma_preferido=idioma_actual,
            estado_suscripcion=raw_sub,
            fecha_expiracion=raw_exp
        )

    sucursal_nombre = "Sucursal Eliminada"
    if profile.get("sucursal_id"):
        try:
            sucursales = db.get("sucursales", {"id": f"eq.{profile['sucursal_id']}"})
            if sucursales:
                sucursal_nombre = sucursales[0]["nombre"]
        except Exception:
            pass

    return LoginResponse(
        token=signed_token,
        user_id=UUID(profile["id"]),
        nombre_completo=profile["nombre_completo"],
        username=profile["username"],
        email=profile["email"],
        rol=profile["rol"],
        avatar_url=profile.get("avatar_url"),
        sucursal_id=UUID(profile["sucursal_id"]) if profile.get("sucursal_id") else None,
        sucursal_nombre=sucursal_nombre,
        idioma_preferido=idioma_actual,
        estado_suscripcion=raw_sub,
        fecha_expiracion=raw_exp
    )


@router.post("/auth/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest):
    """
    Registro público de cuentas para Alumnos y Profesores.
    El rol de Administrador está bloqueado desde el formulario público.
    Usa RPC SECURITY DEFINER: password se hashea en la BD, sin exponer la tabla.
    """
    db = get_db()
    rol_solicitado = req.rol.lower().strip()
    if rol_solicitado == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The Administrator role is exclusive and restricted for security."
        )

    if rol_solicitado not in ["alumno", "profesor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration role must be 'alumno' or 'profesor'."
        )

    usr_clean = req.username.strip().lower()
    usr_email = f"{usr_clean}@mock.com"

    # Validar sucursal (sucursales SÍ es legible por anon)
    sucursal = None
    if req.sucursal_id:
        sucursales = db.get("sucursales", {"id": f"eq.{req.sucursal_id}"})
        if sucursales:
            sucursal = sucursales[0]

    if not sucursal:
        all_sucursales = db.get("sucursales", {})
        if all_sucursales:
            sucursal = all_sucursales[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No academies registered in the system. Please create an academy first."
            )

    try:
        created_users = db.rpc("public_signup", {
            "p_nombre_completo": req.nombre_completo,
            "p_username": req.username.strip(),
            "p_email": usr_email,
            "p_password": req.password,
            "p_rol": rol_solicitado,
            "p_sucursal_id": sucursal["id"]
        })
    except Exception as e:
        err = str(e).lower()
        if "unique" in err or "duplicate" in err or "23505" in err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{req.username}' is already registered."
            )
        raise

    if not created_users:
        raise HTTPException(status_code=500, detail="Error creating user.")
    created_user = created_users[0] if isinstance(created_users, list) else created_users

    signed_token = _sign_token({
        "uid": str(created_user["id"]),
        "role": created_user["rol"],
        "email": created_user["email"],
        "sucursal_id": str(created_user["sucursal_id"])
    })

    return LoginResponse(
        token=signed_token,
        user_id=UUID(created_user["id"]),
        nombre_completo=created_user["nombre_completo"],
        username=created_user["username"],
        email=created_user["email"],
        rol=created_user["rol"],
        avatar_url=created_user.get("avatar_url"),
        sucursal_id=UUID(created_user["sucursal_id"]),
        sucursal_nombre=sucursal["nombre"],
        idioma_preferido="es",
        estado_suscripcion=created_user.get("estado_suscripcion", "pendiente" if created_user["rol"] == "alumno" else "activo"),
        fecha_expiracion=str(created_user.get("fecha_expiracion")) if created_user.get("fecha_expiracion") else None
    )

@router.get("/auth/usuarios", response_model=List[LoginResponse], status_code=status.HTTP_200_OK)
async def listar_usuarios(authorization: Optional[str] = Header(None)):
    """
    Lista todos los usuarios (para vista de administrador).
    Usa RPC SECURITY DEFINER para no exponer la tabla usuarios a anon.
    """
    require_admin(authorization)
    db = get_db()
    usuarios = db.rpc("admin_list_users", {})

    resultado = []
    for u in usuarios:
        resultado.append(LoginResponse(
            token="",
            user_id=UUID(u["id"]),
            nombre_completo=u["nombre_completo"],
            username=u["username"],
            email=u["email"],
            rol=u["rol"],
            avatar_url=u.get("avatar_url"),
            sucursal_id=UUID(u["sucursal_id"]) if u.get("sucursal_id") else None,
            sucursal_nombre=u.get("sucursal_nombre") or "Sucursal Eliminada",
            idioma_preferido=get_user_idioma(u["id"]),
            estado_suscripcion=u.get("estado_suscripcion") or ("activo" if u.get("rol") in ("admin", "profesor") else "pendiente"),
            fecha_expiracion=str(u.get("fecha_expiracion")) if u.get("fecha_expiracion") else None
        ))
    return resultado

@router.put("/auth/usuarios/{user_id}", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def update_usuario(user_id: UUID, req: UserUpdateRequest, authorization: Optional[str] = Header(None)):
    """
    Actualizar perfil de usuario (nombre, contraseña, foto base64).
    - Admin puede actualizar a cualquier usuario.
    - Usuario normal solo puede actualizarse a sí mismo.
    Usa RPC SECURITY DEFINER: password se hashea en la BD.
    Bajo ninguna circunstancia altera estado_suscripcion ni fecha_expiracion.
    """
    caller = require_auth(authorization)

    # Autorización: admin O el propio usuario
    caller_uid = caller.get("uid")
    caller_role = caller.get("role")
    if caller_role != "admin" and str(user_id) != str(caller_uid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this profile."
        )

    db = get_db()

    if req.idioma_preferido is not None:
        set_user_idioma(user_id, req.idioma_preferido)

    updated_list = db.rpc("admin_update_user", {
        "p_user_id": str(user_id),
        "p_nombre": req.nombre_completo,
        "p_password": req.password if (req.password and req.password.strip() != "") else None,
        "p_avatar_url": req.avatar_url
    })
    if not updated_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    updated = updated_list[0]
    idioma_actual = get_user_idioma(updated["id"])

    signed_token = _sign_token({
        "uid": str(updated["id"]),
        "role": updated["rol"],
        "email": updated["email"],
        "sucursal_id": str(updated["sucursal_id"]) if updated.get("sucursal_id") else ""
    })

    sub_status = updated.get("estado_suscripcion")
    if not sub_status:
        sub_status = "activo" if updated.get("rol") in ("admin", "profesor") else "pendiente"
    exp_status = str(updated.get("fecha_expiracion")) if updated.get("fecha_expiracion") else None

    return LoginResponse(
        token=signed_token,
        user_id=UUID(updated["id"]),
        nombre_completo=updated["nombre_completo"],
        username=updated["username"],
        email=updated["email"],
        rol=updated["rol"],
        avatar_url=updated.get("avatar_url"),
        sucursal_id=UUID(updated["sucursal_id"]) if updated.get("sucursal_id") else None,
        sucursal_nombre=updated.get("sucursal_nombre") or "Sucursal Eliminada",
        idioma_preferido=idioma_actual,
        estado_suscripcion=sub_status,
        fecha_expiracion=exp_status
    )

@router.put("/auth/usuarios/{user_id}/idioma", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def actualizar_idioma_usuario(
    user_id: UUID,
    req: IdiomaUpdateRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Actualiza la preferencia de idioma del usuario ('es', 'pt', 'en').
    Cualquier usuario autenticado puede cambiar su propio idioma, o admin a cualquiera.
    """
    caller = require_auth(authorization)
    caller_uid = caller.get("uid")
    caller_role = caller.get("role")
    if caller_role != "admin" and str(user_id) != str(caller_uid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this preference."
        )

    clean_lang = req.idioma.lower().strip()
    if clean_lang not in ["es", "pt", "en"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idioma no soportado. Valores permitidos: 'es', 'pt', 'en'."
        )

    res = set_user_idioma(user_id, clean_lang)
    return {"user_id": str(user_id), "idioma_preferido": res}

@router.put("/auth/usuarios/{user_id}/cambiar-sucursal", response_model=CambiarSucursalResponse, status_code=status.HTTP_200_OK)
async def cambiar_sucursal_usuario(
    user_id: UUID,
    req: CambiarSucursalRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Permite a un Administrador o Profesor reasignar la sucursal activa de un alumno.
    Integridad Referencial: Las evaluaciones previas conservan la sucursal donde se realizaron.
    """
    caller = require_staff(authorization)
    db = get_db()
    try:
        res = db.rpc("admin_cambiar_sucursal_usuario", {
            "p_user_id": str(user_id),
            "p_nueva_sucursal_id": str(req.nueva_sucursal_id)
        })
    except Exception as e:
        logger.error(f"Error cambiando sucursal: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    if not res:
        raise HTTPException(status_code=404, detail="Usuario o sucursal no encontrados.")

    data = res[0]
    return CambiarSucursalResponse(
        success=True,
        user_id=UUID(data["id"]),
        nombre_completo=data["nombre_completo"],
        username=data["username"],
        sucursal_anterior_id=UUID(data["sucursal_anterior_id"]) if data.get("sucursal_anterior_id") else None,
        sucursal_nueva_id=UUID(data["sucursal_nueva_id"]),
        sucursal_nueva_nombre=data["sucursal_nueva_nombre"],
        mensaje="Sucursal actualizada exitosamente. Historial de evaluaciones previas preservado intacto."
    )

@router.get("/auth/me", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def get_mi_perfil(authorization: Optional[str] = Header(None)):
    """Retorna el perfil completo del usuario autenticado actual, incluyendo su idioma_preferido."""
    caller = require_auth(authorization)
    raw_token = ""
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split("Bearer ", 1)[1].strip()
    elif authorization:
        raw_token = authorization.strip()

    uid = caller.get("uid")
    db = get_db()
    try:
        profile_list = db.rpc("get_user_profile", {"user_id": str(uid)})
        profile = profile_list[0] if profile_list else None
    except Exception:
        profile = None

    idioma = get_user_idioma(uid)

    raw_sub = profile.get("estado_suscripcion") if profile else None
    if not raw_sub:
        raw_sub = "activo" if caller.get("role") in ("admin", "profesor") else "pendiente"
    raw_exp = str(profile.get("fecha_expiracion")) if (profile and profile.get("fecha_expiracion")) else None

    if not profile:
        return LoginResponse(
            token=raw_token,
            user_id=UUID(uid),
            nombre_completo=caller.get("email", "").split("@")[0].replace(".", " ").title(),
            username=caller.get("email", "").split("@")[0],
            email=caller.get("email", ""),
            rol=caller.get("role", "alumno"),
            avatar_url=None,
            sucursal_id=UUID(caller["sucursal_id"]) if caller.get("sucursal_id") else None,
            sucursal_nombre="Sucursal Principal",
            idioma_preferido=idioma,
            estado_suscripcion=raw_sub,
            fecha_expiracion=raw_exp
        )

    sucursal_nombre = "Sucursal Eliminada"
    if profile.get("sucursal_id"):
        try:
            sucursales = db.get("sucursales", {"id": f"eq.{profile['sucursal_id']}"})
            if sucursales:
                sucursal_nombre = sucursales[0]["nombre"]
        except Exception:
            pass

    return LoginResponse(
        token=raw_token,
        user_id=UUID(profile["id"]),
        nombre_completo=profile["nombre_completo"],
        username=profile["username"],
        email=profile["email"],
        rol=profile["rol"],
        avatar_url=profile.get("avatar_url"),
        sucursal_id=UUID(profile["sucursal_id"]) if profile.get("sucursal_id") else None,
        sucursal_nombre=sucursal_nombre,
        idioma_preferido=idioma,
        estado_suscripcion=raw_sub,
        fecha_expiracion=raw_exp
    )

@router.post("/auth/impersonate/{user_id}", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def impersonate_user(user_id: UUID, authorization: Optional[str] = Header(None)):
    """
    Permite a un administrador tomar la sesión de cualquier usuario por ID sin contraseña.
    """
    require_admin(authorization)
    db = get_db()
    users = db.rpc("admin_get_user_full", {"p_user_id": str(user_id)})
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user = users[0]
    signed_token = _sign_token({
        "uid": str(user["id"]),
        "role": user["rol"],
        "email": user["email"],
        "sucursal_id": str(user["sucursal_id"]) if user.get("sucursal_id") else ""
    })
    idioma = get_user_idioma(user["id"])
    raw_sub = user.get("estado_suscripcion") or ("activo" if user.get("rol") in ("admin", "profesor") else "pendiente")
    raw_exp = str(user.get("fecha_expiracion")) if user.get("fecha_expiracion") else None

    return LoginResponse(
        token=signed_token,
        user_id=UUID(user["id"]),
        nombre_completo=user["nombre_completo"],
        username=user["username"],
        email=user["email"],
        rol=user["rol"],
        avatar_url=user.get("avatar_url"),
        sucursal_id=UUID(user["sucursal_id"]) if user.get("sucursal_id") else None,
        sucursal_nombre=user.get("sucursal_nombre") or "Sucursal Eliminada",
        idioma_preferido=idioma,
        estado_suscripcion=raw_sub,
        fecha_expiracion=raw_exp
    )


@router.delete("/auth/usuarios/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(
    user_id: UUID,
    reasignar_a: Optional[UUID] = None,
    auto_reasignar: bool = False,
    authorization: Optional[str] = Header(None),
):
    """
    Elimina un usuario del sistema (solo Admin).
    - Impide auto-eliminación del administrador en sesión.
    - Si es profesor con videos/patrones/teoría asociados, exige reasignación
      (`reasignar_a` o `auto_reasignar=true` para reasignar al administrador).
    - Si es alumno, Postgres ejecuta limpieza en cascada de evaluaciones y pases.
    """
    caller = require_admin(authorization)
    caller_uid = str(caller.get("uid") or "")
    if str(user_id) == caller_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta de administrador.",
        )

    target_reassign = reasignar_a
    if target_reassign is None and auto_reasignar and caller_uid:
        target_reassign = UUID(caller_uid)

    db = get_db()
    rows = db.rpc(
        "admin_delete_user",
        {
            "p_user_id": str(user_id),
            "p_caller_id": caller_uid or None,
            "p_reasignar_a": str(target_reassign) if target_reassign else None,
        },
    )
    result = rows[0] if isinstance(rows, list) and rows else (rows if isinstance(rows, dict) else {})
    if not result:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error eliminando usuario.")

    reason = result.get("reason")
    if reason == "NOT_FOUND":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if reason == "SELF_DELETE_FORBIDDEN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta de administrador.",
        )
    if reason == "PROFESOR_HAS_CONTENT":
        refs = result.get("reassigned_count") or 0
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El profesor tiene {refs} recursos asociados (videos, patrones o teoría). "
                "Reasígnalos a otro usuario antes de eliminar (auto_reasignar=true)."
            ),
        )
    if not result.get("deleted"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not delete user.")
    return None

@router.get("/sucursales", response_model=List[SucursalResponse], status_code=status.HTTP_200_OK)
async def listar_sucursales():
    """
    Lista todas las sucursales globales registradas con sus coordenadas geográficas.
    """
    db = get_db()
    sucursales = db.get("sucursales")
    return [SucursalResponse(id=UUID(s["id"]), **{k:v for k,v in s.items() if k != "id"}) for s in sucursales]

@router.get("/profesores", response_model=List[ProfesorResponse], status_code=status.HTTP_200_OK)
async def listar_profesores(sucursal_id: Optional[UUID] = None):
    """
    Lista los profesores registrados, opcionalmente filtrados por sucursal.
    Usa RPC SECURITY DEFINER para no exponer la tabla usuarios a anon.
    """
    db = get_db()
    params = {}
    if sucursal_id:
        params["p_sucursal_id"] = str(sucursal_id)
    profesores = db.rpc("admin_list_profesores", params)

    resultado = []
    for p in profesores:
        resultado.append(ProfesorResponse(
            user_id=UUID(p["id"]),
            nombre_completo=p["nombre_completo"],
            username=p["username"],
            email=p["email"],
            avatar_url=p.get("avatar_url"),
            sucursal_id=UUID(p["sucursal_id"]) if p.get("sucursal_id") else None,
            sucursal_nombre=p.get("sucursal_nombre") or "Sucursal Eliminada"
        ))

    return resultado

@router.get("/auth/alumnos", response_model=List[LoginResponse], status_code=status.HTTP_200_OK)
async def listar_alumnos(
    p_sucursal_id: Optional[UUID] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Lista alumnos (para panel del profesor).
    - Profesor: solo ve alumnos de su propia sucursal.
    - Admin: ve todos.
    """
    caller = require_auth(authorization)

    # Si es profesor, forzar su propia sucursal
    if caller.get("role") == "profesor":
        caller_sucursal = caller.get("sucursal_id")
        if not caller_sucursal:
            return []
        p_sucursal_id = UUID(caller_sucursal)
    elif caller.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor or administrator privileges required."
        )

    db = get_db()
    params = {}
    if p_sucursal_id:
        params["p_sucursal_id"] = str(p_sucursal_id)

    try:
        alumnos = db.rpc("admin_list_alumnos", params)
    except Exception:
        alumnos = []

    resultado = []
    for a in alumnos:
        resultado.append(LoginResponse(
            token="",
            user_id=UUID(a["id"]),
            nombre_completo=a["nombre_completo"],
            username=a["username"],
            email=a["email"],
            rol="alumno",
            avatar_url=a.get("avatar_url"),
            sucursal_id=UUID(a["sucursal_id"]) if a.get("sucursal_id") else None,
            sucursal_nombre=a.get("sucursal_nombre") or "Sucursal Eliminada"
        ))
    return resultado


@router.get("/auth/alumnos/pendientes", response_model=List[AlumnoPendienteResponse], status_code=status.HTTP_200_OK)
async def listar_alumnos_pendientes(
    authorization: Optional[str] = Header(None)
):
    """
    Devuelve la lista de alumnos con estado_suscripcion = 'pendiente' o expirados
    que pertenezcan a la misma sucursal del profesor (o todas si es admin).
    """
    caller = require_staff(authorization)
    db = get_db()
    profesor_id = caller.get("uid")

    try:
        pendientes = db.rpc("get_alumnos_pendientes", {"p_profesor_id": str(profesor_id)})
    except Exception as e:
        logger.error(f"Error calling get_alumnos_pendientes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar alumnos pendientes: {str(e)}"
        )

    resultado = []
    for p in pendientes:
        resultado.append(AlumnoPendienteResponse(
            id=UUID(p["id"]),
            nombre_completo=p.get("nombre_completo", ""),
            username=p.get("username", ""),
            email=p.get("email", ""),
            sucursal_id=UUID(p["sucursal_id"]) if p.get("sucursal_id") else None,
            sucursal_nombre=p.get("sucursal_nombre") or "Sucursal Principal",
            avatar_url=p.get("avatar_url"),
            fecha_registro=p.get("fecha_registro"),
            estado_suscripcion=p.get("estado_suscripcion", "pendiente"),
            fecha_expiracion=p.get("fecha_expiracion")
        ))
    return resultado


@router.post("/auth/alumnos/{alumno_id}/activar", response_model=ActivarPaseResponse, status_code=status.HTTP_200_OK)
@router.post("/alumnos/{alumno_id}/activar", response_model=ActivarPaseResponse, status_code=status.HTTP_200_OK)
async def activar_pase_tatami(
    alumno_id: UUID,
    req: Optional[ActivarPaseRequest] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Activa el 'Pase de Tatami' por 30 días para un alumno tras verificación de pago en tatami.
    Solo accesible por profesores de la misma sucursal o administradores.
    """
    caller = require_staff(authorization)
    db = get_db()
    profesor_id = caller.get("uid")
    dias = req.dias if req and req.dias else 30

    try:
        res = db.rpc("activar_pase_alumno", {
            "p_alumno_id": str(alumno_id),
            "p_profesor_id": str(profesor_id),
            "p_dias": dias
        })
        if isinstance(res, str):
            res = json.loads(res)
        logger.info(f"[AUDITORIA] Pase de Tatami activado para alumno {alumno_id} por {caller.get('email')} ({profesor_id}) por {dias} días.")
        return ActivarPaseResponse(
            success=True,
            alumno_id=alumno_id,
            nombre_completo=res.get("nombre_completo"),
            estado_suscripcion=res.get("estado_suscripcion", "activo"),
            fecha_expiracion=res.get("fecha_expiracion"),
            profesor_id=UUID(profesor_id)
        )
    except Exception as e:
        logger.error(f"Error activando pase de alumno: {e}")
        err_msg = str(e)
        if "El profesor solo puede activar alumnos de su propia sucursal" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only activate students from your own branch/academy."
            )
        if "Alumno no encontrado" in err_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not activate pass: {e}"
        )

@router.get("/auth/alumnos/{alumno_id}/evaluaciones", status_code=status.HTTP_200_OK)
async def listar_evaluaciones_alumno(
    alumno_id: UUID,
    authorization: Optional[str] = Header(None)
):
    """
    Lista hasta 50 evaluaciones para el historial propio o el panel del profesor.
    - Profesor: solo puede ver alumnos de su sucursal.
    - Admin: cualquier alumno.
    """
    caller = require_auth(authorization)

    db = get_db()

    es_propio_alumno = caller.get("role") == "alumno" and str(caller.get("uid")) == str(alumno_id)

    # El alumno puede consultar su propio historial; el personal conserva el acceso actual.
    if caller.get("role") == "profesor":
        caller_sucursal = caller.get("sucursal_id")
        if not caller_sucursal:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token missing academy.")

        alumno = db.rpc("admin_get_user_full", {"p_user_id": str(alumno_id)})
        if not alumno:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")
        if str(alumno[0].get("sucursal_id")) != str(caller_sucursal):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot view students from another academy."
            )
    elif caller.get("role") != "admin" and not es_propio_alumno:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor or administrator privileges required."
        )

    try:
        evaluaciones = db.rpc("admin_list_evaluaciones_alumno", {"p_alumno_id": str(alumno_id)})
    except Exception:
        evaluaciones = []

    for evaluacion in evaluaciones or []:
        if not evaluacion.get("feedback_summary"):
            evaluacion["feedback_summary"] = clean_fallback_summary(evaluacion.get("feedback_gemini_es") or evaluacion.get("feedback_gemini_pt"))

        # Recuperar metadata del timestamp del error y articulaciones si existe
        eval_id_str = str(evaluacion.get("id"))
        meta_file = f"/tmp/corpocmente_frames/meta_{eval_id_str}.json"
        evaluacion["articulaciones_criticas"] = evaluacion.get("articulaciones_criticas") or []
        evaluacion["nombres_articulaciones_criticas"] = evaluacion.get("nombres_articulaciones_criticas") or []

        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as mf:
                    meta_json = json.load(mf)
                    evaluacion["timestamp_error_segundos"] = meta_json.get("timestamp_error_segundos", 0.0)
                    if not evaluacion["articulaciones_criticas"]:
                        evaluacion["articulaciones_criticas"] = meta_json.get("articulaciones_criticas", [])
                    if not evaluacion["nombres_articulaciones_criticas"]:
                        evaluacion["nombres_articulaciones_criticas"] = meta_json.get("nombres_articulaciones_criticas", [])
            except Exception:
                evaluacion["timestamp_error_segundos"] = 0.0
        else:
            evaluacion["timestamp_error_segundos"] = evaluacion.get("timestamp_error_segundos", 0.0)

        user_idioma = get_user_idioma(alumno_id)
        from corpocmente.infrastructure.ai.adapters import obtener_nombres_articulaciones
        joints_source = evaluacion["nombres_articulaciones_criticas"] or evaluacion["articulaciones_criticas"] or []
        evaluacion["nombres_articulaciones_criticas"] = obtener_nombres_articulaciones(joints_source, idioma=user_idioma)

        critico_frame = f"/tmp/corpocmente_frames/critico_{eval_id_str}.jpg"
        if os.path.exists(critico_frame):
            evaluacion["frame_error_url"] = f"/static/frames/critico_{eval_id_str}.jpg"
        else:
            evaluacion["frame_error_url"] = None

        from corpocmente.infrastructure.persistence.video_storage import resolver_video_estatico

        evaluacion["url_video_alumno"] = resolver_video_estatico(
            evaluacion.get("url_video_alumno"),
            es_referencia=False,
        )
        evaluacion["video_referencia_url"] = resolver_video_estatico(
            evaluacion.get("video_referencia_url"),
            es_referencia=True,
            tecnica_id=evaluacion.get("tecnica_id"),
            tecnica_nombre=evaluacion.get("tecnica_nombre"),
            db=db,
        )
    return evaluaciones or []

@router.post("/sucursales", response_model=SucursalResponse, status_code=status.HTTP_201_CREATED)
async def crear_sucursal(nueva: SucursalCreate, authorization: Optional[str] = Header(None)):
    """
    Permite al Administrador registrar una nueva sucursal marcando la latitud y longitud.
    Usa RPC SECURITY DEFINER (anon no tiene INSERT en sucursales).
    """
    require_admin(authorization)
    db = get_db()
    created = db.rpc("admin_create_sucursal", {
        "p_nombre": nueva.nombre,
        "p_pais": nueva.pais,
        "p_ciudad": nueva.ciudad,
        "p_direccion": nueva.direccion,
        "p_latitud": float(nueva.latitud),
        "p_longitud": float(nueva.longitud)
    })
    if not created:
        raise HTTPException(status_code=500, detail="Error creating academy.")
    c = created[0] if isinstance(created, list) else created
    return SucursalResponse(id=UUID(c["id"]), **{k:v for k,v in c.items() if k != "id"})

@router.put("/sucursales/{sucursal_id}", response_model=SucursalResponse, status_code=status.HTTP_200_OK)
async def actualizar_sucursal(sucursal_id: UUID, req: SucursalCreate, authorization: Optional[str] = Header(None)):
    """
    Permite al Administrador modificar los datos o coordenadas de una sucursal existente.
    Usa RPC SECURITY DEFINER (anon no tiene UPDATE en sucursales).
    """
    require_admin(authorization)
    db = get_db()
    updated = db.rpc("admin_update_sucursal", {
        "p_sucursal_id": str(sucursal_id),
        "p_nombre": req.nombre,
        "p_pais": req.pais,
        "p_ciudad": req.ciudad,
        "p_direccion": req.direccion,
        "p_latitud": float(req.latitud),
        "p_longitud": float(req.longitud)
    })
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academy not found."
        )
    c = updated[0]
    return SucursalResponse(id=UUID(c["id"]), **{k:v for k,v in c.items() if k != "id"})

@router.delete("/sucursales/{sucursal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sucursal(sucursal_id: UUID, authorization: Optional[str] = Header(None)):
    """
    Permite al Administrador eliminar una sucursal del sistema.
    Usa RPC SECURITY DEFINER que valida internamente si tiene usuarios vinculados.
    """
    require_admin(authorization)
    db = get_db()
    try:
        deleted_ok = db.rpc("admin_delete_sucursal", {"p_sucursal_id": str(sucursal_id)})
    except Exception as e:
        resp_text = getattr(getattr(e, "response", None), "text", "")
        err = f"{str(e)} {resp_text}".lower()
        if "sucursal_con_usuarios" in err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete academy with linked users. Reassign or delete users first."
            )
        raise

    if not deleted_ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academy not found."
        )
    return None

@router.post("/sucursales/parse-gmaps-link", response_model=ParseGmapsResponse, status_code=status.HTTP_200_OK)
async def parse_gmaps_link(req: ParseGmapsRequest, authorization: Optional[str] = Header(None)):
    """
    Servicio backend de scraping y geocodificación para enlaces de Google Maps.
    Requiere autenticación de staff (Admin o Profesor) para mitigar riesgos de SSRF.
    """
    require_staff(authorization)
    url_input = req.url.strip()

    try:
        http_req = urllib.request.Request(
            url_input,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        with urllib.request.urlopen(http_req) as resp:
            final_url = resp.geturl()
    except Exception:
        final_url = url_input

    pin_matches = re.findall(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", final_url)
    if pin_matches:
        lat, lng = float(pin_matches[-1][0]), float(pin_matches[-1][1])
    else:
        query_match = re.search(r"(?:q|query|ll)=(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if query_match:
            lat, lng = float(query_match.group(1)), float(query_match.group(2))
        else:
            at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
            if at_match:
                lat, lng = float(at_match.group(1)), float(at_match.group(2))
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid coordinates found in the provided link."
                )

    place_name = None
    place_match = re.search(r"\/place\/([^\/@]+)", final_url)
    if place_match:
        raw_name = urllib.parse.unquote(place_match.group(1)).replace("+", " ")
        if not re.search(r"[2-9A-Z]{4,8}\+[2-9A-Z]{2,4}", raw_name, re.I):
            place_name = raw_name

    nom_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&addressdetails=1"
    nom_req = urllib.request.Request(
        nom_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    )
    
    direccion, ciudad, pais = None, None, None
    try:
        with urllib.request.urlopen(nom_req) as nom_resp:
            nom_data = json.loads(nom_resp.read().decode("utf-8"))
            addr = nom_data.get("address", {})
            
            road = addr.get("road") or addr.get("pedestrian") or addr.get("building") or addr.get("amenity") or addr.get("university") or ""
            hn = addr.get("house_number")
            house_str = f" #{hn}" if hn else ""
            if road:
                direccion = f"{road}{house_str}"
            else:
                try:
                    import openlocationcode.openlocationcode as olc
                    full_code = olc.encode(lat, lng, 11)
                    short_code = full_code[4:12]
                    city_str = addr.get("city") or addr.get("town") or addr.get("municipality") or ""
                    if city_str:
                        direccion = f"{short_code}, {city_str}"
                    else:
                        direccion = short_code
                except ImportError:
                    disp = nom_data.get("display_name", "")
                    if disp:
                        direccion = disp.split(",")[0]
            
            ciudad = addr.get("city") or addr.get("town") or addr.get("municipality") or addr.get("state_district") or addr.get("state")
            pais = addr.get("country")
    except Exception as e:
        pass

    return ParseGmapsResponse(
        nombre=place_name,
        direccion=direccion,
        ciudad=ciudad,
        pais=pais,
        latitud=lat,
        longitud=lng
    )
