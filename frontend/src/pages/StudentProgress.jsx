import { useEffect, useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { getTranslation } from '../i18n/translations';

import { API_BASE } from '../api/config';

export const resolveVideoUrl = (rawUrl) => {
  if (!rawUrl) return null;
  let url = String(rawUrl).trim();
  if (url.includes('localhost:8000/static/')) {
    url = url.replace(/^https?:\/\/localhost:8000/, '');
  }
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  if (!url.startsWith('/')) url = '/' + url;
  return `${API_BASE}${url}`;
};

function StudentVideoPlayer({ videoSrc, timestampError, frameErrorUrl, nombresArticulaciones, t }) {
  const [showFrameModal, setShowFrameModal] = useState(false);
  const [videoError, setVideoError] = useState(false);
  const videoRef = useRef(null);
  const ts = typeof timestampError === 'number' ? timestampError : Number(timestampError || 0);
  const articulaciones = Array.isArray(nombresArticulaciones) ? nombresArticulaciones : [];

  return (
    <div>
      <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
        {t('myVideo')}
      </h4>
      {videoSrc && !videoError ? (
        <>
          <video
            ref={videoRef}
            controls
            playsInline
            preload="metadata"
            key={videoSrc}
            onError={() => setVideoError(true)}
            style={{ width: '100%', height: 'auto', minHeight: 200, maxHeight: 280, objectFit: 'contain', background: '#08090b', borderRadius: 8 }}
          >
            <source src={videoSrc} type="video/mp4" />
            {t('videoNotSupported')}
          </video>
          {ts > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', marginTop: '0.5rem', padding: '0.5rem 0.6rem', background: 'rgba(0,0,0,0.3)', borderRadius: 6, flexWrap: 'wrap' }}>
              <span style={{ color: '#ffd43b', fontSize: '0.82rem' }}>
                ⚠️ {t('errorDetectedAt')} {ts.toFixed(2)}s
              </span>
              <button
                type="button"
                onClick={() => {
                  if (videoRef.current) {
                    videoRef.current.currentTime = ts;
                    videoRef.current.pause();
                  }
                  setShowFrameModal(true);
                }}
                style={{
                  background: '#d01118',
                  color: 'white',
                  border: 'none',
                  borderRadius: 6,
                  padding: '0.4rem 0.75rem',
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  minHeight: '44px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {t('jumpToError')}
              </button>
            </div>
          )}
          {showFrameModal && (
            <div
              role="dialog"
              aria-modal="true"
              style={{
                position: 'fixed',
                inset: 0,
                zIndex: 9999,
                backgroundColor: 'rgba(0, 0, 0, 0.85)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '1rem',
                backdropFilter: 'blur(4px)',
              }}
              onClick={() => setShowFrameModal(false)}
            >
              <div
                className="glass-panel"
                style={{
                  maxWidth: '720px',
                  width: '100%',
                  backgroundColor: '#12141a',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  boxShadow: '0 20px 40px rgba(0, 0, 0, 0.7)',
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ margin: 0, color: '#f8fafc', fontSize: '1.15rem' }}>
                    {t('criticalFrameTitle')} ({ts.toFixed(2)}s)
                  </h3>
                  <button
                    type="button"
                    onClick={() => setShowFrameModal(false)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#94a3b8',
                      fontSize: '1.5rem',
                      lineHeight: 1,
                      cursor: 'pointer',
                    }}
                  >
                    &times;
                  </button>
                </div>

                {frameErrorUrl ? (
                  <div style={{ width: '100%', maxHeight: '440px', display: 'flex', justifyContent: 'center', background: '#000', borderRadius: '8px', overflow: 'hidden' }}>
                    <img
                      src={frameErrorUrl}
                      alt={t('criticalFrameTitle')}
                      style={{ maxWidth: '100%', maxHeight: '440px', objectFit: 'contain' }}
                    />
                  </div>
                ) : (
                  <p style={{ color: '#94a3b8', textAlign: 'center' }}>{t('criticalFrameUnavailable')}</p>
                )}

                <div style={{ padding: '0.75rem 1rem', background: 'rgba(239, 68, 68, 0.12)', borderLeft: '4px solid #ef4444', borderRadius: '4px' }}>
                  <p style={{ margin: 0, color: '#ef4444', fontWeight: 'bold', fontSize: '0.95rem' }}>
                    {t('affectedJoints')} {articulaciones.length > 0 ? articulaciones.join(', ') : t('notSpecified')}
                  </p>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                  <button
                    type="button"
                    onClick={() => setShowFrameModal(false)}
                    style={{
                      background: '#d01118',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '0.5rem 1.25rem',
                      fontWeight: 'bold',
                      fontSize: '0.9rem',
                      cursor: 'pointer',
                    }}
                  >
                    {t('close')}
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: 8, textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
          ⚠️ {t('studentVideoUnavailable')}
        </div>
      )}
    </div>
  );
}

function CoachVideoPlayer({ videoSrc, coachNombre, t }) {
  const [videoError, setVideoError] = useState(false);
  return (
    <div>
      <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
        {t('coachDemonstration')} · {coachNombre}
      </h4>
      {videoSrc && !videoError ? (
        <video
          controls
          playsInline
          preload="metadata"
          key={videoSrc}
          onError={() => setVideoError(true)}
          style={{ width: '100%', height: 'auto', minHeight: 200, maxHeight: 280, objectFit: 'contain', background: '#08090b', borderRadius: 8 }}
        >
          <source src={videoSrc} type="video/mp4" />
          {t('videoNotSupported')}
        </video>
      ) : (
        <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: 8, textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
          ⚠️ {t('referenceVideoUnavailable')}
        </div>
      )}
    </div>
  );
}

export default function StudentProgress({ user, idioma, onViewTheory }) {
  const [evaluaciones, setEvaluaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const t = (key) => getTranslation(idioma, key);
  const lang = (idioma || 'es').toLowerCase();
  const dateLocale = lang === 'pt' ? 'pt-BR' : lang === 'en' ? 'en-US' : 'es-ES';

  useEffect(() => {
    let active = true;
    fetch(`${API_BASE}/api/v1/auth/alumnos/${user.user_id}/evaluaciones`, {
      headers: { Authorization: `Bearer ${user.token}` },
    })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || t('couldNotLoadProgress'));
        }
        return response.json();
      })
      .then((data) => { if (active) setEvaluaciones(Array.isArray(data) ? data : []); })
      .catch((cause) => { if (active) setError(cause.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [user.user_id, user.token]);

  return (
    <section style={{ width: 'min(1100px, 100%)', margin: '1rem auto', padding: '1rem 0.5rem', color: 'white', boxSizing: 'border-box' }}>
      <h2 style={{ color: 'var(--brand-red)', marginTop: 0 }}>{t('myProgress')}</h2>
      <p style={{ color: 'var(--text-secondary)' }}>{t('progressSubtitle')}</p>
      {loading && <p>{t('loadingProgress')}</p>}
      {error && <p role="alert" style={{ color: '#ff8787' }}>{error}</p>}
      {!loading && !error && evaluaciones.length === 0 && <p>{t('noEvaluationsYet')}</p>}
      <div style={{ display: 'grid', gap: '1.25rem' }}>
        {evaluaciones.map((item) => {
          const score = Number(item.porcentaje_similitud || 0);
          const videoAlumno = resolveVideoUrl(item.url_video_alumno || item.video_alumno_url);
          const videoProfesor = resolveVideoUrl(item.video_referencia_url);
          const rawCoach = item.video_referencia_profesor_nombre || t('coach');
          const coachNombre = lang === 'en'
            ? rawCoach.replace(/Mestre|Profesor/gi, 'Coach')
            : (lang === 'pt' ? rawCoach.replace(/Profesor|Coach/gi, 'Mestre') : rawCoach.replace(/Mestre|Coach/gi, 'Profesor'));

          return (
            <article key={item.id} className="glass-panel" style={{ padding: '1.25rem', borderRadius: 12, boxSizing: 'border-box' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{item.tecnica_nombre || 'Jiu-Jitsu'}</h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.2rem' }}>
                    <small style={{ color: 'var(--text-secondary)' }}>
                      {item.fecha_evaluacion ? new Date(item.fecha_evaluacion).toLocaleString(dateLocale) : t('dateUnavailable')}
                    </small>
                    {item.sucursal_nombre && (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.2rem',
                        background: 'rgba(255, 255, 255, 0.08)',
                        padding: '0.15rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        color: 'rgba(255, 255, 255, 0.85)',
                        border: '1px solid rgba(255, 255, 255, 0.15)'
                      }}>
                        📍 {item.sucursal_nombre}
                      </span>
                    )}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', flexWrap: 'wrap', width: 'auto' }}>
                  <button
                    type="button"
                    onClick={() => onViewTheory && onViewTheory(item.tecnica_nombre, item.frame_error_url)}
                    className="btn-secondary"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.4rem',
                      background: 'rgba(208, 17, 24, 0.15)',
                      border: '1px solid var(--brand-red)',
                      color: '#ffffff',
                      padding: '0.5rem 1rem',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      fontWeight: 'bold',
                      minHeight: '44px',
                      transition: 'all 0.2s',
                    }}
                    title={t('techniqueTheory')}
                  >
                    <span>📖</span> {t('techniqueTheory')}
                  </button>
                  <strong style={{ color: score >= 85 ? '#69db7c' : score >= 70 ? '#ffd43b' : '#ff8787', fontSize: '1.25rem' }}>
                    {Math.round(score)}% {t('similarity')}
                  </strong>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '1rem', marginTop: '1rem' }}>
                <StudentVideoPlayer
                  videoSrc={videoAlumno}
                  timestampError={item.timestamp_error_segundos}
                  frameErrorUrl={item.frame_error_url ? (item.frame_error_url.startsWith('http') ? item.frame_error_url : `${API_BASE}${item.frame_error_url}`) : null}
                  nombresArticulaciones={item.nombres_articulaciones_criticas}
                  t={t}
                />
                <CoachVideoPlayer
                  videoSrc={videoProfesor}
                  coachNombre={coachNombre}
                  t={t}
                />
              </div>
              <div style={{ marginTop: '1rem', lineHeight: 1.5, borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '0.75rem' }}>
                {item.feedback_summary && (
                  <p style={{ margin: '0 0 0.4rem 0', color: '#ffffff', fontSize: '1rem' }}>
                    <strong>{item.feedback_summary}</strong>
                  </p>
                )}
                <div style={{ color: '#d1d5db', fontSize: '0.95rem' }}>
                  <ReactMarkdown>
                    {(lang === 'pt' ? item.feedback_gemini_pt : (lang === 'es' ? item.feedback_gemini_es : (item.feedback_gemini_en || item.feedback_gemini_es))) || item.feedback_gemini_es || item.feedback_gemini_pt || t('noCorrectionAvailable')}
                  </ReactMarkdown>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
