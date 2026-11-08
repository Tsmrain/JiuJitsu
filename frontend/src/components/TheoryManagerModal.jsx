import { useState, useEffect } from 'react';
import { API_BASE } from '../api/config';
import { getTranslation } from '../i18n/translations';

/**
 * Modal to manage and display theory for a technique.
 * Shows instructor specific instructions (mensaje_profesor) and indexed RAG chunks.
 */
export default function TheoryManagerModal({ isOpen, user, tecnica, idioma, onClose }) {
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');

  const currentLang = idioma || user?.idioma_preferido || 'es';
  const t = (key) => getTranslation(currentLang, key);

  useEffect(() => {
    if (!isOpen || !tecnica) return;
    fetchChunks();
  }, [isOpen, tecnica?.id]);

  const fetchChunks = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/conocimiento/teoria/${tecnica.id}?solo_mios=true`,
        { headers: { Authorization: `Bearer ${user.token}` } }
      );
      if (!res.ok) {
        setError(t('couldNotLoadTheory') || 'No se pudo cargar la teoría.');
        setLoading(false);
        return;
      }
      const data = await res.json();
      setChunks(data.chunks || []);
    } catch (e) {
      console.error(e);
      setError(t('connectionError') || 'Error de conexión con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAll = async () => {
    const confirmMsg = t('confirmDeleteAllTheory') || `¿Eliminar todos los extractos de teoría para "${tecnica.nombre}"?`;
    if (!confirm(confirmMsg)) {
      return;
    }
    setDeleting(true);
    setError('');
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/conocimiento/teoria/${tecnica.id}`,
        {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${user.token}` }
        }
      );
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || t('errorDeletingTheory') || 'Error eliminando teoría.');
        setDeleting(false);
        return;
      }
      setChunks([]);
    } catch (e) {
      console.error(e);
      setError(t('connectionError') || 'Error de conexión al eliminar.');
    } finally {
      setDeleting(false);
    }
  };

  if (!isOpen || !tecnica) return null;

  const formatFecha = (iso) => {
    if (!iso) return '—';
    try {
      const dateLocale = currentLang === 'pt' ? 'pt-BR' : currentLang === 'en' ? 'en-US' : 'es-ES';
      return new Date(iso).toLocaleString(dateLocale, {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch {
      return iso;
    }
  };

  const hasInstructorMessage = Boolean(tecnica.mensaje_profesor && tecnica.mensaje_profesor.trim());

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="modal-content glass-panel"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '680px', maxHeight: '85vh', overflowY: 'auto' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 data-testid="theory-modal-title" style={{ margin: 0, color: 'var(--brand-red)', fontSize: '1.25rem' }}>
            {t('techniqueTheory')} — {tecnica.nombre}
          </h3>
          <button
            data-testid="close-theory-modal-btn"
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'white', fontSize: '1.25rem', cursor: 'pointer' }}
            aria-label={t('close')}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 1.25rem 0' }}>
          {t('theoryModalSubtitle')}
        </p>

        {/* 1. Sección Destacada: Instrucciones del Instructor (si existen) */}
        {hasInstructorMessage && (
          <div data-testid="instructor-instructions-box" style={{
            background: 'rgba(208, 17, 24, 0.12)',
            border: '1px solid var(--brand-red)',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1.25rem'
          }}>
            <h4 style={{ margin: '0 0 0.4rem 0', color: 'var(--brand-red)', fontSize: '0.92rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span>🥋</span> {t('instructorInstructions')}
            </h4>
            <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: '1.5', color: '#f8fafc', whiteSpace: 'pre-wrap' }}>
              {tecnica.mensaje_profesor}
            </p>
          </div>
        )}

        {error && (
          <div style={{
            background: 'rgba(208, 17, 24, 0.2)',
            border: '1px solid var(--brand-red)',
            color: '#ff6b6b',
            padding: '0.6rem',
            borderRadius: '6px',
            fontSize: '0.85rem',
            marginBottom: '1rem'
          }}>
            {error}
          </div>
        )}

        {/* 2. Sección Chunks RAG */}
        {loading ? (
          <p style={{ color: 'var(--text-secondary)' }}>{t('loading') || 'Cargando teoría...'}</p>
        ) : chunks.length === 0 ? (
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            padding: '1.5rem',
            borderRadius: '8px',
            textAlign: 'center',
            color: 'var(--text-secondary)',
            fontSize: '0.9rem',
            lineHeight: '1.5'
          }}>
            {t('noTheoryUploaded')}
          </div>
        ) : (
          <>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {chunks.length} {t('totalExcerpts')}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.25rem' }}>
              {chunks.map((c, idx) => (
                <div
                  key={c.id || idx}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    padding: '0.9rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                    <span>Chunk #{c.chunk_index}</span>
                    <span>{formatFecha(c.fecha_ingesta)}</span>
                  </div>
                  {(c.fuente_nombre || c.fuente_tipo || c.fuente_referencia || c.fuente_url) && (
                    <p style={{ margin: '0 0 0.55rem', fontSize: '0.8rem', color: 'var(--brand-red)' }}>
                      {[c.fuente_nombre || c.fuente_tipo, c.fuente_referencia, c.fuente_url].filter(Boolean).join(' · ')}
                    </p>
                  )}
                  <p style={{ margin: 0, fontSize: '0.85rem', lineHeight: '1.4', whiteSpace: 'pre-wrap' }}>
                    {c.contenido_texto}
                  </p>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={handleDeleteAll}
              disabled={deleting}
              style={{
                width: '100%',
                padding: '0.75rem',
                background: 'rgba(208, 17, 24, 0.15)',
                border: '1px solid var(--brand-red)',
                color: '#ff6b6b',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '0.9rem'
              }}
            >
              {deleting ? (t('deleting') || 'Eliminando...') : `🗑 ${t('deleteAllMyTheory')}`}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
