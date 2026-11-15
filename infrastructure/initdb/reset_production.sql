-- =====================================================================================
-- RESET PRODUCTION DATABASE - CORPO E MENTE BJJ
-- Limpieza absoluta de datos transaccionales para Clean State de Producción
-- Metodología Craig Larman: Cero cabos sueltos, preservación de integridad referencial
-- =====================================================================================

BEGIN;

-- 1. Limpieza total de tablas transaccionales y de prueba mediante TRUNCATE CASCADE
TRUNCATE TABLE 
    evaluaciones_alumnos, 
    comparaciones_video, 
    teoria_referencia, 
    activaciones_pases, 
    videos_referencia,
    patrones_referencia
CASCADE;

-- 3. Erradicación de usuarios de prueba / alumnos
DELETE FROM usuarios WHERE rol = 'alumno';

-- 4. Asegurar que únicamente existan los usuarios staff oficiales: admin, mike y milton
DELETE FROM usuarios WHERE username NOT IN ('admin', 'mike', 'milton');

-- 5. Restablecer los datos de suscripción para staff (siempre activo y sin expiración)
UPDATE usuarios 
SET estado_suscripcion = 'activo', fecha_expiracion = NULL 
WHERE username IN ('admin', 'mike', 'milton');

-- 6. Garantizar que solo existan las 3 sedes oficiales de producción
DELETE FROM sucursales WHERE id NOT IN (
    'b1000000-0000-0000-0000-000000000001',
    'b2000000-0000-0000-0000-000000000002',
    'b3000000-0000-0000-0000-000000000003'
);

COMMIT;

-- 7. Notificar a PostgREST para recarga inmediata de esquemas en memoria
NOTIFY pgrst, 'reload schema';

