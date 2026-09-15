-- database/05_usuarios.sql
-- Autenticación BCNF: cada determinante funcional es clave candidata.
-- email UNIQUE es clave alterna (no se permiten dos cuentas con el mismo correo).

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario     VARCHAR(36)  PRIMARY KEY,
    email          VARCHAR(255) NOT NULL UNIQUE,
    nombre_completo VARCHAR(120) NOT NULL CHECK (char_length(nombre_completo) > 0),
    rol            VARCHAR(20)  NOT NULL CHECK (rol IN ('alumno', 'profesor')),
    password_hash  VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios (LOWER(email));
CREATE INDEX IF NOT EXISTS idx_usuarios_rol   ON usuarios (rol);
