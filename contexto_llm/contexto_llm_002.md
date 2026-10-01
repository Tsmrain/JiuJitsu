

--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/ui/api/auth_routes.py ---
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, EmailStr
import urllib.request
import urllib.parse
import json
import re
import jwt as pyjwt

from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.config import settings

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


def get_db():
    return PostgrestClient()

def _decode_jwt(authorization: Optional[str]) -> dict:
    """
    Decodifica y verifica un JWT firmado (HS256).
    Lanza HTTPException 401 si falta el header, está malformado o expiró.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación."
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
            detail="Token expirado."
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o firma incorrecta."
        )

    if not payload.get("uid") or not payload.get("role"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token incompleto."
        )

    return payload


def require_admin(authorization: Optional[str]) -> dict:
    """Verifica JWT válido + rol admin."""
    payload = _decode_jwt(authorization)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador."
        )
    return payload


def require_staff(authorization: Optional[str]) -> dict:
    """Verifica JWT válido + rol admin o profesor."""
    payload = _decode_jwt(authorization)
    if payload.get("role") not in ["admin", "profesor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de staff (admin o profesor)."
        )
    return payload


def require_auth(authorization: Optional[str]) -> dict:
    """Verifica JWT válido (cualquier rol)."""
    return _decode_jwt(authorization)


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
            detail="Nombre de usuario o contraseña incorrectos."
        )

    # PostgREST puede devolver {"token": None} si el RPC retorna NULL (credenciales inválidas)
    if not token_resp or not token_resp.get("token"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos."
        )

    try:
        legacy_payload = json.loads(token_resp["token"])
    except (KeyError, json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos."
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
            sucursal_nombre="Sucursal Principal"
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
        sucursal_nombre=sucursal_nombre
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
            detail="El rol de Administrador es exclusivo y reservado por seguridad."
        )

    if rol_solicitado not in ["alumno", "profesor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol de registro debe ser 'alumno' o 'profesor'."
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
                detail="No hay sucursales registradas en el sistema para asociar al usuario. Por favor, crea una sucursal primero."
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
                detail=f"El nombre de usuario '{req.username}' ya está registrado."
            )
        raise

    if not created_users:
        raise HTTPException(status_code=500, detail="Error creando usuario")
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
        sucursal_nombre=sucursal["nombre"]
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
            sucursal_nombre=u.get("sucursal_nombre") or "Sucursal Eliminada"
        ))
    return resultado

@router.put("/auth/usuarios/{user_id}", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def update_usuario(user_id: UUID, req: UserUpdateRequest, authorization: Optional[str] = Header(None)):
    """
    Actualizar perfil de usuario (nombre, contraseña, foto base64).
    - Admin puede actualizar a cualquier usuario.
    - Usuario normal solo puede actualizarse a sí mismo.
    Usa RPC SECURITY DEFINER: password se hashea en la BD.
    """
    caller = require_auth(authorization)

    # Autorización: admin O el propio usuario
    caller_uid = caller.get("uid")
    caller_role = caller.get("role")
    if caller_role != "admin" and str(user_id) != str(caller_uid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este perfil."
        )

    db = get_db()

    updated_list = db.rpc("admin_update_user", {
        "p_user_id": str(user_id),
        "p_nombre": req.nombre_completo,
        "p_password": req.password if (req.password and req.password.strip() != "") else None,
        "p_avatar_url": req.avatar_url
    })
    if not updated_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    updated = updated_list[0]

    signed_token = _sign_token({
        "uid": str(updated["id"]),
        "role": updated["rol"],
        "email": updated["email"],
        "sucursal_id": str(updated["sucursal_id"]) if updated.get("sucursal_id") else ""
    })

    return LoginResponse(
        token=signed_token,
        user_id=UUID(updated["id"]),
        nombre_completo=updated["nombre_completo"],
        username=updated["username"],
        email=updated["email"],
        rol=updated["rol"],
        avatar_url=updated.get("avatar_url"),
        sucursal_id=UUID(updated["sucursal_id"]) if updated.get("sucursal_id") else None,
        sucursal_nombre=updated.get("sucursal_nombre") or "Sucursal Eliminada"
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user = users[0]
    signed_token = _sign_token({
        "uid": str(user["id"]),
        "role": user["rol"],
        "email": user["email"],
        "sucursal_id": str(user["sucursal_id"]) if user.get("sucursal_id") else ""
    })

    return LoginResponse(
        token=signed_token,
        user_id=UUID(user["id"]),
        nombre_completo=user["nombre_completo"],
        username=user["username"],
        email=user["email"],
        rol=user["rol"],
        avatar_url=user.get("avatar_url"),
        sucursal_id=UUID(user["sucursal_id"]) if user.get("sucursal_id") else None,
        sucursal_nombre=user.get("sucursal_nombre") or "Sucursal Eliminada"
    )

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
            detail="Se requieren privilegios de profesor o administrador."
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

@router.get("/auth/alumnos/{alumno_id}/evaluaciones", status_code=status.HTTP_200_OK)
async def listar_evaluaciones_alumno(
    alumno_id: UUID,
    authorization: Optional[str] = Header(None)
):
    """
    Lista las últimas 20 evaluaciones de un alumno (para panel del profesor).
    - Profesor: solo puede ver alumnos de su sucursal.
    - Admin: cualquier alumno.
    """
    caller = require_auth(authorization)

    db = get_db()

    # Verificar que el alumno pertenece a la sucursal del profesor (o que es admin)
    if caller.get("role") == "profesor":
        caller_sucursal = caller.get("sucursal_id")
        if not caller_sucursal:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token sin sucursal.")

        alumno = db.rpc("admin_get_user_full", {"p_user_id": str(alumno_id)})
        if not alumno:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado.")
        if str(alumno[0].get("sucursal_id")) != str(caller_sucursal):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes ver alumnos de otra sucursal."
            )
    elif caller.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de profesor o administrador."
        )

    try:
        evaluaciones = db.rpc("admin_list_evaluaciones_alumno", {"p_alumno_id": str(alumno_id)})
    except Exception:
        evaluaciones = []

    return evaluaciones

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
        raise HTTPException(status_code=500, detail="Error creando sucursal")
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
            detail="Sucursal no encontrada."
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
                detail="No se puede eliminar esta sucursal porque tiene usuarios (profesores o alumnos) vinculados. Reasigna o elimina los usuarios primero."
            )
        raise

    if not deleted_ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal no encontrada."
        )
    return None

@router.post("/sucursales/parse-gmaps-link", response_model=ParseGmapsResponse, status_code=status.HTTP_200_OK)
async def parse_gmaps_link(req: ParseGmapsRequest):
    """
    Servicio backend de scraping y geocodificación para enlaces de Google Maps.
    """
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
                    detail="No se encontraron coordenadas válidas en el enlace proporcionado."
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



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/ui/api/routes.py ---
import os
import shutil
import tempfile
from uuid import UUID, uuid4
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel

from corpocmente.infrastructure.ai.adapters import GeminiApiAdapter
from corpocmente.application.use_cases.ingest_knowledge_use_case import IngestKnowledgeUseCase
from corpocmente.application.dtos.knowledge_dtos import IngestionRequest
from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.ui.api.auth_routes import require_auth, require_admin
from corpocmente.config import settings

router = APIRouter(prefix="/api/v1", tags=["Evaluaciones", "Conocimiento"])

class ResultadoWorkerDTO(BaseModel):
    similitud: float
    feedback: str
    estado: str


VIDEOS_DIR = "/tmp/corpocmente_videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

def get_db():
    return PostgrestClient()

def require_worker(x_worker_token: Optional[str] = Header(None)) -> None:
    """
    Verifica que el header X-Worker-Token coincida con el token de servicio configurado.
    El Worker de Colab no tiene token de usuario; usa un shared secret.
    """
    if not x_worker_token or x_worker_token != settings.WORKER_SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de Worker inválido o ausente."
        )

@router.post("/evaluaciones/analizar", status_code=status.HTTP_200_OK)
async def analizar_video(
    tecnica_id: UUID = Form(...),
    tecnica_nombre: str = Form(...),
    profesor_id: Optional[UUID] = Form(None),
    video: UploadFile = File(...),
    alumno_id: UUID = Form(...),
    authorization: Optional[str] = Header(None)
):
    caller = require_auth(authorization)

    # Autorización: solo el propio alumno o un admin pueden crear evaluaciones
    if caller.get("role") != "admin" and str(caller.get("uid")) != str(alumno_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes crear evaluaciones a nombre de otro usuario."
        )

    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado. Debe ser un video (MP4, AVI, MOV, MKV)."
        )

    eval_id = str(uuid4())
    video_path = os.path.join(VIDEOS_DIR, f"{eval_id}.mp4")

    # Guardar video en directorio persistente para el worker
    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    db = get_db()

    # Buscar el video de referencia del PROFESOR ESPECÍFICO si se proveyó
    try:
        if profesor_id:
            videos_ref = db.rpc("get_video_referencia_by_tecnica_profesor", {
                "p_tecnica_id": str(tecnica_id),
                "p_profesor_id": str(profesor_id),
            })
        else:
            videos_ref = db.rpc("get_video_referencia_by_tecnica", {
                "p_tecnica_id": str(tecnica_id)
            })
    except Exception:
        videos_ref = []

    if not videos_ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay video de referencia para esta técnica, por lo que no se puede evaluar."
        )
    video_ref_id = videos_ref[0]["id"]

    try:
        created = db.rpc("create_evaluacion", {
            "p_id": eval_id,
            "p_alumno_id": str(alumno_id),
            "p_tecnica_id": str(tecnica_id),
            "p_video_referencia_id": str(video_ref_id),
            "p_url_video_alumno": video_path
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando evaluación: {e}")

    if not created:
        raise HTTPException(status_code=500, detail="Error creando evaluación")

    return {"evaluacion_id": eval_id, "estado": "procesando"}

# --- Endpoints para el Worker de Colab Web ---

@router.get("/evaluaciones/pendientes")
async def listar_pendientes(x_worker_token: Optional[str] = Header(None)):
    """El Worker de Colab consulta esto para obtener la siguiente tarea."""
    require_worker(x_worker_token)
    db = get_db()
    try:
        pendientes = db.rpc("worker_claim_next_pending", {})
    except Exception:
        pendientes = []

    if not pendientes:
        return None

    eval_data = pendientes[0]
    return {
        "id": eval_data["id"],
        "video_path": eval_data["video_path"],
        "tecnica_id": eval_data["tecnica_id"],
        "tecnica_nombre": eval_data["tecnica_nombre"],
        "estado": eval_data["estado"]
    }

@router.get("/evaluaciones/video/{evaluacion_id}")
async def descargar_video_alumno(evaluacion_id: UUID, x_worker_token: Optional[str] = Header(None)):
    """El Worker descarga el archivo de video del alumno."""
    require_worker(x_worker_token)
    db = get_db()
    try:
        rows = db.rpc("worker_get_video_path", {"p_evaluacion_id": str(evaluacion_id)})
    except Exception:
        rows = []

    if not rows:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    video_path = rows[0]["video_path"]
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video no encontrado localmente")

    return FileResponse(video_path, media_type="video/mp4", filename=f"{evaluacion_id}.mp4")

@router.post("/evaluaciones/resultado/{evaluacion_id}")
async def recibir_resultado(
    evaluacion_id: UUID,
    payload: ResultadoWorkerDTO,
    x_worker_token: Optional[str] = Header(None)
):
    """El Worker POSTea el resultado final."""
    require_worker(x_worker_token)
    db = get_db()
    try:
        updated_ok = db.rpc("worker_update_result", {
            "p_evaluacion_id": str(evaluacion_id),
            "p_similitud": payload.similitud,
            "p_feedback_es": payload.feedback,
            "p_estado": payload.estado
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando resultado: {e}")

    if not updated_ok:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    return {"status": "ok"}

@router.get("/evaluaciones/{evaluacion_id}")
async def consultar_evaluacion(
    evaluacion_id: UUID,
    authorization: Optional[str] = Header(None)
):
    """El frontend consulta el estado de una evaluación (polling)."""
    caller = require_auth(authorization)

    db = get_db()
    try:
        evaluaciones = db.rpc("get_evaluacion_by_id", {
            "p_evaluacion_id": str(evaluacion_id)
        })
    except Exception:
        evaluaciones = []

    if not evaluaciones:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    eval_data = evaluaciones[0]

    # Autorización: solo el dueño de la evaluación o un admin
    if caller.get("role") != "admin" and str(caller.get("uid")) != str(eval_data["alumno_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar esta evaluación."
        )

    # Convertir ruta local del video de referencia a URL pública estática
    raw_video_path = eval_data.get("video_referencia_url") or ""
    video_ref_url = None
    if raw_video_path:
        filename = os.path.basename(raw_video_path)
        video_ref_url = f"/static/videos/{filename}"

    return {
        "id": eval_data["id"],
        "estado": eval_data["estado"],
        "similitud": eval_data["porcentaje_similitud"],
        "feedback": eval_data["feedback_gemini_es"] or eval_data["feedback_gemini_pt"],
        "tecnica_id": eval_data["tecnica_id"],
        "tecnica_nombre": eval_data["tecnica_nombre"],
        "video_referencia_url": video_ref_url,
        "video_referencia_profesor_nombre": eval_data.get("video_referencia_profesor_nombre"),
    }

@router.post("/evaluaciones/validar-spam", status_code=status.HTTP_200_OK)
async def validar_spam(video: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    """
    Endpoint HTTP aislado para validar tempranamente si un video es de Jiu-Jitsu (SPAM filter).
    Requiere cualquier usuario autenticado.
    """
    require_auth(authorization)

    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        shutil.copyfileobj(video.file, temp_video)
        temp_video_path = temp_video.name

    try:
        gemini_adapter = GeminiApiAdapter()
        es_valido = gemini_adapter.validar_es_jiujitsu(temp_video_path)
        if not es_valido:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El video proporcionado no parece estar relacionado con Jiu-Jitsu o Grappling."
            )
        return {"status": "ok", "message": "El video es válido."}
    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)


# --- Endpoints de Ingestión de Conocimiento (RAG) ---

@router.post("/conocimiento/teoria", status_code=status.HTTP_201_CREATED)
async def ingerir_teoria(payload: IngestionRequest, authorization: Optional[str] = Header(None)):
    """
    Endpoint HTTP: Ingestión de teoría del profesor al sistema RAG.
    Persiste tanto en Qdrant (vectores) como en PostgreSQL (metadata).
    """
    caller = require_auth(authorization)
    if caller.get("role") not in ("admin", "profesor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de profesor o administrador."
        )

    use_case = IngestKnowledgeUseCase()
    resultado = use_case.execute(
        tecnica_id=payload.tecnica_id,
        contenido_texto=payload.contenido_texto,
        profesor_id=caller.get("uid"),
        sucursal_id=caller.get("sucursal_id"),
    )
    return {"status": "ok", "chunks_procesados": resultado.chunks_procesados}


from corpocmente.application.use_cases.list_theory_use_case import ListTheoryUseCase
from corpocmente.application.use_cases.delete_theory_use_case import DeleteTheoryUseCase


@router.get("/conocimiento/teoria/{tecnica_id}", status_code=status.HTTP_200_OK)
async def listar_teoria(
    tecnica_id: UUID,
    solo_mios: bool = False,
    authorization: Optional[str] = Header(None)
):
    """
    Endpoint HTTP: Lista los chunks de teoría de una técnica.

    - Cualquier usuario autenticado puede ver el material de una técnica.
    - Con ?solo_mios=true, un profesor ve únicamente sus propios aportes.
    """
    caller = require_auth(authorization)

    profesor_id = caller.get("uid") if solo_mios else None

    use_case = ListTheoryUseCase()
    chunks = use_case.execute(tecnica_id=str(tecnica_id), profesor_id=profesor_id)

    return {
        "tecnica_id": str(tecnica_id),
        "total": len(chunks),
        "chunks": chunks,
    }


@router.delete("/conocimiento/teoria/{tecnica_id}", status_code=status.HTTP_200_OK)
async def eliminar_teoria(
    tecnica_id: UUID,
    authorization: Optional[str] = Header(None)
):
    """
    Endpoint HTTP: Elimina TODA la teoría que el profesor autenticado subió
    para esta técnica (en Postgres y en Qdrant).
    """
    caller = require_auth(authorization)
    if caller.get("role") not in ("admin", "profesor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de profesor o administrador."
        )

    use_case = DeleteTheoryUseCase()
    resultado = use_case.execute(
        tecnica_id=str(tecnica_id),
        profesor_id=caller.get("uid"),
    )
    return {"status": "ok", **resultado}






--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/corpocmente/ui/api/tecnicas_routes.py ---
import os
import shutil
from uuid import UUID, uuid4
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Header
from pydantic import BaseModel

from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
from corpocmente.ui.api.auth_routes import require_auth, require_admin, require_staff

router = APIRouter(prefix="/api/v1/tecnicas", tags=["Técnicas"])


class TecnicaCreate(BaseModel):
    nombre: str
    nivel_cinturon: str


class TecnicaResponse(TecnicaCreate):
    id: UUID
    tiene_video: bool = False
    video_url: Optional[str] = None


UPLOAD_DIR = "/tmp/corpocmente_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    return PostgrestClient()


def require_staff(authorization: Optional[str]) -> dict:
    """Permite admin o profesor."""
    caller = require_auth(authorization)
    if caller.get("role") not in ("admin", "profesor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de profesor o administrador."
        )
    return caller


@router.get("", response_model=List[TecnicaResponse], status_code=status.HTTP_200_OK)
async def listar_tecnicas(profesor_id: Optional[UUID] = None):
    """
    Lista todas las técnicas del catálogo global (público).
    Si se provee profesor_id, marca las que ese profesor ya tiene con video.
    """
    db = get_db()
    try:
        rows = db.rpc("get_tecnicas_with_videos", {})
    except Exception:
        rows = []

    # Agrupar por técnica (una técnica puede tener varios videos de distintos profesores)
    tecnicas_map: dict = {}
    for r in rows:
        tid = r["id"]
        if tid not in tecnicas_map:
            tecnicas_map[tid] = {
                "id": tid,
                "nombre": r["nombre"],
                "nivel_cinturon": r["nivel_cinturon"],
                "videos": []
            }
        if r.get("video_id"):
            tecnicas_map[tid]["videos"].append({
                "profesor_id": r.get("video_profesor_id"),
                "url": r.get("video_url")
            })

    resultados = []
    for t in tecnicas_map.values():
        tiene_video = False
        video_url = None
        if profesor_id:
            vid = next((v for v in t["videos"] if str(v["profesor_id"]) == str(profesor_id)), None)
            if vid:
                tiene_video = True
                filename = os.path.basename(vid["url"])
                video_url = f"http://localhost:8000/static/videos/{filename}"

        resultados.append(TecnicaResponse(
            id=UUID(t["id"]),
            nombre=t["nombre"],
            nivel_cinturon=t["nivel_cinturon"],
            tiene_video=tiene_video,
            video_url=video_url
        ))

    return resultados


@router.post("", response_model=TecnicaResponse, status_code=status.HTTP_201_CREATED)
async def crear_tecnica(req: TecnicaCreate, authorization: Optional[str] = Header(None)):
    """
    Agrega una nueva técnica al catálogo global.
    Requiere token de admin o profesor. Usa RPC SECURITY DEFINER.
    """
    require_staff(authorization)
    db = get_db()
    created = db.rpc("admin_create_tecnica", {
        "p_nombre": req.nombre,
        "p_nivel_cinturon": req.nivel_cinturon
    })
    if not created:
        raise HTTPException(status_code=500, detail="Error creando técnica")
    c = created[0] if isinstance(created, list) else created
    return TecnicaResponse(
        id=UUID(c["id"]),
        nombre=c["nombre"],
        nivel_cinturon=c["nivel_cinturon"]
    )


@router.put("/{tecnica_id}", response_model=TecnicaResponse, status_code=status.HTTP_200_OK)
async def actualizar_tecnica(tecnica_id: UUID, req: TecnicaCreate, authorization: Optional[str] = Header(None)):
    """
    Edita una técnica del catálogo. Requiere token de admin o profesor.
    """
    require_staff(authorization)
    db = get_db()
    updated = db.rpc("admin_update_tecnica", {
        "p_tecnica_id": str(tecnica_id),
        "p_nombre": req.nombre,
        "p_nivel_cinturon": req.nivel_cinturon
    })
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnica no encontrada.")
    c = updated[0] if isinstance(updated, list) else updated
    return TecnicaResponse(
        id=UUID(c["id"]),
        nombre=c["nombre"],
        nivel_cinturon=c["nivel_cinturon"]
    )


@router.delete("/{tecnica_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_tecnica(tecnica_id: UUID, authorization: Optional[str] = Header(None)):
    """
    Elimina una técnica del catálogo. Requiere token de admin o profesor.
    """
    require_staff(authorization)
    db = get_db()
    deleted_ok = db.rpc("admin_delete_tecnica", {"p_tecnica_id": str(tecnica_id)})
    if not deleted_ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnica no encontrada.")
    return None


@router.post("/{tecnica_id}/video", status_code=status.HTTP_200_OK)
async def subir_video_referencia(
    tecnica_id: UUID,
    profesor_id: UUID = Form(...),
    video: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Sube un video de referencia para una técnica.
    Requiere token de profesor o admin. Un profesor solo puede subir sus propios videos.
    """
    caller = require_staff(authorization)

    # Autorización: profesor solo puede subir videos a su propio nombre
    if caller.get("role") != "admin" and str(caller.get("uid")) != str(profesor_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes subir videos a nombre de otro profesor."
        )

    if not video.filename.endswith(('.mp4', '.avi', '.mov', '.webm')):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de video no soportado.")

    db = get_db()

    # Verificar que la técnica existe vía RPC
    try:
        exists = db.rpc("tecnica_exists", {"p_tecnica_id": str(tecnica_id)})
    except Exception:
        exists = False

    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnica no encontrada en el catálogo.")

    file_path = os.path.join(UPLOAD_DIR, f"{uuid4()}_{video.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    # Guardar vía RPC (upsert: borra el anterior del mismo profesor y crea uno nuevo)
    try:
        result = db.rpc("admin_save_video_referencia", {
            "p_tecnica_id": str(tecnica_id),
            "p_profesor_id": str(profesor_id),
            "p_url_video": file_path
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando referencia de video: {e}")

    if not result:
        raise HTTPException(status_code=500, detail="Error guardando referencia de video.")

    video_id = result[0]["video_id"] if isinstance(result, list) else result["video_id"]
    return {"status": "ok", "message": "Video de referencia actualizado.", "video_id": video_id}



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/scripts/ingest_reference_video.py ---
#!/usr/bin/env python3
"""
ingest_reference_video.py — Ingesta REAL del video de referencia de un profesor.

Flujo:
  1. Extrae frames del video (muestreo cada N) y los guarda como JPG en /tmp.
  2. Envía el video al Colab Worker (/extraer_poses) para obtener keypoints reales.
  3. Persiste en Qdrant con payload {tecnica_id, frame_idx, frame_path, discrepancias}.
  4. Las discrepancias se rellenan luego con un experto (o vacío inicialmente).

Uso:
    python scripts/ingest_reference_video.py \
        --video /ruta/armbar_miguel.mp4 \
        --tecnica-id d3b07384-d9a4-4f6c-947b-11347076a5b6 \
        --tecnica-nombre "Armbar desde guardia"
"""
import argparse
import os
import sys
import uuid

import cv2
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# Añadir el directorio padre al path para importar corpocmente
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from corpocmente.config import settings

FRAMES_DIR = "/tmp/corpocmente_reference_frames"
os.makedirs(FRAMES_DIR, exist_ok=True)


def extract_frames(video_path: str, tecnica_id: str, every_n: int = 5) -> dict[int, str]:
    """Extrae 1 de cada N frames como JPG. Retorna {frame_idx: jpg_path}."""
    out_dir = os.path.join(FRAMES_DIR, tecnica_id)
    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir el video: {video_path}")

    mapping: dict[int, str] = {}
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % every_n == 0:
            path = os.path.join(out_dir, f"ref_{idx:05d}.jpg")
            cv2.imwrite(path, frame)
            mapping[idx] = path
        idx += 1
    cap.release()
    print(f"  Total frames en video: {idx}")
    return mapping


def request_poses(video_path: str, colab_url: str) -> list[dict]:
    """Llama al worker real de Colab. Sin fallback a vectores dummy."""
    if not colab_url or "placeholder" in colab_url:
        raise RuntimeError(
            "COLAB_TUNNEL_URL no está configurada en .env "
            "(vacía o contiene 'placeholder'). "
            "Ejecutar el notebook colab_worker.ipynb y copiar la URL de ngrok."
        )

    endpoint = f"{colab_url.rstrip('/')}/extraer_poses"
    print(f"→ POST {endpoint}")
    with open(video_path, "rb") as f:
        resp = requests.post(
            endpoint,
            files={"video": f},
            headers={"ngrok-skip-browser-warning": "1"},
            timeout=600,
        )
    resp.raise_for_status()
    data = resp.json()
    esqueletos = data.get("esqueletos", [])
    if not esqueletos:
        raise RuntimeError("El worker no devolvió esqueletos. Revisar video y endpoint.")
    print(f"✓ {len(esqueletos)} frames con pose detectada.")
    return esqueletos


def ensure_collection(client: QdrantClient, collection_name: str):
    """Crea la colección con size=133, distance=COSINE si no existe."""
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=133, distance=Distance.COSINE),
        )
        print(f"✓ Colección '{collection_name}' creada (size=133, COSINE).")
    else:
        print(f"  Colección '{collection_name}' ya existe.")


def main():
    ap = argparse.ArgumentParser(
        description="Ingesta REAL de video de referencia → Colab Worker → Qdrant"
    )
    ap.add_argument("--video", required=True, help="Ruta al video de referencia del profesor")
    ap.add_argument("--tecnica-id", required=True, help="UUID de la técnica (e.g. d3b07384-...)")
    ap.add_argument("--tecnica-nombre", default="", help="Nombre legible de la técnica")
    ap.add_argument("--colab-url", default=None,
                    help="URL del tunnel ngrok (default: lee de .env COLAB_TUNNEL_URL)")
    ap.add_argument("--every-n", type=int, default=5,
                    help="Muestreo de frames para JPG (1 = todos, 5 = 1 de cada 5)")
    args = ap.parse_args()

    colab_url = args.colab_url or settings.COLAB_TUNNEL_URL

    if not os.path.exists(args.video):
        print(f"❌ Video no encontrado: {args.video}")
        sys.exit(1)

    print(f"=== Ingesta de referencia: {args.tecnica_nombre or args.tecnica_id} ===")
    print(f"  Video: {args.video}")
    print(f"  Técnica ID: {args.tecnica_id}")
    print(f"  Colab URL: {colab_url}")
    print(f"  Muestreo: 1 de cada {args.every_n} frames")
    print()

    # 1. Extraer frames reales del video como JPG
    frame_map = extract_frames(args.video, args.tecnica_id, every_n=args.every_n)
    print(f"✓ {len(frame_map)} frames extraídos a {FRAMES_DIR}/{args.tecnica_id}")

    # 2. Extraer keypoints reales del worker de Colab (YOLO26-pose)
    esqueletos = request_poses(args.video, colab_url)

    # 3. Persistir en Qdrant
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    ensure_collection(client, settings.QDRANT_COLLECTION)

    points = []
    skipped = 0
    for esk in esqueletos:
        fidx = esk.get("frame_idx")
        kp = esk.get("keypoints133", [])

        # Validar que el frame tiene keypoints de 133 dims
        if len(kp) != 133:
            skipped += 1
            continue

        # Mapear al JPG correspondiente si existe
        frame_path = frame_map.get(fidx, "")

        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=kp,
            payload={
                "tecnica_id": args.tecnica_id,
                "tecnica_nombre": args.tecnica_nombre,
                "frame_idx": fidx,
                "frame_path": frame_path,
                "discrepancias": [],  # el profesor/experto las anota después
            },
        ))

    if skipped:
        print(f"  ⚠ {skipped} esqueletos descartados (keypoints != 133 dims)")

    if not points:
        print("❌ Ningún punto válido para insertar. Verifica el worker y el muestreo.")
        sys.exit(1)

    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    print(f"\n✅ {len(points)} puntos persistidos en '{settings.QDRANT_COLLECTION}'.")
    print(f"   Frames JPG guardados en: {FRAMES_DIR}/{args.tecnica_id}")

    # 4. Verificación rápida
    info = client.get_collection(settings.QDRANT_COLLECTION)
    print(f"   Total puntos en colección: {info.points_count}")


