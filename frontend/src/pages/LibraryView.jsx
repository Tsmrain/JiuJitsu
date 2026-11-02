import { useState } from 'react';
import { getTranslation } from '../i18n/translations';

const API_BASE = 'http://localhost:8000';

export default function LibraryView({ user, idioma, onClose }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const t = (key) => getTranslation(idioma, key);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) return;

    setLoading(true);
    setErrorMsg('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/conocimiento/biblioteca/buscar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user?.token || ''}`,
        },
        body: JSON.stringify({
          query: cleanQuery,
          idioma: idioma || 'es',
          limit: 12,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Error al buscar en la biblioteca.');
      }

      const data = await res.json();
      setResults(data.resultados || []);
      setHasSearched(true);
    } catch (err) {
      console.error('Error buscando en biblioteca:', err);
      setErrorMsg(err.message || t('connectionError'));
    } finally {
      setLoading(false);
    }
  };

  const getMediaUrl = (relativeUrl) => {
    if (!relativeUrl) return '';
    const fullUrl = relativeUrl.startsWith('http') ? relativeUrl : `${API_BASE}${relativeUrl}`;
    return user?.token ? `${fullUrl}?token=${encodeURIComponent(user.token)}` : fullUrl;
  };

  return (
    <div style={{ width: '100%', maxWidth: '1200px', margin: '0 auto', padding: '1.5rem 1rem', boxSizing: 'border-box' }}>
      {/* Header Banner */}
      <div className="glass-panel" style={{ padding: '1.8rem', borderRadius: '12px', marginBottom: '1.5rem', position: 'relative' }}>
        {onClose && (
          <button
            onClick={onClose}
            className="btn-secondary"
            style={{ position: 'absolute', top: '1.2rem', right: '1.2rem', padding: '0.3rem 0.8rem', fontSize: '0.8rem' }}
          >
            ✕ {t('close')}
          </button>
        )}
        <h2 style={{ margin: '0 0 0.4rem 0', color: 'var(--brand-red)', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span>📖</span> {t('libraryTitle')}
        </h2>
        <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          {t('librarySubtitle')}
        </p>

        {/* Search Input Bar */}
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.8rem', marginTop: '1.2rem', flexWrap: 'wrap' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('searchPlaceholder')}
            style={{
              flex: 1,
              minWidth: '260px',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: 'white',
              fontSize: '1rem',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary"
            style={{ padding: '0.75rem 1.8rem', fontSize: '0.95rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            {loading ? (
              <>
                <span className="spinner" style={{ width: 14, height: 14, border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', display: 'inline-block', animation: 'spin 1s linear infinite' }}></span>
                {t('searching')}
              </>
            ) : (
              <>🔍 {t('searchButton')}</>
            )}
          </button>
        </form>

        {errorMsg && (
          <div style={{ marginTop: '0.8rem', color: '#ff6b6b', fontSize: '0.85rem' }}>
            ⚠️ {errorMsg}
          </div>
        )}
      </div>

      {/* Resultados */}
      {hasSearched && (
        <div style={{ marginBottom: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>
            {results.length} {t('resultsFound')}
          </span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            🌐 Qwen3-VL Dense Retrieval
          </span>
        </div>
      )}

      {/* Grid de Tarjetas */}
      {results.length > 0 ? (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
          gap: '1.5rem',
        }}>
          {results.map((item, idx) => {
            const pageImgUrl = getMediaUrl(item.media_url);
            const scorePct = Math.round((item.score || 0) * 100);
            return (
              <div
                key={item.id || idx}
                className="glass-panel"
                style={{
                  borderRadius: '10px',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  background: 'rgba(20, 24, 30, 0.85)',
                  transition: 'transform 0.18s ease, box-shadow 0.18s ease',
                }}
              >
                {/* Header de la Tarjeta */}
                <div style={{
                  padding: '0.75rem 1rem',
                  background: 'rgba(0, 0, 0, 0.35)',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <span style={{ fontWeight: 'bold', fontSize: '0.88rem', color: '#ffd43b', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    📚 {item.cita || `${item.fuente_nombre || 'Manual'} (p. ${item.pagina || '?'})`}
                  </span>
                  <span style={{
                    fontSize: '0.75rem',
                    background: 'rgba(208, 17, 24, 0.25)',
                    color: '#ff8585',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '12px',
                    border: '1px solid rgba(208, 17, 24, 0.5)',
                  }}>
                    {scorePct}% match
                  </span>
                </div>

                {/* Previsualización de Imagen de Página */}
                {pageImgUrl ? (
                  <div
                    onClick={() => setSelectedImage({ url: pageImgUrl, cita: item.cita, texto: item.contenido_texto })}
                    style={{
                      height: '240px',
                      background: '#0d1117',
                      cursor: 'zoom-in',
                      overflow: 'hidden',
                      position: 'relative',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                    title={t('viewFullImage')}
                  >
                    <img
                      src={pageImgUrl}
                      alt={item.cita || 'Página de manual'}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'contain',
                        transition: 'transform 0.2s ease',
                      }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                    <div style={{
                      position: 'absolute',
                      bottom: 8,
                      right: 8,
                      background: 'rgba(0, 0, 0, 0.75)',
                      padding: '0.2rem 0.6rem',
                      borderRadius: 4,
                      fontSize: '0.72rem',
                      color: '#ddd',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                    }}>
                      🔍 {t('viewFullImage')}
                    </div>
                  </div>
                ) : (
                  <div style={{
                    height: '140px',
                    background: '#161b22',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--text-secondary)',
                    fontSize: '0.85rem',
                  }}>
                    📄 {item.fuente_referencia || 'Sin fotograma visual'}
                  </div>
                )}

                {/* Texto del libro */}
                <div style={{ padding: '1rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <div style={{
                    color: '#e6edf3',
                    fontSize: '0.85rem',
                    lineHeight: '1.45',
                    maxHeight: '150px',
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap',
                    background: 'rgba(0, 0, 0, 0.25)',
                    padding: '0.65rem 0.8rem',
                    borderRadius: '6px',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                  }}>
                    {item.contenido_texto}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : hasSearched && !loading ? (
        <div className="glass-panel" style={{ padding: '3rem 1.5rem', textAlign: 'center', borderRadius: '12px' }}>
          <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', margin: '0 0 1rem 0' }}>
            {t('noResults')}
          </p>
          <span style={{ fontSize: '0.9rem', color: '#8b949e' }}>
            Prueba buscando con términos en inglés o sinónimos de Jiu-Jitsu (ej: "armbar", "guard pass", "kimura", "choke").
          </span>
        </div>
      ) : !hasSearched && (
        <div className="glass-panel" style={{ padding: '3.5rem 1.5rem', textAlign: 'center', borderRadius: '12px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.8rem' }}>🥋📚</div>
          <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
            {t('libraryTitle')}
          </h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '520px', margin: '0 auto', fontSize: '0.92rem' }}>
            {t('initialSearchHint')}
          </p>
        </div>
      )}

      {/* Modal Visor de Imagen en Alta Resolución */}
      {selectedImage && (
        <div
          role="dialog"
          aria-modal="true"
          onClick={() => setSelectedImage(null)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.88)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem',
            boxSizing: 'border-box',
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="glass-panel"
            style={{
              maxWidth: '920px',
              maxHeight: '92vh',
              width: '100%',
              borderRadius: '12px',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              background: '#0d1117',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}
          >
            <div style={{
              padding: '0.8rem 1.2rem',
              background: '#161b22',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            }}>
              <span style={{ fontWeight: 'bold', color: '#ffd43b', fontSize: '0.95rem' }}>
                📖 {selectedImage.cita}
              </span>
              <button
                type="button"
                onClick={() => setSelectedImage(null)}
                className="btn-secondary"
                style={{ padding: '0.25rem 0.7rem', fontSize: '0.8rem' }}
              >
                ✕ {t('close')}
              </button>
            </div>
            <div style={{
              padding: '1rem',
              overflow: 'auto',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#040608',
            }}>
              <img
                src={selectedImage.url}
                alt={selectedImage.cita}
                style={{
                  maxWidth: '100%',
                  maxHeight: '75vh',
                  objectFit: 'contain',
                  borderRadius: '6px',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
