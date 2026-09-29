-- ==============================================================================
-- AUTENTICACIÓN Y ROLES PARA POSTGREST - ITERACIÓN C2
-- ==============================================================================

-- Habilitar extensión pgcrypto para hash de contraseñas
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Crear roles de PostgREST
-- El rol authenticator es usado por la conexión de BD de PostgREST
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'mysecretpassword';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'alumno') THEN
        CREATE ROLE alumno NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'profesor') THEN
        CREATE ROLE profesor NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
        CREATE ROLE admin NOLOGIN;
    END IF;
END
$$;

GRANT anon TO authenticator;
GRANT alumno TO authenticator;
GRANT profesor TO authenticator;
GRANT admin TO authenticator;

-- 2. Estructura del JWT
CREATE TYPE jwt_token AS (
    token text
);

-- 3. Función de Autenticación (Login)
-- Busca por email O username para compatibilidad con el formulario de login del frontend.
CREATE OR REPLACE FUNCTION authenticate(
    email text,
    password text
) RETURNS jwt_token AS $$
DECLARE
    account usuarios;
    token_str text;
BEGIN
    SELECT a.* INTO account
    FROM usuarios AS a
    WHERE a.email = authenticate.email
       OR a.username = authenticate.email;

    IF account IS NULL THEN
        RETURN NULL;
    END IF;

    -- Verificar contraseña: bcrypt (producción)
    IF account.password_hash = crypt(password, account.password_hash)
    THEN
        token_str := format(
            '{"role": "%s", "email": "%s", "uid": "%s", "sucursal_id": "%s"}',
            account.rol,
            account.email,
            account.id,
            COALESCE(account.sucursal_id::text, '')
        );
        -- row() explícito para evitar "malformed record literal" en PostgREST
        RETURN row(token_str)::jwt_token;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Función de Registro (Signup)
CREATE OR REPLACE FUNCTION signup(
    nombre_completo text,
    email text,
    password text,
    rol text,
    sucursal_id uuid
) RETURNS void AS $$
BEGIN
    INSERT INTO usuarios (nombre_completo, email, password_hash, rol, sucursal_id)
    VALUES (
        signup.nombre_completo,
        signup.email,
        crypt(signup.password, gen_salt('bf')),
        signup.rol,
        signup.sucursal_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Permisos
GRANT EXECUTE ON FUNCTION authenticate(text, text) TO anon;
GRANT EXECUTE ON FUNCTION signup(text, text, text, text, uuid) TO anon;
GRANT USAGE ON SCHEMA public TO anon, alumno, profesor, admin;

-- 5. Función de Perfil (SECURITY DEFINER — lectura segura sin exponer la tabla usuarios a anon)
-- Usada por el backend tras la autenticación para obtener nombre_completo, username, avatar_url, etc.
DROP FUNCTION IF EXISTS get_user_profile(uuid);
CREATE FUNCTION get_user_profile(user_id uuid)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.nombre_completo, u.username, u.email, u.rol, u.avatar_url, u.sucursal_id
    FROM usuarios u
    WHERE u.id = get_user_profile.user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_user_profile(uuid) TO anon;

-- anon puede leer sucursales para mostrar el nombre de la sucursal al hacer login
GRANT SELECT ON sucursales TO anon;
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename='sucursales' AND policyname='anon_read_sucursales'
  ) THEN
    CREATE POLICY anon_read_sucursales ON sucursales FOR SELECT TO anon USING (true);
  END IF;
END $$;

-- ==============================================================================
-- C10.3 — REVERTIR regresión de seguridad introducida por Task 5
-- El rol anon NO debe leer la tabla usuarios directamente.
-- Todo acceso se hace por funciones SECURITY DEFINER.
-- ==============================================================================

REVOKE SELECT ON usuarios FROM anon;
DROP POLICY IF EXISTS anon_read_usuarios ON usuarios;

-- ==============================================================================
-- RPCs ADMIN (SECURITY DEFINER) — la validación de rol admin se hace en Python
-- ==============================================================================