if __name__ == "__main__":
    main()



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/scripts/migrar_db.py ---
import os
import psycopg2

def migrar_db():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_dir = os.path.join(base_dir, 'database')
    
    scripts = [
        '01_schema_3nf.sql',
        '02_auth_jwt.sql',
        '03_rls_policies.sql',
        '04_seed_data.sql',
    ]
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="corpocmente",
            user="postgres",
            password="postgres",
            port="5432"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        for script in scripts:
            script_path = os.path.join(db_dir, script)
            print(f"Ejecutando {script}...")
            with open(script_path, 'r', encoding='utf-8') as f:
                sql = f.read()
                cursor.execute(sql)
            print(f"✅ {script} ejecutado con éxito.")
            
        print("✅ Migración completada correctamente.")
        
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cursor.fetchall()
        print(f"Tablas en 'public': {tables}")
        
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='auth';")
        tables = cursor.fetchall()
        print(f"Tablas en 'auth': {tables}")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    migrar_db()



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/scripts/reconcile_rag.py ---
#!/usr/bin/env python3
"""
reconcile_rag.py — Auditoría y reconciliación Postgres ↔ Qdrant.

Detecta orphans en ambas direcciones y, con --fix, elimina los orphans de Qdrant
(Postgres es la fuente de verdad; Qdrant es índice reconstruible desde teoria_referencia).

Uso:
    python scripts/reconcile_rag.py              # solo detecta, no modifica
    python scripts/reconcile_rag.py --fix        # detecta y limpia orphans en Qdrant
"""
import argparse
import os
import sys
import psycopg2
import requests

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "host=localhost dbname=corpocmente user=postgres password=postgres")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "rag_knowledge"


