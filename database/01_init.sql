-- database/01_init.sql
-- Habilitar extensión vectorial para tipos compatibles
CREATE EXTENSION IF NOT EXISTS vector;
-- Nota: La persistencia vectorial principal se delega a Qdrant Local. PostgreSQL permanece puramente relacional (BCNF).

CREATE TABLE IF NOT EXISTS tecnicas_patron (
    id_tecnica VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    matriz_esqueletica JSONB NOT NULL, -- Almacenamiento flexible de la matriz esquelética
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recursos_didacticos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    contenido_texto TEXT NOT NULL,
    embedding vector(2048), -- Dimensión para Qwen3-VL-Embedding-2B
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- NOTA HNSW: pgvector limita índices HNSW/IVFFlat a 2000 dimensiones.
-- Para 2048d (Qwen3-VL-Embedding-2B), se utiliza búsqueda secuencial KNN directa con operador (<=>).
-- CREATE INDEX IF NOT EXISTS idx_recursos_embedding_hnsw 
-- ON recursos_didacticos 
-- USING hnsw (embedding vector_cosine_ops);

-- Técnicas estándar precargadas para evaluación e histórico
INSERT INTO tecnicas_patron (id_tecnica, nombre, descripcion, matriz_esqueletica)
VALUES 
  ('armbar_guardia', 'Armbar desde Guardia', 'Llave de brazo recta ejecutada desde la guardia cerrada', '{"angulos": {"codo_derecho": 90.0}}'),
  ('triangulo_guardia', 'Triángulo desde Guardia', 'Estrangulamiento triangular con las piernas', '{"angulos": {"rodilla": 45.0}}'),
  ('kimura_guardia', 'Kimura desde Guardia', 'Llave doble de muñeca y hombro desde la guardia', '{"angulos": {"hombro": 90.0}}'),
  ('omoplata', 'Omoplata', 'Ataque articular de hombro con las piernas', '{"angulos": {"cadera": 70.0}}')
ON CONFLICT (id_tecnica) DO NOTHING;
