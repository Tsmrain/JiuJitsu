-- C13.2: el alumno puede revisar su historial y recuperar ambos videos del análisis.
-- La autorización del historial propio se aplica en el endpoint FastAPI.

DROP FUNCTION IF EXISTS admin_list_evaluaciones_alumno(UUID);
CREATE OR REPLACE FUNCTION admin_list_evaluaciones_alumno(p_alumno_id UUID)
RETURNS TABLE(
    id UUID,
    tecnica_id UUID,
    tecnica_nombre VARCHAR,
    porcentaje_similitud NUMERIC,
    estado VARCHAR,
    feedback_gemini_es TEXT,
    feedback_gemini_pt TEXT,
    feedback_summary TEXT,
    fecha_evaluacion TIMESTAMPTZ,
    url_video_alumno TEXT,
    video_referencia_url TEXT,
    video_referencia_profesor_nombre VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.tecnica_id,
        COALESCE(t.nombre, 'Técnica')::VARCHAR,
        e.porcentaje_similitud,
        e.estado,
        e.feedback_gemini_es,
        e.feedback_gemini_pt,
        e.feedback_summary,
        e.fecha_evaluacion,
        e.url_video_alumno::TEXT,
        vr.url_video_gcs::TEXT,
        COALESCE(u_prof.nombre_completo, 'Profesor')::VARCHAR
    FROM evaluaciones_alumnos e
    LEFT JOIN tecnicas t ON t.id = e.tecnica_id
    LEFT JOIN videos_referencia vr ON vr.id = e.video_referencia_id
    LEFT JOIN usuarios u_prof ON u_prof.id = vr.profesor_id
    WHERE e.alumno_id = p_alumno_id
    ORDER BY e.fecha_evaluacion DESC
    LIMIT 50;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_evaluaciones_alumno(UUID) TO anon;

NOTIFY pgrst, 'reload schema';