-- 1. Listar todos los usuarios con nombre de sucursal
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
    sucursal_nombre varchar
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
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    ORDER BY u.fecha_registro;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_users() TO anon;

-- 2. Obtener un usuario por ID (con sucursal)
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
    sucursal_nombre varchar
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
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_get_user_full(uuid) TO anon;

-- 3. Actualizar un usuario (hash de password dentro de la función)
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
    sucursal_nombre varchar
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
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_update_user(uuid, text, text, text) TO anon;

-- 4. Listar profesores (con filtro opcional por sucursal)
DROP FUNCTION IF EXISTS admin_list_profesores(uuid);
CREATE OR REPLACE FUNCTION admin_list_profesores(p_sucursal_id uuid DEFAULT NULL)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    avatar_url text,
    sucursal_id uuid,
    sucursal_nombre varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        u.email,
        u.avatar_url,
        u.sucursal_id,
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.rol = 'profesor'
      AND (p_sucursal_id IS NULL OR u.sucursal_id = p_sucursal_id)
    ORDER BY u.fecha_registro;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_profesores(uuid) TO anon;

-- 5. Signup público (hash de password dentro de la función)
DROP FUNCTION IF EXISTS public_signup(text, text, text, text, text, uuid);
CREATE OR REPLACE FUNCTION public_signup(
    p_nombre_completo text,
    p_username text,
    p_email text,
    p_password text,
    p_rol text,
    p_sucursal_id uuid
)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid
) AS $$
DECLARE
    new_id uuid;
BEGIN
    INSERT INTO usuarios (nombre_completo, username, email, password_hash, rol, sucursal_id)
    VALUES (
        p_nombre_completo,
        p_username,
        p_email,
        crypt(p_password, gen_salt('bf')),
        p_rol,
        p_sucursal_id
    )
    RETURNING usuarios.id INTO new_id;

    RETURN QUERY
    SELECT u.id, u.nombre_completo, u.username, u.email, u.rol, u.avatar_url, u.sucursal_id
    FROM usuarios u
    WHERE u.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public_signup(text, text, text, text, text, uuid) TO anon;

-- ==============================================================================
-- C10.4 — RPCs ADMIN para CRUD de Sucursales
-- Migra las operaciones de escritura de la tabla sucursales a SECURITY DEFINER
-- para que no dependan del rol anon (que NO tiene INSERT/UPDATE/DELETE).
-- ==============================================================================

-- 1. Crear sucursal
DROP FUNCTION IF EXISTS admin_create_sucursal(text, text, text, text, numeric, numeric);
CREATE OR REPLACE FUNCTION admin_create_sucursal(
    p_nombre text,
    p_pais text,
    p_ciudad text,
    p_direccion text,
    p_latitud numeric,
    p_longitud numeric
)
RETURNS TABLE(
    id uuid,
    nombre varchar,
    pais varchar,
    ciudad varchar,
    direccion varchar,
    latitud numeric,
    longitud numeric
) AS $$
DECLARE
    new_id uuid;
BEGIN
    INSERT INTO sucursales (nombre, pais, ciudad, direccion, latitud, longitud)
    VALUES (p_nombre, p_pais, p_ciudad, p_direccion, p_latitud, p_longitud)
    RETURNING sucursales.id INTO new_id;

    RETURN QUERY
    SELECT s.id, s.nombre, s.pais, s.ciudad, s.direccion, s.latitud, s.longitud
    FROM sucursales s
    WHERE s.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_create_sucursal(text, text, text, text, numeric, numeric) TO anon;

