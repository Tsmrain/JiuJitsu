from pydantic import BaseModel

class IngestionRequest(BaseModel):
    """DTO de entrada para la ingestión de teoría RAG."""
    tecnica_id: str
    contenido_texto: str

class IngestionResponse(BaseModel):
    """DTO de salida para la respuesta de ingestión."""
    status: str
    chunks_procesados: int
