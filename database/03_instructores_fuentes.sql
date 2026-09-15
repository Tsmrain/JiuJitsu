-- database/03_instructores_fuentes.sql
-- Gestión de Instructores y Fuentes de Conocimiento (RAG) - Mannino BCNF

CREATE TABLE IF NOT EXISTS instructores (
    id_instructor VARCHAR(50) PRIMARY KEY,
    nombre_completo VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS fuentes_conocimiento (
    id_fuente VARCHAR(64) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    id_documento VARCHAR(64),
    id_tecnica VARCHAR(50) REFERENCES tecnicas_patron(id_tecnica) ON DELETE SET NULL,
    id_instructor VARCHAR(50) REFERENCES instructores(id_instructor),
    titulo VARCHAR(200) NOT NULL,
    tipo_recurso VARCHAR(50) DEFAULT 'Manual',
    contenido_texto TEXT,
    chunk_texto TEXT,
    fecha_carga TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE fuentes_conocimiento ADD COLUMN IF NOT EXISTS id_documento VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_fuentes_id_documento ON fuentes_conocimiento(id_documento);
CREATE INDEX IF NOT EXISTS idx_fuentes_instructor ON fuentes_conocimiento(id_instructor);
CREATE INDEX IF NOT EXISTS idx_fuentes_tecnica ON fuentes_conocimiento(id_tecnica);

-- Agrupación lógica retrospectiva de chunks existentes bajo su id_documento
UPDATE fuentes_conocimiento
SET id_documento = 'doc_' || SUBSTRING(MD5(REGEXP_REPLACE(titulo, '\s*\[Parte\s+\d+\]$', '')), 1, 12)
WHERE id_documento IS NULL;

-- Extender tabla de tecnicas_patron para vincular con instructor y video demostrativo
ALTER TABLE tecnicas_patron ADD COLUMN IF NOT EXISTS id_instructor VARCHAR(50) REFERENCES instructores(id_instructor);
ALTER TABLE tecnicas_patron ADD COLUMN IF NOT EXISTS video_url TEXT;

-- Instructores iniciales
INSERT INTO instructores (id_instructor, nombre_completo)
VALUES 
  ('inst_carlos', 'Prof. Carlos Ribeiro'),
  ('inst_santiago', 'Prof. Santiago Morales')
ON CONFLICT (id_instructor) DO NOTHING;

-- Vincular tecnicas base precargadas con el instructor titular y video por defecto
UPDATE tecnicas_patron 
SET 
  id_instructor = 'inst_carlos',
  video_url = '/static/videos_patron/armbar_guardia.mp4' 
WHERE id_instructor IS NULL;