-- 2. Actualizar sucursal
DROP FUNCTION IF EXISTS admin_update_sucursal(uuid, text, text, text, text, numeric, numeric);
CREATE OR REPLACE FUNCTION admin_update_sucursal(
    p_sucursal_id uuid,
    p_nombre text,
    p_pais text,
    p_ciudad text,
    p_direccion text,
    p_latitud numeric,
    p_longitud numeric
)
RETURNS TABLE(
    id uuid,
    nombre varchar,
    pais varchar,
    ciudad varchar,
    direccion varchar,
    latitud numeric,
    longitud numeric
) AS $$
BEGIN
    UPDATE sucursales
    SET
        nombre = p_nombre,
        pais = p_pais,
        ciudad = p_ciudad,
        direccion = p_direccion,
        latitud = p_latitud,
        longitud = p_longitud
    WHERE sucursales.id = p_sucursal_id;

    RETURN QUERY
    SELECT s.id, s.nombre, s.pais, s.ciudad, s.direccion, s.latitud, s.longitud
    FROM sucursales s
    WHERE s.id = p_sucursal_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_update_sucursal(uuid, text, text, text, text, numeric, numeric) TO anon;

-- 3. Contar usuarios en una sucursal (evita que anon lea la tabla usuarios)
DROP FUNCTION IF EXISTS admin_count_users_in_sucursal(uuid);
CREATE OR REPLACE FUNCTION admin_count_users_in_sucursal(p_sucursal_id uuid)
RETURNS bigint AS $$
DECLARE
    cnt bigint;
BEGIN
    SELECT COUNT(*) INTO cnt
    FROM usuarios
    WHERE sucursal_id = p_sucursal_id;
    RETURN cnt;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_count_users_in_sucursal(uuid) TO anon;

-- 4. Eliminar sucursal (valida que no tenga usuarios dentro de la función)
DROP FUNCTION IF EXISTS admin_delete_sucursal(uuid);
CREATE OR REPLACE FUNCTION admin_delete_sucursal(p_sucursal_id uuid)
RETURNS boolean AS $$
DECLARE
    user_count bigint;
    deleted_count int;
BEGIN
    SELECT COUNT(*) INTO user_count
    FROM usuarios
    WHERE sucursal_id = p_sucursal_id;

    IF user_count > 0 THEN
        RAISE EXCEPTION 'SUCURSAL_CON_USUARIOS: La sucursal tiene % usuarios vinculados.', user_count;
    END IF;

    DELETE FROM sucursales WHERE id = p_sucursal_id;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_delete_sucursal(uuid) TO anon;

-- ==============================================================================
-- C10.5 — RPCs para el flujo de evaluaciones (usuario)
-- Migra lecturas/escrituras de videos_referencia y evaluaciones_alumnos
-- a funciones SECURITY DEFINER.
-- ==============================================================================

-- 1. Buscar video de referencia para una técnica
DROP FUNCTION IF EXISTS get_video_referencia_by_tecnica(uuid);
CREATE OR REPLACE FUNCTION get_video_referencia_by_tecnica(p_tecnica_id uuid)
RETURNS TABLE(
    id uuid,
    url_video_gcs varchar,
    profesor_id uuid
) AS $$
BEGIN
    RETURN QUERY
    SELECT vr.id, vr.url_video_gcs, vr.profesor_id
    FROM videos_referencia vr
    WHERE vr.tecnica_id = p_tecnica_id
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_video_referencia_by_tecnica(uuid) TO anon;

-- 2. Crear evaluación de alumno
DROP FUNCTION IF EXISTS create_evaluacion(uuid, uuid, uuid, uuid, text);
CREATE OR REPLACE FUNCTION create_evaluacion(
    p_id uuid,
    p_alumno_id uuid,
    p_tecnica_id uuid,
    p_video_referencia_id uuid,
    p_url_video_alumno text
)
RETURNS TABLE(
    id uuid,
    alumno_id uuid,
    tecnica_id uuid,
    video_referencia_id uuid,
    url_video_alumno varchar,
    estado varchar
) AS $$
BEGIN
    INSERT INTO evaluaciones_alumnos (
        id, alumno_id, tecnica_id, video_referencia_id, url_video_alumno, estado
    )
    VALUES (
        p_id, p_alumno_id, p_tecnica_id, p_video_referencia_id, p_url_video_alumno, 'procesando'
    );

    RETURN QUERY
    SELECT e.id, e.alumno_id, e.tecnica_id, e.video_referencia_id, e.url_video_alumno, e.estado
    FROM evaluaciones_alumnos e
    WHERE e.id = p_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION create_evaluacion(uuid, uuid, uuid, uuid, text) TO anon;

