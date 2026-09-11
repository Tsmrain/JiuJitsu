# src/presentation/api.py
import uuid
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from src.application.controllers import EvaluacionController

app = FastAPI(title="API Biomecánica BJJ", version="1.0.0")

# Almacén temporal de estado para tareas asíncronas (en producción Redis o BD)
TAREAS_ESTADO: Dict[str, Dict[str, Any]] = {}

# Contenedor de dependencias para desacoplamiento e inyección en tests
container: Dict[str, Any] = {}

class SolicitudEvaluacionDTO(BaseModel):
    id_tecnica: str
    video_url_o_path: str

class EvaluacionRespuestaDTO(BaseModel):
    id_tecnica: str
    es_valido: bool
    total_desviaciones: int
    desviaciones: List[Dict[str, Any]]
    consejo_pedagogico: str

class SolicitudAsincronaDTO(BaseModel):
    id_tecnica: str
    video_url_o_path: str
    id_alumno: str = "alumno_demo"

# Función de dependencia para inyectar el controlador
def get_controller() -> EvaluacionController:
    if "evaluacion_controller" in container and container["evaluacion_controller"] is not None:
        return container["evaluacion_controller"]
    from src.infrastructure.mocks import MockYOLOEngine, MockGeminiService, MockTecnicaRepository
    return EvaluacionController(
        inference_engine=MockYOLOEngine(desviacion_grados=12.0),
        generation_service=MockGeminiService(),
        tecnica_repository=MockTecnicaRepository()
    )

def tarea_procesar_evaluacion(tarea_id: str, video_path: str, id_tecnica: str, id_alumno: str = "alumno_demo"):
    """Tarea en segundo plano para procesar la evaluación biomecánica y guardar en historial."""
    try:
        TAREAS_ESTADO[tarea_id]["estado"] = "PROCESANDO"
        controller = container.get("evaluacion_controller") or get_controller()
        resultado = controller.evaluar_ejecucion(video_path, id_tecnica)
        
        # Guardar en historial si el repositorio está configurado en el contenedor
        historial_repo = container.get("historial_repository")
        if historial_repo:
            historial_repo.guardar_evaluacion(id_alumno, id_tecnica, resultado)

        TAREAS_ESTADO[tarea_id]["estado"] = "COMPLETADO"
        TAREAS_ESTADO[tarea_id]["resultado"] = resultado
    except Exception as e:
        TAREAS_ESTADO[tarea_id]["estado"] = "ERROR"
        TAREAS_ESTADO[tarea_id]["error"] = str(e)

# Endpoint Síncrono (CU-02)
@app.post("/api/v1/evaluaciones/evaluar", response_model=EvaluacionRespuestaDTO)
def evaluar_tecnica(solicitud: SolicitudEvaluacionDTO, controller: EvaluacionController = Depends(get_controller)):
    try:
        resultado = controller.evaluar_ejecucion(
            video_path=solicitud.video_url_o_path, 
            id_tecnica=solicitud.id_tecnica
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

# Endpoint Asíncrono (No bloqueante)
@app.post("/api/v1/evaluaciones/evaluar-asincrono")
def evaluar_tecnica_asincrono(solicitud: SolicitudAsincronaDTO, background_tasks: BackgroundTasks):
    tarea_id = str(uuid.uuid4())
    TAREAS_ESTADO[tarea_id] = {"estado": "PENDIENTE", "resultado": None}
    
    background_tasks.add_task(
        tarea_procesar_evaluacion, 
        tarea_id, 
        solicitud.video_url_o_path, 
        solicitud.id_tecnica,
        solicitud.id_alumno
    )
    
    return {"tarea_id": tarea_id, "mensaje": "Procesamiento iniciado."}

# Endpoint de Consulta de Estado
@app.get("/api/v1/evaluaciones/tareas/{tarea_id}")
def obtener_estado_tarea(tarea_id: str):
    if tarea_id not in TAREAS_ESTADO:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    return TAREAS_ESTADO[tarea_id]

# Endpoint de Consulta de Historial de Progreso (CU-04)
@app.get("/api/v1/alumnos/{id_alumno}/progreso")
def obtener_progreso_alumno(id_alumno: str):
    from src.infrastructure.history_repository import PostgresHistorialRepository
    import os
    db_url = os.getenv("DATABASE_URL", "postgresql://usuario:password@localhost:5432/bjj_db")
    try:
        repo = container.get("historial_repository") or PostgresHistorialRepository(db_url)
        progreso = repo.obtener_progreso(id_alumno)
        return {
            "id_alumno": id_alumno,
            "total_evaluaciones": len(progreso),
            "historial": progreso
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando historial: {str(e)}")

