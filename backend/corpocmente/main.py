import time
import logging
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from corpocmente.config import settings
from corpocmente.ui.api.routes import router as evaluaciones_router
from corpocmente.ui.api.auth_routes import router as auth_router
from corpocmente.ui.api.tecnicas_routes import router as tecnicas_router
from corpocmente.api.routes.comparaciones import router as comparaciones_router

logger = logging.getLogger("corpocmente.api")

app = FastAPI(
    title=settings.APP_NAME,
    description="API RESTful Backend para la plataforma Corpo e Mente (Análisis Biomecánico con IA)",
    version="1.0.0",
    debug=settings.DEBUG
)

# Rate Limiter Middleware para prevenir ataques de fuerza bruta en autenticación
class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_attempts: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path.endswith("/auth/login"):
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            self.attempts[client_ip] = [
                t for t in self.attempts[client_ip] if now - t < self.window_seconds
            ]
            if len(self.attempts[client_ip]) >= self.max_attempts:
                logger.warning(f"Rate limit exceeded for IP: {client_ip} on /auth/login")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many login attempts. Please try again later."}
                )
            self.attempts[client_ip].append(now)

        return await call_next(request)

app.add_middleware(AuthRateLimitMiddleware)

# Configuración de CORS segura para producción y desarrollo local
allowed_origins = [
    origin.strip()
    for origin in settings.ALLOWED_ORIGINS.split(",")
    if origin.strip()
]

cors_kwargs = {
    "allow_origins": allowed_origins,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": ["*"],
}
if settings.ENVIRONMENT != "production":
    cors_kwargs["allow_origin_regex"] = r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|0\.0\.0\.0)(:\d+)?$"

app.add_middleware(CORSMiddleware, **cors_kwargs)

# Global Exception Handler para mitigar fuga de stack traces en producción
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact the administrator."}
    )

# Montar carpeta pública para videos de referencia
import os
import shutil
from fastapi.staticfiles import StaticFiles

UPLOAD_DIR = "/tmp/corpocmente_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Seeding preventivo de videos de referencia conocidos
def seed_reference_videos():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    mapping = {
        "67beb825-87d1-4c46-8380-9b0cb6ef0489.mp4": "profesor salida de Guardia Parandose.mp4",
        "38f8b98c-b6bd-4cd7-ac18-1bd922174854.mp4": "Escape de 100 kilos brazo por debajo.mp4",
        "53062479-765e-4a33-b467-2ab120ccd3f6.mp4": "Profesor ensena 1 escape de guardia cerrada.mp4",
        "e74b10ca-f33c-4662-8f08-b4fb9a4b1110.mp4": "Profesor dill pasaje de guardia abierta.mp4",
        "c92e5499-d2bc-48da-aaff-a1995c09d964.mp4": "Maestro.mp4",
    }
    for target_name, src_name in mapping.items():
        dst = os.path.join(UPLOAD_DIR, target_name)
        if not os.path.exists(dst):
            src = os.path.join(repo_root, src_name)
            if os.path.exists(src):
                try:
                    shutil.copy2(src, dst)
                except Exception:
                    pass

seed_reference_videos()
app.mount("/static/videos", StaticFiles(directory=UPLOAD_DIR), name="videos")

FRAMES_DIR = "/tmp/corpocmente_frames"
os.makedirs(FRAMES_DIR, exist_ok=True)
app.mount("/static/frames", StaticFiles(directory=FRAMES_DIR), name="frames")

# Registrar rutas del dominio
app.include_router(evaluaciones_router)
app.include_router(auth_router)
app.include_router(tecnicas_router)
app.include_router(comparaciones_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}
