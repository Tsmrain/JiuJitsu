# src/infrastructure/history_repository.py
import uuid
import psycopg2
from typing import List, Dict, Any

class PostgresHistorialRepository:
    """Implementación de persistencia para el historial de progreso de evaluaciones del alumno."""

    def __init__(self, db_url: str):
        self._db_url = db_url

    def guardar_evaluacion(self, id_alumno: str, id_tecnica: str, resultado: Dict[str, Any]) -> str:
        """Persiste el resultado de una evaluación biomecánica en PostgreSQL."""
        id_evaluacion = str(uuid.uuid4())
        desviaciones = resultado.get("desviaciones", [])
        promedio = sum(d["desviacion"] for d in desviaciones) / len(desviaciones) if desviaciones else 0.0

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO evaluaciones_alumno 
                    (id_evaluacion, id_alumno, id_tecnica, es_valido, total_desviaciones, desviacion_promedio_grados, consejo_pedagogico)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        id_evaluacion,
                        id_alumno,
                        id_tecnica,
                        resultado["es_valido"],
                        resultado["total_desviaciones"],
                        promedio,
                        resultado["consejo_pedagogico"]
                    )
                )
            conn.commit()
        return id_evaluacion

    def obtener_progreso(self, id_alumno: str) -> List[Dict[str, Any]]:
        """Recupera la secuencia histórica de evaluaciones de un alumno ordenada cronológicamente."""
        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id_evaluacion, id_tecnica, es_valido, total_desviaciones, 
                           desviacion_promedio_grados, consejo_pedagogico, fecha_evaluacion
                    FROM evaluaciones_alumno
                    WHERE id_alumno = %s
                    ORDER BY fecha_evaluacion DESC;
                    """,
                    (id_alumno,)
                )
                rows = cur.fetchall()
                # Acceso seguro por índice posicional para tuplas nativas de psycopg2
                return [
                    {
                        "id_evaluacion": str(r[0]),
                        "id_tecnica": r[1],
                        "es_valido": r[2],
                        "total_desviaciones": r[3],
                        "desviacion_promedio_grados": r[4],
                        "consejo_pedagogico": r[5],
                        "fecha": r[6].isoformat() if hasattr(r[6], 'isoformat') else str(r[6])
                    }
                    for r in rows
                ]
