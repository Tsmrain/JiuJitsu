import requests
import sys
import os

API_URL = os.environ.get("API_URL", "http://localhost:8000/api/v1/conocimiento/teoria")
TOKEN = os.environ.get("JWT_TOKEN", "tu_token_jwt_aqui")

def ingest_file(filepath: str, tecnica_id: str, token: str = TOKEN):
    if not os.path.exists(filepath):
        print(f"❌ Error: El archivo '{filepath}' no existe.")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        texto = f.read()

    payload = {"tecnica_id": tecnica_id, "contenido_texto": texto}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"Ingestando '{filepath}' para la técnica {tecnica_id}...")
    try:
        res = requests.post(API_URL, json=payload, headers=headers)
        if res.status_code in (200, 201):
            print("✅ Éxito:", res.json())
        else:
            print("❌ Error:", res.status_code, res.text)
    except Exception as e:
        print(f"❌ Error al conectar con el backend: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python ingest_real_data.py <archivo.txt> <tecnica_id> [token_opcional]")
        sys.exit(1)
    
    token = sys.argv[3] if len(sys.argv) > 3 else TOKEN
    ingest_file(sys.argv[1], sys.argv[2], token)
