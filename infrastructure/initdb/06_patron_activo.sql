-- ==============================================================================
-- C12.10 — Migración: Patrón Biomecánico Activo en PostgreSQL
-- Establece a PostgreSQL como la fuente de verdad del patrón activo por técnica.
-- Qdrant almacena los vectores crudos (133 dims) con patron_id en payload.
-- ==============================================================================

-- 1. Añadir columna patron_activo_id a tecnicas
ALTER TABLE tecnicas
ADD COLUMN IF NOT EXISTS patron_activo_id UUID NULL;

CREATE INDEX IF NOT EXISTS idx_tecnicas_patron_activo ON tecnicas(patron_activo_id);

-- 2. RPC: Activar patrón de técnica
CREATE OR REPLACE FUNCTION admin_activar_patron_tecnica(
    p_tecnica_id UUID,
    p_patron_id UUID
)
RETURNS TABLE (
    tecnica_id UUID,
    patron_activo_id UUID,
    patron_anterior_id UUID
) AS $$
DECLARE
    v_anterior UUID;
BEGIN
    SELECT t.patron_activo_id INTO v_anterior
    FROM tecnicas t
    WHERE t.id = p_tecnica_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Técnica con ID % no encontrada.', p_tecnica_id;
    END IF;

    UPDATE tecnicas
    SET patron_activo_id = p_patron_id
    WHERE id = p_tecnica_id;

    RETURN QUERY
    SELECT p_tecnica_id, p_patron_id, v_anterior;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_activar_patron_tecnica(UUID, UUID) TO anon;

-- 3. RPC: Obtener ID del patrón activo
CREATE OR REPLACE FUNCTION get_patron_activo(
    p_tecnica_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_patron_id UUID;
BEGIN
    SELECT patron_activo_id INTO v_patron_id
    FROM tecnicas
    WHERE id = p_tecnica_id;

    RETURN v_patron_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_patron_activo(UUID) TO anon;
