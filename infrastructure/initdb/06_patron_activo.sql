-- ==============================================================================
-- C12.10 — Migración: Soporte 1:N de Patrones Biomecánicos de Referencia
-- Establece a PostgreSQL como la fuente de verdad de los patrones de referencia (1:N).
-- Qdrant almacena los vectores crudos (133 dims) con patron_id en payload.
-- ==============================================================================

-- 1. Eliminar columna patron_activo_id de tecnicas
ALTER TABLE tecnicas DROP COLUMN IF EXISTS patron_activo_id;

-- 2. Nueva tabla patrones_referencia (Relación 1:N)
CREATE TABLE IF NOT EXISTS patrones_referencia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tecnica_id UUID NOT NULL REFERENCES tecnicas(id) ON DELETE CASCADE,
    profesor_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre_referencia VARCHAR(150),
    qdrant_patron_id UUID UNIQUE NOT NULL, -- ID del patrón agrupado en Qdrant
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patrones_ref_tecnica ON patrones_referencia(tecnica_id);
CREATE INDEX IF NOT EXISTS idx_patrones_ref_profesor ON patrones_referencia(profesor_id);
CREATE INDEX IF NOT EXISTS idx_patrones_ref_qdrant ON patrones_referencia(qdrant_patron_id);

GRANT ALL ON patrones_referencia TO anon, alumno, profesor, admin, postgres;

-- 3. RPC: Activar/Registrar patrón de técnica (soporte 1:N acumulativo)
DROP FUNCTION IF EXISTS admin_activar_patron_tecnica(UUID, UUID);
DROP FUNCTION IF EXISTS admin_activar_patron_tecnica(UUID, UUID, UUID, VARCHAR);

CREATE OR REPLACE FUNCTION admin_activar_patron_tecnica(
    p_tecnica_id UUID,
    p_patron_id UUID,
    p_profesor_id UUID DEFAULT NULL,
    p_nombre_referencia VARCHAR DEFAULT 'Patrón Maestro'
)
RETURNS TABLE (
    tecnica_id UUID,
    patron_activo_id UUID,
    patron_anterior_id UUID
) AS $$
DECLARE
    v_prof_id UUID := p_profesor_id;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM tecnicas WHERE id = p_tecnica_id) THEN
        RAISE EXCEPTION 'Técnica con ID % no encontrada.', p_tecnica_id;
    END IF;

    -- Si no se suministra profesor_id, intentar resolver del usuario actual o tomar profesor de referencia
    IF v_prof_id IS NULL THEN
        BEGIN
            v_prof_id := (current_setting('request.jwt.claims', true)::jsonb ->> 'uid')::UUID;
        EXCEPTION WHEN OTHERS THEN
            v_prof_id := NULL;
        END;
    END IF;

    IF v_prof_id IS NULL OR NOT EXISTS (SELECT 1 FROM usuarios WHERE id = v_prof_id) THEN
        SELECT profesor_id INTO v_prof_id FROM videos_referencia WHERE videos_referencia.tecnica_id = p_tecnica_id LIMIT 1;
        IF v_prof_id IS NULL THEN
            SELECT id INTO v_prof_id FROM usuarios WHERE rol IN ('profesor', 'admin') LIMIT 1;
        END IF;
    END IF;

    INSERT INTO patrones_referencia (tecnica_id, profesor_id, nombre_referencia, qdrant_patron_id, activo)
    VALUES (p_tecnica_id, v_prof_id, p_nombre_referencia, p_patron_id, TRUE)
    ON CONFLICT (qdrant_patron_id) DO UPDATE SET activo = TRUE;

    -- En el modelo 1:N acumulativo, no se reemplaza ni se descarta ningún patrón anterior
    RETURN QUERY
    SELECT p_tecnica_id, p_patron_id, NULL::UUID;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_activar_patron_tecnica(UUID, UUID, UUID, VARCHAR) TO anon, alumno, profesor, admin;

-- 4. RPC: Obtener el ID del patrón activo más reciente (compatibilidad hacia atrás)
CREATE OR REPLACE FUNCTION get_patron_activo(
    p_tecnica_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_patron_id UUID;
BEGIN
    SELECT qdrant_patron_id INTO v_patron_id
    FROM patrones_referencia
    WHERE tecnica_id = p_tecnica_id AND activo = TRUE
    ORDER BY fecha_creacion DESC
    LIMIT 1;

    RETURN v_patron_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_patron_activo(UUID) TO anon, alumno, profesor, admin;

-- 5. RPC: Listar todos los patrones de referencia activos para una técnica (1:N)
CREATE OR REPLACE FUNCTION get_patrones_referencia(
    p_tecnica_id UUID
)
RETURNS TABLE (
    id UUID,
    tecnica_id UUID,
    profesor_id UUID,
    nombre_referencia VARCHAR,
    qdrant_patron_id UUID,
    activo BOOLEAN,
    fecha_creacion TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT pr.id, pr.tecnica_id, pr.profesor_id, pr.nombre_referencia, pr.qdrant_patron_id, pr.activo, pr.fecha_creacion
    FROM patrones_referencia pr
    WHERE pr.tecnica_id = p_tecnica_id AND pr.activo = TRUE
    ORDER BY pr.fecha_creacion ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_patrones_referencia(UUID) TO anon, alumno, profesor, admin;
