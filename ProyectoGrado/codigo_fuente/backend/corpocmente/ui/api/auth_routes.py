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
