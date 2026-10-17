-- Limpieza deliberada del entorno de demostración.
-- Conserva admin, mike y santi; elimina técnicas, fuentes, videos y todo el historial.
BEGIN;

DO $$
DECLARE
    cuentas_objetivo INT;
BEGIN
    SELECT COUNT(*) INTO cuentas_objetivo
    FROM usuarios
    WHERE username IN ('admin', 'mike', 'santi')
      AND ((username = 'admin' AND rol = 'admin')
        OR (username = 'mike' AND rol = 'profesor')
        OR (username = 'santi' AND rol = 'alumno'));

    IF cuentas_objetivo <> 3 THEN
        RAISE EXCEPTION 'Limpieza cancelada: deben existir las cuentas admin, mike y santi con sus roles esperados; encontradas: %', cuentas_objetivo;
    END IF;
END $$;

DO $$
BEGIN
    IF to_regclass('public.comparaciones_video') IS NOT NULL THEN
        EXECUTE 'DELETE FROM public.comparaciones_video';
    END IF;
    IF to_regclass('public.teoria_referencia') IS NOT NULL THEN
        EXECUTE 'DELETE FROM public.teoria_referencia';
    END IF;
END $$;

DELETE FROM evaluaciones_alumnos;
DELETE FROM videos_referencia;
DELETE FROM tecnicas;
DELETE FROM usuarios WHERE username NOT IN ('admin', 'mike', 'santi');
UPDATE usuarios SET nombre_completo = 'Santiago' WHERE username = 'santi';

COMMIT;

-- Verificación rápida: deben quedar exactamente estas tres cuentas.
SELECT username, nombre_completo, rol
FROM usuarios
ORDER BY CASE username WHEN 'admin' THEN 1 WHEN 'mike' THEN 2 ELSE 3 END;
