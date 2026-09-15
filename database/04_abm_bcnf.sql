-- database/04_abm_bcnf.sql
-- Sprint 4: Persistencia BCNF y Gestión de Datos Maestros (Mannino 7th Ed., Cap. 6-8)
-- Justificación: Normalización BCNF garantizada donde cada determinante funcional es clave candidata/primaria.

-- Habilitar extensión vectorial si no existe
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Tabla Profesores: BCNF verificada (email es clave alterna única, no hay dependencias parciales/transitivas)
CREATE TABLE IF NOT EXISTS profesores (
    id_profesor VARCHAR(36) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL CHECK (char_length(nombre) > 0),
    email VARCHAR(255) NOT NULL UNIQUE CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'),
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Tabla Técnicas Patrón: 
-- JSONB aceptable según Mannino Cap. 8 cuando la estructura interna es opaca al dominio relacional.
-- La matriz tridimensional se valida mediante AdaptadorYOLO antes de persistir.
CREATE TABLE IF NOT EXISTS tecnicas_patron (
    id_tecnica VARCHAR(50) PRIMARY KEY,
    id_profesor VARCHAR(36) REFERENCES profesores(id_profesor) ON DELETE CASCADE,
    nombre VARCHAR(150) NOT NULL,
    categoria VARCHAR(50) NOT NULL DEFAULT 'General',
    matriz_esqueletica JSONB NOT NULL,
    video_url TEXT,
    descripcion TEXT
);

-- Asegurar columnas si tecnicas_patron fue creada por 01_init.sql previamente
ALTER TABLE tecnicas_patron ADD COLUMN IF NOT EXISTS id_profesor VARCHAR(36) REFERENCES profesores(id_profesor) ON DELETE CASCADE;
ALTER TABLE tecnicas_patron ADD COLUMN IF NOT EXISTS categoria VARCHAR(50) NOT NULL DEFAULT 'General';

-- Índice GIN para consultas eficientes de atributos internos de la matriz postural JSONB
CREATE INDEX IF NOT EXISTS idx_tecnicas_matriz_gin ON tecnicas_patron USING gin (matriz_esqueletica);
CREATE INDEX IF NOT EXISTS idx_tecnicas_id_profesor ON tecnicas_patron (id_profesor);

-- 3. Tabla Fuentes Conocimiento: Metadatos relacionales BCNF (Mannino).
-- Nota de Arquitectura (Larman): La persistencia e indexación vectorial reside exclusivamente en Qdrant.
CREATE TABLE IF NOT EXISTS fuentes_conocimiento (
    id_fuente VARCHAR(64) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    id_documento VARCHAR(64),
    id_tecnica VARCHAR(50) REFERENCES tecnicas_patron(id_tecnica) ON DELETE SET NULL,
    titulo VARCHAR(200) NOT NULL,
    tipo_recurso VARCHAR(50) NOT NULL DEFAULT 'Manual',
    chunk_texto TEXT NOT NULL,
    fecha_carga TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE fuentes_conocimiento ADD COLUMN IF NOT EXISTS id_documento VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_fuentes_id_documento ON fuentes_conocimiento (id_documento);
CREATE INDEX IF NOT EXISTS idx_fuentes_id_tecnica ON fuentes_conocimiento (id_tecnica);
