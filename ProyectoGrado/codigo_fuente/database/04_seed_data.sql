-- Sucursal semilla
INSERT INTO sucursales (id, nombre, pais, ciudad, direccion, latitud, longitud, idioma_predeterminado)
VALUES (
  '8b315b4e-43f2-4ca1-904d-dec87242f347',
  'JIU JITSU CORPO E MENTE MIGUEL BAIGORRIA',
  'Bolivia',
  'Santa Cruz de la Sierra',
  'Avenida Cristóbal de Mendoza',
  -17.7702061,
  -63.1699065,
  'es'
) ON CONFLICT DO NOTHING;

-- Usuario admin
INSERT INTO usuarios (id, sucursal_id, nombre_completo, username, email, password_hash, rol, idioma_preferido)
VALUES (
  '00000000-0000-0000-0000-000000000000',
  '8b315b4e-43f2-4ca1-904d-dec87242f347',
  'Administrador General',
  'admin',
  'admin@corpocmente.com',
  crypt('admin123', gen_salt('bf')),
  'admin',
  'es'
) ON CONFLICT DO NOTHING;

-- Usuario profesor
INSERT INTO usuarios (id, sucursal_id, nombre_completo, username, email, password_hash, rol, idioma_preferido)
VALUES (
  '7e455a7d-cbc8-4190-9a10-3b959f6425fc',
  '8b315b4e-43f2-4ca1-904d-dec87242f347',
  'Mestre Mike Baigorria',
  'mike',
  'mike@corpocmente.com',
  crypt('password123', gen_salt('bf')),
  'profesor',
  'es'
) ON CONFLICT DO NOTHING;

-- Usuario alumno
INSERT INTO usuarios (id, sucursal_id, nombre_completo, username, email, password_hash, rol, idioma_preferido)
VALUES (
  'bce12c1c-91f1-4bfb-813b-a18c5426b51e',
  '8b315b4e-43f2-4ca1-904d-dec87242f347',
  'Santi',
  'santi',
  'santi@corpocmente.com',
  crypt('password123', gen_salt('bf')),
  'alumno',
  'es'
) ON CONFLICT DO NOTHING;

-- Técnicas semilla
INSERT INTO tecnicas (id, nombre, nivel_cinturon) VALUES
  ('d3b07384-d9a4-4f6c-947b-11347076a5b6', 'Armbar (Llave de Brazo)', 'Blanco'),
  ('e8b15394-d9a4-4f6c-947b-11347076a5b7', 'Triângulo', 'Blanco'),
  ('a1b2c3d4-e5f6-4a5b-8c9d-0123456789ab', 'Salir de 100 kilos', 'Blanco')
ON CONFLICT DO NOTHING;
