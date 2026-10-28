-- C13.3: distinguir fuentes de conocimiento globales de instrucciones por técnica.

ALTER TABLE teoria_referencia ALTER COLUMN tecnica_id DROP NOT NULL;
ALTER TABLE teoria_referencia ALTER COLUMN sucursal_id DROP NOT NULL;
ALTER TABLE teoria_referencia
    ADD COLUMN IF NOT EXISTS alcance TEXT NOT NULL DEFAULT 'tecnica';
ALTER TABLE teoria_referencia
    DROP CONSTRAINT IF EXISTS teoria_referencia_alcance_check;
ALTER TABLE teoria_referencia
    ADD CONSTRAINT teoria_referencia_alcance_check CHECK (alcance IN ('global', 'tecnica'));

ALTER TABLE tecnicas
    ADD COLUMN IF NOT EXISTS mensaje_profesor TEXT NOT NULL DEFAULT '';

DROP FUNCTION IF EXISTS admin_save_teoria_chunk(UUID, UUID, UUID, INT, TEXT, UUID, TEXT, TEXT, TEXT, TEXT);
CREATE OR REPLACE FUNCTION admin_save_teoria_chunk(
    p_tecnica_id UUID,
    p_profesor_id UUID,
    p_sucursal_id UUID,
    p_chunk_index INT,
    p_contenido_texto TEXT,
    p_qdrant_point_id UUID,
    p_fuente_tipo TEXT,
    p_fuente_nombre TEXT,
    p_fuente_referencia TEXT,
    p_fuente_url TEXT,
    p_alcance TEXT
)
RETURNS TABLE(id UUID, tecnica_id UUID, profesor_id UUID, chunk_index INT, fecha_ingesta TIMESTAMPTZ) AS $$
DECLARE
    new_id UUID;
BEGIN
    INSERT INTO teoria_referencia (
        tecnica_id, profesor_id, sucursal_id, chunk_index, contenido_texto,
        qdrant_point_id, fuente_tipo, fuente_nombre, fuente_referencia, fuente_url, alcance
    ) VALUES (
        p_tecnica_id, p_profesor_id, p_sucursal_id, p_chunk_index, p_contenido_texto,
        p_qdrant_point_id, p_fuente_tipo, p_fuente_nombre, p_fuente_referencia, p_fuente_url, p_alcance
    ) RETURNING teoria_referencia.id INTO new_id;

    RETURN QUERY
    SELECT t.id, t.tecnica_id, t.profesor_id, t.chunk_index, t.fecha_ingesta
    FROM teoria_referencia t WHERE t.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_save_teoria_chunk(
    UUID, UUID, UUID, INT, TEXT, UUID, TEXT, TEXT, TEXT, TEXT, TEXT
) TO anon;

CREATE OR REPLACE FUNCTION admin_list_fuentes_globales()
RETURNS TABLE(
    id UUID, contenido_texto TEXT, chunk_index INT, profesor_id UUID,
    fecha_ingesta TIMESTAMPTZ, fuente_tipo TEXT, fuente_nombre TEXT,
    fuente_referencia TEXT, fuente_url TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT t.id, t.contenido_texto, t.chunk_index, t.profesor_id, t.fecha_ingesta,
           t.fuente_tipo, t.fuente_nombre, t.fuente_referencia, t.fuente_url
    FROM teoria_referencia t
    WHERE t.alcance = 'global'
    ORDER BY t.fecha_ingesta DESC, t.chunk_index ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_fuentes_globales() TO anon;

DROP FUNCTION IF EXISTS admin_create_tecnica(TEXT, TEXT);
CREATE OR REPLACE FUNCTION admin_create_tecnica(p_nombre TEXT, p_nivel_cinturon TEXT, p_mensaje_profesor TEXT)
RETURNS TABLE(id UUID, nombre VARCHAR, nivel_cinturon VARCHAR, mensaje_profesor TEXT) AS $$
DECLARE new_id UUID;
BEGIN
    INSERT INTO tecnicas(nombre, nivel_cinturon, mensaje_profesor)
    VALUES (p_nombre, p_nivel_cinturon, p_mensaje_profesor)
    RETURNING tecnicas.id INTO new_id;
    RETURN QUERY SELECT t.id, t.nombre, t.nivel_cinturon, t.mensaje_profesor FROM tecnicas t WHERE t.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
GRANT EXECUTE ON FUNCTION admin_create_tecnica(TEXT, TEXT, TEXT) TO anon;

DROP FUNCTION IF EXISTS admin_update_tecnica(UUID, TEXT, TEXT);
CREATE OR REPLACE FUNCTION admin_update_tecnica(
    p_tecnica_id UUID, p_nombre TEXT, p_nivel_cinturon TEXT, p_mensaje_profesor TEXT
)
RETURNS TABLE(id UUID, nombre VARCHAR, nivel_cinturon VARCHAR, mensaje_profesor TEXT) AS $$
BEGIN
    UPDATE tecnicas SET nombre = p_nombre, nivel_cinturon = p_nivel_cinturon,
        mensaje_profesor = p_mensaje_profesor
    WHERE tecnicas.id = p_tecnica_id;
    RETURN QUERY SELECT t.id, t.nombre, t.nivel_cinturon, t.mensaje_profesor
    FROM tecnicas t WHERE t.id = p_tecnica_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
GRANT EXECUTE ON FUNCTION admin_update_tecnica(UUID, TEXT, TEXT, TEXT) TO anon;

DROP FUNCTION IF EXISTS get_tecnicas_with_videos();
CREATE FUNCTION get_tecnicas_with_videos()
RETURNS TABLE(
    id UUID, nombre VARCHAR, nivel_cinturon VARCHAR, video_id UUID,
    video_profesor_id UUID, video_url VARCHAR, tiene_patron BOOLEAN,
    mensaje_profesor TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT t.id, t.nombre, t.nivel_cinturon, vr.id, vr.profesor_id, vr.url_video_gcs,
           (t.patron_activo_id IS NOT NULL), t.mensaje_profesor
    FROM tecnicas t LEFT JOIN videos_referencia vr ON vr.tecnica_id = t.id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
GRANT EXECUTE ON FUNCTION get_tecnicas_with_videos() TO anon;

NOTIFY pgrst, 'reload schema';