def fetch_postgres_ids() -> set[str]:
    """Retorna el conjunto de qdrant_point_id registrados en teoria_referencia."""
    with psycopg2.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT qdrant_point_id FROM teoria_referencia;")
            return {str(row[0]) for row in cur.fetchall()}


def fetch_qdrant_ids() -> set[str]:
    """Retorna el conjunto de IDs de puntos en la colección rag_knowledge."""
    r = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
        json={"limit": 10000, "with_payload": False},
        timeout=30,
    )
    r.raise_for_status()
    points = r.json().get("result", {}).get("points", [])
    return {p["id"] for p in points}


def delete_qdrant_points(ids: list[str]) -> None:
    """Borra los puntos indicados en Qdrant."""
    if not ids:
        return
    r = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/delete",
        json={"points": ids},
        timeout=30,
    )
    r.raise_for_status()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="Elimina orphans en Qdrant")
    args = parser.parse_args()

    print("=" * 70)
    print("RECONCILIACIÓN POSTGRES ↔ QDRANT")
    print("=" * 70)

    pg_ids = fetch_postgres_ids()
    qdrant_ids = fetch_qdrant_ids()

    print(f"Postgres (fuente de verdad): {len(pg_ids)} chunks")
    print(f"Qdrant (índice):             {len(qdrant_ids)} puntos")

    orphans_qdrant = qdrant_ids - pg_ids       # en Qdrant pero no en Postgres
    orphans_postgres = pg_ids - qdrant_ids     # en Postgres pero no en Qdrant

    print()
    if not orphans_qdrant and not orphans_postgres:
        print("✅ CONSISTENCIA TOTAL — Sin orphans en ninguna dirección.")
        return 0

    if orphans_qdrant:
        print(f"⚠️  {len(orphans_qdrant)} orphan(s) en Qdrant (sin fila en Postgres):")
        for oid in sorted(orphans_qdrant):
            print(f"    - {oid}")

    if orphans_postgres:
        print(f"🚨 {len(orphans_postgres)} orphan(s) en Postgres (sin punto en Qdrant):")
        for oid in sorted(orphans_postgres):
            print(f"    - {oid}")
        print("    ⚠️  Postgres es la fuente de verdad — investigar manualmente.")

    if args.fix and orphans_qdrant:
        print()
        print(f"🔧 Aplicando --fix: eliminando {len(orphans_qdrant)} orphan(s) de Qdrant...")
        delete_qdrant_points(sorted(orphans_qdrant))
        print("✅ Eliminados. Re-ejecuta sin --fix para verificar consistencia.")

    return 0


if __name__ == "__main__":
    sys.exit(main())



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/scripts/verify_rag_e2e.py ---
#!/usr/bin/env python3
"""
verify_rag_e2e.py — Verificación funcional end-to-end del sistema RAG.

Prueba de integración con el stack REAL (sin mocks):
  1. Preflight: Backend + Qdrant + Colab responden.
  2. Ingestión: Envía texto real a `/api/v1/conocimiento/teoria`.
  3. Persistencia: Verifica que los chunks llegaron a Qdrant.
  4. Recuperación: Consulta semántica vía Colab embedding + Qdrant search.

Uso:
    python scripts/verify_rag_e2e.py \
        --texto /ruta/a/teoria_real.txt \
        --tecnica-id d3b07384-d9a4-4f6c-947b-11347076a5b6 \
        --jwt <TOKEN_JWT>

Requiere que COLAB_TUNNEL_URL esté en .env o pase como --colab-url.
"""
import argparse
import os
import sys

import psycopg2
import requests

QDRANT_URL = "http://localhost:6333"
COLLECTION = "rag_knowledge"
DB_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/corpocmente")


def postgres_count(tecnica_id: str) -> int:
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM teoria_referencia WHERE tecnica_id = %s;", (tecnica_id,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"[WARN] Error al consultar PostgreSQL: {e}")
        return 0


def check_services(api_url: str, colab_url: str) -> bool:
    print("=" * 70)
    print("PREFLIGHT CHECKS")
    print("=" * 70)
    ok = True

    # Backend
    try:
        r = requests.get(f"{api_url}/health", timeout=5)
        r.raise_for_status()
        print(f"[OK] Backend: {r.json()}")
    except Exception as e:
        print(f"[FAIL] Backend no responde en {api_url}: {e}")
        ok = False

    # Qdrant
    try:
        r = requests.get(f"{QDRANT_URL}/collections", timeout=5)
        r.raise_for_status()
        colls = [c["name"] for c in r.json()["result"]["collections"]]
        print(f"[OK] Qdrant: {len(colls)} colecciones -> {colls}")
    except Exception as e:
        print(f"[FAIL] Qdrant no responde en {QDRANT_URL}: {e}")
        ok = False

    # Colab Worker
    if not colab_url or "placeholder" in colab_url:
        print("[FAIL] COLAB_TUNNEL_URL no configurado")
        ok = False
    else:
        try:
            r = requests.get(f"{colab_url.rstrip('/')}/health", timeout=15)
            r.raise_for_status()
            print(f"[OK] Colab: {r.json()}")
        except Exception as e:
            print(f"[FAIL] Colab no responde en {colab_url}: {e}")
            ok = False

    return ok


def qdrant_count() -> int:
    try:
        r = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/count",
            json={"exact": True},
            timeout=5,
        )
        return r.json().get("result", {}).get("count", 0)
    except Exception:
        return 0


def ingest(api_url: str, jwt: str, tecnica_id: str, texto: str) -> int | None:
    print("\n" + "=" * 70)
    print("FASE 1: INGESTIÓN (texto real -> Colab -> Qdrant + Postgres)")
    print("=" * 70)
    print(f"  Texto: {len(texto)} caracteres")

    r = requests.post(
        f"{api_url}/api/v1/conocimiento/teoria",
        headers={"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"},
        json={"tecnica_id": tecnica_id, "contenido_texto": texto},
        timeout=180,
    )
    print(f"  HTTP {r.status_code}")
    if r.status_code != 201:
        print(f"[FAIL] Ingestión falló: {r.text}")
        return None
    data = r.json()
    print(f"[OK] {data}")
    return data.get("chunks_procesados", 0)


def query(colab_url: str, tecnica_id: str, query_text: str):
    print("\n" + "=" * 70)
    print("FASE 2: RECUPERACIÓN (consulta semántica)")
    print("=" * 70)
    print(f"  Query: {query_text[:100]}")

    # Generar embedding de la query vía Colab
    r = requests.post(
        f"{colab_url.rstrip('/')}/embed_text",
        data={"texto": query_text},
        timeout=60,
    )
    if r.status_code != 200:
        print(f"[FAIL] Colab embedding: {r.status_code} {r.text[:200]}")
        return None
    emb_data = r.json()
    query_vec = emb_data["embeddings"][0]
    print(f"[OK] Query embedding: {len(query_vec)} dims")

    # Buscar en Qdrant
    r = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
        json={
            "vector": {"name": "dense", "vector": query_vec},
            "limit": 3,
            "filter": {
                "must": [
                    {"key": "tecnica_id", "match": {"value": tecnica_id}}
                ]
            },
            "with_payload": True,
        },
        timeout=30,
    )
    if r.status_code != 200:
        print(f"[FAIL] Qdrant search: {r.status_code} {r.text[:200]}")
        return None
    results = r.json().get("result", [])
    print(f"[OK] {len(results)} chunks recuperados\n")
    for i, hit in enumerate(results, 1):
        score = hit.get("score", 0)
        chunk = hit.get("payload", {}).get("contenido_texto", "")
        preview = chunk[:220].replace("\n", " ")
        print(f"  [{i}] score={score:.4f}")
        print(f"      {preview}...")
        print()
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--texto", required=True, help="Ruta al archivo de texto real")
    parser.add_argument("--tecnica-id", required=True)
    parser.add_argument("--jwt", required=True)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--colab-url", default=os.getenv("COLAB_TUNNEL_URL", ""))
    parser.add_argument("--query", default="¿Cómo se ejecuta correctamente la técnica?")
    args = parser.parse_args()

    if not os.path.exists(args.texto):
        print(f"[FAIL] Archivo no existe: {args.texto}")
        sys.exit(1)

    with open(args.texto, "r", encoding="utf-8") as f:
        texto = f.read().strip()

    if not texto:
        print(f"[FAIL] Archivo vacío: {args.texto}")
        sys.exit(1)

    if not check_services(args.api_url, args.colab_url):
        print("\n[ABORT] Preflight falló. Corrige los servicios antes de continuar.")
        sys.exit(1)

    pg_before = postgres_count(args.tecnica_id)
    count_before = qdrant_count()
    print(f"\n  Filas en Postgres ANTES: {pg_before}")
    print(f"  Puntos en Qdrant ANTES: {count_before}")

    chunks = ingest(args.api_url, args.jwt, args.tecnica_id, texto)
    if chunks is None:
        sys.exit(1)

    pg_after = postgres_count(args.tecnica_id)
    count_after = qdrant_count()
    pg_delta = pg_after - pg_before
    delta = count_after - count_before
    print(f"  Filas en Postgres DESPUÉS: {pg_after} (delta: {pg_delta})")
    print(f"  Puntos en Qdrant DESPUÉS: {count_after} (delta: {delta})")

    if pg_delta <= 0 or delta <= 0:
        print(f"\n[FAIL] Ingestión incompleta: Postgres delta={pg_delta}, Qdrant delta={delta}")
        sys.exit(1)

    query(args.colab_url, args.tecnica_id, args.query)

    print("=" * 70)
    print("✅ VERIFICACIÓN COMPLETA (Persistencia Dual: Postgres + Qdrant)")
    print("=" * 70)


if __name__ == "__main__":
    main()



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/conftest.py ---
import pytest
from fastapi.testclient import TestClient
from corpocmente.main import app

@pytest.fixture
def client():
    return TestClient(app)



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/domain/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/domain/test_intelligence_facade.py ---
import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter, VectorSearchResultDTO
from corpocmente.domain.entities.models import EsqueletoBiomecanico

def test_ejecutar_analisis_completo_flujo_exitoso():
    # Arrange
    tecnica_id = uuid4()
    mock_yolo = Mock(spec=YOLOPoseAdapter)
    mock_qdrant = Mock(spec=QdrantVectorAdapter)
    mock_gemini = Mock(spec=GeminiApiAdapter)
    
    # Simular extraccion YOLO
    mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
    mock_esqueleto.to_vector_array.return_value = [0.1, 0.2, 0.3]
    mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]
    
    # Simular busqueda en Qdrant
    mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
        score=0.80,
        frame_path="/tmp/frame.jpg",
        discrepancias=["Cadera muy baja", "Agarre suelto"]
    )
    
    # Simular respuesta Gemini
    mock_gemini.generar_texto_feedback.return_value = "Feedback generado por IA."
    
    facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
    
    # Act
    resultado = facade.ejecutar_analisis_completo("/tmp/video.mp4", tecnica_id, "Armbar")
    
    # Assert
    assert resultado.similitud == 0.80
    assert resultado.feedback == "Feedback generado por IA."
    mock_yolo.extraer_keypoints.assert_called_once_with("/tmp/video.mp4")
    mock_qdrant.buscar_maxima_diferencia.assert_called_once_with([mock_esqueleto], tecnica_id)
    # Validar que Gemini fue llamado
    mock_gemini.generar_texto_feedback.assert_called_once()

