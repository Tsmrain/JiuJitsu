import { useState, useEffect } from 'react';

/**
 * Modal de gestión de teoría RAG para una técnica.
 * Permite al profesor ver todos los chunks que subió y borrarlos de golpe.
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
        `http://localhost:8000/api/v1/conocimiento/teoria/${tecnica.id}?solo_mios=true`,
        { headers: { Authorization: `Bearer ${user.token}` } }
      );
      if (!res.ok) {
        setError('No se pudo cargar la teoría.');
        setLoading(false);
        return;
      }
      const data = await res.json();
      setChunks(data.chunks || []);
    } catch (e) {
      console.error(e);
      setError('Error de conexión con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm(`¿Eliminar TODOS los aportes de teoría que subiste para "${tecnica.nombre}"? Esta acción no se puede deshacer.`)) {
      return;
    }
    setDeleting(true);
    setError('');
    try {
      const res = await fetch(
        `http://localhost:8000/api/v1/conocimiento/teoria/${tecnica.id}`,
        {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${user.token}` }
        }
      );
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || 'Error al eliminar.');
        setDeleting(false);
        return;
      }
      const data = await res.json();
      alert(`Eliminados: ${data.chunks_eliminados_postgres} de Postgres y ${data.chunks_eliminados_qdrant} de Qdrant.`);
      setChunks([]);
    } catch (e) {
      console.error(e);
      setError('Error de conexión al eliminar.');
    } finally {
      setDeleting(false);
    }
  };

  if (!isOpen || !tecnica) return null;

  const formatFecha = (iso) => {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString('es-ES', {
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
            Teoría RAG — {tecnica.nombre}
          </h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'white', fontSize: '1.25rem', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 1rem 0' }}>
          Estos son los fragmentos de teoría que subiste. Gemini los leerá para dar feedback a tus alumnos.
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
          <p>Cargando teoría...</p>
        ) : chunks.length === 0 ? (
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            padding: '1.5rem',
            borderRadius: '8px',
            textAlign: 'center',
            color: 'var(--text-secondary)',
            fontSize: '0.9rem'
          }}>
            Aún no has subido teoría para esta técnica.<br />
            <span style={{ fontSize: '0.8rem', opacity: 0.7 }}>
              Edita la técnica y usa el campo "Manual del Maestro (Teoría RAG)" para agregar contenido.
            </span>
          </div>
        ) : (
          <>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {chunks.length} {chunks.length === 1 ? 'fragmento' : 'fragmentos'} en total
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
              {deleting ? 'Eliminando...' : '🗑 Eliminar toda mi teoría de esta técnica'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
