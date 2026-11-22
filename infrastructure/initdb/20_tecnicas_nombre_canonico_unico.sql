-- Mannino (Integridad Referencial y de Dominio en SGBD) + Larman (NombreTecnica canónico):
-- Garantiza unicidad de técnicas ignorando mayúsculas, tildes, espacios y símbolos
-- (ej. 'Montada' = 'montada' = 'mONTAda'; 'Llave de Brazo' = 'llavedebrazo')
-- preservando en `tecnicas.nombre` el texto legible con espacios para UI y RAG.

CREATE OR REPLACE FUNCTION normalizar_clave_tecnica(p_nombre TEXT)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT regexp_replace(
        translate(
            lower(trim(p_nombre)),
            'áàâäãåéèêëíìîïóòôöõúùûüñçÁÀÂÄÃÅÉÈÊËÍÌÎÏÓÒÔÖÕÚÙÛÜÑÇ',
            'aaaaaaeeeeiiiiooooouuuuncaaaaaaeeeeiiiiooooouuuunc'
        ),
        '[^a-z0-9]+',
        '',
        'g'
    );
$$;

-- Limpiar espacios redundantes en registros existentes antes de indexar
UPDATE tecnicas
SET nombre = regexp_replace(trim(nombre), '\s+', ' ', 'g')
WHERE nombre <> regexp_replace(trim(nombre), '\s+', ' ', 'g');

CREATE UNIQUE INDEX IF NOT EXISTS uq_tecnicas_nombre_canonico
    ON tecnicas (normalizar_clave_tecnica(nombre));

CREATE OR REPLACE FUNCTION admin_create_tecnica(
    p_nombre TEXT,
    p_nivel_cinturon TEXT,
    p_mensaje_profesor TEXT
)
RETURNS TABLE(id UUID, nombre VARCHAR, nivel_cinturon VARCHAR, mensaje_profesor TEXT) AS $$
DECLARE
    new_id UUID;
    v_nombre TEXT;
    v_clave TEXT;
    v_existente TEXT;
BEGIN
    v_nombre := regexp_replace(trim(COALESCE(p_nombre, '')), '\s+', ' ', 'g');
    v_clave := normalizar_clave_tecnica(v_nombre);

    IF v_nombre = '' OR v_clave = '' THEN
        RAISE EXCEPTION 'El nombre de la técnica no puede estar vacío.'
            USING ERRCODE = 'check_violation';
    END IF;

    SELECT t.nombre INTO v_existente
    FROM tecnicas t
    WHERE normalizar_clave_tecnica(t.nombre) = v_clave
    LIMIT 1;

    IF v_existente IS NOT NULL THEN
        RAISE EXCEPTION 'DUPLICATE_TECHNIQUE:%', v_existente
            USING ERRCODE = 'unique_violation';
    END IF;

    INSERT INTO tecnicas(nombre, nivel_cinturon, mensaje_profesor)
    VALUES (v_nombre, p_nivel_cinturon, COALESCE(p_mensaje_profesor, ''))
    RETURNING tecnicas.id INTO new_id;

    RETURN QUERY
    SELECT t.id, t.nombre, t.nivel_cinturon, t.mensaje_profesor
    FROM tecnicas t
    WHERE t.id = new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_create_tecnica(TEXT, TEXT, TEXT) TO anon;

CREATE OR REPLACE FUNCTION admin_update_tecnica(
    p_tecnica_id UUID,
    p_nombre TEXT,
    p_nivel_cinturon TEXT,
    p_mensaje_profesor TEXT
)
RETURNS TABLE(id UUID, nombre VARCHAR, nivel_cinturon VARCHAR, mensaje_profesor TEXT) AS $$
DECLARE
    v_nombre TEXT;
    v_clave TEXT;
    v_existente TEXT;
BEGIN
    v_nombre := regexp_replace(trim(COALESCE(p_nombre, '')), '\s+', ' ', 'g');
    v_clave := normalizar_clave_tecnica(v_nombre);

    IF v_nombre = '' OR v_clave = '' THEN
        RAISE EXCEPTION 'El nombre de la técnica no puede estar vacío.'
            USING ERRCODE = 'check_violation';
    END IF;

    SELECT t.nombre INTO v_existente
    FROM tecnicas t
    WHERE t.id <> p_tecnica_id
      AND normalizar_clave_tecnica(t.nombre) = v_clave
    LIMIT 1;

    IF v_existente IS NOT NULL THEN
        RAISE EXCEPTION 'DUPLICATE_TECHNIQUE:%', v_existente
            USING ERRCODE = 'unique_violation';
    END IF;

    UPDATE tecnicas
    SET nombre = v_nombre,
        nivel_cinturon = p_nivel_cinturon,
        mensaje_profesor = COALESCE(p_mensaje_profesor, '')
    WHERE tecnicas.id = p_tecnica_id;

    RETURN QUERY
    SELECT t.id, t.nombre, t.nivel_cinturon, t.mensaje_profesor
    FROM tecnicas t
    WHERE t.id = p_tecnica_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION admin_update_tecnica(UUID, TEXT, TEXT, TEXT) TO anon;

NOTIFY pgrst, 'reload schema';
