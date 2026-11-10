-- 17_ampliar_fuente_tipo_teoria.sql
-- Permite almacenar el tipo real de documento en teoria_referencia (manual_pdf, texto, docx, imagen, etc.)
-- manteniendo total compatibilidad con fuentes previas ('manual', 'video', 'articulo').

ALTER TABLE teoria_referencia
    DROP CONSTRAINT IF EXISTS teoria_referencia_fuente_tipo_check;

ALTER TABLE teoria_referencia
    ADD CONSTRAINT teoria_referencia_fuente_tipo_check
    CHECK (
        fuente_tipo IS NULL
        OR fuente_tipo IN (
            'manual',
            'manual_pdf',
            'texto',
            'docx',
            'imagen',
            'video',
            'articulo',
            'instructor_message'
        )
    );

NOTIFY pgrst, 'reload schema';
