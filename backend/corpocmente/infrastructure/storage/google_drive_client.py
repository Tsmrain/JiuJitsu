"""
google_drive_client.py
Cliente para el Data Lake en Google Drive usando OAuth 2.0.
Permite subir videos, crear tareas asíncronas y consultar resultados para Colab.
"""
import io
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload, MediaFileUpload

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']
BACKEND_DIR = Path(__file__).resolve().parents[3]
DEFAULT_CREDENTIALS = BACKEND_DIR / "credentials.json"
DEFAULT_TOKEN = BACKEND_DIR / "token.json"
DEFAULT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1bxH5ZuvL-yxGqAZd5pbd7pLRoSI8gSwK")


class GoogleDriveDataLakeClient:
    def __init__(
        self,
        folder_id: Optional[str] = None,
        credentials_file: Optional[Path] = None,
        token_file: Optional[Path] = None
    ):
        self.folder_id = folder_id or DEFAULT_FOLDER_ID
        self.credentials_file = credentials_file or DEFAULT_CREDENTIALS
        self.token_file = token_file or DEFAULT_TOKEN
        self._service = None

    def _get_service(self):
        if self._service is not None:
            return self._service

        creds = None
        if self.token_file.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(self.token_file, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            elif self.credentials_file.exists():
                flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_file), SCOPES)
                creds = flow.run_local_server(port=0)
                with open(self.token_file, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            else:
                raise FileNotFoundError(
                    f"No se encontró token.json ni credentials.json en {BACKEND_DIR}."
                )

        self._service = build("drive", "v3", credentials=creds)
        return self._service

    def subir_archivo(self, local_path: str, nombre_drive: Optional[str] = None, mime_type: Optional[str] = None) -> str:
        """Sube un archivo local a la carpeta de Google Drive y retorna su file_id."""
        service = self._get_service()
        file_name = nombre_drive or os.path.basename(local_path)
        metadata = {
            "name": file_name,
            "parents": [self.folder_id]
        }
        media = MediaFileUpload(local_path, mimetype=mime_type or "application/octet-stream", resumable=True)
        created = service.files().create(body=metadata, media_body=media, fields="id, name").execute()
        file_id = created.get("id")
        logger.info("Archivo subido a Drive: %s (ID: %s)", file_name, file_id)
        return file_id

    def subir_json(self, nombre_drive: str, datos: Dict[str, Any]) -> str:
        """Sube un diccionario JSON directamente a la carpeta de Drive."""
        service = self._get_service()
        metadata = {
            "name": nombre_drive,
            "parents": [self.folder_id]
        }
        json_bytes = json.dumps(datos, ensure_ascii=False, indent=2).encode("utf-8")
        media = MediaIoBaseUpload(io.BytesIO(json_bytes), mimetype="application/json")
        created = service.files().create(body=metadata, media_body=media, fields="id, name").execute()
        file_id = created.get("id")
        logger.info("JSON subido a Drive: %s (ID: %s)", nombre_drive, file_id)
        return file_id

    def crear_tarea_video(self, evaluacion_id: str, video_drive_id: str, persona_idx: int = 0, tecnica_id: Optional[str] = None, tecnica_nombre: Optional[str] = None) -> str:
        """Crea el archivo de tarea tarea_video_{evaluacion_id}.json en Drive para que Colab lo tome."""
        tarea = {
            "tipo": "video_evaluacion",
            "evaluacion_id": evaluacion_id,
            "video_drive_id": video_drive_id,
            "persona_idx": persona_idx,
            "tecnica_id": str(tecnica_id) if tecnica_id else None,
            "tecnica_nombre": tecnica_nombre or "Técnica",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return self.subir_json(f"tarea_video_{evaluacion_id}.json", tarea)

    def _descargar_y_eliminar_json(self, nombre_archivo: str) -> Optional[Dict[str, Any]]:
        """Busca un archivo JSON en Drive por su nombre, lo descarga, lo parsea y lo elimina."""
        service = self._get_service()
        query = f"'{self.folder_id}' in parents and name = '{nombre_archivo}' and trashed = false"
        res = service.files().list(q=query, fields="files(id, name)").execute()
        files = res.get("files", [])
        if not files:
            return None

        file_id = files[0]["id"]
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)
        datos = json.loads(fh.read().decode("utf-8"))

        # Limpiar el resultado de Drive para no acumular basura
        try:
            service.files().delete(fileId=file_id).execute()
        except Exception:
            pass

        return datos

    def buscar_resultado_video(self, evaluacion_id: str) -> Optional[Dict[str, Any]]:
        """Busca si Colab ya subió resultado_video_{evaluacion_id}.json y lo descarga."""
        return self._descargar_y_eliminar_json(f"resultado_video_{evaluacion_id}.json")

    def vectorizar_texto_qwen(self, texto: str, job_id: str, timeout: int = 240) -> Dict[str, Any]:
        """
        Envía texto al worker de Colab vía Google Drive para vectorizar con Qwen3-VL-Embedding.
        Retorna: { 'chunks': [...], 'embeddings': [...], 'dimension': 2048 }
        """
        import time
        tarea_nombre = f"tarea_qwen_texto_{job_id}.json"
        tarea_data = {
            "tipo": "qwen_embed_texto",
            "job_id": job_id,
            "texto": texto,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.subir_json(tarea_nombre, tarea_data)

        resultado_nombre = f"resultado_qwen_texto_{job_id}.json"
        inicio = time.time()
        logger.info("Esperando vectorización de texto con Qwen en Drive (job_id: %s, timeout=%ss)...", job_id, timeout)
        while time.time() - inicio < timeout:
            res = self._descargar_y_eliminar_json(resultado_nombre)
            if res is not None:
                return res
            time.sleep(2)

        raise TimeoutError(f"Colab Worker no respondió a la tarea de vectorización de texto {job_id} tras {timeout}s.")

    def vectorizar_imagenes_qwen(self, lote_imagenes: List[Dict[str, Any]], job_id: str, timeout: int = 240) -> Dict[str, Any]:
        """
        Envía un lote de imágenes (en base64) al worker de Colab vía Google Drive para vectorizar con Qwen3-VL.
        Retorna: { 'chunks': [...], 'embeddings': [...], 'dimension': 2048 }
        """
        import time
        tarea_nombre = f"tarea_qwen_img_{job_id}.json"
        tarea_data = {
            "tipo": "qwen_embed_imagenes",
            "job_id": job_id,
            "imagenes": lote_imagenes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.subir_json(tarea_nombre, tarea_data)

        resultado_nombre = f"resultado_qwen_img_{job_id}.json"
        inicio = time.time()
        logger.info("Esperando vectorización de imágenes con Qwen en Drive (job_id: %s, timeout=%ss)...", job_id, timeout)
        while time.time() - inicio < timeout:
            res = self._descargar_y_eliminar_json(resultado_nombre)
            if res is not None:
                return res
            time.sleep(2)

        raise TimeoutError(f"Colab Worker no respondió a la tarea de vectorización de imágenes {job_id} tras {timeout}s.")

    def eliminar_archivo(self, file_id: str) -> bool:
        """Elimina un archivo de Google Drive por su ID."""
        try:
            service = self._get_service()
            service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            logger.warning("No se pudo eliminar archivo %s de Drive: %s", file_id, e)
            return False

