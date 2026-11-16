import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { getTranslation } from '../i18n/translations';

import { API_BASE } from '../api/config';

export default function LibraryView({ user, idioma, onClose, initialQuery, initialImageUrl }) {
  const [activeTab, setActiveTab] = useState('search'); // 'search' | 'catalog'
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedSourceSnippet, setSelectedSourceSnippet] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [activeImageUrl, setActiveImageUrl] = useState(initialImageUrl || null);
  const chatEndRef = useRef(null);

  // Estado del Catálogo de Libros PDF
  const [manuales, setManuales] = useState([]);
  const [loadingManuales, setLoadingManuales] = useState(false);
  const [deletingManual, setDeletingManual] = useState(null);
  const [selectedPdf, setSelectedPdf] = useState(null);
  const initialQueryProcessed = useRef(false);

  const t = (key) => getTranslation(idioma, key);

  useEffect(() => {
    if (initialImageUrl) {
      setActiveImageUrl(initialImageUrl);
    }
  }, [initialImageUrl]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSearch = async (e, customQuery = null, customImage = undefined) => {
    if (e) e.preventDefault();
    const cleanQuery = (customQuery !== null ? customQuery : query).trim();
    if (!cleanQuery || loading) return;
    if (customQuery === null) {
      setQuery('');
    }

    const targetImg = customImage !== undefined ? customImage : activeImageUrl;
    const userMsgId = `u-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        role: 'user',
        text: cleanQuery,
        imageUrl: targetImg || null,
      },
    ]);

    setLoading(true);
    setErrorMsg('');
    try {
      const payload = {
        query: cleanQuery,
        idioma: idioma || 'es',
        limit: 6,
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
      const sources = Array.isArray(data.sources)
        ? data.sources
        : (data.resultados || []).slice(0, 3).map((item, idx) => ({ ...item, index: idx + 1 }));
      const answerText = (data.answer || '').trim() || (sources.length > 0 ? sources[0].contenido_texto : t('noResults'));

      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          text: answerText,
          sources,
        },
      ]);
    } catch (err) {
      console.error('Error buscando en biblioteca:', err);
      setErrorMsg(err.message || t('connectionError'));
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          text: `⚠️ ${err.message || t('connectionError')}`,
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCitationClick = (src) => {
    if (!src) return;
    const isInstructorMsg =
      src.fuente_tipo === 'instructor_message' ||
      /instrucciones del profesor/i.test(src.fuente_nombre || '');

    if (isInstructorMsg) {
      setSelectedSourceSnippet(src);
      return;
    }

    const detectedPage = src.pagina || (src.contenido_texto?.match(/\[P[aá]gina\s+(\d+)\]/i)?.[1] ?? null);
    const mediaUrl = src.media_url ? getMediaUrl(src.media_url) : '';
    const rawSourceUrl = src.fuente_url || '';
    const isMediaImg = mediaUrl && !mediaUrl.toLowerCase().includes('.pdf');

    if (isMediaImg) {
      setSelectedImage({
        url: mediaUrl,
        cita: src.cita || `${src.fuente_nombre || 'Manual'}${detectedPage ? `, p. ${detectedPage}` : ''}`,
      });
      return;
    }

    const pdfCandidate = (src.media_url && src.media_url.toLowerCase().includes('.pdf'))
      ? src.media_url
      : rawSourceUrl;

    if (pdfCandidate) {
      const urlWithPage = (detectedPage && !pdfCandidate.includes('#') && pdfCandidate.toLowerCase().includes('.pdf'))
        ? `${pdfCandidate}#page=${detectedPage}`
        : pdfCandidate;
      setSelectedPdf({
        nombre: src.cita || src.fuente_nombre || 'Manual',
        url: urlWithPage,
        filename: src.fuente_nombre,
      });
      return;
    }

    setSelectedSourceSnippet(src);
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

  const canDeleteManual = user?.rol === 'profesor' || user?.rol === 'admin';

  const handleDeleteManual = async (filename, title) => {
    if (!filename || !canDeleteManual) return;
    if (!confirm(`${t('confirmDeleteManual')} "${title}"?`)) return;

    setDeletingManual(filename);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/conocimiento/manuales/${encodeURIComponent(filename)}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${user?.token || ''}`,
          },
        }
      );
      if (res.ok) {
        await fetchManuales();
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(errData.detail || t('errorDeletingManual'));
      }
    } catch (err) {
      console.error('Error eliminando manual:', err);
      alert(t('connectionError'));
    } finally {
      setDeletingManual(null);
    }
  };

  useEffect(() => {
    if (initialQuery && initialQuery.trim() && !initialQueryProcessed.current) {
      initialQueryProcessed.current = true;
      setActiveTab('search');
      setMessages([]);
      handleSearch(null, initialQuery.trim(), initialImageUrl);
    }
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

        {/* PESTAÑA 1: CHAT RAG CON CITAS (Multimodal Banner si aplica) */}
        {activeTab === 'search' && activeImageUrl && (
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
              onClick={() => setActiveImageUrl(null)}
              style={{ background: 'none', border: 'none', color: '#ff8787', fontSize: '0.85rem', cursor: 'pointer', padding: '0.2rem 0.5rem' }}
              title={t('removeImageSearch')}
            >
              ✕ {t('removeImageSearch')}
            </button>
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

      {/* CONTENIDO TAB 1: CHATBOT RAG CON HISTORIAL Y CHIPS DE CITA */}
      {activeTab === 'search' && (
        <div
          className="glass-panel"
          style={{
            borderRadius: '12px',
            display: 'flex',
            flexDirection: 'column',
            minHeight: '460px',
            maxHeight: '68vh',
            overflow: 'hidden',
            border: '1px solid rgba(255, 255, 255, 0.12)',
          }}
        >
          <div style={{
            padding: '0.75rem 1.15rem',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            background: 'rgba(0, 0, 0, 0.25)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.82rem',
            color: 'var(--text-secondary)',
          }}>
            <span>🥋 {t('virtualProfessorTitle') || 'Profesor Virtual IA'}</span>
            {messages.length > 0 && (
              <button
                type="button"
                onClick={() => setMessages([])}
                className="btn-secondary"
                style={{ padding: '0.2rem 0.65rem', fontSize: '0.75rem' }}
              >
                Limpiar chat
              </button>
            )}
          </div>

          {/* Historial de mensajes */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '1.2rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            {messages.length === 0 && !loading && (
              <div style={{
                margin: 'auto',
                textAlign: 'center',
                maxWidth: '480px',
                color: 'var(--text-secondary)',
                padding: '2rem 1rem',
              }}>
                <div style={{ fontSize: '2.2rem', marginBottom: '0.6rem' }}>💬</div>
                <p style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#e6edf3', fontWeight: 600 }}>
                  Pregunta sobre técnicas, escapes o principios de tus manuales
                </p>
                <p style={{ margin: 0, fontSize: '0.85rem' }}>
                  Cada respuesta incluye citas inline `[1]`, `[2]`, `[3]` con acceso directo a la página del manual.
                </p>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  gap: '0.45rem',
                }}
              >
                <div style={{
                  maxWidth: '85%',
                  padding: '0.85rem 1.05rem',
                  borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                  background: msg.role === 'user'
                    ? 'rgba(208, 17, 24, 0.22)'
                    : 'rgba(22, 27, 34, 0.92)',
                  border: msg.role === 'user'
                    ? '1px solid rgba(208, 17, 24, 0.45)'
                    : '1px solid rgba(255, 255, 255, 0.12)',
                  color: '#e6edf3',
                  fontSize: '0.92rem',
                  lineHeight: '1.55',
                  whiteSpace: 'pre-wrap',
                }}>
                  {msg.imageUrl && (
                    <img
                      src={getMediaUrl(msg.imageUrl)}
                      alt="Contexto visual"
                      style={{
                        width: '72px',
                        height: '52px',
                        objectFit: 'cover',
                        borderRadius: '6px',
                        marginBottom: '0.45rem',
                        display: 'block',
                        border: '1px solid #ffd43b',
                      }}
                    />
                  )}
                  {msg.role === 'assistant' ? (
                    <div className="markdown-chat-body" style={{ whiteSpace: 'normal' }}>
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                  ) : (
                    msg.text
                  )}
                </div>

                {/* Chips de cita debajo de cada respuesta del asistente */}
                {msg.role === 'assistant' && Array.isArray(msg.sources) && msg.sources.length > 0 && (
                  <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.45rem',
                    maxWidth: '85%',
                  }}>
                    {msg.sources.map((src, sIdx) => {
                      const chipNum = src.index || sIdx + 1;
                      const detectedPage = src.pagina || (src.contenido_texto?.match(/\[P[aá]gina\s+(\d+)\]/i)?.[1] ?? null);
                      const isInstructorMsg =
                        src.fuente_tipo === 'instructor_message' ||
                        /instrucciones del profesor/i.test(src.fuente_nombre || '');
                      const rawBookName = (src.fuente_nombre || src.cita || 'Manual')
                        .replace(/,\s*p\.\s*\d+$/i, '')
                        .trim();
                      const shortBookName = rawBookName.length > 26
                        ? `${rawBookName.slice(0, 25).trim()}…`
                        : rawBookName;
                      const chipLabel = detectedPage ? `${shortBookName} (p. ${detectedPage})` : shortBookName;
                      const hasUrl = Boolean(
                        (src.media_url && String(src.media_url).trim()) ||
                        (src.fuente_url && String(src.fuente_url).trim())
                      );
                      const hasSnippet = Boolean(src.contenido_texto && String(src.contenido_texto).trim());
                      const isClickable = isInstructorMsg ? hasSnippet : (hasUrl || hasSnippet);
                      const chipTooltip = !isClickable
                        ? 'Página no disponible'
                        : isInstructorMsg
                          ? `Ver nota del instructor: ${rawBookName}`
                          : `${rawBookName}${detectedPage ? ` (p. ${detectedPage})` : ''}${src.contenido_texto ? ` — ${src.contenido_texto.slice(0, 150)}` : ''}`;
                      return (
                        <span
                          key={src.id || `${msg.id}-src-${sIdx}`}
                          title={chipTooltip}
                          style={{ display: 'inline-flex' }}
                        >
                          <button
                            type="button"
                            disabled={!isClickable}
                            aria-disabled={!isClickable}
                            onClick={() => isClickable && handleCitationClick(src)}
                            style={{
                              padding: '0.32rem 0.68rem',
                              borderRadius: '999px',
                              background: isClickable ? 'rgba(255, 212, 59, 0.12)' : 'rgba(255, 255, 255, 0.05)',
                              border: isClickable ? '1px solid rgba(255, 212, 59, 0.35)' : '1px solid rgba(255, 255, 255, 0.14)',
                              color: isClickable ? '#ffd43b' : '#8b949e',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              cursor: isClickable ? 'pointer' : 'not-allowed',
                              opacity: isClickable ? 1 : 0.65,
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.35rem',
                            }}
                          >
                            <span>[{chipNum}]</span>
                            <span>{isInstructorMsg ? '🥋' : '📚'} {chipLabel}</span>
                          </button>
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div style={{
                alignSelf: 'flex-start',
                padding: '0.75rem 1rem',
                borderRadius: '14px 14px 14px 4px',
                background: 'rgba(22, 27, 34, 0.92)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: 'var(--text-secondary)',
                fontSize: '0.88rem',
              }}>
                ⏳ {t('searching')}
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input de consulta del chat */}
          <form
            onSubmit={handleSearch}
            className="library-search-form"
            style={{
              padding: '0.85rem 1rem',
              margin: 0,
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              background: 'rgba(0, 0, 0, 0.3)',
            }}
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('searchPlaceholder')}
              className="library-search-input"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="btn-primary library-search-btn"
            >
              {loading ? t('searching') : t('searchButton')}
            </button>
          </form>
        </div>
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
                          <span>👁️ {t('previewFile') || 'Previsualizar'}</span>
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
                      {canDeleteManual && (
                        <button
                          type="button"
                          onClick={() => handleDeleteManual(filename, title)}
                          disabled={deletingManual === filename}
                          className="btn-secondary"
                          style={{
                            padding: '0.65rem 0.85rem',
                            fontSize: '0.85rem',
                            background: 'rgba(239, 68, 68, 0.14)',
                            color: '#fca5a5',
                            border: '1px solid rgba(239, 68, 68, 0.35)',
                            cursor: deletingManual === filename ? 'not-allowed' : 'pointer',
                            opacity: deletingManual === filename ? 0.6 : 1,
                          }}
                          title={`${t('deleteManual')} ${title}`}
                        >
                          {deletingManual === filename ? '...' : `🗑️ ${t('deleteManual')}`}
                        </button>
                      )}
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
      {selectedSourceSnippet && (
        <div
          role="dialog"
          aria-modal="true"
          onClick={() => setSelectedSourceSnippet(null)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.85)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem',
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="glass-panel"
            style={{
              maxWidth: '640px',
              width: '100%',
              borderRadius: '12px',
              background: '#0d1117',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              overflow: 'hidden',
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
              <span style={{ fontWeight: 'bold', color: '#ffd43b' }}>
                📚 [{selectedSourceSnippet.index || 1}] {selectedSourceSnippet.cita || selectedSourceSnippet.fuente_nombre}
              </span>
              <button type="button" onClick={() => setSelectedSourceSnippet(null)} className="btn-secondary" style={{ padding: '0.25rem 0.7rem', fontSize: '0.8rem' }}>
                ✕ {t('close')}
              </button>
            </div>
            <div style={{ padding: '1.1rem', color: '#e6edf3', whiteSpace: 'pre-wrap', lineHeight: 1.55, maxHeight: '65vh', overflowY: 'auto' }}>
              {selectedSourceSnippet.contenido_texto}
            </div>
          </div>
        </div>
      )}

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
