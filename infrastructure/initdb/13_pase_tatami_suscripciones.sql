-- ==============================================================================
-- MIGRACIÓN: CONTROL DE SUSCRIPCIONES B2B2C ("PASE DE TATAMI") - ITERACIÓN 4A
-- Metodología: Michael V. Mannino / Craig Larman
-- ==============================================================================

-- 1. Agregar columnas a tabla usuarios si no existen
ALTER TABLE usuarios 
ADD COLUMN IF NOT EXISTS estado_suscripcion VARCHAR(20) DEFAULT 'pendiente';

-- Asegurar restricción check para estado_suscripcion
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_estado_suscripcion'
    ) THEN
        ALTER TABLE usuarios 
        ADD CONSTRAINT check_estado_suscripcion 
        CHECK (estado_suscripcion IN ('pendiente', 'activo', 'expirado'));
    END IF;
END $$;

ALTER TABLE usuarios 
ADD COLUMN IF NOT EXISTS fecha_expiracion TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- 2. Asegurar que administradores y profesores estén activos sin expiración
UPDATE usuarios 
SET estado_suscripcion = 'activo', fecha_expiracion = NULL 
WHERE rol IN ('admin', 'profesor');

-- Alumno santi inicializado con pase activo de 30 días para compatibilidad de suite
UPDATE usuarios 
SET estado_suscripcion = 'activo', fecha_expiracion = CURRENT_TIMESTAMP + INTERVAL '30 days' 
WHERE username = 'santi';

-- 3. Tabla de auditoría de activaciones de pases de tatami
CREATE TABLE IF NOT EXISTS activaciones_pases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alumno_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    profesor_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    sucursal_id UUID NOT NULL REFERENCES sucursales(id) ON DELETE CASCADE,
    fecha_activacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP WITH TIME ZONE NOT NULL,
    dias_activados INT DEFAULT 30,
    notas TEXT
);

CREATE INDEX IF NOT EXISTS idx_activaciones_alumno ON activaciones_pases(alumno_id);
CREATE INDEX IF NOT EXISTS idx_activaciones_profesor ON activaciones_pases(profesor_id);

