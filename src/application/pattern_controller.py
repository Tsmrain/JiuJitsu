# src/application/pattern_controller.py
import json
import psycopg2
from src.domain.interfaces import IInferenceEngine

class RegistrarTecnicaController:
    """Controlador de Aplicación para CU-01: Registrar Técnica Patrón."""
    
    def __init__(self, inference_engine: IInferenceEngine, db_url: str):
        self._inference_engine = inference_engine
        self._db_url = db_url

    def registrar_patron(self, id_tecnica: str, nombre: str, descripcion: str, video_maestro_path: str) -> bool:
        """Extrae el molde postural 3D del instructor y lo persiste en PostgreSQL."""
        # 1. Extraer esqueleto 3D del video del maestro
        matriz_patron = self._inference_engine.inferir_esqueleto_3d(video_maestro_path)
        
        # 2. Serializar a JSONB compatible con Punto3D
        puntos = matriz_patron.puntos_3d if getattr(matriz_patron, 'puntos_3d', None) else matriz_patron.puntos
        matriz_json = json.dumps({
            str(k): {"x": v.x, "y": v.y, "z": v.z}
            for k, v in puntos.items()
        })

        # 3. Guardar en PostgreSQL (Upsert)
        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tecnicas_patron (id_tecnica, nombre, descripcion, matriz_esqueletica)
                    VALUES (%s, %s, %s, %s::jsonb)
                    ON CONFLICT (id_tecnica) DO UPDATE 
                    SET nombre = EXCLUDED.nombre,
                        descripcion = EXCLUDED.descripcion,
                        matriz_esqueletica = EXCLUDED.matriz_esqueletica;
                    """,
                    (id_tecnica, nombre, descripcion, matriz_json)
                )
            conn.commit()
        return True
