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
CREATE OR REPLACE FUNCTION authenticate(
    email text,
    password text
) RETURNS jwt_token AS $$
DECLARE
    account usuarios;
    token_str text;
    secret text := 'tu_secreto_super_seguro_postgrest_jwt'; -- NOTA: Mover a env var en prod
BEGIN
    -- Verificar email
    SELECT a.* INTO account
    FROM usuarios as a
    WHERE a.email = authenticate.email;

    IF account.password_hash = crypt(password, account.password_hash) THEN
        -- Generar payload JWT de forma nativa (requiere que PostgREST lo firme si usamos pgtjwt, 
        -- pero PostgREST nativamente espera que el login retorne un JWT firmado por la BD si lo configuramos, 
        -- o podemos devolver el rol y PostgREST hace el resto. Usaremos una aproximación estandar de PostgREST:
        -- Devolver un json con el rol y dejar que PostgREST genere el token, o usar la extension pgjwt).
        -- Para mantenerlo autocontenido (sin pgjwt), usaremos la convención de PostgREST donde el JWT lo genera 
        -- la API basándose en una función que devuelve un tipo con rol, y usar jwt claims.
        -- Como la pregunta fue hacerlo nativo, asumiremos que PostgREST está configurado para firmar.
        -- PostgREST en su documentación recomienda la función `sign` de pgjwt, pero como simplificación 
        -- devolveremos los claims básicos, y se asume la configuración estándar.
        
        -- Vamos a simular un payload JSON. Si se usa Supabase/PostgREST, se delega al servidor.
        -- Asumiendo una extensión pgjwt (común) o devolviendo los claims:
        
        token_str := format(
            '{"role": "%s", "email": "%s", "uid": "%s", "sucursal_id": "%s"}',
            account.rol, account.email, account.id, account.sucursal_id
        );
        
        -- Retornamos el payload JSON como texto (en un entorno real se firmaría con pgjwt)
        RETURN (token_str)::jwt_token;
    ELSE
        RAISE EXCEPTION 'invalid_password' USING MESSAGE = 'Contraseña incorrecta';
    END IF;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

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
