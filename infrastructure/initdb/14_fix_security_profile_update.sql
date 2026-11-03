-- ==============================================================================
-- MIGRACIÓN 14: FIX DE SEGURIDAD EN ACTUALIZACIÓN DE PERFIL Y RESPETO DE SUSCRIPCIÓN
-- ==============================================================================

-- 1. admin_update_user: solo actualiza nombre_completo, password_hash y avatar_url.
-- Bajo ninguna circunstancia toca estado_suscripcion ni fecha_expiracion.
DROP FUNCTION IF EXISTS admin_update_user(uuid, text, text, text);
CREATE OR REPLACE FUNCTION admin_update_user(
    p_user_id uuid,
    p_nombre text DEFAULT NULL,
    p_password text DEFAULT NULL,
    p_avatar_url text DEFAULT NULL
)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid,
    sucursal_nombre varchar,
    estado_suscripcion varchar,
    fecha_expiracion timestamptz
) AS $$
BEGIN
    UPDATE usuarios u2
    SET
        nombre_completo = COALESCE(p_nombre, u2.nombre_completo),
        password_hash = CASE
            WHEN p_password IS NOT NULL AND p_password <> ''
            THEN crypt(p_password, gen_salt('bf'))
            ELSE u2.password_hash
        END,
        avatar_url = COALESCE(p_avatar_url, u2.avatar_url)
    WHERE u2.id = p_user_id;

    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        u.email,
        u.rol,
        u.avatar_url,
        u.sucursal_id,
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre,
        u.estado_suscripcion,
        u.fecha_expiracion
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
GRANT EXECUTE ON FUNCTION admin_update_user(uuid, text, text, text) TO anon;

-- 2. admin_get_user_full: retorna también estado_suscripcion y fecha_expiracion
DROP FUNCTION IF EXISTS admin_get_user_full(uuid);
CREATE OR REPLACE FUNCTION admin_get_user_full(p_user_id uuid)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid,
    sucursal_nombre varchar,
    estado_suscripcion varchar,
    fecha_expiracion timestamptz
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        u.email,
        u.rol,
        u.avatar_url,
        u.sucursal_id,
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre,
        u.estado_suscripcion,
        u.fecha_expiracion
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
GRANT EXECUTE ON FUNCTION admin_get_user_full(uuid) TO anon;

-- 3. admin_list_users: retorna también estado_suscripcion y fecha_expiracion
DROP FUNCTION IF EXISTS admin_list_users();
CREATE OR REPLACE FUNCTION admin_list_users()
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid,
    sucursal_nombre varchar,
    estado_suscripcion varchar,
    fecha_expiracion timestamptz
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        u.email,
        u.rol,
        u.avatar_url,
        u.sucursal_id,
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre,
        u.estado_suscripcion,
        u.fecha_expiracion
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    ORDER BY u.fecha_registro;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
GRANT EXECUTE ON FUNCTION admin_list_users() TO anon;

NOTIFY pgrst, 'reload schema';
