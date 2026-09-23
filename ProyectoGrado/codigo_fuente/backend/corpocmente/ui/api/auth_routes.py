from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/v1", tags=["Autenticación y Sucursales"])

# Modelos Pydantic DTO
class LoginRequest(BaseModel):
    email: str
    password: str
    rol: str = "alumno" # 'alumno', 'profesor', 'admin'

class LoginResponse(BaseModel):
    token: str
    user_id: UUID
    nombre_completo: str
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

# Datos en memoria (Mock / In-memory para pruebas de la iteración)
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

# Endpoints
@router.post("/auth/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(req: LoginRequest):
    """
    Endpoint de Autenticación por Roles (Alumno, Profesor, Administrador).
    """
    rol_solicitado = req.rol.lower()
    if rol_solicitado not in ['admin', 'profesor', 'alumno']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol inválido. Debe ser 'admin', 'profesor' o 'alumno'."
        )

    # Nombres representativos para prueba
    nombres = {
        'admin': "Administrador General Corpo e Mente",
        'profesor': "Prof. Mestre Humberto Tavares",
        'alumno': "Alumno Hans Santiago"
    }

    return LoginResponse(
        token=f"jwt-token-mock-for-{rol_solicitado}",
        user_id=uuid4(),
        nombre_completo=nombres.get(rol_solicitado, "Usuario Corpo e Mente"),
        email=req.email,
        rol=rol_solicitado,
        sucursal_id=SUCURSALES_DB[0].id,
        sucursal_nombre=SUCURSALES_DB[0].nombre
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
