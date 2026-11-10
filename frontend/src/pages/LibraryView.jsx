import { useState, useEffect } from 'react';
import { getTranslation } from '../i18n/translations';

import { API_BASE } from '../api/config';

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
    const [baseWithoutHash, hash] = relativeUrl.split('#');
    const fullUrl = baseWithoutHash.startsWith('http') ? baseWithoutHash : `${API_BASE}${baseWithoutHash}`;
    const separator = fullUrl.includes('?') ? '&' : '?';
    const withToken = user?.token ? `${fullUrl}${separator}token=${encodeURIComponent(user.token)}` : fullUrl;
    return hash ? `${withToken}#${hash}` : withToken;
  };

  const getPdfUrl = (itemOrFilename) => {
    if (!itemOrFilename) return '';
    let raw;
    if (typeof itemOrFilename === 'object' && itemOrFilename.url) {
      raw = itemOrFilename.url.startsWith('http') ? itemOrFilename.url : `${API_BASE}${itemOrFilename.url}`;
    } else {
      const filename = typeof itemOrFilename === 'object' ? (itemOrFilename.filename || itemOrFilename.fuente_nombre) : itemOrFilename;
      raw = `${API_BASE}/api/v1/conocimiento/manuales/${encodeURIComponent(filename)}`;
    }
    const [baseWithoutHash, hash] = raw.split('#');
    const separator = baseWithoutHash.includes('?') ? '&' : '?';
    const withToken = user?.token ? `${baseWithoutHash}${separator}token=${encodeURIComponent(user.token)}` : baseWithoutHash;
    return hash ? `${withToken}#${hash}` : withToken;
  };

  const cleanBookName = (itemOrFilename) => {
    if (!itemOrFilename) return 'Documento';
    if (typeof itemOrFilename === 'object') {
      return itemOrFilename.nombre || itemOrFilename.fuente_nombre || itemOrFilename.filename || 'Documento';
    }
    return String(itemOrFilename)
      .replace(/\.(pdf|docx|txt|jpg|jpeg|png|webp)$/i, '')
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
            <form onSubmit={handleSearch} className="library-search-form">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t('searchPlaceholder')}
                className="library-search-input"
              />
              <button
                type="submit"
                disabled={loading}
                className="btn-primary library-search-btn"
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
              gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 340px), 1fr))',
              gap: '1.25rem',
            }}>
              {results.map((item, idx) => {
                const pageImgUrl = getMediaUrl(item.media_url);
                const scorePct = Math.round((item.score || 0) * 100);
                const detectedPage = item.pagina || (item.contenido_texto?.match(/\[P[aá]gina\s+(\d+)\]/i)?.[1] ?? null);
                const rawSourceUrl = item.fuente_url || '';
                const sourceUrlLower = rawSourceUrl.toLowerCase();
                const isSourcePdf = sourceUrlLower.includes('.pdf') || item.fuente_tipo === 'manual_pdf';
                const isSourceTxt = sourceUrlLower.includes('.txt') || item.fuente_tipo === 'texto';
                const isSourceDocx = sourceUrlLower.includes('.docx') || item.fuente_tipo === 'docx';
                const pdfSourceUrl = isSourcePdf && rawSourceUrl
                  ? (detectedPage && !rawSourceUrl.includes('#') ? `${rawSourceUrl}#page=${detectedPage}` : rawSourceUrl)
                  : rawSourceUrl;

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
                        📚 {item.cita || `${item.fuente_nombre || 'Manual'}${detectedPage ? ` (p. ${detectedPage})` : ''}`}
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
                      pageImgUrl.toLowerCase().includes('.pdf') ? (
                        <div
                          onClick={() => setSelectedPdf({
                            nombre: item.cita || item.fuente_nombre || 'Manual PDF',
                            url: item.media_url,
                            filename: item.fuente_nombre,
                          })}
                          style={{
                            height: '130px',
                            background: 'linear-gradient(135deg, rgba(208, 17, 24, 0.14), rgba(13, 17, 23, 0.95))',
                            overflow: 'hidden',
                            cursor: 'pointer',
                            position: 'relative',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.45rem',
                            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                          }}
                          title={t('openPdf')}
                        >
                          <span style={{ fontSize: '2rem' }}>📖</span>
                          <span style={{ fontSize: '0.86rem', color: '#ffd43b', fontWeight: 'bold' }}>
                            {detectedPage ? `${t('openPdf')} (p. ${detectedPage})` : t('openPdf')}
                          </span>
                        </div>
                      ) : (
                        <div
                          onClick={() => setSelectedImage({ url: pageImgUrl, cita: item.cita || `${item.fuente_nombre}${detectedPage ? ` (p. ${detectedPage})` : ''}` })}
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
                      )
                    ) : rawSourceUrl && isSourcePdf ? (
                      <div
                        onClick={() => setSelectedPdf({
                          nombre: item.cita || item.fuente_nombre || 'Manual PDF',
                          url: pdfSourceUrl,
                          filename: item.fuente_nombre,
                        })}
                        style={{
                          height: '115px',
                          background: 'linear-gradient(135deg, rgba(208, 17, 24, 0.14), rgba(13, 17, 23, 0.95))',
                          cursor: 'pointer',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.35rem',
                          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                        }}
                        title={t('openPdf')}
                      >
                        <span style={{ fontSize: '1.75rem' }}>📕</span>
                        <span style={{ fontSize: '0.84rem', color: '#ffd43b', fontWeight: 'bold' }}>
                          {detectedPage ? `${t('openPdf')} (p. ${detectedPage})` : t('openPdf')}
                        </span>
                      </div>
                    ) : rawSourceUrl && isSourceTxt ? (
                      <div
                        onClick={() => setSelectedPdf({
                          nombre: item.cita || item.fuente_nombre || 'Documento TXT',
                          url: rawSourceUrl,
                          filename: item.fuente_nombre,
                        })}
                        style={{
                          height: '110px',
                          background: '#161b22',
                          cursor: 'pointer',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.35rem',
                          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                        }}
                        title={t('previewFile') || 'Previsualizar'}
                      >
                        <span style={{ fontSize: '1.6rem' }}>📄</span>
                        <span style={{ fontSize: '0.82rem', color: '#ffd43b', fontWeight: 'bold' }}>
                          👁️ {t('previewFile') || 'Previsualizar'}
                        </span>
                      </div>
                    ) : rawSourceUrl && isSourceDocx ? (
                      <a
                        href={getMediaUrl(rawSourceUrl)}
                        download
                        style={{
                          height: '110px',
                          background: '#161b22',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.35rem',
                          textDecoration: 'none',
                          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                        }}
                      >
                        <span style={{ fontSize: '1.6rem' }}>📘</span>
                        <span style={{ fontSize: '0.82rem', color: '#ffd43b', fontWeight: 'bold' }}>
                          ⬇️ {t('downloadFile') || 'Descargar'} DOCX
                        </span>
                      </a>
                    ) : (
                      <div style={{
                        height: '110px',
                        background: '#161b22',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--text-secondary)',
                        fontSize: '0.85rem',
                        padding: '0 1rem',
                        textAlign: 'center',
                      }}>
                        📄 {item.fuente_referencia || 'Fragmento textual de manual'}
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
              gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 280px), 1fr))',
              gap: '1.25rem',
            }}>
              {manuales.map((bookItem, idx) => {
                const isObject = typeof bookItem === 'object' && bookItem !== null;
                const title = isObject
                  ? (bookItem.fuente_nombre || bookItem.filename || 'Documento')
                  : cleanBookName(bookItem);
                const filename = isObject
                  ? (bookItem.filename || bookItem.fuente_nombre || '')
                  : bookItem;
                const formato = isObject
                  ? (bookItem.formato || (bookItem.fuente_url?.toLowerCase().includes('.pdf') ? 'pdf' : 'otro'))
                  : (String(bookItem).toLowerCase().endsWith('.pdf') ? 'pdf' : 'otro');
                const directUrl = isObject && bookItem.fuente_url
                  ? getMediaUrl(bookItem.fuente_url)
                  : getPdfUrl(filename);
                const totalChunks = isObject ? bookItem.total_chunks : null;

                const isPdf = formato === 'pdf';
                const isImg = formato === 'imagen';
                const isTxt = formato === 'txt';

                const icon = isPdf ? '📕' : (isImg ? '🖼️' : (formato === 'docx' ? '📘' : '📄'));
                const badgeText = isPdf
                  ? (t('officialPdfBadge') || 'Manual Oficial PDF')
                  : isImg
                    ? (t('imageKnowledgeBadge') || 'Imagen / Diagrama')
                    : isTxt
                      ? (t('textKnowledgeBadge') || 'Documento TXT')
                      : formato === 'docx'
                        ? (t('docxKnowledgeBadge') || 'Documento Word (DOCX)')
                        : 'Manual de Conocimiento';

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
                          flexShrink: 0,
                        }}>
                          {icon}
                        </div>
                        <div style={{ minWidth: 0 }}>
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
                            {badgeText}
                          </span>
                          <h4 style={{ margin: 0, fontSize: '1.1rem', color: '#ffffff', lineHeight: 1.3, wordBreak: 'break-word' }}>
                            {title}
                          </h4>
                        </div>
                      </div>
                      <p style={{ margin: '0 0 1.2rem 0', fontSize: '0.82rem', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
                        {totalChunks ? `${totalChunks} ${t('indexedChunks') || 'fragmentos indexados'}` : filename}
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                      {isPdf ? (
                        <button
                          type="button"
                          onClick={() => setSelectedPdf({ nombre: title, url: isObject ? (bookItem.fuente_url || '') : '', filename })}
                          className="btn-primary"
                          style={{ flex: 1, padding: '0.65rem 1rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                          </svg>
                          <span>{t('openPdf')}</span>
                        </button>
                      ) : isImg ? (
                        <button
                          type="button"
                          onClick={() => setSelectedImage({ url: directUrl, cita: title })}
                          className="btn-primary"
                          style={{ flex: 1, padding: '0.65rem 1rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}
                        >
                          <span>🔍 {t('viewFullImage') || 'Ver Imagen'}</span>
                        </button>
                      ) : isTxt ? (
                        <button
                          type="button"
                          onClick={() => setSelectedPdf({ nombre: title, url: isObject ? (bookItem.fuente_url || '') : '', filename })}
                          className="btn-primary"
                          style={{ flex: 1, padding: '0.65rem 1rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}
                        >
                          <span>👁️ {t('previewFile') || 'Previsualizar'}</span>
                        </button>
                      ) : (
                        <a
                          href={directUrl}
                          download={filename}
                          className="btn-primary"
                          style={{ flex: 1, padding: '0.65rem 1rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', textDecoration: 'none' }}
                        >
                          <span>⬇️ {t('downloadFile') || 'Descargar'}</span>
                        </a>
                      )}

                      <a
                        href={directUrl}
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
            className="glass-panel pdf-modal-wrapper"
            style={{
              backgroundColor: '#0d1117',
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
              flexWrap: 'wrap',
              gap: '0.5rem',
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
                  style={{ padding: '0.4rem 0.85rem', fontSize: '0.85rem', textDecoration: 'none', minHeight: '44px', display: 'inline-flex', alignItems: 'center' }}
                >
                  ↗ {t('openNewTab')}
                </a>
                <button
                  type="button"
                  onClick={() => setSelectedPdf(null)}
                  className="btn-primary"
                  style={{ padding: '0.4rem 0.85rem', fontSize: '0.85rem', minHeight: '44px', display: 'inline-flex', alignItems: 'center' }}
                >
                  ✕ {t('closePdf')}
                </button>
              </div>
            </div>

            {/* Iframe Viewer */}
            <div className="pdf-iframe-holder">
              <iframe
                src={getPdfUrl(selectedPdf)}
                title={cleanBookName(selectedPdf)}
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