def test_ejecutar_analisis_construye_query_textual_para_rag():
    """
    Regression test C11.4: cuando se inyecta un qwen_adapter, la fachada debe:
    1. Construir una query textual con tecnica_nombre + discrepancias.
    2. Llamar a `generar_embedding_texto` (NO al método deprecado de imagen).
    3. Pasar esa query textual a `recuperar_contexto_rag`.
    """
    from unittest.mock import Mock
    from uuid import uuid4
    from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
    from corpocmente.infrastructure.persistence.qdrant_adapter import VectorSearchResultDTO

    # Arrange
    tecnica_id = uuid4()
    mock_yolo = Mock(spec=YOLOPoseAdapter)
    mock_qdrant = Mock(spec=QdrantVectorAdapter)
    mock_gemini = Mock(spec=GeminiApiAdapter)
    mock_qwen = Mock(spec=QwenEmbeddingAdapter)

    mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
    mock_esqueleto.to_vector_array.return_value = [0.1, 0.2, 0.3]
    mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

    # Simular baja similitud para forzar el camino RAG
    mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
        score=0.60,
        frame_path="/tmp/frame.jpg",
        discrepancias=["Cadera alta", "Agarre flojo"]
    )
    mock_yolo.dibujar_error_en_frame.return_value = "/tmp/frame_resaltado.jpg"

    # Simular el embedding textual (2048 dims) y la teoría recuperada
    mock_qwen.generar_embedding_texto.return_value = [0.05] * 2048
    mock_qdrant.recuperar_contexto_rag.return_value = "Teoría recuperada sobre control de cadera."

    mock_gemini.generar_texto_feedback.return_value = "Feedback enriquecido con teoría."

    facade = IntelligenceAnalysisFacade(
        yolo_adapter=mock_yolo,
        qdrant_adapter=mock_qdrant,
        gemini_adapter=mock_gemini,
        qwen_adapter=mock_qwen
    )

    # Act
    resultado = facade.ejecutar_analisis_completo(
        video_path="/tmp/video.mp4",
        tecnica_id=tecnica_id,
        tecnica_nombre="Armbar"
    )

    # Assert
    # 1. Debe llamar a generar_embedding_texto (no a generar_embedding de imagen)
    mock_qwen.generar_embedding_texto.assert_called_once()
    mock_qwen.generar_embedding.assert_not_called()

    # 2. La query debe contener el nombre de la técnica y las discrepancias
    query_usada = mock_qwen.generar_embedding_texto.call_args.args[0]
    assert "Armbar" in query_usada, "La query textual debe incluir el nombre de la técnica"
    assert "Cadera alta" in query_usada or "Agarre flojo" in query_usada, \
        "La query textual debe incluir las discrepancias"

    # 3. Debe recuperar contexto RAG con el embedding textual
    mock_qdrant.recuperar_contexto_rag.assert_called_once()

    # 4. El feedback debe seguir generándose
    assert resultado.feedback == "Feedback enriquecido con teoría."




--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/domain/test_models_regression.py ---
"""
Tests de regresión para los fixes del pipeline biomecánico (C12.5).

Cubre:
  - EsqueletoBiomecanico.to_vector_array() retorna keypoints133 reales
  - EsqueletoBiomecanico acepta frame_idx del worker
  - to_vector_array() siempre retorna exactamente 133 dims
"""
import pytest
import math
from corpocmente.domain.entities.models import EsqueletoBiomecanico


# --- Vectores realistas (no [0.5]*133) para los tests ---
# Simula 17 keypoints COCO × 3 (x, y, conf) = 51 dims + 82 padding = 133
REALISTIC_KP = [
    # Nose
    0.523, 0.312, 0.95,
    # Left Eye
    0.545, 0.289, 0.93,
    # Right Eye
    0.501, 0.291, 0.92,
    # Left Ear
    0.578, 0.301, 0.88,
    # Right Ear
    0.468, 0.303, 0.87,
    # Left Shoulder
    0.612, 0.445, 0.96,
    # Right Shoulder
    0.434, 0.448, 0.95,
    # Left Elbow
    0.678, 0.578, 0.91,
    # Right Elbow
    0.367, 0.581, 0.90,
    # Left Wrist
    0.712, 0.689, 0.85,
    # Right Wrist
    0.334, 0.692, 0.84,
    # Left Hip
    0.589, 0.667, 0.97,
    # Right Hip
    0.456, 0.669, 0.96,
    # Left Knee
    0.601, 0.812, 0.93,
    # Right Knee
    0.445, 0.815, 0.92,
    # Left Ankle
    0.598, 0.945, 0.89,
    # Right Ankle
    0.448, 0.948, 0.88,
] + [0.0] * 82  # padding to 133


class TestEsqueletoBiomecanicoToVectorArray:
    """Regression tests for Fix 1.1: to_vector_array()."""

    def test_to_vector_array_returns_list_not_none(self):
        """to_vector_array() was returning None (pass). Must return a list."""
        esq = EsqueletoBiomecanico(keypoints133=REALISTIC_KP)
        result = esq.to_vector_array()
        assert result is not None, "to_vector_array() must not return None"
        assert isinstance(result, list), "Must return a list"

    def test_to_vector_array_returns_exact_133_dims(self):
        """Vector size must match Qdrant VectorParams(size=133)."""
        esq = EsqueletoBiomecanico(keypoints133=REALISTIC_KP)
        vec = esq.to_vector_array()
        assert len(vec) == 133, f"Expected 133 dims, got {len(vec)}"

    def test_to_vector_array_values_match_keypoints(self):
        """The returned vector must be a faithful copy of keypoints133."""
        esq = EsqueletoBiomecanico(keypoints133=REALISTIC_KP)
        vec = esq.to_vector_array()
        for i, (a, b) in enumerate(zip(vec, REALISTIC_KP)):
            assert math.isclose(a, b, rel_tol=1e-9), (
                f"Mismatch at index {i}: {a} != {b}"
            )

    def test_to_vector_array_returns_copy(self):
        """Returned list should be a copy (not a reference to the internal list)."""
        esq = EsqueletoBiomecanico(keypoints133=REALISTIC_KP)
        vec = esq.to_vector_array()
        vec[0] = 999.0
        assert esq.keypoints133[0] != 999.0, "Must return a copy, not a reference"


class TestEsqueletoBiomecanicoFrameIdx:
    """Regression tests for Fix 1.2: frame_idx field."""

    def test_frame_idx_default_zero(self):
        """frame_idx should default to 0 when not provided."""
        esq = EsqueletoBiomecanico(keypoints133=REALISTIC_KP)
        assert esq.frame_idx == 0

    def test_frame_idx_accepted_from_worker(self):
        """Pydantic must accept frame_idx from the Colab worker response dict."""
        worker_response = {
            "frame_idx": 42,
            "keypoints133": REALISTIC_KP,
            "angulos_articulares": {"codo_izq": 135.5},
        }
        esq = EsqueletoBiomecanico(**worker_response)
        assert esq.frame_idx == 42

    def test_frame_idx_preserved_in_dict(self):
        """frame_idx should be serialized back to dict."""
        esq = EsqueletoBiomecanico(frame_idx=17, keypoints133=REALISTIC_KP)
        d = esq.model_dump()
        assert "frame_idx" in d
        assert d["frame_idx"] == 17



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/domain/test_threshold_prompt_regression.py ---
"""
Tests de regresión para el fix del umbral y la estrategia de prompt (C12.5).

Cubre:
  - Fix 3.1: UMBRAL_ACEPTABLE = 85.0 (escala 0–100, no 0.85)
  - Fix 3.2: SpanishPromptStrategy incluye "FOTOGRAMA CRÍTICO" y pide articulaciones
"""
import pytest
from unittest.mock import Mock
from uuid import uuid4

from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter, GeminiApiAdapter
from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter, VectorSearchResultDTO
from corpocmente.domain.entities.models import EsqueletoBiomecanico
from corpocmente.domain.strategies.prompt_strategies import SpanishPromptStrategy


class TestUmbralAceptableEscala:
    """Regression tests para Fix 3.1: el umbral debe estar en escala 0–100."""

    def test_score_75_triggers_gemini(self):
        """
        Con score=75.0 (escala 0–100) la similitud está BAJO el umbral (85.0).
        Gemini DEBE ser invocado. Con el bug anterior (0.85), 75.0 >= 0.85
        era True → Gemini nunca se llamaba.
        """
        mock_yolo = Mock(spec=YOLOPoseAdapter)
        mock_qdrant = Mock(spec=QdrantVectorAdapter)
        mock_gemini = Mock(spec=GeminiApiAdapter)

        mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
        mock_esqueleto.to_vector_array.return_value = [0.5] * 133
        mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

        # Score 75 → bajo el umbral → Gemini debería invocarse
        mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
            score=75.0,
            frame_path="/tmp/frame.jpg",
            discrepancias=["Cadera alta"]
        )
        mock_yolo.dibujar_error_en_frame.return_value = "/tmp/resaltado.jpg"
        mock_gemini.generar_texto_feedback.return_value = "Feedback correctivo real."

        facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
        resultado = facade.ejecutar_analisis_completo("/tmp/video.mp4", uuid4(), "Armbar")

        # Gemini DEBE haber sido llamado
        mock_gemini.generar_texto_feedback.assert_called_once()
        assert resultado.feedback == "Feedback correctivo real."
        assert resultado.feedback != "¡Técnica ejecutada correctamente. Excelente trabajo!"

    def test_score_90_skips_gemini(self):
        """
        Con score=90.0, la similitud está SOBRE el umbral (85.0).
        Gemini NO debe ser invocado → respuesta genérica positiva.
        """
        mock_yolo = Mock(spec=YOLOPoseAdapter)
        mock_qdrant = Mock(spec=QdrantVectorAdapter)
        mock_gemini = Mock(spec=GeminiApiAdapter)

        mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
        mock_esqueleto.to_vector_array.return_value = [0.5] * 133
        mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

        mock_qdrant.buscar_maxima_diferencia.return_value = VectorSearchResultDTO(
            score=90.0,
            frame_path="/tmp/frame.jpg",
            discrepancias=[]
        )

        facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
        resultado = facade.ejecutar_analisis_completo("/tmp/video.mp4", uuid4(), "Armbar")

        mock_gemini.generar_texto_feedback.assert_not_called()
        assert "Excelente" in resultado.feedback or "correctamente" in resultado.feedback


class TestSpanishPromptStrategyEnhanced:
    """Regression tests para Fix 3.2: prompt mejorado con contexto de frame."""

    def test_prompt_contains_fotograma_critico(self):
        """El prompt debe mencionar 'FOTOGRAMA CRÍTICO' para dar contexto a Gemini."""
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            "Armbar desde guardia",
            ["Cadera alta", "Agarre suelto"]
        )
        assert "FOTOGRAMA CRÍTICO" in prompt

    def test_prompt_contains_tecnica_nombre(self):
        """El prompt debe incluir el nombre de la técnica."""
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion(
            "Triangle choke",
            ["Ángulo de pierna incorrecto"]
        )
        assert "Triangle choke" in prompt

    def test_prompt_lists_all_discrepancias(self):
        """Todas las discrepancias deben aparecer en el prompt."""
        strategy = SpanishPromptStrategy()
        discrepancias = ["Rodilla en 45°", "Cadera elevada", "Agarre débil"]
        prompt = strategy.construir_prompt_evaluacion("Omoplata", discrepancias)
        for d in discrepancias:
            assert d in prompt, f"Discrepancia '{d}' no encontrada en el prompt"

    def test_prompt_asks_for_articulacion(self):
        """El prompt mejorado debe pedir a Gemini que mencione articulaciones."""
        strategy = SpanishPromptStrategy()
        prompt = strategy.construir_prompt_evaluacion("Kimura", ["Hombro rotado"])
        assert "articulación" in prompt.lower()



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/infrastructure/__init__.py ---



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/infrastructure/test_gemini_adapter.py ---
import pytest
from unittest.mock import MagicMock, patch
from corpocmente.infrastructure.ai.adapters import GeminiApiAdapter, GeminiRateLimitError
from google.genai.errors import APIError