-- 3. Obtener evaluación por id (con nombre de técnica y video de referencia del profesor)
DROP FUNCTION IF EXISTS get_evaluacion_by_id(uuid);
CREATE OR REPLACE FUNCTION get_evaluacion_by_id(p_evaluacion_id uuid)
RETURNS TABLE(
    id uuid,
    alumno_id uuid,
    tecnica_id uuid,
    tecnica_nombre varchar,
    estado varchar,
    porcentaje_similitud numeric,
    feedback_gemini_es text,
    feedback_gemini_pt text,
    video_referencia_url varchar,
    video_referencia_profesor_nombre varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.alumno_id,
        e.tecnica_id,
        COALESCE(t.nombre, 'Técnica')::varchar AS tecnica_nombre,
        e.estado,
        e.porcentaje_similitud,
        e.feedback_gemini_es,
        e.feedback_gemini_pt,
        COALESCE(vr.url_video_gcs, '')::varchar AS video_referencia_url,
        COALESCE(u_prof.nombre_completo, 'Profesor')::varchar AS video_referencia_profesor_nombre
    FROM evaluaciones_alumnos e
    LEFT JOIN tecnicas t ON t.id = e.tecnica_id
    LEFT JOIN videos_referencia vr ON vr.id = e.video_referencia_id
    LEFT JOIN usuarios u_prof ON u_prof.id = vr.profesor_id
    WHERE e.id = p_evaluacion_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_evaluacion_by_id(uuid) TO anon;

-- ==============================================================================
-- C10.6 — RPC para listar técnicas con su video de referencia
-- ==============================================================================

DROP FUNCTION IF EXISTS get_tecnicas_with_videos();
CREATE OR REPLACE FUNCTION get_tecnicas_with_videos()
RETURNS TABLE(
    id uuid,
    nombre varchar,
    nivel_cinturon varchar,
    video_id uuid,
    video_profesor_id uuid,
    video_url varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.nombre,
        t.nivel_cinturon,
        vr.id AS video_id,
        vr.profesor_id AS video_profesor_id,
        vr.url_video_gcs AS video_url
    FROM tecnicas t
    LEFT JOIN videos_referencia vr ON vr.tecnica_id = t.id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_tecnicas_with_videos() TO anon;

-- Verificar técnica existe (para subir_video_referencia)
DROP FUNCTION IF EXISTS tecnica_exists(uuid);
CREATE OR REPLACE FUNCTION tecnica_exists(p_tecnica_id uuid)
RETURNS boolean AS $$
DECLARE
    cnt bigint;
BEGIN
    SELECT COUNT(*) INTO cnt FROM tecnicas WHERE id = p_tecnica_id;
    RETURN cnt > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION tecnica_exists(uuid) TO anon;

-- ==============================================================================
-- C10.7 — RPCs para CRUD de técnicas y videos de referencia
-- Migra operaciones de escritura que fallan por RLS con anon.
-- ==============================================================================

-- 1. Crear técnica
DROP FUNCTION IF EXISTS admin_create_tecnica(text, text);
CREATE OR REPLACE FUNCTION admin_create_tecnica(
    p_nombre text,
    p_nivel_cinturon text
)
RETURNS TABLE(id uuid, nombre varchar, nivel_cinturon varchar) AS $$
DECLARE
    new_id uuid;
BEGIN
    INSERT INTO tecnicas (nombre, nivel_cinturon)
    VALUES (p_nombre, p_nivel_cinturon)
    RETURNING tecnicas.id INTO new_id;

    RETURN QUERY
    SELECT t.id, t.nombre, t.nivel_cinturon FROM tecnicas t WHERE t.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_create_tecnica(text, text) TO anon;

-- 2. Actualizar técnica
DROP FUNCTION IF EXISTS admin_update_tecnica(uuid, text, text);
CREATE OR REPLACE FUNCTION admin_update_tecnica(
    p_tecnica_id uuid,
    p_nombre text,
    p_nivel_cinturon text
)
RETURNS TABLE(id uuid, nombre varchar, nivel_cinturon varchar) AS $$
BEGIN
    UPDATE tecnicas
    SET nombre = p_nombre, nivel_cinturon = p_nivel_cinturon
    WHERE tecnicas.id = p_tecnica_id;

    RETURN QUERY
    SELECT t.id, t.nombre, t.nivel_cinturon FROM tecnicas t WHERE t.id = p_tecnica_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_update_tecnica(uuid, text, text) TO anon;

-- 3. Eliminar técnica
DROP FUNCTION IF EXISTS admin_delete_tecnica(uuid);
CREATE OR REPLACE FUNCTION admin_delete_tecnica(p_tecnica_id uuid)
RETURNS boolean AS $$
DECLARE
    deleted_count int;
BEGIN
    DELETE FROM tecnicas WHERE id = p_tecnica_id;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_delete_tecnica(uuid) TO anon;

-- 4. Guardar (upsert) video de referencia de un profesor para una técnica
DROP FUNCTION IF EXISTS admin_save_video_referencia(uuid, uuid, text);
CREATE OR REPLACE FUNCTION admin_save_video_referencia(
    p_tecnica_id uuid,
    p_profesor_id uuid,
    p_url_video text
)
RETURNS TABLE(video_id uuid) AS $$
DECLARE
    new_id uuid;
BEGIN
    -- Borrar si existía para esta técnica + profesor
    DELETE FROM videos_referencia
    WHERE tecnica_id = p_tecnica_id AND profesor_id = p_profesor_id;

    INSERT INTO videos_referencia (tecnica_id, profesor_id, url_video_gcs, vector_qdrant_id)
    VALUES (p_tecnica_id, p_profesor_id, p_url_video, uuid_generate_v4())
    RETURNING videos_referencia.id INTO new_id;

    RETURN QUERY SELECT new_id AS video_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_save_video_referencia(uuid, uuid, text) TO anon;

-- 5. Listar alumnos de una sucursal (para el panel del profesor)
DROP FUNCTION IF EXISTS admin_list_alumnos(uuid);
CREATE OR REPLACE FUNCTION admin_list_alumnos(p_sucursal_id uuid DEFAULT NULL)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    avatar_url text,
    sucursal_id uuid,
    sucursal_nombre varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.nombre_completo,
        u.username,
        u.email,
        u.avatar_url,
        u.sucursal_id,
        COALESCE(s.nombre, 'Sucursal Eliminada')::varchar AS sucursal_nombre
    FROM usuarios u
    LEFT JOIN sucursales s ON s.id = u.sucursal_id
    WHERE u.rol = 'alumno'
      AND (p_sucursal_id IS NULL OR u.sucursal_id = p_sucursal_id)
    ORDER BY u.fecha_registro;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_alumnos(uuid) TO anon;

-- ==============================================================================
-- C10.8 — RPC para listar evaluaciones de un alumno (panel del profesor)
-- ==============================================================================

DROP FUNCTION IF EXISTS admin_list_evaluaciones_alumno(uuid);
CREATE OR REPLACE FUNCTION admin_list_evaluaciones_alumno(p_alumno_id uuid)
RETURNS TABLE(
    id uuid,
    tecnica_nombre varchar,
    porcentaje_similitud numeric,
    estado varchar,
    feedback_gemini_es text,
    feedback_gemini_pt text,
    fecha_evaluacion timestamp with time zone
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        COALESCE(t.nombre, 'Técnica')::varchar AS tecnica_nombre,
        e.porcentaje_similitud,
        e.estado,
        e.feedback_gemini_es,
        e.feedback_gemini_pt,
        e.fecha_evaluacion
    FROM evaluaciones_alumnos e
    LEFT JOIN tecnicas t ON t.id = e.tecnica_id
    WHERE e.alumno_id = p_alumno_id
    ORDER BY e.fecha_evaluacion DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_list_evaluaciones_alumno(uuid) TO anon;

-- ==============================================================================
-- C10.9 — RPCs para el Worker de Colab
-- Migra las operaciones del worker (polling, update de estado) a SECURITY DEFINER.
-- El worker se autentica con X-Worker-Token en FastAPI, no con JWT de usuario.
-- ==============================================================================

-- 1. Obtener la siguiente evaluación pendiente y marcarla como en progreso (atómico)
DROP FUNCTION IF EXISTS worker_claim_next_pending();
CREATE OR REPLACE FUNCTION worker_claim_next_pending()
RETURNS TABLE(
    id uuid,
    video_path varchar,
    tecnica_id uuid,
    tecnica_nombre varchar,
    estado varchar
) AS $$
DECLARE
    claimed_id uuid;
BEGIN
    -- Bloqueo para evitar doble asignación
    SELECT e.id INTO claimed_id
    FROM evaluaciones_alumnos e
    WHERE e.estado = 'procesando'
    ORDER BY e.fecha_evaluacion ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    IF claimed_id IS NULL THEN
        RETURN;
    END IF;

    UPDATE evaluaciones_alumnos
    SET estado = 'en_progreso_worker'
    WHERE id = claimed_id;

    RETURN QUERY
    SELECT
        e.id,
        e.url_video_alumno,
        e.tecnica_id,
        COALESCE(t.nombre, 'Técnica')::varchar AS tecnica_nombre,
        e.estado
    FROM evaluaciones_alumnos e
    LEFT JOIN tecnicas t ON t.id = e.tecnica_id
    WHERE e.id = claimed_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION worker_claim_next_pending() TO anon;

-- 2. Obtener el video_path de una evaluación (para que el worker lo descargue)
DROP FUNCTION IF EXISTS worker_get_video_path(uuid);
CREATE OR REPLACE FUNCTION worker_get_video_path(p_evaluacion_id uuid)
RETURNS TABLE(video_path varchar) AS $$
BEGIN
    RETURN QUERY
    SELECT e.url_video_alumno
    FROM evaluaciones_alumnos e
    WHERE e.id = p_evaluacion_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION worker_get_video_path(uuid) TO anon;

-- 3. Actualizar el resultado de una evaluación (usado por el worker)
DROP FUNCTION IF EXISTS worker_update_result(uuid, numeric, text, text);
CREATE OR REPLACE FUNCTION worker_update_result(
    p_evaluacion_id uuid,
    p_similitud numeric,
    p_feedback_es text,
    p_estado text
)
RETURNS boolean AS $$
DECLARE
    updated_count int;
BEGIN
    UPDATE evaluaciones_alumnos
    SET
        porcentaje_similitud = p_similitud,
        feedback_gemini_es = p_feedback_es,
        estado = p_estado
    WHERE id = p_evaluacion_id;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION worker_update_result(uuid, numeric, text, text) TO anon;

-- ==============================================================================
-- C12.7 — RPC para obtener el video de referencia de un profesor específico
-- Reemplaza el uso genérico de get_video_referencia_by_tecnica cuando el alumno
-- ha seleccionado explícitamente un profesor en el frontend.
-- ==============================================================================

DROP FUNCTION IF EXISTS get_video_referencia_by_tecnica_profesor(uuid, uuid);
CREATE OR REPLACE FUNCTION get_video_referencia_by_tecnica_profesor(
    p_tecnica_id uuid,
    p_profesor_id uuid
)
RETURNS TABLE(
    id uuid,
    url_video_gcs varchar,
    profesor_id uuid
) AS $$
BEGIN
    RETURN QUERY
    SELECT vr.id, vr.url_video_gcs, vr.profesor_id
    FROM videos_referencia vr
    WHERE vr.tecnica_id = p_tecnica_id
      AND vr.profesor_id = p_profesor_id
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_video_referencia_by_tecnica_profesor(uuid, uuid) TO anon;
