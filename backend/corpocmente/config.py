from pathlib import Path
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


def storage_root() -> Path:
    """
    Directorio raíz canónico para almacenamiento de datos (data/).
    Permite override mediante variable de entorno CORPOCMENTE_DATA_DIR.
    """
    env_dir = os.getenv("CORPOCMENTE_DATA_DIR")
    if env_dir:
        root = Path(env_dir).resolve()
    else:
        root = Path(__file__).resolve().parents[2] / "data"
    root.mkdir(parents=True, exist_ok=True)
    return root


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Corpo e Mente Biomechanics AI"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Qdrant DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "vectores_poses_jiujitsu"
    QDRANT_RAG_COLLECTION: str = "rag_knowledge"
    
    # Colab Worker Tunnel URL
    COLAB_TUNNEL_URL: str = ""
    
    # Inferencia Local Qwen (Apple Silicon MLX)
    USE_LOCAL_QWEN: bool = True
    LOCAL_QWEN_MODEL: str = "mlx-community/Qwen3-VL-Embedding-2B-8bit"
    
    # Visión por Computadora: YOLO Segmentation multi-etapa (Opcional, default False)
    USE_SEGMENTATION: bool = False
    
    # PostgreSQL / PostgREST
    POSTGREST_URL: str = "http://localhost:3000"
    POSTGREST_JWT_SECRET: str = ""
    
    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS — lista separada por comas de orígenes permitidos
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:4173"
    
    # Worker Service Token (para autenticar al Colab Worker)
    WORKER_SERVICE_TOKEN: str = "dev_worker_token_change_in_prod"
    
    # JWT para autenticación de usuarios
    JWT_SECRET_KEY: str = "dev_jwt_secret_change_in_prod_min_32_chars_long"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 168
    
    model_config = SettingsConfigDict(
        env_file=[
            str(Path(__file__).resolve().parents[1] / ".env"),
            ".env",
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("POSTGREST_JWT_SECRET")
    @classmethod
    def check_not_empty(cls, v: str, info):
        if not v or v.strip() == "":
            raise ValueError(f"La variable de entorno {info.field_name} no puede estar vacía.")
        return v

    @property
    def manuales_dir(self) -> Path:
        d = storage_root() / "manuales"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def rag_frames_dir(self) -> Path:
        d = storage_root() / "rag_frames"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def video_frames_dir(self) -> Path:
        d = storage_root() / "manuales" / "video_frames"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def comparaciones_dir(self) -> Path:
        d = storage_root() / "comparaciones"
        d.mkdir(parents=True, exist_ok=True)
        return d


settings = Settings()
