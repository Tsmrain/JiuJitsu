-- database/03_instructores_fuentes.sql
-- Gestión de Instructores y Fuentes de Conocimiento (RAG) - Mannino BCNF

CREATE TABLE IF NOT EXISTS instructores (
    id_instructor VARCHAR(50) PRIMARY KEY,
    nombre_completo VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS fuentes_conocimiento (
    id_fuente UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_instructor VARCHAR(50) NOT NULL REFERENCES instructores(id_instructor),
    titulo VARCHAR(200) NOT NULL,
    contenido_texto TEXT NOT NULL,
    embedding vector(768),
    fecha_carga TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fuentes_instructor ON fuentes_conocimiento(id_instructor);

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
