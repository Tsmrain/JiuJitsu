#!/usr/bin/env python3
"""
setup_drive_oauth.py
Genera token.json autorizando el acceso a Google Drive mediante OAuth 2.0 (Desktop app).
"""
import os
import io
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
BACKEND_DIR = Path(__file__).resolve().parents[1]
CREDENTIALS_FILE = BACKEND_DIR / "credentials.json"
TOKEN_FILE = BACKEND_DIR / "token.json"
FOLDER_ID = "1bxH5ZuvL-yxGqAZd5pbd7pLRoSI8gSwK"

def authenticate_and_test():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refrescando token existente...")
            creds.refresh(Request())
        else:
            print("Iniciando flujo de autorización en el navegador...")
            print(f"Leyendo credenciales desde: {CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token_out:
            token_out.write(creds.to_json())
        print(f"✅ Token guardado exitosamente en: {TOKEN_FILE}")

    print("\nVerificando conexión con Google Drive...")
    service = build("drive", "v3", credentials=creds)
    folder = service.files().get(fileId=FOLDER_ID, fields="id, name, owners").execute()
    print(f"Carpeta vinculada: {folder.get('name')} (ID: {folder.get('id')})")

    print("\nProbando subida de archivo de prueba al Data Lake...")
    file_metadata = {
        "name": "ping_datalake_test.txt",
        "parents": [FOLDER_ID]
    }
    media = MediaIoBaseUpload(io.BytesIO(b"DataLake Corpo e Mente funcionando OK"), mimetype="text/plain")
    created = service.files().create(body=file_metadata, media_body=media, fields="id, name").execute()
    file_id = created.get("id")
    print(f"🎉 ¡ÉXITO TOTAL! Archivo creado en tu Drive sin restricciones de cuota: ID {file_id}")

    service.files().delete(fileId=file_id).execute()
    print("Archivo de prueba eliminado. El Data Lake está 100% operativo.")

if __name__ == "__main__":
    authenticate_and_test()
