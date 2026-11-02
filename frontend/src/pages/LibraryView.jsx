import { useState, useEffect } from 'react';
import { getTranslation } from '../i18n/translations';

const API_BASE = 'http://localhost:8000';

export default function LibraryView({ user, idioma, onClose, initialQuery, initialImageUrl }) {
  const [activeTab, setActiveTab] = useState('search'); // 'search' | 'catalog'
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [activeImageUrl, setActiveImageUrl] = useState(initialImageUrl || null);

  // Estado del Catálogo de Libros PDF
  const [manuales, setManuales] = useState([]);
  const [loadingManuales, setLoadingManuales] = useState(false);
  const [selectedPdf, setSelectedPdf] = useState(null);

  const t = (key) => getTranslation(idioma, key);

  useEffect(() => {
    if (initialImageUrl) {
      setActiveImageUrl(initialImageUrl);
    }
  }, [initialImageUrl]);

  const handleSearch = async (e, customQuery = null, customImage = undefined) => {
    if (e) e.preventDefault();
    const cleanQuery = (customQuery !== null ? customQuery : query).trim();
    if (!cleanQuery) return;
    if (customQuery !== null) {
      setQuery(customQuery);
    }

    const targetImg = customImage !== undefined ? customImage : activeImageUrl;

    setLoading(true);
    setErrorMsg('');
    try {
      const payload = {
        query: cleanQuery,
        idioma: idioma || 'es',
        limit: 12,
      };
      if (targetImg) {
        payload.imagen_url = targetImg;
      }

      const res = await fetch(`${API_BASE}/api/v1/conocimiento/biblioteca/buscar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user?.token || ''}`,
        },
        body: JSON.stringify(payload),
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

  const fetchManuales = async () => {
    setLoadingManuales(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/conocimiento/manuales`, {
        headers: {
          'Authorization': `Bearer ${user?.token || ''}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setManuales(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Error cargando manuales:', err);
    } finally {
      setLoadingManuales(false);
    }
  };

  useEffect(() => {
    // Si viene una consulta inicial desde el botón de teoría, ejecutarla; si no, 'guardia'
    const targetQuery = initialQuery && initialQuery.trim() ? initialQuery.trim() : 'guardia';
    setActiveTab('search');
    handleSearch(null, targetQuery, initialImageUrl);
  }, [initialQuery, initialImageUrl]);

  useEffect(() => {
    if (activeTab === 'catalog' && manuales.length === 0) {
      fetchManuales();
    }
  }, [activeTab]);

  const getMediaUrl = (relativeUrl) => {
    if (!relativeUrl) return '';
    const fullUrl = relativeUrl.startsWith('http') ? relativeUrl : `${API_BASE}${relativeUrl}`;
    return user?.token ? `${fullUrl}?token=${encodeURIComponent(user.token)}` : fullUrl;
  };

  const getPdfUrl = (filename) => {
    const raw = `${API_BASE}/api/v1/conocimiento/manuales/${encodeURIComponent(filename)}`;
    return user?.token ? `${raw}?token=${encodeURIComponent(user.token)}` : raw;
  };

  const cleanBookName = (filename) => {
    return filename
      .replace(/\.pdf$/i, '')
      .replace(/[-_]/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
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

        {/* Selector de Pestañas (Tabs) */}
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.25rem', borderBottom: '1px solid rgba(255, 255, 255, 0.12)', paddingBottom: '0.5rem' }}>
          <button
            type="button"
            onClick={() => setActiveTab('search')}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'search' ? '3px solid var(--brand-red)' : '3px solid transparent',
              color: activeTab === 'search' ? '#ffffff' : 'var(--text-secondary)',
              fontWeight: 'bold',
              fontSize: '1rem',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s ease',
            }}
          >
            <span>🔍</span> {t('semanticSearchTab')}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('catalog')}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'catalog' ? '3px solid var(--brand-red)' : '3px solid transparent',
              color: activeTab === 'catalog' ? '#ffffff' : 'var(--text-secondary)',
              fontWeight: 'bold',
              fontSize: '1rem',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s ease',
            }}
          >
            <span>📚</span> {t('catalogTab')}
          </button>
        </div>

        {/* PESTAÑA 1: BÚSQUEDA SEMÁNTICA */}
        {activeTab === 'search' && (
          <div>
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
                disabled={loading}
                className="btn-primary"
                style={{ padding: '0.75rem 1.5rem', fontSize: '1rem', whiteSpace: 'nowrap' }}
              >
                {loading ? t('searching') : t('searchButton')}
              </button>
            </form>

            {/* Banner de Fotograma de Error Analizado (Búsqueda Multimodal) */}
            {activeImageUrl && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.85rem',
                background: 'rgba(208, 17, 24, 0.15)',
                border: '1px solid rgba(208, 17, 24, 0.4)',
                padding: '0.55rem 0.9rem',
                borderRadius: '8px',
                marginTop: '0.85rem',
              }}>
                <img
                  src={getMediaUrl(activeImageUrl)}
                  alt="Frame error"
                  style={{ width: '60px', height: '45px', objectFit: 'cover', borderRadius: '4px', border: '1px solid #ffd43b' }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 'bold', color: '#ffd43b', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span>✨</span> {t('multimodalSearchActive')}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    {t('comparingErrorFrame')}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setActiveImageUrl(null);
                    handleSearch(null, query, null);
                  }}
                  style={{ background: 'none', border: 'none', color: '#ff8787', fontSize: '0.85rem', cursor: 'pointer', padding: '0.2rem 0.5rem' }}
                  title={t('removeImageSearch')}
                >
                  ✕ {t('removeImageSearch')}
                </button>
              </div>
            )}
          </div>
        )}

        {/* PESTAÑA 2: CATÁLOGO DE LIBROS */}
        {activeTab === 'catalog' && (
          <div style={{ marginTop: '1.2rem' }}>
            <h3 style={{ margin: '0 0 0.3rem 0', fontSize: '1.1rem', color: '#ffd43b' }}>
              {t('catalogTitle')}
            </h3>
            <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              {t('catalogSubtitle')}
            </p>
          </div>
        )}

        {errorMsg && (
          <p style={{ color: '#ff6b6b', marginTop: '0.8rem', fontSize: '0.9rem' }}>
            ⚠️ {errorMsg}
          </p>
        )}
      </div>

      {/* CONTENIDO TAB 1: RESULTADOS DE BÚSQUEDA */}
      {activeTab === 'search' && (
        <>
          {hasSearched && (
            <div style={{ marginBottom: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>
                {results.length} {t('resultsFound')}
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                🌐 Qwen3-VL Dense Retrieval & Cognitive Rewriting
              </span>
            </div>
          )}

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
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        background: scorePct >= 50 ? 'rgba(34, 197, 94, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                        color: scorePct >= 50 ? '#4ade80' : 'var(--text-secondary)',
                        fontWeight: '600',
                      }}>
                        {scorePct}% {t('similarityScore')}
                      </span>
                    </div>

                    {pageImgUrl ? (
                      <div
                        onClick={() => setSelectedImage({ url: pageImgUrl, cita: item.cita || `${item.fuente_nombre} (p. ${item.pagina})` })}
                        style={{
                          height: '240px',
                          background: '#040608',
                          overflow: 'hidden',
                          cursor: 'pointer',
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
            </div>
          ) : null}
        </>
      )}

      {/* CONTENIDO TAB 2: CATÁLOGO DE LIBROS PDF */}
      {activeTab === 'catalog' && (
        <div>
          {loadingManuales ? (
            <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', borderRadius: '12px' }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>{t('loadingCatalog')}</p>
            </div>
          ) : manuales.length === 0 ? (
            <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', borderRadius: '12px' }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>{t('noBooksFound')}</p>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: '1.5rem',
            }}>
              {manuales.map((bookFilename, idx) => {
                const title = cleanBookName(bookFilename);
                const pdfUrl = getPdfUrl(bookFilename);
                return (
                  <div
                    key={idx}
                    className="glass-panel"
                    style={{
                      borderRadius: '12px',
                      padding: '1.5rem',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      background: 'rgba(20, 24, 30, 0.85)',
                      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '1rem' }}>
                        <div style={{
                          width: '48px',
                          height: '48px',
                          borderRadius: '10px',
                          background: 'rgba(208, 17, 24, 0.2)',
                          border: '1px solid var(--brand-red)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '1.6rem',
                        }}>
                          📕
                        </div>
                        <div>
                          <span style={{
                            display: 'inline-block',
                            background: 'rgba(255, 255, 255, 0.1)',
                            color: '#ffd43b',
                            fontSize: '0.72rem',
                            fontWeight: 'bold',
                            padding: '0.15rem 0.5rem',
                            borderRadius: '4px',
                            marginBottom: '0.2rem',
                          }}>
                            {t('officialPdfBadge')}
                          </span>
                          <h4 style={{ margin: 0, fontSize: '1.1rem', color: '#ffffff', lineHeight: 1.3 }}>
                            {title}
                          </h4>
                        </div>
                      </div>
                      <p style={{ margin: '0 0 1.2rem 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {bookFilename}
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        onClick={() => setSelectedPdf(bookFilename)}
                        className="btn-primary"
                        style={{ flex: 1, padding: '0.65rem 1rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}
                      >
                        <span>👁️</span> {t('openPdf')}
                      </button>
                      <a
                        href={pdfUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-secondary"
                        style={{ padding: '0.65rem 0.9rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', textDecoration: 'none' }}
                        title={t('openNewTab')}
                      >
                        ↗
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Modal Visor de PDF embebido (iframe) */}
      {selectedPdf && (
        <div
          role="dialog"
          aria-modal="true"
          onClick={() => setSelectedPdf(null)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.88)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.2rem',
            boxSizing: 'border-box',
            backdropFilter: 'blur(4px)',
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="glass-panel"
            style={{
              maxWidth: '1100px',
              width: '100%',
              height: '92vh',
              borderRadius: '12px',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              background: '#0d1117',
              border: '1px solid rgba(255, 255, 255, 0.25)',
              boxShadow: '0 25px 50px rgba(0, 0, 0, 0.8)',
            }}
          >
            {/* Modal Header */}
            <div style={{
              padding: '0.8rem 1.25rem',
              background: '#161b22',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            }}>
              <span style={{ fontWeight: 'bold', color: '#ffd43b', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                📕 {cleanBookName(selectedPdf)}
              </span>
              <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
                <a
                  href={getPdfUrl(selectedPdf)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary"
                  style={{ padding: '0.3rem 0.75rem', fontSize: '0.8rem', textDecoration: 'none' }}
                >
                  ↗ {t('openNewTab')}
                </a>
                <button
                  type="button"
                  onClick={() => setSelectedPdf(null)}
                  className="btn-primary"
                  style={{ padding: '0.3rem 0.85rem', fontSize: '0.8rem' }}
                >
                  ✕ {t('closePdf')}
                </button>
              </div>
            </div>

            {/* Iframe Viewer */}
            <div style={{ flex: 1, background: '#1e232a', overflow: 'hidden' }}>
              <iframe
                src={getPdfUrl(selectedPdf)}
                title={selectedPdf}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                  display: 'block',
                }}
              />
            </div>
          </div>
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