@pytest.fixture
def mock_genai_client():
    with patch("corpocmente.infrastructure.ai.adapters.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        yield mock_instance

def test_validar_es_jiujitsu_exitoso(mock_genai_client, tmp_path):
    # Crear un archivo de prueba temporal
    fake_video = tmp_path / "test_video.mp4"
    fake_video.write_bytes(b"fake video content")

    # Configurar Mocks
    mock_file = MagicMock()
    mock_file.name = "files/12345"
    mock_genai_client.files.upload.return_value = mock_file
    
    mock_response = MagicMock()
    mock_response.text = "SI, el video muestra un pasaje de guardia de Jiu-Jitsu."
    mock_genai_client.models.generate_content.return_value = mock_response

    adapter = GeminiApiAdapter(api_key="fake_key")
    es_valido = adapter.validar_es_jiujitsu(str(fake_video))

    assert es_valido is True
    mock_genai_client.files.upload.assert_called_once()
    mock_genai_client.files.delete.assert_called_once_with(name="files/12345")

def test_validar_es_jiujitsu_contenido_invalido(mock_genai_client, tmp_path):
    fake_video = tmp_path / "fake_dance.mp4"
    fake_video.write_bytes(b"fake content")

    mock_file = MagicMock(name="files/67890")
    mock_genai_client.files.upload.return_value = mock_file
    
    mock_response = MagicMock()
    mock_response.text = "NO, el video es un baile."
    mock_genai_client.models.generate_content.return_value = mock_response

    adapter = GeminiApiAdapter(api_key="fake_key")
    es_valido = adapter.validar_es_jiujitsu(str(fake_video))

    assert es_valido is False

def test_generar_texto_feedback_rate_limit(mock_genai_client, tmp_path):
    fake_frame = tmp_path / "frame.jpg"
    fake_frame.write_bytes(b"fake image data")

    import requests
    mock_requests_response = MagicMock(spec=requests.Response)
    mock_requests_response.json.return_value = {"error": {"message": "RESOURCE_EXHAUSTED", "code": 429}}
    api_error = APIError(code=429, response=mock_requests_response)
    mock_genai_client.models.generate_content.side_effect = api_error

    adapter = GeminiApiAdapter(api_key="fake_key")

    with pytest.raises(GeminiRateLimitError):
        adapter.generar_texto_feedback("Prompt de prueba", str(fake_frame))



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/infrastructure/test_qdrant_adapter.py ---
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter, VectorSearchResultDTO
from qdrant_client.models import ScoredPoint

@pytest.fixture
def mock_qdrant_client():
    client = MagicMock()
    # Simular que no existen colecciones
    mock_collection_description = MagicMock()
    mock_collection_description.name = "otras_colecciones"
    mock_collections_response = MagicMock()
    mock_collections_response.collections = [mock_collection_description]
    client.get_collections.return_value = mock_collections_response
    return client

def test_asegurar_coleccion_crea_nueva_coleccion(mock_qdrant_client):
    adapter = QdrantVectorAdapter(client=mock_qdrant_client, collection_name="vectores_jiujitsu")
    adapter.asegurar_coleccion(vector_size=133)

    mock_qdrant_client.create_collection.assert_called_once()

def test_insertar_vector_exitoso(mock_qdrant_client):
    adapter = QdrantVectorAdapter(client=mock_qdrant_client, collection_name="vectores_jiujitsu")
    vector_id = uuid4()
    vector = [0.1] * 133
    payload = {"tecnica_id": str(uuid4()), "frame_path": "/tmp/ref.jpg"}

    adapter.insertar_vector(vector_id, vector, payload)

    mock_qdrant_client.upsert.assert_called_once()

def test_buscar_similitud_pose_retorna_dto(mock_qdrant_client):
    adapter = QdrantVectorAdapter(client=mock_qdrant_client, collection_name="vectores_jiujitsu")
    tecnica_id = uuid4()
    vector_alumno = [0.5] * 133

    # Simular resultado de busqueda
    mock_scored_point = MagicMock(spec=ScoredPoint)
    mock_scored_point.score = 0.945
    mock_scored_point.payload = {
        "frame_path": "/tmp/maestro_pasaje.jpg",
        "discrepancias": ["Base de sustentación estrecha"]
    }
    mock_qdrant_client.search.return_value = [mock_scored_point]

    resultado = adapter.buscar_similitud_pose(vector_alumno, tecnica_id)

    assert isinstance(resultado, VectorSearchResultDTO)
    assert resultado.score == 94.5
    assert resultado.frame_path == "/tmp/maestro_pasaje.jpg"
    assert "Base de sustentación estrecha" in resultado.discrepancias
    mock_qdrant_client.search.assert_called_once()

def test_recuperar_contexto_rag_exitoso():
    from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter
    import uuid
    from unittest.mock import MagicMock
    
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.payload = {"contenido_texto": "El Jiu-Jitsu es un arte marcial..."}
    mock_client.search.return_value = [mock_result]
    
    adapter = QdrantVectorAdapter(client=mock_client)
    tecnica_id = uuid.uuid4()
    
    # Act
    texto = adapter.recuperar_contexto_rag([0.5]*2048, tecnica_id)
    
    # Assert
    assert texto == "El Jiu-Jitsu es un arte marcial..."
    mock_client.search.assert_called_once()

def test_recuperar_contexto_rag_usa_named_vector_y_concatena():
    """
    Regression test C11.4: recuperar_contexto_rag debe:
    1. Usar query_vector=("dense", vector) — named vector de la colección rag_knowledge.
    2. Solicitar limit=3 (top-3).
    3. Concatenar los chunks con el separador '\n\n---\n\n'.
    """
    from unittest.mock import MagicMock
    import uuid

    mock_client = MagicMock()
    # Simular 3 resultados con contenido
    r1 = MagicMock(); r1.payload = {"contenido_texto": "Chunk A sobre control de cadera."}
    r2 = MagicMock(); r2.payload = {"contenido_texto": "Chunk B sobre agarre del brazo."}
    r3 = MagicMock(); r3.payload = {"contenido_texto": "Chunk C sobre peso del cuerpo."}
    mock_client.search.return_value = [r1, r2, r3]

    adapter = QdrantVectorAdapter(client=mock_client)
    tecnica_id = uuid.uuid4()

    # Act
    texto = adapter.recuperar_contexto_rag([0.5] * 2048, tecnica_id)

    # Assert
    # 1. Debe llamar con named vector ("dense", ...) y limit=3
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["query_vector"] == ("dense", [0.5] * 2048), \
        "Debe usar named vector ('dense', vector) — fix C11.4"
    assert call_kwargs["limit"] == 3, "Debe solicitar top-3 (fix C11.4)"
    assert call_kwargs["collection_name"] == "rag_knowledge"

    # 2. Debe concatenar los 3 chunks
    assert "Chunk A" in texto
    assert "Chunk B" in texto
    assert "Chunk C" in texto
    assert "\n\n---\n\n" in texto, "Debe usar el separador '---' entre chunks"




--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/infrastructure/test_qdrant_maxdiff_regression.py ---
"""
Tests de regresión para buscar_maxima_diferencia (C12.5 Fix 2.1).

Verifica que el método reescrito:
  - Usa client.scroll() en vez de N queries individuales
  - Compara localmente con numpy (coseno)
  - Retorna el par alumno↔referencia con MENOR similitud
  - Score está en escala 0–100
"""
import pytest
import math
from unittest.mock import MagicMock, patch
from uuid import uuid4

from corpocmente.infrastructure.persistence.qdrant_adapter import (
    QdrantVectorAdapter,
    VectorSearchResultDTO,
)
from corpocmente.domain.entities.models import EsqueletoBiomecanico


# Vectores realistas (17 kp × 3 = 51 dims + 82 padding)
def _make_kp(seed: float) -> list[float]:
    """Genera un vector de 133 dims variando un seed."""
    import random
    rng = random.Random(int(seed * 1000))
    base = [rng.uniform(0.1, 0.9) for _ in range(51)]
    return base + [0.0] * 82


def _make_mock_point(vector: list[float], payload: dict):
    """Crea un mock de qdrant Record para scroll results."""
    p = MagicMock()
    p.vector = vector
    p.payload = payload
    return p


class TestBuscarMaximaDiferenciaScrollNumpy:

    def test_uses_scroll_not_search(self):
        """Debe usar client.scroll() una sola vez, no client.search() N veces."""
        mock_client = MagicMock()
        ref_vec = _make_kp(1.0)
        mock_client.scroll.return_value = (
            [_make_mock_point(ref_vec, {"frame_path": "/tmp/ref.jpg", "discrepancias": []})],
            None,
        )

        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")
        alumno = EsqueletoBiomecanico(keypoints133=_make_kp(2.0))

        adapter.buscar_maxima_diferencia([alumno], uuid4())

        mock_client.scroll.assert_called_once()
        mock_client.search.assert_not_called()

    def test_returns_worst_frame(self):
        """Debe retornar el par con MENOR similitud coseno."""
        mock_client = MagicMock()

        # Referencia: un solo vector
        ref_vec = _make_kp(1.0)
        mock_client.scroll.return_value = (
            [_make_mock_point(ref_vec, {
                "frame_path": "/tmp/ref_00010.jpg",
                "discrepancias": ["Cadera baja"],
            })],
            None,
        )

        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")

        # Alumno: dos frames, uno similar y otro muy diferente
        alumno_similar = EsqueletoBiomecanico(keypoints133=ref_vec[:])  # copia idéntica
        alumno_distinto = EsqueletoBiomecanico(keypoints133=_make_kp(99.0))

        result = adapter.buscar_maxima_diferencia(
            [alumno_similar, alumno_distinto], uuid4()
        )

        assert isinstance(result, VectorSearchResultDTO)
        # El score del frame idéntico sería ~100, el distinto será menor
        # Debe elegir el peor (menor score)
        assert result.score < 100.0

    def test_score_is_0_to_100_scale(self):
        """Score debe estar en escala 0–100 (no 0–1)."""
        mock_client = MagicMock()
        ref_vec = _make_kp(1.0)
        mock_client.scroll.return_value = (
            [_make_mock_point(ref_vec, {"frame_path": "", "discrepancias": []})],
            None,
        )

        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")
        alumno = EsqueletoBiomecanico(keypoints133=_make_kp(5.0))

        result = adapter.buscar_maxima_diferencia([alumno], uuid4())

        # Coseno similarity × 100 → debería estar entre 0 y 100
        assert 0.0 <= result.score <= 100.0, f"Score {result.score} fuera de rango 0–100"

    def test_raises_on_empty_references(self):
        """Debe lanzar ValueError si no hay referencias en Qdrant."""
        mock_client = MagicMock()
        mock_client.scroll.return_value = ([], None)

        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")
        alumno = EsqueletoBiomecanico(keypoints133=_make_kp(1.0))

        with pytest.raises(ValueError, match="No hay vectores de referencia"):
            adapter.buscar_maxima_diferencia([alumno], uuid4())

    def test_raises_on_empty_alumno_list(self):
        """Debe lanzar ValueError si la lista de esqueletos está vacía."""
        mock_client = MagicMock()
        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")

        with pytest.raises(ValueError, match="lista de esqueletos del alumno está vacía"):
            adapter.buscar_maxima_diferencia([], uuid4())

    def test_payload_propagated_to_result(self):
        """El frame_path y discrepancias del payload deben llegar al DTO."""
        mock_client = MagicMock()
        payload = {
            "frame_path": "/tmp/corpocmente_reference_frames/abc/ref_00025.jpg",
            "discrepancias": ["Rodilla en ángulo incorrecto", "Guardia abierta"],
        }
        mock_client.scroll.return_value = (
            [_make_mock_point(_make_kp(1.0), payload)],
            None,
        )

        adapter = QdrantVectorAdapter(client=mock_client, collection_name="test_col")
        alumno = EsqueletoBiomecanico(keypoints133=_make_kp(2.0))

        result = adapter.buscar_maxima_diferencia([alumno], uuid4())

        assert result.frame_path == payload["frame_path"]
        assert result.discrepancias == payload["discrepancias"]



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/infrastructure/test_qwen_adapter.py ---
import pytest
from unittest.mock import patch, MagicMock
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter

def test_qwen_embedding_adapter_fallback():
    # Arrange
    adapter = QwenEmbeddingAdapter(colab_url="")
    
    # Act
    embedding = adapter.generar_embedding("dummy_frame.jpg")
    
    # Assert
    assert len(embedding) == 2048
    assert embedding == [0.05] * 2048

@patch("corpocmente.infrastructure.ai.qwen_adapter.requests.post")
def test_qwen_embedding_adapter_colab_success(mock_post):
    # Arrange
    adapter = QwenEmbeddingAdapter(colab_url="http://fake-colab.com")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"embeddings": [[0.1] * 2048]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    # Act
    embedding = adapter.generar_embedding("dummy_frame.jpg")
    
    # Assert
    assert len(embedding) == 2048
    assert embedding == [0.1] * 2048
    mock_post.assert_called_once()

@patch("corpocmente.infrastructure.ai.qwen_adapter.requests.post")
def test_generar_embedding_texto_usa_form_data(mock_post):
    """
    Regression test C11.4: generar_embedding_texto debe enviar
    `data={"texto": ...}` (form-data) al Worker de Colab, NO `json={"text": ...}`.
    """
    # Arrange
    adapter = QwenEmbeddingAdapter(colab_url="http://fake-colab.com")
    mock_response = MagicMock()
    mock_response.json.return_value = {"embeddings": [[0.07] * 2048]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    # Act
    embedding = adapter.generar_embedding_texto("Teoría del Armbar")

    # Assert
    assert len(embedding) == 2048
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs

    # Debe usar `data=`, NO `json=`
    assert "data" in call_kwargs, "El fix C11.4 requiere enviar form-data (data=)"
    assert "json" not in call_kwargs, "El fix C11.4 prohíbe enviar JSON"
    assert call_kwargs["data"] == {"texto": "Teoría del Armbar"}, \
        "El campo debe llamarse 'texto' (como espera el endpoint /embed_text de FastAPI)"




--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/ui/__init__.py ---
"""UI tests package."""



--- ARCHIVO: ProyectoGrado/codigo_fuente/backend/tests/ui/api/__init__.py ---
"""API routes tests package."""



--- ARCHIVO: ProyectoGrado/codigo_fuente/data/Salida100kg.txt ---
1. La postura de supervivencia (Evitar el Knee on Belly)Para Saulo Ribeiro, el mayor peligro cuando estás atrapado en los 100 kg no es la posición en sí, sino permitir que el rival progrese a una posición más dominante como la montada o la rodilla al estómago (knee on belly).El bloqueo preventivo: Debes acostarte con el cuerpo ligeramente angulado de lado (hacia el oponente).Posición de los brazos: El brazo que está más cerca de las piernas del rival debe colocarse con el codo pegado a tu propio cuerpo y la mano bloqueando directamente la cadera o el muslo del oponente. Esto detiene en seco cualquier intento de que suban la rodilla a tu abdomen.No empujar desesperadamente: Saulo enfatiza firmemente que nunca debes empujar el pecho del rival con los brazos estirados. Esto solo expone tus extremidades a llaves de brazo (armbars) o sumisiones directas. El marco debe ser rígido pero con los codos pegados a ti.2. El escape de recuperación de guardia (Básico)Una vez que has estabilizado la presión y tu oponente no puede avanzar, aplicas el contraataque mecánico:Aliviar el Crossface: Si el rival tiene mucha presión sobre tu cuello, realiza un puente (upa) explosivo en diagonal hacia el hombro del rival. Esto no busca tirarlo, sino desplazar temporalmente su peso para quitar la presión de tu cabeza.Crear el espacio: Al bajar del puente, encoge la cadera hacia atrás con una fuga de cadera (shrimp).Introducir la rodilla: Aprovechando el centímetro de espacio creado, desliza tu rodilla de abajo (la más cercana a su cadera) directamente cruzando su estómago. Una vez que la rodilla entra como escudo, el control de 100 kg queda neutralizado y puedes recomponer la guardia completa o una guardia de mariposa.3. El escape en carrera (The Running Escape)Este es uno de los movimientos más famosos desarrollados y difundidos por Saulo Ribeiro. Se utiliza específicamente cuando el oponente te tiene completamente plano, bloqueando tu cabeza y tus piernas, impidiéndote girar hacia él para hacer la fuga de cadera tradicional.Girar en sentido contrario: En lugar de luchar para girar de frente al oponente, giras dándole la espalda (hacia el lado externo de sus piernas).Hacer el puente de hombro (Shoulder Bump): Utilizas las piernas para dar un fuerte impulso hacia arriba y hacia afuera, simulando una posición de "carrera" en el suelo (un brazo estirado hacia adelante y las piernas moviéndose como si corrieras).Proteger el brazo y el cuello: Aunque tu espalda queda expuesta por un instante, tu codo debe permanecer estrictamente conectado a tu pierna o costilla para evitar que metan ganchos. Tu cabeza va pegada al piso, lo que imposibilita que te estrangulen eficazmente.Pivote y Guardia: Usas el pie de apoyo para generar palanca, impulsarte hacia atrás, girar de frente rápidamente y meter al oponente directo en tu guardia.


--- ARCHIVO: ProyectoGrado/codigo_fuente/data/teoria_jiujitsu.txt ---
El pasaje de guardia en Jiu-Jitsu Brasileño requiere controlar las caderas y piernas del oponente para neutralizar sus defensas y establecer una posición superior como el control lateral o la montada.
Existen varias técnicas fundamentales para pasar la guardia:
1. Toreando Pass: Consiste en agarrar los pantalones del oponente a la altura de las rodillas, empujar sus piernas hacia un lado y avanzar hacia el lado opuesto para pasar la línea de defensa.
2. Knee Slice: Implica insertar una rodilla sobre el muslo del oponente, inmovilizando una de sus piernas mientras se desliza la cadera para consolidar el control lateral.
3. Stack Pass: Consiste en levantar las piernas del oponente, apilando su peso sobre su cuello y hombros para limitar su movilidad, y luego rodear su guardia para pasar al control lateral.
Es crucial mantener una base fuerte y evitar que el oponente recupere su guardia con la inserción de escudos de rodilla (knee shields) o lazos (lasso).
El control lateral (Side Control) se logra al inmovilizar la parte superior del torso del oponente, bloqueando su cadera y sus hombros contra el tatami.
Desde el control lateral, se puede transicionar a la montada (Mount) deslizando una rodilla sobre el abdomen del oponente y estabilizando el peso sobre su cadera.



--- ARCHIVO: ProyectoGrado/codigo_fuente/database/01_schema_3nf.sql ---
-- ==============================================================================
-- DISEÑO DE BASE DE DATOS HÍBRIDA (CAPA RELACIONAL) - ITERACIÓN C2
-- Metodología: Michael V. Mannino (Normalización 3NF / BCNF)
-- ==============================================================================

-- Habilitar extensión para UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Tabla: sucursales
CREATE TABLE sucursales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(50) NOT NULL,
    ciudad VARCHAR(50) NOT NULL,
    direccion VARCHAR(200),
    latitud NUMERIC(10, 7),
    longitud NUMERIC(10, 7),
    idioma_predeterminado VARCHAR(10) DEFAULT 'es',
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla: usuarios (Contiene alumnos, profesores y admins)
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sucursal_id UUID NOT NULL REFERENCES sucursales(id) ON DELETE RESTRICT,
    nombre_completo VARCHAR(150) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'profesor', 'alumno')),
    idioma_preferido VARCHAR(10) DEFAULT 'es',
    avatar_url TEXT,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla: tecnicas
