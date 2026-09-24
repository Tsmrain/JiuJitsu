from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

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


# Datos en memoria
SUCURSALES_DB: List[SucursalResponse] = [
    SucursalResponse(
        id=UUID('8b315b4e-43f2-4ca1-904d-dec87242f347'),
        nombre='JIU JITSU CORPO E MENTE MIGUEL BAIGORRIA',
        pais='Bolivia',
        ciudad='Municipio Santa Cruz de la Sierra',
        direccion='Avenida Cristóbal de Mendoza',
        latitud=-17.7702061,
        longitud=-63.1699065
    )
]

# Base de Usuarios Registrados (Credenciales por defecto del Admin)
USUARIOS_DB = [
    {
        "user_id": UUID("00000000-0000-0000-0000-000000000000"),
        "nombre_completo": "Administrador General",
        "username": "admin",
        "email": "admin@corpocmente.com",
        "password": "admin123",
        "rol": "admin",
        "avatar_url": None,
        "sucursal_id": None
    },
    {
        'user_id': UUID('7e455a7d-cbc8-4190-9a10-3b959f6425fc'),
        'nombre_completo': 'mike',
        'username': 'mike',
        'email': 'mike@mock.com',
        'password': 'password123',
        'rol': 'profesor',
        'avatar_url': None,
        'sucursal_id': UUID('8b315b4e-43f2-4ca1-904d-dec87242f347')
    },
    {
        'user_id': UUID('bce12c1c-91f1-4bfb-813b-a18c5426b51e'),
        'nombre_completo': 'santi',
        'username': 'santi',
        'email': 'santi@mock.com',
        'password': 'password123',
        'rol': 'alumno',
        'avatar_url': None,
        'sucursal_id': UUID('8b315b4e-43f2-4ca1-904d-dec87242f347')
    }
]

# Endpoints
@router.post("/auth/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(req: LoginRequest):
    """
    Endpoint de Autenticación por Nombre de Usuario / Email y Contraseña.
    """
    usr_key = req.username_or_email.strip().lower()
    
    # Buscar usuario en la base de datos
    user = next((u for u in USUARIOS_DB if u["username"].lower() == usr_key or u["email"].lower() == usr_key), None)
    
    if not user or user["password"] != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos."
        )

    sucursal = next((s for s in SUCURSALES_DB if s.id == user["sucursal_id"]), None)
    sucursal_nombre = sucursal.nombre if sucursal else "Sucursal Eliminada"

    return LoginResponse(
        token=f"jwt-token-{user['rol']}-{user['username']}",
        user_id=user["user_id"],
        nombre_completo=user["nombre_completo"],
        username=user["username"],
        email=user["email"],
        rol=user["rol"],
        sucursal_id=user["sucursal_id"],
        sucursal_nombre=sucursal_nombre
    )

@router.post("/auth/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest):
    """
    Registro público de cuentas para Alumnos y Profesores.
    El rol de Administrador está bloqueado desde el formulario público.
    """
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

    if any(u["username"].lower() == usr_clean for u in USUARIOS_DB):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nombre de usuario '{req.username}' ya está registrado."
        )

    sucursal = next((s for s in SUCURSALES_DB if s.id == req.sucursal_id), None)
    
    # Prevenir registro si no hay sucursales disponibles
    if not sucursal:
        if len(SUCURSALES_DB) > 0:
            sucursal = SUCURSALES_DB[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay sucursales registradas en el sistema para asociar al usuario. Por favor, crea una sucursal primero."
            )

    new_user = {
        "user_id": uuid4(),
        "nombre_completo": req.nombre_completo,
        "username": req.username.strip(),
        "email": f"{usr_clean}@mock.com", # Auto-generado para cumplir con base de datos
        "password": req.password,
        "rol": rol_solicitado,
        "avatar_url": None,
        "sucursal_id": sucursal.id
    }
    
    USUARIOS_DB.append(new_user)

    return LoginResponse(
        token=f"jwt-token-{new_user['rol']}-{new_user['username']}",
        user_id=new_user["user_id"],
        nombre_completo=new_user["nombre_completo"],
        username=new_user["username"],
        email=new_user["email"],
        rol=new_user["rol"],
        avatar_url=new_user.get("avatar_url"),
        sucursal_id=new_user["sucursal_id"],
        sucursal_nombre=sucursal.nombre
    )

