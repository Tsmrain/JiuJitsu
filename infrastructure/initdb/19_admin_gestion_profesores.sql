-- ==============================================================================
-- MIGRACIÓN 19: GESTIÓN ADMINISTRATIVA DE PROFESORES (CREAR / MODIFICAR)
-- ==============================================================================
-- Permite al administrador (dueño de la marca) crear y modificar profesores
-- mediante RPCs SECURITY DEFINER invocadas desde FastAPI tras require_admin().
-- ==============================================================================

DROP FUNCTION IF EXISTS admin_create_profesor(text, text, text, text, uuid, text, text);
CREATE OR REPLACE FUNCTION admin_create_profesor(
    p_nombre_completo text,
    p_username text,
    p_email text,
    p_password text,
    p_sucursal_id uuid,
    p_rol text DEFAULT 'profesor',
    p_idioma_preferido text DEFAULT 'es'
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
    idioma_preferido varchar,
    estado_suscripcion varchar,
    fecha_expiracion timestamptz
) AS $$
DECLARE
    v_new_id uuid;
    v_rol_clean text := lower(trim(COALESCE(p_rol, 'profesor')));
    v_lang_clean text := lower(trim(COALESCE(p_idioma_preferido, 'es')));
BEGIN
    IF v_rol_clean NOT IN ('profesor', 'alumno') THEN
        RAISE EXCEPTION 'ROL_INVALIDO';
    END IF;
    IF v_lang_clean NOT IN ('es', 'pt', 'en') THEN
        v_lang_clean := 'es';
    END IF;

    INSERT INTO usuarios (
        nombre_completo,
        username,
        email,
        password_hash,
        rol,
        sucursal_id,
        idioma_preferido,
        estado_suscripcion,
        fecha_expiracion
    )
    VALUES (
        trim(p_nombre_completo),
        trim(p_username),
        lower(trim(p_email)),
        crypt(p_password, gen_salt('bf')),
        v_rol_clean,
        p_sucursal_id,
        v_lang_clean,
        CASE WHEN v_rol_clean = 'profesor' THEN 'activo' ELSE 'pendiente' END,
        NULL
    )
    RETURNING usuarios.id INTO v_new_id;

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
        COALESCE(u.idioma_preferido, 'es')::varchar AS idioma_preferido,
        COALESCE(u.estado_suscripcion, 'activo')::varchar AS estado_suscripcion,
        u.fecha_expiracion
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.id = v_new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_create_profesor(text, text, text, text, uuid, text, text) TO anon;


DROP FUNCTION IF EXISTS admin_manage_profesor(uuid, text, text, text, text, uuid, text, text);
CREATE OR REPLACE FUNCTION admin_manage_profesor(
    p_user_id uuid,
    p_nombre_completo text DEFAULT NULL,
    p_username text DEFAULT NULL,
    p_email text DEFAULT NULL,
    p_password text DEFAULT NULL,
    p_sucursal_id uuid DEFAULT NULL,
    p_rol text DEFAULT NULL,
    p_idioma_preferido text DEFAULT NULL
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
    idioma_preferido varchar,
    estado_suscripcion varchar,
    fecha_expiracion timestamptz
) AS $$
DECLARE
    v_rol_clean text;
    v_lang_clean text;
BEGIN
    IF p_rol IS NOT NULL AND trim(p_rol) <> '' THEN
        v_rol_clean := lower(trim(p_rol));
        IF v_rol_clean NOT IN ('profesor', 'alumno') THEN
            RAISE EXCEPTION 'ROL_INVALIDO';
        END IF;
    ELSE
        v_rol_clean := NULL;
    END IF;

    IF p_idioma_preferido IS NOT NULL AND trim(p_idioma_preferido) <> '' THEN
        v_lang_clean := lower(trim(p_idioma_preferido));
        IF v_lang_clean NOT IN ('es', 'pt', 'en') THEN
            v_lang_clean := NULL;
        END IF;
    ELSE
        v_lang_clean := NULL;
    END IF;

    UPDATE usuarios u2
    SET
        nombre_completo = COALESCE(NULLIF(trim(p_nombre_completo), ''), u2.nombre_completo),
        username = COALESCE(NULLIF(trim(p_username), ''), u2.username),
        email = COALESCE(NULLIF(lower(trim(p_email)), ''), u2.email),
        password_hash = CASE
            WHEN p_password IS NOT NULL AND trim(p_password) <> ''
            THEN crypt(p_password, gen_salt('bf'))
            ELSE u2.password_hash
        END,
        sucursal_id = COALESCE(p_sucursal_id, u2.sucursal_id),
        rol = COALESCE(v_rol_clean, u2.rol),
        idioma_preferido = COALESCE(v_lang_clean, u2.idioma_preferido),
        estado_suscripcion = CASE
            WHEN COALESCE(v_rol_clean, u2.rol) IN ('profesor', 'admin') THEN 'activo'
            ELSE u2.estado_suscripcion
        END,
        fecha_expiracion = CASE
            WHEN COALESCE(v_rol_clean, u2.rol) IN ('profesor', 'admin') THEN NULL
            ELSE u2.fecha_expiracion
        END
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
        COALESCE(u.idioma_preferido, 'es')::varchar AS idioma_preferido,
        COALESCE(u.estado_suscripcion, 'activo')::varchar AS estado_suscripcion,
        u.fecha_expiracion
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_manage_profesor(uuid, text, text, text, text, uuid, text, text) TO anon;
