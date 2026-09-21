ALTER TABLE evaluaciones_alumno 
ADD COLUMN IF NOT EXISTS desviaciones_detalle JSONB DEFAULT '[]'::jsonb;