CREATE TABLE tecnicas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL,
    nivel_cinturon VARCHAR(20) NOT NULL
);

-- 4. Tabla: videos_referencia (Videos base para comparar)
CREATE TABLE videos_referencia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tecnica_id UUID NOT NULL REFERENCES tecnicas(id) ON DELETE CASCADE,
    profesor_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    url_video_gcs VARCHAR(255) NOT NULL,
    duracion_segundos NUMERIC(5,2),
    vector_qdrant_id UUID UNIQUE NOT NULL,
    fecha_subida TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabla: evaluaciones_alumnos (Resultados de inferencia)
CREATE TABLE evaluaciones_alumnos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alumno_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tecnica_id UUID NOT NULL REFERENCES tecnicas(id) ON DELETE CASCADE,
    video_referencia_id UUID NOT NULL REFERENCES videos_referencia(id) ON DELETE CASCADE,
    url_video_alumno VARCHAR(255) NOT NULL,
    porcentaje_similitud NUMERIC(5,2),
    feedback_gemini_es TEXT,
    feedback_gemini_pt TEXT,
    vector_qdrant_id UUID UNIQUE,
    estado VARCHAR(30) NOT NULL DEFAULT 'procesando',
    fecha_evaluacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices adicionales para rendimiento
CREATE INDEX idx_usuarios_sucursal ON usuarios(sucursal_id);
CREATE INDEX idx_videos_referencia_tecnica ON videos_referencia(tecnica_id);
CREATE INDEX idx_evaluaciones_alumno ON evaluaciones_alumnos(alumno_id);



--- ARCHIVO: ProyectoGrado/codigo_fuente/database/02_auth_jwt.sql ---
-- ==============================================================================
-- AUTENTICACIÓN Y ROLES PARA POSTGREST - ITERACIÓN C2
-- ==============================================================================

-- Habilitar extensión pgcrypto para hash de contraseñas
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Crear roles de PostgREST
-- El rol authenticator es usado por la conexión de BD de PostgREST
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'mysecretpassword';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'alumno') THEN
        CREATE ROLE alumno NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'profesor') THEN
        CREATE ROLE profesor NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
        CREATE ROLE admin NOLOGIN;
    END IF;
END
$$;

GRANT anon TO authenticator;
GRANT alumno TO authenticator;
GRANT profesor TO authenticator;
GRANT admin TO authenticator;

-- 2. Estructura del JWT
CREATE TYPE jwt_token AS (
    token text
);

-- 3. Función de Autenticación (Login)
-- Busca por email O username para compatibilidad con el formulario de login del frontend.
CREATE OR REPLACE FUNCTION authenticate(
    email text,
    password text
) RETURNS jwt_token AS $$
DECLARE
    account usuarios;
    token_str text;
BEGIN
    SELECT a.* INTO account
    FROM usuarios AS a
    WHERE a.email = authenticate.email
       OR a.username = authenticate.email;

    IF account IS NULL THEN
        RETURN NULL;
    END IF;

    -- Verificar contraseña: bcrypt (producción)
    IF account.password_hash = crypt(password, account.password_hash)
    THEN
        token_str := format(
            '{"role": "%s", "email": "%s", "uid": "%s", "sucursal_id": "%s"}',
            account.rol,
            account.email,
            account.id,
            COALESCE(account.sucursal_id::text, '')
        );
        -- row() explícito para evitar "malformed record literal" en PostgREST
        RETURN row(token_str)::jwt_token;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Función de Registro (Signup)
CREATE OR REPLACE FUNCTION signup(
    nombre_completo text,
    email text,
    password text,
    rol text,
    sucursal_id uuid
) RETURNS void AS $$
BEGIN
    INSERT INTO usuarios (nombre_completo, email, password_hash, rol, sucursal_id)
    VALUES (
        signup.nombre_completo,
        signup.email,
        crypt(signup.password, gen_salt('bf')),
        signup.rol,
        signup.sucursal_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Permisos
GRANT EXECUTE ON FUNCTION authenticate(text, text) TO anon;
GRANT EXECUTE ON FUNCTION signup(text, text, text, text, uuid) TO anon;
GRANT USAGE ON SCHEMA public TO anon, alumno, profesor, admin;

-- 5. Función de Perfil (SECURITY DEFINER — lectura segura sin exponer la tabla usuarios a anon)
-- Usada por el backend tras la autenticación para obtener nombre_completo, username, avatar_url, etc.
DROP FUNCTION IF EXISTS get_user_profile(uuid);
CREATE FUNCTION get_user_profile(user_id uuid)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.nombre_completo, u.username, u.email, u.rol, u.avatar_url, u.sucursal_id
    FROM usuarios u
    WHERE u.id = get_user_profile.user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_user_profile(uuid) TO anon;

-- anon puede leer sucursales para mostrar el nombre de la sucursal al hacer login
GRANT SELECT ON sucursales TO anon;
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename='sucursales' AND policyname='anon_read_sucursales'
  ) THEN
    CREATE POLICY anon_read_sucursales ON sucursales FOR SELECT TO anon USING (true);
  END IF;
END $$;

-- ==============================================================================
-- C10.3 — REVERTIR regresión de seguridad introducida por Task 5
-- El rol anon NO debe leer la tabla usuarios directamente.
-- Todo acceso se hace por funciones SECURITY DEFINER.
-- ==============================================================================

REVOKE SELECT ON usuarios FROM anon;
DROP POLICY IF EXISTS anon_read_usuarios ON usuarios;

-- ==============================================================================
-- RPCs ADMIN (SECURITY DEFINER) — la validación de rol admin se hace en Python
-- ==============================================================================

-- 1. Listar todos los usuarios con nombre de sucursal
DROP FUNCTION IF EXISTS admin_list_users();
CREATE OR REPLACE FUNCTION admin_list_users()
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid,
    sucursal_nombre varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        u.email,
        u.rol,
        u.avatar_url,
        u.sucursal_id,
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    ORDER BY u.fecha_registro;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_users() TO anon;

-- 2. Obtener un usuario por ID (con sucursal)
DROP FUNCTION IF EXISTS admin_get_user_full(uuid);
CREATE OR REPLACE FUNCTION admin_get_user_full(p_user_id uuid)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid,
    sucursal_nombre varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        u.email,
        u.rol,
        u.avatar_url,
        u.sucursal_id,
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_get_user_full(uuid) TO anon;

-- 3. Actualizar un usuario (hash de password dentro de la función)
DROP FUNCTION IF EXISTS admin_update_user(uuid, text, text, text);
CREATE OR REPLACE FUNCTION admin_update_user(
    p_user_id uuid,
    p_nombre text DEFAULT NULL,
    p_password text DEFAULT NULL,
    p_avatar_url text DEFAULT NULL
)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid,
    sucursal_nombre varchar
) AS $$
BEGIN
    UPDATE usuarios u2
    SET
        nombre_completo = COALESCE(p_nombre, u2.nombre_completo),
        password_hash = CASE
            WHEN p_password IS NOT NULL AND p_password <> ''
            THEN crypt(p_password, gen_salt('bf'))
            ELSE u2.password_hash
        END,
        avatar_url = COALESCE(p_avatar_url, u2.avatar_url)
    WHERE u2.id = p_user_id;

    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        u.email,
        u.rol,
        u.avatar_url,
        u.sucursal_id,
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_update_user(uuid, text, text, text) TO anon;

-- 4. Listar profesores (con filtro opcional por sucursal)
DROP FUNCTION IF EXISTS admin_list_profesores(uuid);
CREATE OR REPLACE FUNCTION admin_list_profesores(p_sucursal_id uuid DEFAULT NULL)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    avatar_url text,
    sucursal_id uuid,
    sucursal_nombre varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        u.email,
        u.avatar_url,
        u.sucursal_id,
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.rol = 'profesor'
      AND (p_sucursal_id IS NULL OR u.sucursal_id = p_sucursal_id)
    ORDER BY u.fecha_registro;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_profesores(uuid) TO anon;

-- 5. Signup público (hash de password dentro de la función)
DROP FUNCTION IF EXISTS public_signup(text, text, text, text, text, uuid);
CREATE OR REPLACE FUNCTION public_signup(
    p_nombre_completo text,
    p_username text,
    p_email text,
    p_password text,
    p_rol text,
    p_sucursal_id uuid
)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid
) AS $$
DECLARE
    new_id uuid;
BEGIN
    INSERT INTO usuarios (nombre_completo, username, email, password_hash, rol, sucursal_id)
    VALUES (
        p_nombre_completo,
        p_username,
        p_email,
        crypt(p_password, gen_salt('bf')),
        p_rol,
        p_sucursal_id
    )
    RETURNING usuarios.id INTO new_id;

    RETURN QUERY
    SELECT u.id, u.nombre_completo, u.username, u.email, u.rol, u.avatar_url, u.sucursal_id
    FROM usuarios u
    WHERE u.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public_signup(text, text, text, text, text, uuid) TO anon;

-- ==============================================================================
-- C10.4 — RPCs ADMIN para CRUD de Sucursales
-- Migra las operaciones de escritura de la tabla sucursales a SECURITY DEFINER
-- para que no dependan del rol anon (que NO tiene INSERT/UPDATE/DELETE).
-- ==============================================================================

-- 1. Crear sucursal
DROP FUNCTION IF EXISTS admin_create_sucursal(text, text, text, text, numeric, numeric);
CREATE OR REPLACE FUNCTION admin_create_sucursal(
    p_nombre text,
    p_pais text,
    p_ciudad text,
    p_direccion text,
    p_latitud numeric,
    p_longitud numeric
)
RETURNS TABLE(
    id uuid,
    nombre varchar,
    pais varchar,
    ciudad varchar,
    direccion varchar,
    latitud numeric,
    longitud numeric
) AS $$
DECLARE
    new_id uuid;
BEGIN
    INSERT INTO sucursales (nombre, pais, ciudad, direccion, latitud, longitud)
    VALUES (p_nombre, p_pais, p_ciudad, p_direccion, p_latitud, p_longitud)
    RETURNING sucursales.id INTO new_id;

    RETURN QUERY
    SELECT s.id, s.nombre, s.pais, s.ciudad, s.direccion, s.latitud, s.longitud
    FROM sucursales s
    WHERE s.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_create_sucursal(text, text, text, text, numeric, numeric) TO anon;

