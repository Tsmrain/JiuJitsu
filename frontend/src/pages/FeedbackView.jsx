import { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './FeedbackView.css';
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

export default function FeedbackView({ user, result, tecnica, onReset, idioma }) {
  const [videoError, setVideoError] = useState(false);
  const [videoAlumnoError, setVideoAlumnoError] = useState(false);
  const [showFrameModal, setShowFrameModal] = useState(false);
  const videoRef = useRef(null);

  const t = (key) => getTranslation(idioma, key);

  if (!result) return null;

  const similitud = typeof result.similitud === 'number' ? result.similitud : 0;
  const isPassing = similitud >= 85;

  const videoUrl = resolveVideoUrl(result.video_referencia_url);
  const videoAlumnoUrl = resolveVideoUrl(result.url_video_alumno || result.video_alumno_url);
  const frameErrorUrl = result.frame_error_url
    ? (result.frame_error_url.startsWith('http') ? result.frame_error_url : `${API_BASE}${result.frame_error_url.startsWith('/') ? '' : '/'}${result.frame_error_url}`)
    : null;

  const timestampError = typeof result.timestamp_error_segundos === 'number'
    ? result.timestamp_error_segundos
    : Number(result.timestamp_error_segundos || 0);

  const tecnicaNombre = tecnica?.nombre || result.tecnica_nombre || 'Jiu-Jitsu';

  const defaultCoach = t('coach');
  const rawProfesor = result.video_referencia_profesor_nombre || tecnica?.profesorRef || defaultCoach;
  const lang = (idioma || 'es').toLowerCase();
  const profesorNombre = lang === 'en'
    ? rawProfesor.replace(/Mestre|Profesor/gi, 'Coach')
    : (lang === 'pt' ? rawProfesor.replace(/Profesor|Coach/gi, 'Mestre') : rawProfesor.replace(/Mestre|Coach/gi, 'Profesor'));

  const feedbackSummary = result.feedback_summary || (result.feedback ? result.feedback.split('.')[0].trim() : t('aiTechnicalAnalysis'));
  const feedbackText = result.feedback || '';

  return (
    <div className="feedback-container">
      <div className="feedback-header">
        <h2>{t('analysisCompleted')}</h2>
        <p>{t('analysisCompletedDesc')}</p>
      </div>

      {tecnica && (
        <div className="tecnica-comparison-card glass-panel">
          <span className="tecnica-badge">{t('evaluatedTechnique')}</span>
          <h3>{tecnicaNombre}</h3>
          <p>
            <strong>{t('referencePattern')}</strong> {profesorNombre}
          </p>
        </div>
      )}

      <div className="feedback-grid-2x2">
        {/* 1. Top-Left: Instructor Reference Video */}
        <section className="glass-panel feedback-card">
          <div className="card-header">
            <span className="card-label">{t('coachReferenceVideo')}</span>
            <h3>{profesorNombre}</h3>
          </div>
          <div className="media-wrapper">
            {videoUrl && !videoError ? (
              <video
                src={videoUrl}
                controls
                playsInline
                preload="metadata"
                key={videoUrl}
                onError={() => setVideoError(true)}
              >
                {t('videoNotSupported')}
              </video>
            ) : (
              <div className="media-placeholder" role="status">
                {t('referenceVideoUnavailablePatternNote')}
              </div>
            )}
          </div>
        </section>

        {/* 2. Top-Right: Student Video with Jump to Error & Critical Frame */}
        <section className="glass-panel feedback-card">
          <div className="card-header">
            <span className="card-label">{t('studentVideo')}</span>
            <h3>{t('biomechanicExecution')}</h3>
          </div>
          <div className="media-wrapper">
            {videoAlumnoUrl && !videoAlumnoError ? (
              <video
                ref={videoRef}
                controls
                playsInline
                preload="metadata"
                key={videoAlumnoUrl}
                onError={() => setVideoAlumnoError(true)}
              >
                <source src={videoAlumnoUrl} type="video/mp4" />
                {t('videoNotSupported')}
              </video>
            ) : frameErrorUrl ? (
              <img src={frameErrorUrl} alt={t('criticalFrameTitle')} />
            ) : (
              <div className="media-placeholder" role="status">
                {t('studentVideoUnavailable')}
              </div>
            )}
          </div>
          {timestampError > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.6rem', padding: '0.5rem 0.75rem', background: 'rgba(0, 0, 0, 0.4)', borderRadius: '6px', flexWrap: 'wrap', gap: '0.5rem' }}>
              <span style={{ color: '#ffd43b', fontSize: '0.85rem', fontWeight: '500' }}>
                ⚠️ {t('errorDetectedAt')} {timestampError.toFixed(2)}s
              </span>
              <button
                type="button"
                onClick={() => {
                  if (videoRef.current) {
                    videoRef.current.currentTime = timestampError;
                    videoRef.current.pause();
                  }
                  setShowFrameModal(true);
                }}
                style={{
                  background: 'var(--brand-red, #d01118)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '0.4rem 0.85rem',
                  fontSize: '0.85rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  minHeight: '44px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'opacity 0.2s',
                }}
              >
                {t('jumpToError')}
              </button>
            </div>
          )}
        </section>

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
                  {t('criticalFrameTitle')} ({timestampError.toFixed(2)}s)
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
                  {t('affectedJoints')} {(result.nombres_articulaciones_criticas && result.nombres_articulaciones_criticas.length > 0) ? result.nombres_articulaciones_criticas.join(', ') : t('notSpecified')}
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

        {/* 3. Bottom Full-Width: AI Analysis Card */}
        <section className="glass-panel feedback-card ai-feedback-card">
          <div className="ai-card-header">
            <span className="card-label">{t('aiTechnicalAnalysis')}</span>
            <div className={`similarity-badge ${isPassing ? 'badge-excellent' : similitud >= 70 ? 'badge-good' : 'badge-needs-work'}`}>
              {Math.round(similitud)}% {t('match')}
            </div>
          </div>
          <div className="ai-card-body">
            {isPassing ? (
              <div className="pass-status">
                <svg className="check-icon" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                <p className="pass-text">{t('greatJob')}</p>
              </div>
            ) : (
              <div className="correction-container">
                {feedbackSummary && (
                  <p className="summary-title">
                    <strong>{feedbackSummary}</strong>
                  </p>
                )}
                <div className="markdown-feedback">
                  <ReactMarkdown>{feedbackText}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>

      <div className="feedback-actions">
        <button className="btn-primary reset-btn" onClick={onReset}>
          {t('analyzeAnotherTechnique')}
        </button>
      </div>
    </div>
  );
}
