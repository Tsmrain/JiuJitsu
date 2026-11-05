-- 16_evaluacion_url_video_alumno.sql
-- Incluye url_video_alumno en la función get_evaluacion_by_id para reproducción consistente de videos

DROP FUNCTION IF EXISTS public.get_evaluacion_by_id(uuid);
CREATE OR REPLACE FUNCTION public.get_evaluacion_by_id(p_evaluacion_id uuid)
  RETURNS TABLE(
    id uuid,
    alumno_id uuid,
    tecnica_id uuid,
    tecnica_nombre character varying,
    estado character varying,
    porcentaje_similitud numeric,
    feedback_gemini_es text,
    feedback_gemini_pt text,
    feedback_summary text,
    url_video_alumno text,
    video_referencia_url character varying,
    video_referencia_profesor_nombre character varying
  )
  LANGUAGE plpgsql
  SECURITY DEFINER
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.alumno_id,
        e.tecnica_id,
        COALESCE(t.nombre, 'Técnica')::varchar AS tecnica_nombre,
        e.estado,
        e.porcentaje_similitud,
        e.feedback_gemini_es,
        e.feedback_gemini_pt,
        e.feedback_summary,
        e.url_video_alumno::text,
        COALESCE(vr.url_video_gcs, '')::varchar AS video_referencia_url,
        COALESCE(u_prof.nombre_completo, 'Profesor')::varchar AS video_referencia_profesor_nombre
    FROM evaluaciones_alumnos e
    LEFT JOIN tecnicas t ON t.id = e.tecnica_id
    LEFT JOIN videos_referencia vr ON vr.id = e.video_referencia_id
    LEFT JOIN usuarios u_prof ON u_prof.id = vr.profesor_id
    WHERE e.id = p_evaluacion_id;
END;
$function$;

GRANT EXECUTE ON FUNCTION public.get_evaluacion_by_id(uuid) TO anon, alumno, profesor, admin, postgres;

