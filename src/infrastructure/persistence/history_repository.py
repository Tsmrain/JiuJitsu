# src/infrastructure/persistence/history_repository.py
import uuid
import json
import psycopg2
from psycopg2.extras import Json
from typing import List, Dict, Any
from src.domain.interfaces import IHistorialRepository
from src.domain.models import ReporteAnalitica, EstadisticaArticular
from datetime import datetime, timezone

class PostgresHistorialRepository(IHistorialRepository):
    """Implementación de persistencia para el historial de progreso de evaluaciones del alumno."""

    def __init__(self, db_url: str):
        self._db_url = db_url

    def guardar_evaluacion(self, id_alumno: str, id_tecnica: str, resultado: Dict[str, Any]) -> str:
        """Persiste el resultado de una evaluación biomecánica en PostgreSQL con soporte JSONB."""
        id_evaluacion = str(uuid.uuid4())
        desviaciones = resultado.get("desviaciones", [])
        
        # Soportar ambas claves "desviacion" y "desviacion_grados"
        suma_desviaciones = 0.0
        for d in desviaciones:
            if isinstance(d, dict):
                suma_desviaciones += d.get("desviacion_grados", d.get("desviacion", 0.0))
            else:
                # If d is a string or something else, handle gracefully
                pass
                
        promedio = suma_desviaciones / len(desviaciones) if desviaciones else 0.0

        # Si viene un diccionario estructurado, lo usamos; si no, estructuramos el string
        consejo_data = resultado.get("consejo_estructurado")
        if not consejo_data or not isinstance(consejo_data, dict):
            raw_consejo = resultado.get("consejo_pedagogico", "")
            if isinstance(raw_consejo, dict):
                consejo_data = raw_consejo
            else:
                consejo_data = {
                    "analisis_postural": str(raw_consejo),
                    "riesgo_lesion": "No especificado",
                    "paso_a_paso": str(raw_consejo),
                    "resumen_ejecutivo": str(raw_consejo)
                }

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO evaluaciones_alumno 
                    (id_evaluacion, id_alumno, id_tecnica, es_valido, total_desviaciones, desviacion_promedio_grados, consejo_pedagogico, desviaciones_detalle)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        id_evaluacion,
                        id_alumno,
                        id_tecnica,
                        resultado.get("es_valido", False),
                        resultado.get("total_desviaciones", len(desviaciones)),
                        promedio,
                        Json(consejo_data),
                        Json(desviaciones)
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
                resultado = []
                for r in rows:
                    raw_consejo = r[5]
                    # Deserializar si viene en formato string
                    if isinstance(raw_consejo, str):
                        try:
                            consejo_obj = json.loads(raw_consejo)
                        except Exception:
                            consejo_obj = raw_consejo
                    else:
                        consejo_obj = raw_consejo

                    # Formatear string para la UI si es un objeto estructurado
                    if isinstance(consejo_obj, dict):
                        resumen = consejo_obj.get("resumen_ejecutivo", "")
                        pasos = consejo_obj.get("paso_a_paso", "")
                        consejo_str = f"{resumen}\n\nPaso a paso correctivo:\n{pasos}" if (resumen and pasos) else (resumen or pasos or str(consejo_obj))
                    else:
                        consejo_str = str(consejo_obj)

                    resultado.append({
                        "id_evaluacion": str(r[0]),
                        "id_tecnica": r[1],
                        "es_valido": r[2],
                        "total_desviaciones": r[3],
                        "desviacion_promedio_grados": r[4],
                        "consejo_pedagogico": consejo_str,
                        "consejo_estructurado": consejo_obj if isinstance(consejo_obj, dict) else None,
                        "fecha": r[6].isoformat() if hasattr(r[6], 'isoformat') else str(r[6])
                    })
                return resultado

    def obtener_analitica_por_tecnica(self, id_tecnica: str) -> ReporteAnalitica:
        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*), SUM(CASE WHEN es_valido THEN 1 ELSE 0 END)
                    FROM evaluaciones_alumno
                    WHERE id_tecnica = %s;
                    """,
                    (id_tecnica,)
                )
                row = cur.fetchone()
                if not row or row[0] == 0:
                    raise ValueError(f"No hay evaluaciones para la técnica {id_tecnica}")
                
                total_evals = row[0]
                aprobadas = row[1]
                tasa = (aprobadas / total_evals) * 100.0

                cur.execute(
                    """
                    SELECT desviaciones_detalle
                    FROM evaluaciones_alumno
                    WHERE id_tecnica = %s;
                    """,
                    (id_tecnica,)
                )
                rows = cur.fetchall()
                
                art_stats = {}
                for (desv_det,) in rows:
                    if desv_det and isinstance(desv_det, list):
                        for d in desv_det:
                            if not isinstance(d, dict):
                                continue
                            art = d.get("nombre_articulacion", d.get("articulacion"))
                            if not art:
                                continue
                            deg = d.get("desviacion_grados", d.get("desviacion", 0.0))
                            if art not in art_stats:
                                art_stats[art] = {"count": 0, "sum": 0.0}
                            art_stats[art]["count"] += 1
                            art_stats[art]["sum"] += deg
                
                articulaciones_criticas = []
                for art, stats in art_stats.items():
                    avg_deg = stats["sum"] / stats["count"]
                    articulaciones_criticas.append(
                        EstadisticaArticular(
                            nombre_articulacion=str(art),
                            total_detecciones=stats["count"],
                            desviacion_promedio_grados=round(avg_deg, 2)
                        )
                    )
                
                articulaciones_criticas.sort(key=lambda x: x.desviacion_promedio_grados, reverse=True)

                return ReporteAnalitica(
                    id_tecnica=id_tecnica,
                    nombre_tecnica=id_tecnica.replace("_", " ").title(),
                    total_evaluaciones=total_evals,
                    evaluaciones_aprobadas=aprobadas,
                    tasa_aprobacion=round(tasa, 2),
                    articulaciones_criticas=articulaciones_criticas,
                    fecha_generacion=datetime.now(timezone.utc)
                )

    def listar_tecnicas_mas_evaluadas(self, limite: int = 5) -> List[Dict[str, Any]]:
        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id_tecnica, COUNT(*) as total
                    FROM evaluaciones_alumno
                    GROUP BY id_tecnica
                    ORDER BY total DESC
                    LIMIT %s;
                    """,
                    (limite,)
                )
                rows = cur.fetchall()
                return [{"id_tecnica": r[0], "total_evaluaciones": r[1]} for r in rows]
