-- database/02_historico.sql
CREATE TABLE IF NOT EXISTS evaluaciones_alumno (
    id_evaluacion UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_alumno VARCHAR(50) NOT NULL,
    id_tecnica VARCHAR(50) NOT NULL REFERENCES tecnicas_patron(id_tecnica),
    es_valido BOOLEAN NOT NULL,
    total_desviaciones INT NOT NULL,
    desviacion_promedio_grados FLOAT NOT NULL,
    consejo_pedagogico TEXT NOT NULL,
    fecha_evaluacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evaluaciones_alumno_fecha 
ON evaluaciones_alumno (id_alumno, fecha_evaluacion DESC);
