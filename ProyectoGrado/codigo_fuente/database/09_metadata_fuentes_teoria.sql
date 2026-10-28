-- C13.1: atribución de la fuente para cada fragmento RAG.
-- Los registros antiguos conservan sus campos de fuente en NULL.

ALTER TABLE teoria_referencia
    ADD COLUMN IF NOT EXISTS fuente_tipo TEXT,
    ADD COLUMN IF NOT EXISTS fuente_nombre TEXT,
    ADD COLUMN IF NOT EXISTS fuente_referencia TEXT,
    ADD COLUMN IF NOT EXISTS fuente_url TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'teoria_referencia_fuente_tipo_check'
          AND conrelid = 'teoria_referencia'::regclass
    ) THEN
        ALTER TABLE teoria_referencia
            ADD CONSTRAINT teoria_referencia_fuente_tipo_check
            CHECK (fuente_tipo IS NULL OR fuente_tipo IN ('manual', 'video', 'articulo'));
    END IF;
END $$;

-- Sustituye la firma anterior para guardar la atribución en los nuevos chunks.
DROP FUNCTION IF EXISTS admin_save_teoria_chunk(uuid, uuid, uuid, int, text, uuid);
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
    p_fuente_url TEXT
)
RETURNS TABLE(
    id UUID,
    tecnica_id UUID,
    profesor_id UUID,
    chunk_index INT,
    fecha_ingesta TIMESTAMPTZ
) AS $$
DECLARE
    new_id UUID;
BEGIN
    INSERT INTO teoria_referencia (
        tecnica_id, profesor_id, sucursal_id, chunk_index,
        contenido_texto, qdrant_point_id, fuente_tipo, fuente_nombre,
        fuente_referencia, fuente_url
    )
    VALUES (
        p_tecnica_id, p_profesor_id, p_sucursal_id, p_chunk_index,
        p_contenido_texto, p_qdrant_point_id, p_fuente_tipo, p_fuente_nombre,
        p_fuente_referencia, p_fuente_url
    )
    RETURNING teoria_referencia.id INTO new_id;

    RETURN QUERY
    SELECT t.id, t.tecnica_id, t.profesor_id, t.chunk_index, t.fecha_ingesta
    FROM teoria_referencia t
    WHERE t.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_save_teoria_chunk(
    UUID, UUID, UUID, INT, TEXT, UUID, TEXT, TEXT, TEXT, TEXT
) TO anon;

-- Incluir la atribución en el listado existente del panel docente.
DROP FUNCTION IF EXISTS admin_list_teoria_by_tecnica(UUID);
CREATE OR REPLACE FUNCTION admin_list_teoria_by_tecnica(p_tecnica_id UUID)
RETURNS TABLE(
    id UUID,
    chunk_index INT,
    contenido_texto TEXT,
    qdrant_point_id UUID,
    profesor_id UUID,
    profesor_nombre VARCHAR,
    sucursal_id UUID,
    fecha_ingesta TIMESTAMPTZ,
    fuente_tipo TEXT,
    fuente_nombre TEXT,
    fuente_referencia TEXT,
    fuente_url TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.chunk_index,
        t.contenido_texto,
        t.qdrant_point_id,
        t.profesor_id,
        COALESCE(u.nombre_completo, 'Profesor Eliminado')::VARCHAR,
        t.sucursal_id,
        t.fecha_ingesta,
        t.fuente_tipo,
        t.fuente_nombre,
        t.fuente_referencia,
        t.fuente_url
    FROM teoria_referencia t
    LEFT JOIN usuarios u ON u.id = t.profesor_id
    WHERE t.tecnica_id = p_tecnica_id
    ORDER BY t.fecha_ingesta DESC, t.chunk_index ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_teoria_by_tecnica(UUID) TO anon;

NOTIFY pgrst, 'reload schema';
