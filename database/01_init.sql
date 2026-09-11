-- database/01_init.sql
CREATE EXTENSION IF NOT EXISTS vector;

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
    embedding vector(768), -- Dimensión estándar para Gemini Embedding
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índice HNSW para búsqueda semántica rápida por similitud de coseno
CREATE INDEX IF NOT EXISTS idx_recursos_embedding_hnsw 
ON recursos_didacticos 
USING hnsw (embedding vector_cosine_ops);
