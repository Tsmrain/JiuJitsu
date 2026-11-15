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

_pkg_logger = logging.getLogger("corpocmente")
_pkg_logger.setLevel(logging.INFO)
if not _pkg_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setLevel(logging.INFO)
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    _pkg_logger.addHandler(_handler)
_pkg_logger.propagate = False

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
from fastapi.staticfiles import StaticFiles
from corpocmente.infrastructure.persistence.video_storage import (
    VIDEOS_DIR as UPLOAD_DIR,
    autocurar_videos_referencia_en_arranque,
)

os.makedirs(UPLOAD_DIR, exist_ok=True)
autocurar_videos_referencia_en_arranque()
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
