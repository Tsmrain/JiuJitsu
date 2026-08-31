"""
Adaptador de Almacenamiento para Huawei Cloud Object Storage Service (OBS).

Implementa el Patrón Adaptador (GoF) / Fabricación Pura (GRASP) y el principio
de Experto en Información (Information Expert) aislando el SDK oficial esdk-obs-python.

Requisitos cubiertos:
- RF-07: Validación estricta de peso de video (<= 5 MB) antes de llamadas al SDK.
- RP-02: Validación estricta de peso de fotograma anotado (<= 100 KB).

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import os
from typing import Any, Optional

try:
    from obs import ObsClient, PutObjectHeader
    # En el SDK esdk-obs-python, las excepciones heredan de Exception
    # Definimos clase base específica o usamos las clases de error de OBS
    from obs import ErrorDocument, FederationTokenException, TemporaryAKSKException
    ObsExceptions = (ErrorDocument, FederationTokenException, TemporaryAKSKException)
except ImportError:  # pragma: no cover
    ObsClient = None  # type: ignore
    PutObjectHeader = None  # type: ignore
    ObsExceptions = ()  # type: ignore

from src.infrastructure.interfaces import IHuaweiOBSStorageAdapter


class StorageOperationError(Exception):
    """Excepción de infraestructura para fallos en transferencias con Huawei Cloud OBS."""
    pass


class HuaweiOBSStorageAdapter(IHuaweiOBSStorageAdapter):
    """Adaptador de infraestructura para Huawei Cloud OBS.

    Abstrae el almacenamiento y recuperación de videos MP4 y fotogramas JPG anotados,
    gestionando la autenticación mediante AK/SK o variables de entorno.
    """

    MAX_VIDEO_BYTES: int = 5 * 1024 * 1024  # 5 MB (RF-07)
    MAX_FRAME_BYTES: int = 100 * 1024       # 100 KB (RP-02)

    def __init__(
        self,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        server: Optional[str] = None,
        bucket_input: Optional[str] = None,
        bucket_output: Optional[str] = None,
        client: Optional[Any] = None,
        is_secure: bool = True,
    ) -> None:
        self.server: str = (
            server
            or os.getenv("OBS_ENDPOINT", "obs.la-south-2.myhuaweicloud.com")
        ).strip()

        default_bucket = os.getenv("OBS_BUCKET_NAME", "bjj-videos-input")
        self.bucket_input: str = (bucket_input or default_bucket).strip()
        self.bucket_output: str = (
            bucket_output or os.getenv("OBS_BUCKET_OUTPUT", "bjj-reports-output")
        ).strip()

        access_key = ak if ak is not None else os.getenv("OBS_ACCESS_KEY", "")
        secret_key = sk if sk is not None else os.getenv("OBS_SECRET_KEY", "")

        # Inyección de dependencia de cliente (para testing y aislamiento)
        if client is not None:
            self.client = client
        else:
            if ObsClient is None:
                raise StorageOperationError(
                    "El SDK oficial 'esdk-obs-python' no está instalado en el entorno."
                )
            self.client = ObsClient(
                access_key_id=access_key,
                secret_access_key=secret_key,
                server=self.server,
                is_secure=is_secure,
            )

    def _construir_url_objeto(self, bucket_name: str, object_key: str) -> str:
        """Construye la URL HTTPS estándar del objeto en Huawei Cloud OBS."""
        servidor_limpio = self.server.replace("https://", "").replace("http://", "")
        return f"https://{bucket_name}.{servidor_limpio}/{object_key}"

    def subir_video(self, video_bytes: bytes, video_id: str) -> str:
        """Sube el flujo binario de un video MP4 al bucket de entrada de OBS.

        Valida estrictamente que el video no supere 5 MB (RF-07) antes
        de interactuar con la nube.

        Args:
            video_bytes: Bytes del archivo de video.
            video_id: Identificador o nombre del archivo (ej. 'ejecucion_123.mp4').

        Returns:
            URL HTTPS del objeto almacenado.

        Raises:
            ValueError: Si el video supera los 5 MB permitidos (RF-07).
            StorageOperationError: Si ocurre un error en la interacción con OBS.
        """
        if len(video_bytes) > self.MAX_VIDEO_BYTES:
            raise ValueError("RF-07 Violado: El video supera los 5MB permitidos")

        try:
            headers = None
            if PutObjectHeader is not None:
                headers = PutObjectHeader(contentType="video/mp4")

            resp = self.client.putObject(
                bucketName=self.bucket_input,
                objectKey=video_id,
                content=video_bytes,
                headers=headers,
            )

            if resp and hasattr(resp, "status") and resp.status >= 300:
                raise StorageOperationError(
                    f"Fallo al subir video '{video_id}' a OBS. "
                    f"Estado: {resp.status} - {getattr(resp, 'reason', '')}"
                )

            return self._construir_url_objeto(self.bucket_input, video_id)
        except Exception as e:
            if isinstance(e, (ValueError, StorageOperationError)):
                raise
            if ObsExceptions and isinstance(e, ObsExceptions):
                raise StorageOperationError(
                    f"Error de cliente Huawei OBS: {str(e)}"
                ) from e
            raise StorageOperationError(
                f"Error inesperado al subir video a Huawei OBS: {str(e)}"
            ) from e

    def subir_fotograma(self, frame_bytes: bytes, analisis_id: str) -> str:
        """Sube la imagen JPG del fotograma clave anotado al bucket de salida.

        Valida estrictamente que el fotograma no supere 100 KB (RP-02) antes
        de interactuar con la nube.

        Args:
            frame_bytes: Bytes de la imagen JPG.
            analisis_id: Identificador o nombre del archivo (ej. 'analisis_456.jpg').

        Returns:
            URL HTTPS del objeto almacenado.

        Raises:
            ValueError: Si el fotograma supera los 100 KB permitidos (RP-02).
            StorageOperationError: Si ocurre un error en la interacción con OBS.
        """
        if len(frame_bytes) > self.MAX_FRAME_BYTES:
            raise ValueError("RP-02 Violado: El fotograma supera los 100KB permitidos")

        try:
            headers = None
            if PutObjectHeader is not None:
                headers = PutObjectHeader(contentType="image/jpeg")

            resp = self.client.putObject(
                bucketName=self.bucket_output,
                objectKey=analisis_id,
                content=frame_bytes,
                headers=headers,
            )

            if resp and hasattr(resp, "status") and resp.status >= 300:
                raise StorageOperationError(
                    f"Fallo al subir fotograma '{analisis_id}' a OBS. "
                    f"Estado: {resp.status} - {getattr(resp, 'reason', '')}"
                )

            return self._construir_url_objeto(self.bucket_output, analisis_id)
        except Exception as e:
            if isinstance(e, (ValueError, StorageOperationError)):
                raise
            if ObsExceptions and isinstance(e, ObsExceptions):
                raise StorageOperationError(
                    f"Error de cliente Huawei OBS: {str(e)}"
                ) from e
            raise StorageOperationError(
                f"Error inesperado al subir fotograma a Huawei OBS: {str(e)}"
            ) from e

    def descargar_objeto(self, object_key: str, bucket_name: Optional[str] = None) -> bytes:
        """Descarga el contenido binario de un objeto desde Huawei Cloud OBS.

        Args:
            object_key: Nombre o clave del objeto a descargar.
            bucket_name: Nombre del bucket (opcional, por defecto bucket_input).

        Returns:
            Contenido binario (bytes) del objeto.

        Raises:
            StorageOperationError: Si falla la descarga o la respuesta es inválida.
        """
        target_bucket = bucket_name or self.bucket_input
        try:
            resp = self.client.getObject(bucketName=target_bucket, objectKey=object_key)

            if resp and hasattr(resp, "status") and resp.status >= 300:
                raise StorageOperationError(
                    f"Fallo al descargar '{object_key}' de '{target_bucket}'. "
                    f"Estado: {resp.status} - {getattr(resp, 'reason', '')}"
                )

            if not hasattr(resp, "body"):
                raise StorageOperationError(
                    f"Respuesta vacía o inválida al descargar '{object_key}'"
                )

            body = resp.body
            if hasattr(body, "read"):
                return body.read()
            elif hasattr(body, "response") and hasattr(body.response, "read"):
                return body.response.read()
            elif hasattr(body, "buffer"):
                return bytes(body.buffer)
            elif isinstance(body, bytes):
                return body
            else:
                return bytes(body)
        except Exception as e:
            if isinstance(e, StorageOperationError):
                raise
            if ObsExceptions and isinstance(e, ObsExceptions):
                raise StorageOperationError(
                    f"Error de cliente Huawei OBS al descargar: {str(e)}"
                ) from e
            raise StorageOperationError(
                f"Error al descargar objeto de Huawei OBS: {str(e)}"
            ) from e

    def cerrar(self) -> None:
        """Cierra el cliente y libera las conexiones HTTP subyacentes."""
        if hasattr(self.client, "close"):
            self.client.close()

