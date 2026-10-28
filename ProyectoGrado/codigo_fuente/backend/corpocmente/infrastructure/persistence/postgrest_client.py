import os
import requests

class PostgrestClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("POSTGREST_URL", "http://localhost:3001")

    def get(self, table: str, params: dict = None, token: str = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.get(f"{self.base_url}/{table}", params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def post(self, table: str, data: dict, token: str = None):
        headers = {"Prefer": "return=representation"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.post(f"{self.base_url}/{table}", json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def patch(self, table: str, filters: dict, data: dict, token: str = None):
        """Actualiza filas que coincidan con los filtros. Retorna la representación actualizada."""
        headers = {"Prefer": "return=representation"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        params = {k: v for k, v in filters.items()}
        response = requests.patch(f"{self.base_url}/{table}", params=params, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def delete(self, table: str, filters: dict, token: str = None):
        """Elimina filas que coincidan con los filtros. Retorna la representación eliminada."""
        headers = {"Prefer": "return=representation"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        params = {k: v for k, v in filters.items()}
        response = requests.delete(f"{self.base_url}/{table}", params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def rpc(self, function_name: str, params: dict, token: str = None):
        """Llama a una función almacenada de PostgreSQL vía el endpoint /rpc/ de PostgREST."""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.post(f"{self.base_url}/rpc/{function_name}", json=params, headers=headers)
        response.raise_for_status()
        return response.json()
