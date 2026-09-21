# src/application/analitica_controller.py
from typing import Dict, Any, List

class AnaliticaController:
    """Session Facade / GRASP Controller para Analítica."""
    
    def __init__(self, historial_repository):
        self._repo = historial_repository

    def obtener_debilidades_grupales(self, id_tecnica: str) -> Dict[str, Any]:
        """
        Calcula métricas grupales de debilidades agregando datos en memoria
        para mantener Protected Variations.
        """
        evaluaciones = self._repo.listar_todas(id_tecnica)
        
        total = len(evaluaciones)
        if total == 0:
            return {
                "total_evaluaciones": 0,
                "tasa_aprobacion": 0.0,
                "debilidades_grupales": []
            }
        
        aprobadas = sum(1 for e in evaluaciones if e.get("es_valido"))
        tasa = (aprobadas / total) * 100.0
        
        frecuencias = {}
        suma_desviaciones = {}
        
        for e in evaluaciones:
            # Compatibilidad retroactiva: puede no tener consejo_estructurado o desviaciones
            consejo = e.get("consejo_estructurado")
            desviaciones = []
            if isinstance(consejo, dict):
                desviaciones = consejo.get("desviaciones", []) or []
                
            for d in desviaciones:
                art = d.get("articulacion", "Desconocida")
                val = d.get("desviacion", 0.0)
                frecuencias[art] = frecuencias.get(art, 0) + 1
                suma_desviaciones[art] = suma_desviaciones.get(art, 0.0) + val
                
        debilidades = []
        for art, freq in frecuencias.items():
            debilidades.append({
                "articulacion": art,
                "frecuencia": freq,
                "promedio_desviacion": suma_desviaciones[art] / freq
            })
            
        debilidades.sort(key=lambda x: x["frecuencia"], reverse=True)
        
        return {
            "total_evaluaciones": total,
            "tasa_aprobacion": round(tasa, 1),
            "debilidades_grupales": debilidades
        }
