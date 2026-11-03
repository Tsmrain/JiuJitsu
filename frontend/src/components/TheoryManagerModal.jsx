import { useState, useEffect } from 'react';
import { API_BASE } from '../api/config';

/**
 * Modal to manage RAG theory for a technique.
 * Allows instructor to view and purge all uploaded chunks for this technique.
 */
export default function TheoryManagerModal({ isOpen, user, tecnica, onClose }) {
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');

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
        setError('Could not load theory.');
        setLoading(false);
        return;
      }
      const data = await res.json();
      setChunks(data.chunks || []);
    } catch (e) {
      console.error(e);
      setError('Connection error with server.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm(`Delete ALL theory chunks you uploaded for "${tecnica.nombre}"? This action cannot be undone.`)) {
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
        setError(errData.detail || 'Error deleting theory.');
        setDeleting(false);
        return;
      }
      const data = await res.json();
      alert(`Deleted: ${data.chunks_eliminados_postgres} from Postgres and ${data.chunks_eliminados_qdrant} from Qdrant.`);
      setChunks([]);
    } catch (e) {
      console.error(e);
      setError('Connection error while deleting.');
    } finally {
      setDeleting(false);
    }
  };

  if (!isOpen || !tecnica) return null;

  const formatFecha = (iso) => {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString('en-US', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content glass-panel"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '680px', maxHeight: '85vh', overflowY: 'auto' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, color: 'var(--brand-red)' }}>
            RAG Theory — {tecnica.nombre}
          </h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'white', fontSize: '1.25rem', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 1rem 0' }}>
          These are the theory excerpts you uploaded. The AI Coach references them to provide technical feedback to students.
        </p>

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

        {loading ? (
          <p>Loading theory...</p>
        ) : chunks.length === 0 ? (
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            padding: '1.5rem',
            borderRadius: '8px',
            textAlign: 'center',
            color: 'var(--text-secondary)',
            fontSize: '0.9rem'
          }}>
            You haven't uploaded theory for this technique yet.<br />
            <span style={{ fontSize: '0.8rem', opacity: 0.7 }}>
              Edit the technique to attach and index theory material.
            </span>
          </div>
        ) : (
          <>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {chunks.length} {chunks.length === 1 ? 'excerpt' : 'excerpts'} total
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
              {deleting ? 'Deleting...' : '🗑 Delete all my theory for this technique'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
