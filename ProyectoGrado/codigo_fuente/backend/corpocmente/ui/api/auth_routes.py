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
