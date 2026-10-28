-- ==============================================================================
-- POLÍTICAS DE SEGURIDAD A NIVEL DE FILA (ROW LEVEL SECURITY - RLS)
-- Iteración C2 - Aislamiento Multi-Tenant y Privacidad de Usuario
-- ==============================================================================

-- 1. Habilitar RLS en todas las tablas
ALTER TABLE sucursales ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE tecnicas ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos_referencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluaciones_alumnos ENABLE ROW LEVEL SECURITY;

-- 2. Políticas para 'sucursales'
-- Todos los usuarios autenticados pueden ver sucursales
CREATE POLICY "Sucursales visibles para todos los autenticados" 
ON sucursales FOR SELECT 
TO alumno, profesor, admin 
USING (true);

-- 3. Políticas para 'usuarios'
-- Alumnos solo pueden ver su propio perfil
CREATE POLICY "Alumnos ven su propio perfil" 
ON usuarios FOR SELECT 
TO alumno 
USING (id = current_setting('request.jwt.claim.uid', true)::uuid);

-- Profesores pueden ver perfiles de su propia sucursal
CREATE POLICY "Profesores ven usuarios de su sucursal" 
ON usuarios FOR SELECT 
TO profesor 
USING (sucursal_id = current_setting('request.jwt.claim.sucursal_id', true)::uuid);

-- 4. Políticas para 'tecnicas'
-- Técnicas son públicas para consulta
CREATE POLICY "Tecnicas publicas para consulta" 
ON tecnicas FOR SELECT 
TO alumno, profesor, admin 
USING (true);

-- 5. Políticas para 'videos_referencia'
-- Todos pueden consultar videos de referencia
CREATE POLICY "Videos de referencia visibles para consulta" 
ON videos_referencia FOR SELECT 
TO alumno, profesor, admin 
USING (true);

-- Profesores pueden insertar videos de referencia para su sucursal
CREATE POLICY "Profesores pueden insertar videos" 
ON videos_referencia FOR INSERT 
TO profesor 
WITH CHECK (profesor_id = current_setting('request.jwt.claim.uid', true)::uuid);

-- 6. Políticas para 'evaluaciones_alumnos'
-- Alumnos solo pueden ver y crear sus propias evaluaciones
CREATE POLICY "Alumnos gestionan sus evaluaciones" 
ON evaluaciones_alumnos FOR ALL 
TO alumno 
USING (alumno_id = current_setting('request.jwt.claim.uid', true)::uuid)
WITH CHECK (alumno_id = current_setting('request.jwt.claim.uid', true)::uuid);

-- Profesores pueden ver evaluaciones de los alumnos de su sucursal
CREATE POLICY "Profesores ven evaluaciones de su sucursal" 
ON evaluaciones_alumnos FOR SELECT 
TO profesor 
USING (
    EXISTS (
        SELECT 1 FROM usuarios u 
        WHERE u.id = evaluaciones_alumnos.alumno_id 
        AND u.sucursal_id = current_setting('request.jwt.claim.sucursal_id', true)::uuid
    )
);

-- 7. Políticas de Administrador (Total Access)
CREATE POLICY "Admins full access sucursales" ON sucursales FOR ALL TO admin USING (true);
CREATE POLICY "Admins full access usuarios" ON usuarios FOR ALL TO admin USING (true);
CREATE POLICY "Admins full access tecnicas" ON tecnicas FOR ALL TO admin USING (true);
CREATE POLICY "Admins full access videos" ON videos_referencia FOR ALL TO admin USING (true);
CREATE POLICY "Admins full access evaluaciones" ON evaluaciones_alumnos FOR ALL TO admin USING (true);

-- 8. Otorgar permisos CRUD básicos sobre las tablas a los roles (RLS se encarga del filtrado)
GRANT SELECT ON sucursales, tecnicas, videos_referencia TO alumno, profesor;
GRANT SELECT, UPDATE ON usuarios TO alumno, profesor;
GRANT SELECT, INSERT ON evaluaciones_alumnos TO alumno;
GRANT SELECT, INSERT, UPDATE, DELETE ON videos_referencia TO profesor;
GRANT ALL ON sucursales, usuarios, tecnicas, videos_referencia, evaluaciones_alumnos TO admin;
