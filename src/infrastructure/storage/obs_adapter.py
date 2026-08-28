"""
Adaptador de Almacenamiento para Huawei Cloud Object Storage Service (OBS).
Implementa el Patrón Adaptador (GoF) / Fabricación Pura (GRASP) aislando el SDK oficial esdk-obs-python.
"""

from typing import Any, Optional
from obs import ObsClient, PutObjectHeader


class StorageOperationError(Exception):
    """Excepción de infraestructura para fallos en transferencias con Huawei Cloud OBS."""
    pass


class HuaweiOBSStorageAdapter:
    """
    Adaptador de infraestructura para Huawei Cloud OBS.
    
    Abstrae el almacenamiento y recuperación de videos MP4 y fotogramas JPG anotados,
    gestionando la autenticación mediante AK/SK o Agencia IAM y garantizando bajo acoplamiento.
    """

    def __init__(
        self,
        ak: str = "",
        sk: str = "",
        server: str = "obs.la-south-2.myhuaweicloud.com",
        bucket_input: str = "bjj-videos-input",
        bucket_output: str = "bjj-reports-output",
        client: Optional[Any] = None,
        is_secure: bool = True,
    ) -> None:
        self.server = server.strip()
        self.bucket_input = bucket_input.strip()
        self.bucket_output = bucket_output.strip()

        # Inyección de dependencia de cliente (útil para pruebas unitarias simuladas con Mocks)
        if client is not None:
            self.client = client
        else:
            self.client = ObsClient(
                access_key_id=ak,
                secret_access_key=sk,
                server=self.server,
                is_secure=is_secure,
            )

    def _construir_url_objeto(self, bucket_name: str, object_key: str) -> str:
        """Construye la URL HTTPS estándar del objeto en Huawei Cloud OBS."""
        servidor_limpio = self.server.replace("https://", "").replace("http://", "")
        return f"https://{bucket_name}.{servidor_limpio}/{object_key}"

    def subir_video(self, video_bytes: bytes, object_key: str) -> str:
        """
        Sube el flujo binario de un video MP4 al bucket de entrada de Huawei Cloud OBS.

        :param video_bytes: Bytes del archivo de video MP4.
        :param object_key: Clave/nombre de destino en el bucket (ej. 'ejecucion_123.mp4').
        :return: URL HTTPS del objeto almacenado.
        """
        try:
            headers = PutObjectHeader(contentType="video/mp4")
            resp = self.client.putObject(
                bucketName=self.bucket_input,
                objectKey=object_key,
                content=video_bytes,
                headers=headers,
            )

            # Verificar código de estado de respuesta OBS
            if resp and hasattr(resp, "status") and resp.status >= 300:
                raise StorageOperationError(
                    f"Fallo al subir video '{object_key}' a OBS. Estado: {resp.status} - {getattr(resp, 'reason', '')}"
                )

            return self._construir_url_objeto(self.bucket_input, object_key)
        except Exception as e:
            if isinstance(e, StorageOperationError):
                raise
            raise StorageOperationError(f"Error inesperado al subir video a Huawei OBS: {str(e)}") from e

    def subir_fotograma(self, foto_bytes: bytes, object_key: str) -> str:
        """
        Sube la imagen JPG del fotograma clave anotado al bucket de salida.

        :param foto_bytes: Bytes de la imagen JPG comprimida (~80 KB).
        :param object_key: Clave/nombre de destino en el bucket (ej. 'analisis_456_annotated.jpg').
        :return: URL HTTPS del objeto almacenado.
        """
        try:
            # Configuración explícita de Content-Type para correcta visualización en navegadores
            headers = PutObjectHeader(contentType="image/jpeg")
            resp = self.client.putObject(
                bucketName=self.bucket_output,
                objectKey=object_key,
                content=foto_bytes,
                headers=headers,
            )

            if resp and hasattr(resp, "status") and resp.status >= 300:
                raise StorageOperationError(
                    f"Fallo al subir fotograma '{object_key}' a OBS. Estado: {resp.status} - {getattr(resp, 'reason', '')}"
                )

            return self._construir_url_objeto(self.bucket_output, object_key)
        except Exception as e:
            if isinstance(e, StorageOperationError):
                raise
            raise StorageOperationError(f"Error inesperado al subir fotograma a Huawei OBS: {str(e)}") from e

    def descargar_objeto(self, object_key: str, bucket_name: str) -> bytes:
        """
        Descarga el flujo binario crudo de un objeto específico desde Huawei Cloud OBS.

        :param object_key: Nombre o clave del objeto a descargar.
        :param bucket_name: Nombre del bucket de origen.
        :return: Bytes del contenido del objeto.
        """
        try:
            resp = self.client.getObject(bucketName=bucket_name, objectKey=object_key)

            if resp and hasattr(resp, "status") and resp.status >= 300:
                raise StorageOperationError(
                    f"Fallo al descargar '{object_key}' de '{bucket_name}'. Estado: {resp.status} - {getattr(resp, 'reason', '')}"
                )

            if not hasattr(resp, "body"):
                raise StorageOperationError(f"Respuesta vacía o inválida al descargar '{object_key}'")

            body = resp.body

            # Extracción del contenido binario según la estructura retornada por el SDK
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
            raise StorageOperationError(f"Error al descargar objeto de Huawei OBS: {str(e)}") from e

    def cerrar(self) -> None:
        """Cierra el cliente y libera las conexiones HTTP subyacentes."""
        if hasattr(self.client, "close"):
            self.client.close()
