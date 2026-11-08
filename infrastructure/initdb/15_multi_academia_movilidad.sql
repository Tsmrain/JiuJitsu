-- ==============================================================================
-- MIGRACIÓN 15: MOVILIDAD MULTI-ACADEMIA E INTEGRIDAD HISTÓRICA (ITERACIÓN 4C)
-- Congela la sucursal en el momento de la evaluación para preservar la historia
-- aún cuando el practicante cambie de academia o viaje.
-- ==============================================================================

-- 1. Agregar columna sucursal_id a evaluaciones_alumnos si no existe
ALTER TABLE evaluaciones_alumnos
ADD COLUMN IF NOT EXISTS sucursal_id UUID REFERENCES sucursales(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_evaluaciones_sucursal ON evaluaciones_alumnos(sucursal_id);

-- 2. Backfill: Actualizar evaluaciones pasadas con la sucursal actual del alumno
UPDATE evaluaciones_alumnos e
SET sucursal_id = u.sucursal_id
FROM usuarios u
WHERE e.alumno_id = u.id
  AND e.sucursal_id IS NULL
  AND u.sucursal_id IS NOT NULL;

-- Asignar sucursal por defecto (Casa Matriz) a cualquier evaluación huérfana
UPDATE evaluaciones_alumnos
SET sucursal_id = 'b3000000-0000-0000-0000-000000000003'
WHERE sucursal_id IS NULL;

-- 3. Stored Procedure: create_evaluacion congelando la sucursal actual
DROP FUNCTION IF EXISTS create_evaluacion(UUID, UUID, UUID, UUID, TEXT);
DROP FUNCTION IF EXISTS create_evaluacion(UUID, UUID, UUID, UUID, TEXT, UUID);

CREATE OR REPLACE FUNCTION create_evaluacion(
    p_id UUID,
    p_alumno_id UUID,
    p_tecnica_id UUID,
    p_video_referencia_id UUID,
    p_url_video_alumno TEXT,
    p_sucursal_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    alumno_id UUID,
    tecnica_id UUID,
    video_referencia_id UUID,
    url_video_alumno VARCHAR,
    estado VARCHAR,
    sucursal_id UUID
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_sucursal_id UUID := p_sucursal_id;
BEGIN
    -- Si la sucursal suministrada no existe en sucursales (stale token), anular para resolver de BD
    IF v_sucursal_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sucursales s WHERE s.id = v_sucursal_id) THEN
        v_sucursal_id := NULL;
    END IF;

    -- Si no se suministra explícitamente o era inválida, congelar la sucursal actual del alumno
    IF v_sucursal_id IS NULL THEN
        SELECT u.sucursal_id INTO v_sucursal_id FROM usuarios u WHERE u.id = p_alumno_id;
    END IF;

    -- Si la sucursal del alumno tampoco existe o era NULL, asignar Casa Matriz por defecto
    IF v_sucursal_id IS NULL OR NOT EXISTS (SELECT 1 FROM sucursales s WHERE s.id = v_sucursal_id) THEN
        v_sucursal_id := 'b3000000-0000-0000-0000-000000000003'::UUID;
    END IF;

    INSERT INTO evaluaciones_alumnos (
        id, alumno_id, tecnica_id, video_referencia_id, url_video_alumno, estado, sucursal_id
    )
    VALUES (
        p_id, p_alumno_id, p_tecnica_id, p_video_referencia_id, p_url_video_alumno, 'procesando', v_sucursal_id
    );

    RETURN QUERY
    SELECT e.id, e.alumno_id, e.tecnica_id, e.video_referencia_id, e.url_video_alumno, e.estado, e.sucursal_id
    FROM evaluaciones_alumnos e
    WHERE e.id = p_id;
END;
$$;

GRANT EXECUTE ON FUNCTION create_evaluacion(UUID, UUID, UUID, UUID, TEXT, UUID) TO public, anon;

-- 4. Stored Procedure: admin_list_evaluaciones_alumno con sucursal congelada histórica
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
    video_referencia_profesor_nombre VARCHAR,
    sucursal_id UUID,
    sucursal_nombre VARCHAR
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
        COALESCE(u_prof.nombre_completo, 'Profesor')::VARCHAR,
        e.sucursal_id,
        COALESCE(s.nombre, 'Sucursal no registrada')::VARCHAR AS sucursal_nombre
    FROM evaluaciones_alumnos e
    LEFT JOIN tecnicas t ON t.id = e.tecnica_id
    LEFT JOIN videos_referencia vr ON vr.id = e.video_referencia_id
    LEFT JOIN usuarios u_prof ON u_prof.id = vr.profesor_id
    LEFT JOIN sucursales s ON s.id = e.sucursal_id
    WHERE e.alumno_id = p_alumno_id
    ORDER BY e.fecha_evaluacion DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_evaluaciones_alumno(UUID) TO public, anon;

-- 5. Stored Procedure: cambiar sucursal de un usuario preservando historial
DROP FUNCTION IF EXISTS admin_cambiar_sucursal_usuario(UUID, UUID);
CREATE OR REPLACE FUNCTION admin_cambiar_sucursal_usuario(
    p_user_id UUID,
    p_nueva_sucursal_id UUID
)
RETURNS TABLE(
    id UUID,
    nombre_completo VARCHAR,
    username VARCHAR,
    sucursal_anterior_id UUID,
    sucursal_nueva_id UUID,
    sucursal_nueva_nombre VARCHAR
) AS $$
DECLARE
    v_old_sucursal_id UUID;
    v_nueva_nombre VARCHAR;
BEGIN
    -- Validar que la nueva sucursal exista
    SELECT s.nombre INTO v_nueva_nombre FROM sucursales s WHERE s.id = p_nueva_sucursal_id;
    IF v_nueva_nombre IS NULL THEN
        RAISE EXCEPTION 'Sucursal destino no encontrada';
    END IF;

    -- Obtener sucursal actual
    SELECT u.sucursal_id INTO v_old_sucursal_id FROM usuarios u WHERE u.id = p_user_id;

    -- Actualizar usuario a la nueva sucursal (las evaluaciones pasadas en evaluaciones_alumnos NO se tocan)
    UPDATE usuarios
    SET sucursal_id = p_nueva_sucursal_id
    WHERE usuarios.id = p_user_id;

    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        v_old_sucursal_id,
        p_nueva_sucursal_id,
        v_nueva_nombre
    FROM usuarios u
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_cambiar_sucursal_usuario(UUID, UUID) TO public, anon;

NOTIFY pgrst, 'reload schema';

