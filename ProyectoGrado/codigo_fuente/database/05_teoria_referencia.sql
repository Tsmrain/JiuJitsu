-- ==============================================================================
-- C11.0 — Tabla de teoría de referencia (chunks RAG con trazabilidad relacional)
-- Cada fila representa un chunk que fue vectorizado y persistido en Qdrant.
-- El campo qdrant_point_id permite trazabilidad bidireccional Postgres <-> Qdrant.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS teoria_referencia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tecnica_id UUID NOT NULL REFERENCES tecnicas(id) ON DELETE CASCADE,
    profesor_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    sucursal_id UUID NOT NULL REFERENCES sucursales(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    contenido_texto TEXT NOT NULL,
    qdrant_point_id UUID UNIQUE NOT NULL,
    fecha_ingesta TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_teoria_tecnica ON teoria_referencia(tecnica_id);
CREATE INDEX IF NOT EXISTS idx_teoria_profesor ON teoria_referencia(profesor_id);
CREATE INDEX IF NOT EXISTS idx_teoria_sucursal ON teoria_referencia(sucursal_id);

-- RLS: anon no tiene acceso directo. Todo se hace vía RPC SECURITY DEFINER.
ALTER TABLE teoria_referencia ENABLE ROW LEVEL SECURITY;

-- RPC: Registrar un chunk de teoría (llamada desde el backend)
DROP FUNCTION IF EXISTS admin_save_teoria_chunk(uuid, uuid, uuid, int, text, uuid);
CREATE OR REPLACE FUNCTION admin_save_teoria_chunk(
    p_tecnica_id uuid,
    p_profesor_id uuid,
    p_sucursal_id uuid,
    p_chunk_index int,
    p_contenido_texto text,
    p_qdrant_point_id uuid
)
RETURNS TABLE(
    id uuid,
    tecnica_id uuid,
    profesor_id uuid,
    chunk_index int,
    fecha_ingesta timestamp with time zone
) AS $$
DECLARE
    new_id uuid;
BEGIN
    INSERT INTO teoria_referencia (
        tecnica_id, profesor_id, sucursal_id, chunk_index,
        contenido_texto, qdrant_point_id
    )
    VALUES (
        p_tecnica_id, p_profesor_id, p_sucursal_id, p_chunk_index,
        p_contenido_texto, p_qdrant_point_id
    )
    RETURNING teoria_referencia.id INTO new_id;

    RETURN QUERY
    SELECT t.id, t.tecnica_id, t.profesor_id, t.chunk_index, t.fecha_ingesta
    FROM teoria_referencia t
    WHERE t.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_save_teoria_chunk(uuid, uuid, uuid, int, text, uuid) TO anon;

-- RPC: Listar chunks de una técnica (para que el profesor vea lo que subió)
DROP FUNCTION IF EXISTS admin_list_teoria_by_tecnica(uuid);
CREATE OR REPLACE FUNCTION admin_list_teoria_by_tecnica(p_tecnica_id uuid)
RETURNS TABLE(
    id uuid,
    chunk_index int,
    contenido_texto text,
    qdrant_point_id uuid,
    profesor_id uuid,
    profesor_nombre varchar,
    sucursal_id uuid,
    fecha_ingesta timestamp with time zone
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.chunk_index,
        t.contenido_texto,
        t.qdrant_point_id,
        t.profesor_id,
        COALESCE(u.nombre_completo, 'Profesor Eliminado')::varchar AS profesor_nombre,
        t.sucursal_id,
        t.fecha_ingesta
    FROM teoria_referencia t
    LEFT JOIN usuarios u ON u.id = t.profesor_id
    WHERE t.tecnica_id = p_tecnica_id
    ORDER BY t.fecha_ingesta DESC, t.chunk_index ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_teoria_by_tecnica(uuid) TO anon;

-- RPC: Eliminar todos los chunks de teoría de una técnica + profesor
DROP FUNCTION IF EXISTS admin_delete_teoria_by_tecnica_profesor(uuid, uuid);
CREATE OR REPLACE FUNCTION admin_delete_teoria_by_tecnica_profesor(
    p_tecnica_id uuid,
    p_profesor_id uuid
)
RETURNS TABLE(deleted_qdrant_ids uuid[]) AS $$
DECLARE
    ids uuid[];
BEGIN
    SELECT array_agg(qdrant_point_id) INTO ids
    FROM teoria_referencia
    WHERE tecnica_id = p_tecnica_id AND profesor_id = p_profesor_id;

    DELETE FROM teoria_referencia
    WHERE tecnica_id = p_tecnica_id AND profesor_id = p_profesor_id;

    RETURN QUERY SELECT COALESCE(ids, ARRAY[]::uuid[]);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_delete_teoria_by_tecnica_profesor(uuid, uuid) TO anon;
