Operación: solicitarAnaliticaTatami(id_tecnica: String?)
Referencias: CU-04 Panel de Analítica para el Tatami
Precondiciones:
  - El Profesor está autenticado.
Postcondiciones:
  - Se recuperó el conjunto de EvaluacionAlumno (consulta de instancias).
  - Se computó la frecuencia de desviación por articulación (derivación).
  - Se computó la tasa de aprobación global (derivación).
  - Se retornó un DTO con debilidades_grupales ordenadas por frecuencia (creación de instancia).
