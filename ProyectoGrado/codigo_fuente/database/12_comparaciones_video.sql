-- Comparaciones video vs video frame por frame
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS comparaciones_video (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estado TEXT NOT NULL DEFAULT 'procesando',
    tecnica_id UUID NULL,
    alumno_id UUID NOT NULL,
    idioma TEXT NOT NULL DEFAULT 'es',

    persona_idx_alumno INT NOT NULL DEFAULT 0,
    persona_idx_maestro INT NOT NULL DEFAULT 0,

    video_alumno_path TEXT NULL,
    video_maestro_path TEXT NULL,
    video_alumno_nombre TEXT NULL,
    video_maestro_nombre TEXT NULL,
    video_comparacion_path TEXT NULL,

    score_similitud NUMERIC(5,2) NULL,
    dtw_distance NUMERIC NULL,
    dtw_normalizado NUMERIC NULL,

    frame_alumno_critico INT NULL,
    frame_maestro_critico INT NULL,

    articulaciones_criticas JSONB NULL,
    alineacion JSONB NULL,

    error_message TEXT NULL,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comparaciones_video_estado ON comparaciones_video(estado);
CREATE INDEX IF NOT EXISTS idx_comparaciones_video_tecnica ON comparaciones_video(tecnica_id);
CREATE INDEX IF NOT EXISTS idx_comparaciones_video_creado ON comparaciones_video(creado_en DESC);

-- Si usas RLS y PostgREST, ajusta políticas según tu modelo de seguridad.
-- Para desarrollo local, esto permite lectura/escritura autenticada:
ALTER TABLE comparaciones_video ADD COLUMN IF NOT EXISTS alumno_id UUID;
ALTER TABLE comparaciones_video ADD COLUMN IF NOT EXISTS video_alumno_nombre TEXT;
ALTER TABLE comparaciones_video ADD COLUMN IF NOT EXISTS video_maestro_nombre TEXT;
ALTER TABLE comparaciones_video ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS comparaciones_video_auth_all ON comparaciones_video;
CREATE POLICY comparaciones_video_auth_all
ON comparaciones_video
FOR ALL
TO authenticated
USING (
    alumno_id::text = (current_setting('request.jwt.claims', true)::jsonb ->> 'uid')
    OR (current_setting('request.jwt.claims', true)::jsonb ->> 'role') = 'admin'
)
WITH CHECK (
    alumno_id::text = (current_setting('request.jwt.claims', true)::jsonb ->> 'uid')
    OR (current_setting('request.jwt.claims', true)::jsonb ->> 'role') = 'admin'
);
