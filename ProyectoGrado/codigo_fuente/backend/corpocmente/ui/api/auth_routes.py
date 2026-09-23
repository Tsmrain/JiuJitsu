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
    email: str
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
    sucursal_id: UUID
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

class ParseGmapsRequest(BaseModel):
    url: str

class ParseGmapsResponse(BaseModel):
    nombre: Optional[str] = None
    pais: Optional[str] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    latitud: float
    longitud: float


# Datos en memoria
SUCURSALES_DB: List[SucursalResponse] = [
    SucursalResponse(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        nombre="Corpo e Mente - Sede Principal Rio de Janeiro",
        pais="Brasil",
        ciudad="Rio de Janeiro",
        direccion="Av. Atlântica 1200, Copacabana",
        latitud=-22.9711,
        longitud=-43.1822
    ),
    SucursalResponse(
        id=UUID("44444444-4444-4444-4444-444444444444"),
        nombre="Corpo e Mente - Sede Santa Cruz",
        pais="Bolivia",
        ciudad="Santa Cruz de la Sierra",
        direccion="Av. San Martín, Equipetrol Norte #450",
        latitud=-17.7833,
        longitud=-63.1821
    ),
    SucursalResponse(
        id=UUID("55555555-5555-5555-5555-555555555555"),
        nombre="Corpo e Mente - Sede La Paz",
        pais="Bolivia",
        ciudad="La Paz",
        direccion="Av. 16 de Julio (El Prado) #1420",
        latitud=-16.5000,
        longitud=-68.1500
    ),
    SucursalResponse(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        nombre="Corpo e Mente - Sede Bogotá",
        pais="Colombia",
        ciudad="Bogotá",
        direccion="Calle 93 # 12-40, Zona T",
        latitud=4.6761,
        longitud=-74.0486
    ),
    SucursalResponse(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        nombre="Corpo e Mente - Sede Tokyo",
        pais="Japón",
        ciudad="Tokyo",
        direccion="Shibuya City, Dogenzaka 2-24-1",
        latitud=35.6580,
        longitud=139.7016
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
        "sucursal_id": SUCURSALES_DB[0].id,
        "sucursal_nombre": SUCURSALES_DB[0].nombre
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

    return LoginResponse(
        token=f"jwt-token-{user['rol']}-{user['username']}",
        user_id=user["user_id"],
        nombre_completo=user["nombre_completo"],
        username=user["username"],
        email=user["email"],
        rol=user["rol"],
        sucursal_id=user["sucursal_id"],
        sucursal_nombre=user["sucursal_nombre"]
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
    email_clean = req.email.strip().lower()

    if any(u["username"].lower() == usr_clean for u in USUARIOS_DB):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nombre de usuario '{req.username}' ya está registrado."
        )

    if any(u["email"].lower() == email_clean for u in USUARIOS_DB):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El correo electrónico '{req.email}' ya está registrado."
        )

    sucursal = next((s for s in SUCURSALES_DB if s.id == req.sucursal_id), SUCURSALES_DB[0])

    new_user = {
        "user_id": uuid4(),
        "nombre_completo": req.nombre_completo,
        "username": req.username.strip(),
        "email": req.email.strip(),
        "password": req.password,
        "rol": rol_solicitado,
        "sucursal_id": sucursal.id,
        "sucursal_nombre": sucursal.nombre
    }
    
    USUARIOS_DB.append(new_user)

    return LoginResponse(
        token=f"jwt-token-{new_user['rol']}-{new_user['username']}",
        user_id=new_user["user_id"],
        nombre_completo=new_user["nombre_completo"],
        username=new_user["username"],
        email=new_user["email"],
        rol=new_user["rol"],
        sucursal_id=new_user["sucursal_id"],
        sucursal_nombre=new_user["sucursal_nombre"]
    )

@router.get("/sucursales", response_model=List[SucursalResponse], status_code=status.HTTP_200_OK)
async def listar_sucursales():
    """
    Lista todas las sucursales globales registradas con sus coordenadas geográficas.
    """
    return SUCURSALES_DB

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
    pin_match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", final_url)
    if pin_match:
        lat, lng = float(pin_match.group(1)), float(pin_match.group(2))
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


