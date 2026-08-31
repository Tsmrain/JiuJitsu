"""Simulador y gestor de almacenamiento local para videos de demostración."""

from typing import Dict, Optional


class LocalVideoStorage:
    """Almacén en memoria/disco local para guardar y recuperar videos de referencia y ejecuciones."""

    _videos: Dict[str, bytes] = {}

    @classmethod
    def guardar_video(cls, video_id: str, contenido: bytes) -> None:
        cls._videos[video_id] = contenido

    @classmethod
    def obtener_video(cls, video_id: str) -> Optional[bytes]:
        return cls._videos.get(video_id)

    @classmethod
    def eliminar_video(cls, video_id: str) -> None:
        cls._videos.pop(video_id, None)

    @classmethod
    def limpiar(cls) -> None:
        cls._videos.clear()