-- 2. Actualizar sucursal
DROP FUNCTION IF EXISTS admin_update_sucursal(uuid, text, text, text, text, numeric, numeric);
CREATE OR REPLACE FUNCTION admin_update_sucursal(
    p_sucursal_id uuid,
    p_nombre text,
    p_pais text,
    p_ciudad text,
    p_direccion text,
    p_latitud numeric,
    p_longitud numeric
)
RETURNS TABLE(
    id uuid,
    nombre varchar,
    pais varchar,
    ciudad varchar,
    direccion varchar,
    latitud numeric,
    longitud numeric
) AS $$
BEGIN
    UPDATE sucursales
    SET
        nombre = p_nombre,
        pais = p_pais,
        ciudad = p_ciudad,
        direccion = p_direccion,
        latitud = p_latitud,
        longitud = p_longitud
    WHERE sucursales.id = p_sucursal_id;

    RETURN QUERY
    SELECT s.id, s.nombre, s.pais, s.ciudad, s.direccion, s.latitud, s.longitud
    FROM sucursales s
    WHERE s.id = p_sucursal_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_update_sucursal(uuid, text, text, text, text, numeric, numeric) TO anon;

-- 3. Contar usuarios en una sucursal (evita que anon lea la tabla usuarios)
DROP FUNCTION IF EXISTS admin_count_users_in_sucursal(uuid);
CREATE OR REPLACE FUNCTION admin_count_users_in_sucursal(p_sucursal_id uuid)
RETURNS bigint AS $$
DECLARE
    cnt bigint;
BEGIN
    SELECT COUNT(*) INTO cnt
    FROM usuarios
    WHERE sucursal_id = p_sucursal_id;
    RETURN cnt;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_count_users_in_sucursal(uuid) TO anon;

-- 4. Eliminar sucursal (valida que no tenga usuarios dentro de la función)
DROP FUNCTION IF EXISTS admin_delete_sucursal(uuid);
CREATE OR REPLACE FUNCTION admin_delete_sucursal(p_sucursal_id uuid)
RETURNS boolean AS $$
DECLARE
    user_count bigint;
    deleted_count int;
BEGIN
    SELECT COUNT(*) INTO user_count
    FROM usuarios
    WHERE sucursal_id = p_sucursal_id;

    IF user_count > 0 THEN
        RAISE EXCEPTION 'SUCURSAL_CON_USUARIOS: La sucursal tiene % usuarios vinculados.', user_count;
    END IF;

    DELETE FROM sucursales WHERE id = p_sucursal_id;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_delete_sucursal(uuid) TO anon;

-- ==============================================================================
-- C10.5 — RPCs para el flujo de evaluaciones (usuario)
-- Migra lecturas/escrituras de videos_referencia y evaluaciones_alumnos
-- a funciones SECURITY DEFINER.
-- ==============================================================================

-- 1. Buscar video de referencia para una técnica
DROP FUNCTION IF EXISTS get_video_referencia_by_tecnica(uuid);
CREATE OR REPLACE FUNCTION get_video_referencia_by_tecnica(p_tecnica_id uuid)
RETURNS TABLE(
    id uuid,
    url_video_gcs varchar,
    profesor_id uuid
) AS $$
BEGIN
    RETURN QUERY
    SELECT vr.id, vr.url_video_gcs, vr.profesor_id
    FROM videos_referencia vr
    WHERE vr.tecnica_id = p_tecnica_id
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_video_referencia_by_tecnica(uuid) TO anon;

-- 2. Crear evaluación de alumno
DROP FUNCTION IF EXISTS create_evaluacion(uuid, uuid, uuid, uuid, text);
CREATE OR REPLACE FUNCTION create_evaluacion(
    p_id uuid,
    p_alumno_id uuid,
    p_tecnica_id uuid,
    p_video_referencia_id uuid,
    p_url_video_alumno text
)
RETURNS TABLE(
    id uuid,
    alumno_id uuid,
    tecnica_id uuid,
    video_referencia_id uuid,
    url_video_alumno varchar,
    estado varchar
) AS $$
BEGIN
    INSERT INTO evaluaciones_alumnos (
        id, alumno_id, tecnica_id, video_referencia_id, url_video_alumno, estado
    )
    VALUES (
        p_id, p_alumno_id, p_tecnica_id, p_video_referencia_id, p_url_video_alumno, 'procesando'
    );

    RETURN QUERY
    SELECT e.id, e.alumno_id, e.tecnica_id, e.video_referencia_id, e.url_video_alumno, e.estado
    FROM evaluaciones_alumnos e
    WHERE e.id = p_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION create_evaluacion(uuid, uuid, uuid, uuid, text) TO anon;

