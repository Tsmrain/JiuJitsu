-- ==============================================================================
-- DISEÑO DE BASE DE DATOS HÍBRIDA (CAPA RELACIONAL) - ITERACIÓN C2
-- Metodología: Michael V. Mannino (Normalización 3NF / BCNF)
-- ==============================================================================

-- Habilitar extensión para UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Tabla: sucursales
CREATE TABLE sucursales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(50) NOT NULL,
    ciudad VARCHAR(50) NOT NULL,
    direccion VARCHAR(200),
    latitud NUMERIC(10, 7),
    longitud NUMERIC(10, 7),
    idioma_predeterminado VARCHAR(10) DEFAULT 'es',
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla: usuarios (Contiene alumnos, profesores y admins)
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sucursal_id UUID NOT NULL REFERENCES sucursales(id) ON DELETE CASCADE,
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'profesor', 'alumno')),
    idioma_preferido VARCHAR(10) DEFAULT 'es',
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla: tecnicas
CREATE TABLE tecnicas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_es VARCHAR(100) NOT NULL,
    nombre_pt VARCHAR(100) NOT NULL,
    descripcion_es TEXT,
    descripcion_pt TEXT,
    nivel_cinturon VARCHAR(20) NOT NULL,
    categoria VARCHAR(50) NOT NULL
);

-- 4. Tabla: videos_referencia (Videos base para comparar)
CREATE TABLE videos_referencia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tecnica_id UUID NOT NULL REFERENCES tecnicas(id) ON DELETE CASCADE,
    profesor_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    url_video_gcs VARCHAR(255) NOT NULL,
    duracion_segundos NUMERIC(5,2),
    vector_qdrant_id UUID UNIQUE NOT NULL,
    fecha_subida TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabla: evaluaciones_alumnos (Resultados de inferencia)
CREATE TABLE evaluaciones_alumnos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alumno_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tecnica_id UUID NOT NULL REFERENCES tecnicas(id) ON DELETE CASCADE,
    video_referencia_id UUID NOT NULL REFERENCES videos_referencia(id) ON DELETE CASCADE,
    url_video_alumno VARCHAR(255) NOT NULL,
    porcentaje_similitud NUMERIC(5,2),
    feedback_gemini_es TEXT,
    feedback_gemini_pt TEXT,
    vector_qdrant_id UUID UNIQUE,
    estado VARCHAR(30) NOT NULL DEFAULT 'procesando',
    fecha_evaluacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices adicionales para rendimiento
CREATE INDEX idx_usuarios_sucursal ON usuarios(sucursal_id);
CREATE INDEX idx_videos_referencia_tecnica ON videos_referencia(tecnica_id);
CREATE INDEX idx_evaluaciones_alumno ON evaluaciones_alumnos(alumno_id);
