from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Corpo e Mente Biomechanics AI"
    ENVIRONMENT: str = "development"
    
    # Gemini API
    GEMINI_API_KEY: str = ""
    
    # Qdrant DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "vectores_poses_jiujitsu"
    
    # Colab Worker Tunnel URL
    COLAB_TUNNEL_URL: str = ""
    
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
    JWT_EXPIRATION_HOURS: int = 24
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("GEMINI_API_KEY", "POSTGREST_JWT_SECRET")
    @classmethod
    def check_not_empty(cls, v: str, info):
        if not v or v.strip() == "":
            raise ValueError(f"La variable de entorno {info.field_name} no puede estar vacía.")
        return v

settings = Settings()