@router.get("/auth/usuarios", response_model=List[LoginResponse], status_code=status.HTTP_200_OK)
async def listar_usuarios():
    """
    Lista todos los usuarios (para vista de administrador).
    """
    resultado = []
    for u in USUARIOS_DB:
        sucursal = next((s for s in SUCURSALES_DB if s.id == u["sucursal_id"]), None)
        resultado.append(LoginResponse(
            token="dummy-token",
            user_id=u["user_id"],
            nombre_completo=u["nombre_completo"],
            username=u["username"],
            email=u["email"],
            rol=u["rol"],
            avatar_url=u.get("avatar_url"),
            sucursal_id=u["sucursal_id"],
            sucursal_nombre=sucursal.nombre if sucursal else "Sucursal Eliminada"
        ))
    return resultado

@router.put("/auth/usuarios/{user_id}", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def update_usuario(user_id: UUID, req: UserUpdateRequest):
    """
    Actualizar perfil de usuario (nombre, contraseña, foto base64).
    """
    user = next((u for u in USUARIOS_DB if u["user_id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if req.nombre_completo is not None:
        user["nombre_completo"] = req.nombre_completo
    if req.password is not None and req.password.strip() != "":
        user["password"] = req.password
    if req.avatar_url is not None:
        user["avatar_url"] = req.avatar_url

    sucursal = next((s for s in SUCURSALES_DB if s.id == user["sucursal_id"]), None)
    sucursal_nombre = sucursal.nombre if sucursal else "Sucursal Eliminada"

    return LoginResponse(
        token=f"jwt-token-{user['rol']}-{user['username']}",
        user_id=user["user_id"],
        nombre_completo=user["nombre_completo"],
        username=user["username"],
        email=user["email"],
        rol=user["rol"],
        avatar_url=user.get("avatar_url"),
        sucursal_id=user["sucursal_id"],
        sucursal_nombre=sucursal_nombre
    )

@router.post("/auth/impersonate/{user_id}", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def impersonate_user(user_id: UUID):
    """
    Permite a un administrador tomar la sesión de cualquier usuario por ID sin contraseña.
    """
    user = next((u for u in USUARIOS_DB if u["user_id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        
    sucursal = next((s for s in SUCURSALES_DB if s.id == user["sucursal_id"]), None)
    sucursal_nombre = sucursal.nombre if sucursal else "Sucursal Eliminada"

    return LoginResponse(
        token=f"jwt-token-{user['rol']}-{user['username']}",
        user_id=user["user_id"],
        nombre_completo=user["nombre_completo"],
        username=user["username"],
        email=user["email"],
        rol=user["rol"],
        avatar_url=user.get("avatar_url"),
        sucursal_id=user["sucursal_id"],
        sucursal_nombre=sucursal_nombre
    )

@router.get("/sucursales", response_model=List[SucursalResponse], status_code=status.HTTP_200_OK)
async def listar_sucursales():
    """
    Lista todas las sucursales globales registradas con sus coordenadas geográficas.
    """
    return SUCURSALES_DB

@router.get("/profesores", response_model=List[ProfesorResponse], status_code=status.HTTP_200_OK)
async def listar_profesores(sucursal_id: Optional[UUID] = None):
    """
    Lista los profesores registrados en el sistema, opcionalmente filtrados por sucursal.
    """
    profesores = [u for u in USUARIOS_DB if u["rol"] == "profesor"]
    if sucursal_id:
        profesores = [p for p in profesores if p["sucursal_id"] == sucursal_id]
        
    resultado = []
    for p in profesores:
        sucursal = next((s for s in SUCURSALES_DB if s.id == p["sucursal_id"]), None)
        resultado.append(ProfesorResponse(
            user_id=p["user_id"],
            nombre_completo=p["nombre_completo"],
            username=p["username"],
            email=p["email"],
            avatar_url=p.get("avatar_url"),
            sucursal_id=p["sucursal_id"],
            sucursal_nombre=sucursal.nombre if sucursal else "Sucursal Eliminada"
        ))
        
    return resultado

@router.post("/sucursales", response_model=SucursalResponse, status_code=status.HTTP_201_CREATED)
async def crear_sucursal(nueva: SucursalCreate):
    """
    Permite al Administrador registrar una nueva sucursal marcando la latitud y longitud.
    """
    sucursal = SucursalResponse(
        id=uuid4(),
        nombre=nueva.nombre,
        pais=nueva.pais,
        ciudad=nueva.ciudad,
        direccion=nueva.direccion,
        latitud=nueva.latitud,
        longitud=nueva.longitud
    )
    SUCURSALES_DB.append(sucursal)
    return sucursal

@router.put("/sucursales/{sucursal_id}", response_model=SucursalResponse, status_code=status.HTTP_200_OK)
async def actualizar_sucursal(sucursal_id: UUID, req: SucursalCreate):
    """
    Permite al Administrador modificar los datos o coordenadas de una sucursal existente.
    """
    for index, s in enumerate(SUCURSALES_DB):
        if s.id == sucursal_id:
            updated = SucursalResponse(
                id=sucursal_id,
                nombre=req.nombre,
                pais=req.pais,
                ciudad=req.ciudad,
                direccion=req.direccion,
                latitud=req.latitud,
                longitud=req.longitud
            )
            SUCURSALES_DB[index] = updated
            return updated

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Sucursal no encontrada."
    )

@router.delete("/sucursales/{sucursal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sucursal(sucursal_id: UUID):
    """
    Permite al Administrador eliminar una sucursal del sistema.
    """
    global SUCURSALES_DB
    
    # Restricción de Integridad Referencial (Mannino 3NF - ON DELETE RESTRICT)
    if any(u["sucursal_id"] == sucursal_id for u in USUARIOS_DB):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar esta sucursal porque tiene usuarios (profesores o alumnos) vinculados. Reasigna o elimina los usuarios primero."
        )

    initial_count = len(SUCURSALES_DB)
    SUCURSALES_DB = [s for s in SUCURSALES_DB if s.id != sucursal_id]

    if len(SUCURSALES_DB) == initial_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal no encontrada."
        )
    return None

import urllib.request
import urllib.parse
import json
import re

@router.post("/sucursales/parse-gmaps-link", response_model=ParseGmapsResponse, status_code=status.HTTP_200_OK)
async def parse_gmaps_link(req: ParseGmapsRequest):
    """
    Servicio backend de scraping y geocodificación para enlaces de Google Maps.
    Resuelve acortadores de URL, extrae coordenadas exactas (!3d/!4d) y autocompleta
    nombre, dirección, ciudad y país mediante OpenStreetMap.
    """
    url_input = req.url.strip()

    # 1. Resolver redirecciones de acortadores si es necesario
    try:
        http_req = urllib.request.Request(
            url_input,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        with urllib.request.urlopen(http_req) as resp:
            final_url = resp.geturl()
    except Exception:
        final_url = url_input

    # 2. Extraer Coordenadas (Prioridad: !3dLat!4dLng > query > @camera)
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

    # 3. Extraer Nombre comercial o del establecimiento
    place_name = None
    place_match = re.search(r"\/place\/([^\/@]+)", final_url)
    if place_match:
        raw_name = urllib.parse.unquote(place_match.group(1)).replace("+", " ")
        if not re.search(r"[2-9A-Z]{4,8}\+[2-9A-Z]{2,4}", raw_name, re.I):
            place_name = raw_name

    # 4. Geocodificación Inversa con OpenStreetMap (Nominatim)
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
                # If no road is found, try to use the Plus Code as fallback (like Google Maps does)
                try:
                    import openlocationcode.openlocationcode as olc
                    # generate full code with precision 11
                    full_code = olc.encode(lat, lng, 11)
                    # Strip the first 4 characters (region code) to get the short code
                    short_code = full_code[4:12] # e.g. 6RW2+Q76
                    city_str = addr.get("city") or addr.get("town") or addr.get("municipality") or ""
                    if city_str:
                        direccion = f"{short_code}, {city_str}"
                    else:
                        direccion = short_code
                except ImportError:
                    # Fallback to display name if openlocationcode is not installed
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


