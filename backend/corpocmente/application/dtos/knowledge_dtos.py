from typing import Literal, Optional
from pydantic import AnyHttpUrl, BaseModel, Field

class IngestionRequest(BaseModel):
    """DTO de entrada para la ingestión de teoría RAG."""
    tecnica_id: Optional[str] = None
    contenido_texto: str = Field(min_length=1)
    alcance: Literal["global", "tecnica"] = "tecnica"
    fuente_tipo: Literal["manual", "video", "articulo"] = "manual"
    fuente_nombre: Optional[str] = Field(default=None, max_length=300)
    fuente_referencia: Optional[str] = Field(default=None, max_length=300)
    fuente_url: Optional[AnyHttpUrl] = None

class IngestionResponse(BaseModel):
    """DTO de salida para la respuesta de ingestión."""
    status: str
    chunks_procesados: int
