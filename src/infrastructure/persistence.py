# src/infrastructure/persistence.py
import json
import psycopg2
from typing import Optional
from src.domain.interfaces import ITecnicaRepository
from src.domain.models import MatrizEsqueletica, Punto3D

class PostgresTecnicaRepository(ITecnicaRepository):
    """Implementación de persistencia relacional en PostgreSQL para técnicas patrón."""

    def __init__(self, db_url: str):
        self._db_url = db_url

    def obtener_patron(self, id_tecnica: str) -> Optional[MatrizEsqueletica]:
        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT matriz_esqueletica FROM tecnicas_patron WHERE id_tecnica = %s;",
                    (id_tecnica,)
                )
                row = cur.fetchone()
                if not row or not row[0]:
                    return None
                
                raw_data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                puntos = {
                    int(k): Punto3D(float(v['x']), float(v['y']), float(v['z'])) 
                    for k, v in raw_data.items()
                }
                return MatrizEsqueletica(puntos_3d=puntos)