-- 3. Obtener evaluación por id (con nombre de técnica y video de referencia del profesor)
DROP FUNCTION IF EXISTS get_evaluacion_by_id(uuid);
CREATE OR REPLACE FUNCTION get_evaluacion_by_id(p_evaluacion_id uuid)
RETURNS TABLE(
    id uuid,
    alumno_id uuid,
    tecnica_id uuid,
    tecnica_nombre varchar,
    estado varchar,
    porcentaje_similitud numeric,
    feedback_gemini_es text,
    feedback_gemini_pt text,
    video_referencia_url varchar,
    video_referencia_profesor_nombre varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.alumno_id,
        e.tecnica_id,
        COALESCE(t.nombre, 'Técnica')::varchar AS tecnica_nombre,
        e.estado,
        e.porcentaje_similitud,
        e.feedback_gemini_es,
        e.feedback_gemini_pt,
        COALESCE(vr.url_video_gcs, '')::varchar AS video_referencia_url,
        COALESCE(u_prof.nombre_completo, 'Profesor')::varchar AS video_referencia_profesor_nombre
    FROM evaluaciones_alumnos e
    LEFT JOIN tecnicas t ON t.id = e.tecnica_id
    LEFT JOIN videos_referencia vr ON vr.id = e.video_referencia_id
    LEFT JOIN usuarios u_prof ON u_prof.id = vr.profesor_id
    WHERE e.id = p_evaluacion_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_evaluacion_by_id(uuid) TO anon;

-- ==============================================================================
-- C10.6 — RPC para listar técnicas con su video de referencia
-- ==============================================================================

DROP FUNCTION IF EXISTS get_tecnicas_with_videos();
CREATE OR REPLACE FUNCTION get_tecnicas_with_videos()
RETURNS TABLE(
    id uuid,
    nombre varchar,
    nivel_cinturon varchar,
    video_id uuid,
    video_profesor_id uuid,
    video_url varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.nombre,
        t.nivel_cinturon,
        vr.id AS video_id,
        vr.profesor_id AS video_profesor_id,
        vr.url_video_gcs AS video_url
    FROM tecnicas t
    LEFT JOIN videos_referencia vr ON vr.tecnica_id = t.id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_tecnicas_with_videos() TO anon;

-- Verificar técnica existe (para subir_video_referencia)
DROP FUNCTION IF EXISTS tecnica_exists(uuid);
CREATE OR REPLACE FUNCTION tecnica_exists(p_tecnica_id uuid)
RETURNS boolean AS $$
DECLARE
    cnt bigint;
BEGIN
    SELECT COUNT(*) INTO cnt FROM tecnicas WHERE id = p_tecnica_id;
    RETURN cnt > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION tecnica_exists(uuid) TO anon;

-- ==============================================================================
-- C10.7 — RPCs para CRUD de técnicas y videos de referencia
-- Migra operaciones de escritura que fallan por RLS con anon.
-- ==============================================================================

-- 1. Crear técnica
DROP FUNCTION IF EXISTS admin_create_tecnica(text, text);
CREATE OR REPLACE FUNCTION admin_create_tecnica(
    p_nombre text,
    p_nivel_cinturon text
)
RETURNS TABLE(id uuid, nombre varchar, nivel_cinturon varchar) AS $$
DECLARE
    new_id uuid;
BEGIN
    INSERT INTO tecnicas (nombre, nivel_cinturon)
    VALUES (p_nombre, p_nivel_cinturon)
    RETURNING tecnicas.id INTO new_id;

    RETURN QUERY
    SELECT t.id, t.nombre, t.nivel_cinturon FROM tecnicas t WHERE t.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_create_tecnica(text, text) TO anon;

-- 2. Actualizar técnica
DROP FUNCTION IF EXISTS admin_update_tecnica(uuid, text, text);
CREATE OR REPLACE FUNCTION admin_update_tecnica(
    p_tecnica_id uuid,
    p_nombre text,
    p_nivel_cinturon text
)
RETURNS TABLE(id uuid, nombre varchar, nivel_cinturon varchar) AS $$
BEGIN
    UPDATE tecnicas
    SET nombre = p_nombre, nivel_cinturon = p_nivel_cinturon
    WHERE tecnicas.id = p_tecnica_id;

    RETURN QUERY
    SELECT t.id, t.nombre, t.nivel_cinturon FROM tecnicas t WHERE t.id = p_tecnica_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_update_tecnica(uuid, text, text) TO anon;

-- 3. Eliminar técnica
DROP FUNCTION IF EXISTS admin_delete_tecnica(uuid);
CREATE OR REPLACE FUNCTION admin_delete_tecnica(p_tecnica_id uuid)
RETURNS boolean AS $$
DECLARE
    deleted_count int;
BEGIN
    DELETE FROM tecnicas WHERE id = p_tecnica_id;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_delete_tecnica(uuid) TO anon;

-- 4. Guardar (upsert) video de referencia de un profesor para una técnica
DROP FUNCTION IF EXISTS admin_save_video_referencia(uuid, uuid, text);
CREATE OR REPLACE FUNCTION admin_save_video_referencia(
    p_tecnica_id uuid,
    p_profesor_id uuid,
    p_url_video text
)
RETURNS TABLE(video_id uuid) AS $$
DECLARE
    new_id uuid;
BEGIN
    -- Borrar si existía para esta técnica + profesor
    DELETE FROM videos_referencia
    WHERE tecnica_id = p_tecnica_id AND profesor_id = p_profesor_id;

    INSERT INTO videos_referencia (tecnica_id, profesor_id, url_video_gcs, vector_qdrant_id)
    VALUES (p_tecnica_id, p_profesor_id, p_url_video, uuid_generate_v4())
    RETURNING videos_referencia.id INTO new_id;

    RETURN QUERY SELECT new_id AS video_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_save_video_referencia(uuid, uuid, text) TO anon;

-- 5. Listar alumnos de una sucursal (para el panel del profesor)
DROP FUNCTION IF EXISTS admin_list_alumnos(uuid);
CREATE OR REPLACE FUNCTION admin_list_alumnos(p_sucursal_id uuid DEFAULT NULL)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    avatar_url text,
    sucursal_id uuid,
    sucursal_nombre varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        u.email,
        u.avatar_url,
        u.sucursal_id,
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.rol = 'alumno'
      AND (p_sucursal_id IS NULL OR u.sucursal_id = p_sucursal_id)
    ORDER BY u.fecha_registro;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_alumnos(uuid) TO anon;

-- ==============================================================================
-- C10.8 — RPC para listar evaluaciones de un alumno (panel del profesor)
-- ==============================================================================

DROP FUNCTION IF EXISTS admin_list_evaluaciones_alumno(uuid);
CREATE OR REPLACE FUNCTION admin_list_evaluaciones_alumno(p_alumno_id uuid)
RETURNS TABLE(
    id uuid,
    tecnica_nombre varchar,
    porcentaje_similitud numeric,
    estado varchar,
    feedback_gemini_es text,
    feedback_gemini_pt text,
    fecha_evaluacion timestamp with time zone
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        COALESCE(t.nombre, 'Técnica')::varchar AS tecnica_nombre,
        e.porcentaje_similitud,
        e.estado,
        e.feedback_gemini_es,
        e.feedback_gemini_pt,
        e.fecha_evaluacion
    FROM evaluaciones_alumnos e
    LEFT JOIN tecnicas t ON t.id = e.tecnica_id
    WHERE e.alumno_id = p_alumno_id
    ORDER BY e.fecha_evaluacion DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_evaluaciones_alumno(uuid) TO anon;

-- ==============================================================================
-- C10.9 — RPCs para el Worker de Colab
-- Migra las operaciones del worker (polling, update de estado) a SECURITY DEFINER.
-- El worker se autentica con X-Worker-Token en FastAPI, no con JWT de usuario.
-- ==============================================================================

-- 1. Obtener la siguiente evaluación pendiente y marcarla como en progreso (atómico)
DROP FUNCTION IF EXISTS worker_claim_next_pending();
CREATE OR REPLACE FUNCTION worker_claim_next_pending()
RETURNS TABLE(
    id uuid,
    video_path varchar,
    tecnica_id uuid,
    tecnica_nombre varchar,
    estado varchar
) AS $$
DECLARE
    claimed_id uuid;
BEGIN
    -- Bloqueo para evitar doble asignación
    SELECT e.id INTO claimed_id
    FROM evaluaciones_alumnos e
    WHERE e.estado = 'procesando'
    ORDER BY e.fecha_evaluacion ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    IF claimed_id IS NULL THEN
        RETURN;
    END IF;

    UPDATE evaluaciones_alumnos
    SET estado = 'en_progreso_worker'
    WHERE id = claimed_id;

    RETURN QUERY
    SELECT
        e.id,
        e.url_video_alumno,
        e.tecnica_id,
        COALESCE(t.nombre, 'Técnica')::varchar AS tecnica_nombre,
        e.estado
    FROM evaluaciones_alumnos e
    LEFT JOIN tecnicas t ON t.id = e.tecnica_id
    WHERE e.id = claimed_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION worker_claim_next_pending() TO anon;

-- 2. Obtener el video_path de una evaluación (para que el worker lo descargue)
DROP FUNCTION IF EXISTS worker_get_video_path(uuid);
CREATE OR REPLACE FUNCTION worker_get_video_path(p_evaluacion_id uuid)
RETURNS TABLE(video_path varchar) AS $$
BEGIN
    RETURN QUERY
    SELECT e.url_video_alumno
    FROM evaluaciones_alumnos e
    WHERE e.id = p_evaluacion_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION worker_get_video_path(uuid) TO anon;

-- 3. Actualizar el resultado de una evaluación (usado por el worker)
DROP FUNCTION IF EXISTS worker_update_result(uuid, numeric, text, text);
CREATE OR REPLACE FUNCTION worker_update_result(
    p_evaluacion_id uuid,
    p_similitud numeric,
    p_feedback_es text,
    p_estado text
)
RETURNS boolean AS $$
DECLARE
    updated_count int;
BEGIN
    UPDATE evaluaciones_alumnos
    SET
        porcentaje_similitud = p_similitud,
        feedback_gemini_es = p_feedback_es,
        estado = p_estado
    WHERE id = p_evaluacion_id;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION worker_update_result(uuid, numeric, text, text) TO anon;

-- ==============================================================================
-- C12.7 — RPC para obtener el video de referencia de un profesor específico
-- Reemplaza el uso genérico de get_video_referencia_by_tecnica cuando el alumno
-- ha seleccionado explícitamente un profesor en el frontend.
-- ==============================================================================

DROP FUNCTION IF EXISTS get_video_referencia_by_tecnica_profesor(uuid, uuid);
CREATE OR REPLACE FUNCTION get_video_referencia_by_tecnica_profesor(
    p_tecnica_id uuid,
    p_profesor_id uuid
)
RETURNS TABLE(
    id uuid,
    url_video_gcs varchar,
    profesor_id uuid
) AS $$
BEGIN
    RETURN QUERY
    SELECT vr.id, vr.url_video_gcs, vr.profesor_id
    FROM videos_referencia vr
    WHERE vr.tecnica_id = p_tecnica_id
      AND vr.profesor_id = p_profesor_id
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_video_referencia_by_tecnica_profesor(uuid, uuid) TO anon;



--- ARCHIVO: ProyectoGrado/codigo_fuente/database/03_rls_policies.sql ---
-- ==============================================================================
-- POLÍTICAS DE SEGURIDAD A NIVEL DE FILA (ROW LEVEL SECURITY - RLS)
-- Iteración C2 - Aislamiento Multi-Tenant y Privacidad de Usuario
-- ==============================================================================

-- 1. Habilitar RLS en todas las tablas
ALTER TABLE sucursales ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE tecnicas ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos_referencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluaciones_alumnos ENABLE ROW LEVEL SECURITY;

-- 2. Políticas para 'sucursales'
-- Todos los usuarios autenticados pueden ver sucursales
CREATE POLICY "Sucursales visibles para todos los autenticados" 
ON sucursales FOR SELECT 
TO alumno, profesor, admin 
USING (true);

-- 3. Políticas para 'usuarios'
-- Alumnos solo pueden ver su propio perfil
CREATE POLICY "Alumnos ven su propio perfil" 
ON usuarios FOR SELECT 
TO alumno 
USING (id = current_setting('request.jwt.claim.uid', true)::uuid);

-- Profesores pueden ver perfiles de su propia sucursal
CREATE POLICY "Profesores ven usuarios de su sucursal" 
ON usuarios FOR SELECT 
TO profesor 
USING (sucursal_id = current_setting('request.jwt.claim.sucursal_id', true)::uuid);

-- 4. Políticas para 'tecnicas'
-- Técnicas son públicas para consulta
CREATE POLICY "Tecnicas publicas para consulta" 
ON tecnicas FOR SELECT 
TO alumno, profesor, admin 
USING (true);

-- 5. Políticas para 'videos_referencia'
-- Todos pueden consultar videos de referencia
CREATE POLICY "Videos de referencia visibles para consulta" 
ON videos_referencia FOR SELECT 
TO alumno, profesor, admin 
USING (true);

-- Profesores pueden insertar videos de referencia para su sucursal
CREATE POLICY "Profesores pueden insertar videos" 
ON videos_referencia FOR INSERT 
TO profesor 
WITH CHECK (profesor_id = current_setting('request.jwt.claim.uid', true)::uuid);

-- 6. Políticas para 'evaluaciones_alumnos'
-- Alumnos solo pueden ver y crear sus propias evaluaciones
CREATE POLICY "Alumnos gestionan sus evaluaciones" 
ON evaluaciones_alumnos FOR ALL 
TO alumno 
USING (alumno_id = current_setting('request.jwt.claim.uid', true)::uuid)
WITH CHECK (alumno_id = current_setting('request.jwt.claim.uid', true)::uuid);

-- Profesores pueden ver evaluaciones de los alumnos de su sucursal
CREATE POLICY "Profesores ven evaluaciones de su sucursal" 
ON evaluaciones_alumnos FOR SELECT 
TO profesor 
USING (
    EXISTS (
        SELECT 1 FROM usuarios u 
        WHERE u.id = evaluaciones_alumnos.alumno_id 
        AND u.sucursal_id = current_setting('request.jwt.claim.sucursal_id', true)::uuid
    )
);

-- 7. Políticas de Administrador (Total Access)
CREATE POLICY "Admins full access sucursales" ON sucursales FOR ALL TO admin USING (true);
CREATE POLICY "Admins full access usuarios" ON usuarios FOR ALL TO admin USING (true);
CREATE POLICY "Admins full access tecnicas" ON tecnicas FOR ALL TO admin USING (true);
CREATE POLICY "Admins full access videos" ON videos_referencia FOR ALL TO admin USING (true);
CREATE POLICY "Admins full access evaluaciones" ON evaluaciones_alumnos FOR ALL TO admin USING (true);

-- 8. Otorgar permisos CRUD básicos sobre las tablas a los roles (RLS se encarga del filtrado)
GRANT SELECT ON sucursales, tecnicas, videos_referencia TO alumno, profesor;
GRANT SELECT, UPDATE ON usuarios TO alumno, profesor;
GRANT SELECT, INSERT ON evaluaciones_alumnos TO alumno;
GRANT SELECT, INSERT, UPDATE, DELETE ON videos_referencia TO profesor;
GRANT ALL ON sucursales, usuarios, tecnicas, videos_referencia, evaluaciones_alumnos TO admin;



--- ARCHIVO: ProyectoGrado/codigo_fuente/database/04_seed_data.sql ---
-- Sucursal semilla
INSERT INTO sucursales (id, nombre, pais, ciudad, direccion, latitud, longitud, idioma_predeterminado)
VALUES (
  '8b315b4e-43f2-4ca1-904d-dec87242f347',
  'JIU JITSU CORPO E MENTE MIGUEL BAIGORRIA',
  'Bolivia',
  'Santa Cruz de la Sierra',
  'Avenida Cristóbal de Mendoza',
  -17.7702061,
  -63.1699065,
  'es'
) ON CONFLICT DO NOTHING;

-- Usuario admin
INSERT INTO usuarios (id, sucursal_id, nombre_completo, username, email, password_hash, rol, idioma_preferido)
VALUES (
  '00000000-0000-0000-0000-000000000000',
  '8b315b4e-43f2-4ca1-904d-dec87242f347',
  'Administrador General',
  'admin',
  'admin@corpocmente.com',
  crypt('admin123', gen_salt('bf')),
  'admin',
  'es'
) ON CONFLICT DO NOTHING;

-- Usuario profesor
INSERT INTO usuarios (id, sucursal_id, nombre_completo, username, email, password_hash, rol, idioma_preferido)
VALUES (
  '7e455a7d-cbc8-4190-9a10-3b959f6425fc',
  '8b315b4e-43f2-4ca1-904d-dec87242f347',
  'Mestre Mike Baigorria',
  'mike',
  'mike@corpocmente.com',
  crypt('password123', gen_salt('bf')),
  'profesor',
  'es'
) ON CONFLICT DO NOTHING;

-- Usuario alumno
INSERT INTO usuarios (id, sucursal_id, nombre_completo, username, email, password_hash, rol, idioma_preferido)
VALUES (
  'bce12c1c-91f1-4bfb-813b-a18c5426b51e',
  '8b315b4e-43f2-4ca1-904d-dec87242f347',
  'Santi',
  'santi',
  'santi@corpocmente.com',
  crypt('password123', gen_salt('bf')),
  'alumno',
  'es'
) ON CONFLICT DO NOTHING;

-- Técnicas semilla
INSERT INTO tecnicas (id, nombre, nivel_cinturon) VALUES
  ('d3b07384-d9a4-4f6c-947b-11347076a5b6', 'Armbar (Llave de Brazo)', 'Blanco'),
  ('e8b15394-d9a4-4f6c-947b-11347076a5b7', 'Triângulo', 'Blanco'),
  ('a1b2c3d4-e5f6-4a5b-8c9d-0123456789ab', 'Salir de 100 kilos', 'Blanco')
ON CONFLICT DO NOTHING;



--- ARCHIVO: ProyectoGrado/codigo_fuente/database/05_teoria_referencia.sql ---
-- ==============================================================================
-- C11.0 — Tabla de teoría de referencia (chunks RAG con trazabilidad relacional)
-- Cada fila representa un chunk que fue vectorizado y persistido en Qdrant.
-- El campo qdrant_point_id permite trazabilidad bidireccional Postgres <-> Qdrant.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS teoria_referencia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tecnica_id UUID NOT NULL REFERENCES tecnicas(id) ON DELETE CASCADE,
    profesor_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    sucursal_id UUID NOT NULL REFERENCES sucursales(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    contenido_texto TEXT NOT NULL,
    qdrant_point_id UUID UNIQUE NOT NULL,
    fecha_ingesta TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_teoria_tecnica ON teoria_referencia(tecnica_id);
CREATE INDEX IF NOT EXISTS idx_teoria_profesor ON teoria_referencia(profesor_id);
CREATE INDEX IF NOT EXISTS idx_teoria_sucursal ON teoria_referencia(sucursal_id);

-- RLS: anon no tiene acceso directo. Todo se hace vía RPC SECURITY DEFINER.
ALTER TABLE teoria_referencia ENABLE ROW LEVEL SECURITY;

-- RPC: Registrar un chunk de teoría (llamada desde el backend)
DROP FUNCTION IF EXISTS admin_save_teoria_chunk(uuid, uuid, uuid, int, text, uuid);
CREATE OR REPLACE FUNCTION admin_save_teoria_chunk(
    p_tecnica_id uuid,
    p_profesor_id uuid,
    p_sucursal_id uuid,
    p_chunk_index int,
    p_contenido_texto text,
    p_qdrant_point_id uuid
)
RETURNS TABLE(
    id uuid,
    tecnica_id uuid,
    profesor_id uuid,
    chunk_index int,
    fecha_ingesta timestamp with time zone
) AS $$
DECLARE
    new_id uuid;
BEGIN
    INSERT INTO teoria_referencia (
        tecnica_id, profesor_id, sucursal_id, chunk_index,
        contenido_texto, qdrant_point_id
    )
    VALUES (
        p_tecnica_id, p_profesor_id, p_sucursal_id, p_chunk_index,
        p_contenido_texto, p_qdrant_point_id
    )
    RETURNING teoria_referencia.id INTO new_id;

    RETURN QUERY
    SELECT t.id, t.tecnica_id, t.profesor_id, t.chunk_index, t.fecha_ingesta
    FROM teoria_referencia t
    WHERE t.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_save_teoria_chunk(uuid, uuid, uuid, int, text, uuid) TO anon;

-- RPC: Listar chunks de una técnica (para que el profesor vea lo que subió)
DROP FUNCTION IF EXISTS admin_list_teoria_by_tecnica(uuid);
CREATE OR REPLACE FUNCTION admin_list_teoria_by_tecnica(p_tecnica_id uuid)
RETURNS TABLE(
    id uuid,
    chunk_index int,
    contenido_texto text,
    qdrant_point_id uuid,
    profesor_id uuid,
    profesor_nombre varchar,
    sucursal_id uuid,
    fecha_ingesta timestamp with time zone
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.chunk_index,
        t.contenido_texto,
        t.qdrant_point_id,
        t.profesor_id,
        COALESCE(u.nombre_completo, 'Profesor Eliminado')::varchar AS profesor_nombre,
        t.sucursal_id,
        t.fecha_ingesta
    FROM teoria_referencia t
    LEFT JOIN usuarios u ON u.id = t.profesor_id
    WHERE t.tecnica_id = p_tecnica_id
    ORDER BY t.fecha_ingesta DESC, t.chunk_index ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_teoria_by_tecnica(uuid) TO anon;

-- RPC: Eliminar todos los chunks de teoría de una técnica + profesor
DROP FUNCTION IF EXISTS admin_delete_teoria_by_tecnica_profesor(uuid, uuid);
CREATE OR REPLACE FUNCTION admin_delete_teoria_by_tecnica_profesor(
    p_tecnica_id uuid,
    p_profesor_id uuid
)
RETURNS TABLE(deleted_qdrant_ids uuid[]) AS $$
DECLARE
    ids uuid[];
BEGIN
    SELECT array_agg(qdrant_point_id) INTO ids
    FROM teoria_referencia
    WHERE tecnica_id = p_tecnica_id AND profesor_id = p_profesor_id;

    DELETE FROM teoria_referencia
    WHERE tecnica_id = p_tecnica_id AND profesor_id = p_profesor_id;

    RETURN QUERY SELECT COALESCE(ids, ARRAY[]::uuid[]);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_delete_teoria_by_tecnica_profesor(uuid, uuid) TO anon;



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/.gitignore ---
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/.oxlintrc.json ---
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "oxc"],
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/index.html ---
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>frontend</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/package.json ---
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "oxlint",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.2.8",
    "react-dom": "^19.2.8"
  },
  "devDependencies": {
    "@types/react": "^19.2.18",
    "@types/react-dom": "^19.2.7",
    "@vitejs/plugin-react": "^6.1.1",
    "oxlint": "^1.81.0",
    "vite": "^8.3.0"
  }
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/vite.config.js ---
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/App.css ---
/* App specific styles, relying mostly on utility classes from index.css */
.app-container {
  max-width: 100%;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
  box-sizing: border-box;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--glass-border);
  margin-bottom: 2rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.brand-logo {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 0 15px rgba(208, 17, 24, 0.4);
}

.brand-text {
  font-weight: 900;
  font-style: italic;
  font-size: 1.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: linear-gradient(to right, var(--brand-white), var(--text-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-accent {
  color: var(--brand-red);
  -webkit-text-fill-color: var(--brand-red);
}

.user-nav {
  display: flex;
  align-items: center;
  gap: 1rem;
}