-- 4. Actualizar función get_user_profile para retornar estado_suscripcion y fecha_expiracion
DROP FUNCTION IF EXISTS get_user_profile(uuid);
CREATE FUNCTION get_user_profile(user_id uuid)
RETURNS TABLE(
    id uuid,
    nombre_completo varchar,
    username varchar,
    email varchar,
    rol varchar,
    avatar_url text,
    sucursal_id uuid,
    estado_suscripcion varchar,
    fecha_expiracion timestamptz
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.nombre_completo, u.username, u.email, u.rol, u.avatar_url, u.sucursal_id,
           u.estado_suscripcion, u.fecha_expiracion
    FROM usuarios u
    WHERE u.id = get_user_profile.user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_user_profile(uuid) TO anon, alumno, profesor, admin;

-- 5. Función RPC para listar alumnos pendientes por sucursal
CREATE OR REPLACE FUNCTION get_alumnos_pendientes(p_profesor_id UUID)
RETURNS TABLE(
    id UUID,
    nombre_completo VARCHAR,
    username VARCHAR,
    email VARCHAR,
    sucursal_id UUID,
    sucursal_nombre VARCHAR,
    avatar_url TEXT,
    fecha_registro TIMESTAMPTZ,
    estado_suscripcion VARCHAR,
    fecha_expiracion TIMESTAMPTZ
) AS $$
DECLARE
    v_profesor usuarios;
BEGIN
    SELECT * INTO v_profesor FROM usuarios WHERE usuarios.id = p_profesor_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Usuario no encontrado';
    END IF;

    IF v_profesor.rol = 'admin' THEN
        RETURN QUERY
        SELECT u.id, u.nombre_completo, u.username, u.email, u.sucursal_id, s.nombre,
               u.avatar_url, u.fecha_registro, u.estado_suscripcion, u.fecha_expiracion
        FROM usuarios u
        JOIN sucursales s ON u.sucursal_id = s.id
        WHERE u.rol = 'alumno' 
          AND (u.estado_suscripcion = 'pendiente' OR u.estado_suscripcion = 'expirado' OR (u.fecha_expiracion IS NOT NULL AND u.fecha_expiracion < NOW()))
        ORDER BY u.fecha_registro DESC;
    ELSE
        RETURN QUERY
        SELECT u.id, u.nombre_completo, u.username, u.email, u.sucursal_id, s.nombre,
               u.avatar_url, u.fecha_registro, u.estado_suscripcion, u.fecha_expiracion
        FROM usuarios u
        JOIN sucursales s ON u.sucursal_id = s.id
        WHERE u.rol = 'alumno'
          AND u.sucursal_id = v_profesor.sucursal_id
          AND (u.estado_suscripcion = 'pendiente' OR u.estado_suscripcion = 'expirado' OR (u.fecha_expiracion IS NOT NULL AND u.fecha_expiracion < NOW()))
        ORDER BY u.fecha_registro DESC;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_alumnos_pendientes(UUID) TO anon, alumno, profesor, admin;

-- 6. Función RPC para activar pase de alumno
CREATE OR REPLACE FUNCTION activar_pase_alumno(
    p_alumno_id UUID,
    p_profesor_id UUID,
    p_dias INT DEFAULT 30
) RETURNS JSONB AS $$
DECLARE
    v_alumno usuarios;
    v_profesor usuarios;
    v_nueva_expiracion TIMESTAMPTZ;
BEGIN
    -- Validar que el profesor existe y es staff (profesor o admin)
    SELECT * INTO v_profesor FROM usuarios WHERE id = p_profesor_id AND rol IN ('profesor', 'admin');
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Profesor o Administrador no autorizado';
    END IF;

    -- Validar alumno
    SELECT * INTO v_alumno FROM usuarios WHERE id = p_alumno_id AND rol = 'alumno';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Alumno no encontrado';
    END IF;

    -- Validar misma sucursal (a menos que sea admin)
    IF v_profesor.rol = 'profesor' AND v_profesor.sucursal_id != v_alumno.sucursal_id THEN
        RAISE EXCEPTION 'El profesor solo puede activar alumnos de su propia sucursal';
    END IF;

    -- Calcular nueva fecha de expiración: si ya estaba activo y no ha expirado, extender; sino NOW() + INTERVAL
    IF v_alumno.fecha_expiracion IS NOT NULL AND v_alumno.fecha_expiracion > NOW() THEN
        v_nueva_expiracion := v_alumno.fecha_expiracion + (p_dias || ' days')::INTERVAL;
    ELSE
        v_nueva_expiracion := NOW() + (p_dias || ' days')::INTERVAL;
    END IF;

    -- Actualizar estado del alumno
    UPDATE usuarios
    SET estado_suscripcion = 'activo',
        fecha_expiracion = v_nueva_expiracion
    WHERE id = p_alumno_id;

    -- Registrar auditoría
    INSERT INTO activaciones_pases (alumno_id, profesor_id, sucursal_id, fecha_expiracion, dias_activados)
    VALUES (p_alumno_id, p_profesor_id, v_alumno.sucursal_id, v_nueva_expiracion, p_dias);

    RETURN jsonb_build_object(
        'success', true,
        'alumno_id', p_alumno_id,
        'nombre_completo', v_alumno.nombre_completo,
        'estado_suscripcion', 'activo',
        'fecha_expiracion', v_nueva_expiracion,
        'profesor_id', p_profesor_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION activar_pase_alumno(UUID, UUID, INT) TO anon, alumno, profesor, admin;

-- Permisos para activaciones_pases
GRANT SELECT, INSERT ON activaciones_pases TO profesor, admin;

