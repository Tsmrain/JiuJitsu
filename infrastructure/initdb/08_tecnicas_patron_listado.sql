-- C12.11 — Exponer el estado del patrón activo en el listado del catálogo.
-- Requiere que 06_patron_activo.sql haya añadido tecnicas.patron_activo_id.

DROP FUNCTION IF EXISTS get_tecnicas_with_videos();
CREATE FUNCTION get_tecnicas_with_videos()
RETURNS TABLE(
    id uuid,
    nombre varchar,
    nivel_cinturon varchar,
    video_id uuid,
    video_profesor_id uuid,
    video_url varchar,
    tiene_patron boolean
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.nombre,
        t.nivel_cinturon,
        vr.id AS video_id,
        vr.profesor_id AS video_profesor_id,
        vr.url_video_gcs AS video_url,
        (t.patron_activo_id IS NOT NULL) AS tiene_patron
    FROM tecnicas t
    LEFT JOIN videos_referencia vr ON vr.tecnica_id = t.id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_tecnicas_with_videos() TO anon;
