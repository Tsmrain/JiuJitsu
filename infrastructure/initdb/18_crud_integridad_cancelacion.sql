-- ==============================================================================
-- MIGRACIÓN 18: COMPLETITUD CRUD, INTEGRIDAD QDRANT↔POSTGRES Y CANCELACIÓN
-- 1. RPC admin_delete_manual_teoria: limpia filas en teoria_referencia y devuelve IDs Qdrant
-- 2. RPC cancelar_evaluacion + guarda en worker_update_result contra estado 'cancelado'
-- 3. RPC admin_delete_user: elimina usuario con validación/reasignación de profesor o cascada
-- ==============================================================================

-- 1. Eliminar registros de teoría de un manual en Postgres y retornar sus qdrant_point_id y URLs
DROP FUNCTION IF EXISTS admin_delete_manual_teoria(TEXT);
CREATE OR REPLACE FUNCTION admin_delete_manual_teoria(p_filename TEXT)
RETURNS TABLE (
    deleted_count INT,
    deleted_qdrant_ids UUID[],
    deleted_urls TEXT[]
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_basename TEXT := regexp_replace(COALESCE(p_filename, ''), '^.*/', '');
    v_ids UUID[];
    v_urls TEXT[];
    v_count INT := 0;
BEGIN
    IF v_basename = '' THEN
        RETURN QUERY SELECT 0, ARRAY[]::UUID[], ARRAY[]::TEXT[];
        RETURN;
    END IF;

    WITH deleted AS (
        DELETE FROM teoria_referencia
        WHERE fuente_nombre = p_filename
           OR fuente_nombre = v_basename
           OR (fuente_url IS NOT NULL AND fuente_url ILIKE '%' || v_basename || '%')
        RETURNING qdrant_point_id, fuente_url
    )
    SELECT
        ARRAY_AGG(qdrant_point_id),
        ARRAY_AGG(DISTINCT fuente_url) FILTER (WHERE fuente_url IS NOT NULL),
        COUNT(*)::INT
    INTO v_ids, v_urls, v_count
    FROM deleted;

    RETURN QUERY SELECT COALESCE(v_count, 0), COALESCE(v_ids, ARRAY[]::UUID[]), COALESCE(v_urls, ARRAY[]::TEXT[]);
END;
$$;

GRANT EXECUTE ON FUNCTION admin_delete_manual_teoria(TEXT) TO anon, alumno, profesor, admin, postgres;

-- 2. Cancelación transaccional de evaluaciones
DROP FUNCTION IF EXISTS cancelar_evaluacion(UUID, UUID, BOOLEAN);
CREATE OR REPLACE FUNCTION cancelar_evaluacion(
    p_evaluacion_id UUID,
    p_usuario_id UUID,
    p_es_admin BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    found BOOLEAN,
    authorized BOOLEAN,
    cancelled BOOLEAN,
    estado_actual VARCHAR,
    url_video_alumno TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_eval RECORD;
BEGIN
    SELECT e.id, e.alumno_id, e.estado, e.url_video_alumno
    INTO v_eval
    FROM evaluaciones_alumnos e
    WHERE e.id = p_evaluacion_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, FALSE, FALSE, NULL::VARCHAR, NULL::TEXT;
        RETURN;
    END IF;

    IF NOT p_es_admin AND v_eval.alumno_id <> p_usuario_id THEN
        RETURN QUERY SELECT TRUE, FALSE, FALSE, v_eval.estado, NULL::TEXT;
        RETURN;
    END IF;

    IF v_eval.estado IN ('procesando', 'en_progreso_worker') THEN
        UPDATE evaluaciones_alumnos
        SET estado = 'cancelado'
        WHERE id = p_evaluacion_id;

        RETURN QUERY SELECT TRUE, TRUE, TRUE, 'cancelado'::VARCHAR, v_eval.url_video_alumno::TEXT;
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE, TRUE, FALSE, v_eval.estado, v_eval.url_video_alumno::TEXT;
END;
$$;

GRANT EXECUTE ON FUNCTION cancelar_evaluacion(UUID, UUID, BOOLEAN) TO anon, alumno, profesor, admin, postgres;

-- 2b. Proteger worker_update_result para nunca sobrescribir evaluaciones canceladas
DROP FUNCTION IF EXISTS worker_update_result(uuid, numeric, text, text);
DROP FUNCTION IF EXISTS worker_update_result(uuid, numeric, text, text, text);
CREATE OR REPLACE FUNCTION worker_update_result(
    p_evaluacion_id uuid,
    p_similitud numeric,
    p_feedback_es text,
    p_estado text,
    p_feedback_summary text DEFAULT NULL
)
RETURNS boolean AS $$
DECLARE
    updated_count int;
BEGIN
    UPDATE evaluaciones_alumnos
    SET
        porcentaje_similitud = p_similitud,
        feedback_gemini_es = p_feedback_es,
        estado = p_estado,
        feedback_summary = COALESCE(p_feedback_summary, feedback_summary)
    WHERE id = p_evaluacion_id
      AND estado <> 'cancelado';

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION worker_update_result(uuid, numeric, text, text, text) TO anon, alumno, profesor, admin, postgres;

-- 3. Eliminar usuario (Admin) con protección de FKs / reasignación de profesor y cascada en alumno
DROP FUNCTION IF EXISTS admin_delete_user(UUID, UUID, UUID);
CREATE OR REPLACE FUNCTION admin_delete_user(
    p_user_id UUID,
    p_caller_id UUID DEFAULT NULL,
    p_reasignar_a UUID DEFAULT NULL
)
RETURNS TABLE (
    deleted BOOLEAN,
    reason TEXT,
    reassigned_count INT,
    deleted_role VARCHAR
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_user RECORD;
    v_videos INT := 0;
    v_patrones INT := 0;
    v_teoria INT := 0;
    v_total_refs INT := 0;
    v_reassigned INT := 0;
BEGIN
    SELECT u.id, u.rol INTO v_user
    FROM usuarios u
    WHERE u.id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'NOT_FOUND'::TEXT, 0, NULL::VARCHAR;
        RETURN;
    END IF;

    IF p_caller_id IS NOT NULL AND p_user_id = p_caller_id THEN
        RETURN QUERY SELECT FALSE, 'SELF_DELETE_FORBIDDEN'::TEXT, 0, v_user.rol;
        RETURN;
    END IF;

    SELECT COUNT(*)::INT INTO v_videos FROM videos_referencia WHERE profesor_id = p_user_id;
    SELECT COUNT(*)::INT INTO v_patrones FROM patrones_referencia WHERE profesor_id = p_user_id;
    SELECT COUNT(*)::INT INTO v_teoria FROM teoria_referencia WHERE profesor_id = p_user_id;
    v_total_refs := v_videos + v_patrones + v_teoria;

    IF v_total_refs > 0 THEN
        IF p_reasignar_a IS NOT NULL AND p_reasignar_a <> p_user_id AND EXISTS (SELECT 1 FROM usuarios WHERE id = p_reasignar_a) THEN
            UPDATE videos_referencia SET profesor_id = p_reasignar_a WHERE profesor_id = p_user_id;
            UPDATE patrones_referencia SET profesor_id = p_reasignar_a WHERE profesor_id = p_user_id;
            UPDATE teoria_referencia SET profesor_id = p_reasignar_a WHERE profesor_id = p_user_id;
            v_reassigned := v_total_refs;
        ELSE
            RETURN QUERY SELECT FALSE, 'PROFESOR_HAS_CONTENT'::TEXT, v_total_refs, v_user.rol;
            RETURN;
        END IF;
    END IF;

    DELETE FROM usuarios WHERE id = p_user_id;
    RETURN QUERY SELECT TRUE, 'DELETED'::TEXT, v_reassigned, v_user.rol;
END;
$$;

GRANT EXECUTE ON FUNCTION admin_delete_user(UUID, UUID, UUID) TO anon, alumno, profesor, admin, postgres;
