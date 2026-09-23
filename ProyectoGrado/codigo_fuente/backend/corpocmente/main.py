from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from corpocmente.config import settings
from corpocmente.ui.api.routes import router as evaluaciones_router
from corpocmente.ui.api.auth_routes import router as auth_router

app = FastAPI(
    title=settings.APP_NAME,
    description="API RESTful Backend para la plataforma Corpo e Mente (Análisis Biomecánico con IA)",
    version="1.0.0"
)

# Configuración de CORS para permitir peticiones desde la aplicación Web / Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas del dominio
app.include_router(evaluaciones_router)
app.include_router(auth_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}
