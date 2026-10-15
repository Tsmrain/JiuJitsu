-- ==============================================================================
-- Migración: Permitir que video_referencia_id sea opcional en evaluaciones
-- Descripción: Con el nuevo sistema de patrones biomecánicos (Entregable 2),
-- la referencia principal es el patrón activo en PostgreSQL y Qdrant.
-- ==============================================================================

ALTER TABLE evaluaciones_alumnos ALTER COLUMN video_referencia_id DROP NOT NULL;

-- Actualizar función RPC create_evaluacion para admitir NULL en video_referencia_id
CREATE OR REPLACE FUNCTION create_evaluacion(
    p_id UUID,
    p_alumno_id UUID,
    p_tecnica_id UUID,
    p_video_referencia_id UUID,
    p_url_video_alumno TEXT
)
RETURNS TABLE (
    id UUID,
    alumno_id UUID,
    tecnica_id UUID,
    video_referencia_id UUID,
    url_video_alumno VARCHAR,
    estado VARCHAR
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    INSERT INTO evaluaciones_alumnos (
        id, alumno_id, tecnica_id, video_referencia_id, url_video_alumno, estado
    )
    VALUES (
        p_id, p_alumno_id, p_tecnica_id, p_video_referencia_id, p_url_video_alumno, 'procesando'
    );

    RETURN QUERY
    SELECT e.id, e.alumno_id, e.tecnica_id, e.video_referencia_id, e.url_video_alumno, e.estado
    FROM evaluaciones_alumnos e
    WHERE e.id = p_id;
END;
$$;

GRANT EXECUTE ON FUNCTION create_evaluacion(UUID, UUID, UUID, UUID, TEXT) TO public;
