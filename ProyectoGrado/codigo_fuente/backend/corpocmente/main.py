from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from corpocmente.config import settings
from corpocmente.ui.api.routes import router as evaluaciones_router
from corpocmente.ui.api.auth_routes import router as auth_router
from corpocmente.ui.api.tecnicas_routes import router as tecnicas_router

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

# Montar carpeta pública para videos de referencia
import os
from fastapi.staticfiles import StaticFiles

UPLOAD_DIR = "/tmp/corpocmente_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static/videos", StaticFiles(directory=UPLOAD_DIR), name="videos")

# Registrar rutas del dominio
app.include_router(evaluaciones_router)
app.include_router(auth_router)
app.include_router(tecnicas_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}
