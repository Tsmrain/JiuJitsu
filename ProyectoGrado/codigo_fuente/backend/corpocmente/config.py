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
    
    # PostgreSQL / PostgREST
    POSTGREST_URL: str = "http://localhost:3000"
    POSTGREST_JWT_SECRET: str = ""
    
    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("GEMINI_API_KEY", "POSTGREST_JWT_SECRET")
    @classmethod
    def check_not_empty(cls, v: str, info):
        if not v or v.strip() == "":
            raise ValueError(f"La variable de entorno {info.field_name} no puede estar vacía.")
        return v

settings = Settings()
