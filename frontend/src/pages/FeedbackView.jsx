import { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './FeedbackView.css';

const API_BASE = 'http://localhost:8000';

export default function FeedbackView({ user, result, tecnica, onReset }) {
  const [videoError, setVideoError] = useState(false);
  const [videoAlumnoError, setVideoAlumnoError] = useState(false);
  const [showFrameModal, setShowFrameModal] = useState(false);
  const videoRef = useRef(null);

  if (!result) return null;

  const similitud = typeof result.similitud === 'number' ? result.similitud : 0;
  const isPassing = similitud >= 85;

  const videoUrl = result.video_referencia_url
    ? `${API_BASE}${result.video_referencia_url}`
    : null;
  const videoAlumnoUrl = result.url_video_alumno
    ? (result.url_video_alumno.startsWith('http') ? result.url_video_alumno : `${API_BASE}${result.url_video_alumno}`)
    : null;
  const frameErrorUrl = result.frame_error_url
    ? `${API_BASE}${result.frame_error_url}`
    : null;

  const timestampError = typeof result.timestamp_error_segundos === 'number'
    ? result.timestamp_error_segundos
    : Number(result.timestamp_error_segundos || 0);

  const tecnicaNombre = tecnica?.nombre || result.tecnica_nombre || 'Jiu-Jitsu';
  const practiceUrl = result.practice_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(tecnicaNombre + ' jiu-jitsu tutorial')}`;

  const rawProfesor = result.video_referencia_profesor_nombre || tecnica?.profesorRef || 'Instructor';
  const profesorNombre = rawProfesor.replace(/Mestre/gi, 'Coach');

  const feedbackSummary = result.feedback_summary || (result.feedback ? result.feedback.split('.')[0].trim() : 'Technique feedback');
  const feedbackText = result.feedback || '';

  return (
    <div className="feedback-container">
      <div className="feedback-header">
        <h2>Biomechanical Analysis Completed</h2>
        <p>Comparison completed against the coach's official reference.</p>
      </div>

      {tecnica && (
        <div className="tecnica-comparison-card glass-panel">
          <span className="tecnica-badge">EVALUATED TECHNIQUE</span>
          <h3>{tecnicaNombre}</h3>
          <p>
            <strong>Reference Pattern:</strong> {profesorNombre}
          </p>
        </div>
      )}

      <div className="feedback-grid-2x2">
        {/* 1. Top-Left: Instructor Reference Video */}
        <section className="glass-panel feedback-card">
          <div className="card-header">
            <span className="card-label">COACH REFERENCE VIDEO</span>
            <h3>{profesorNombre}</h3>
          </div>
          <div className="media-wrapper">
            {videoUrl && !videoError ? (
              <video
                src={videoUrl}
                controls
                playsInline
                preload="metadata"
                onError={() => setVideoError(true)}
              />
            ) : (
              <div className="media-placeholder" role="status">
                The reference video is not available for playback.
              </div>
            )}
          </div>
        </section>

        {/* 2. Top-Right: Student Video with Jump to Error & Critical Frame */}
        <section className="glass-panel feedback-card">
          <div className="card-header">
            <span className="card-label">STUDENT VIDEO</span>
            <h3>Biomechanic Execution</h3>
          </div>
          <div className="media-wrapper">
            {videoAlumnoUrl && !videoAlumnoError ? (
              <video
                ref={videoRef}
                src={videoAlumnoUrl}
                controls
                playsInline
                preload="metadata"
                onError={() => setVideoAlumnoError(true)}
              />
            ) : frameErrorUrl ? (
              <img src={frameErrorUrl} alt="Analyzed student critical frame" />
            ) : (
              <div className="media-placeholder" role="status">
                The analyzed student video is not available.
              </div>
            )}
          </div>
          {timestampError > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.6rem', padding: '0.5rem 0.75rem', background: 'rgba(0, 0, 0, 0.4)', borderRadius: '6px', flexWrap: 'wrap', gap: '0.5rem' }}>
              <span style={{ color: '#ffd43b', fontSize: '0.85rem', fontWeight: '500' }}>
                ⚠️ Error detectado en el segundo {timestampError.toFixed(2)}s
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
                  borderRadius: '4px',
                  padding: '0.3rem 0.75rem',
                  fontSize: '0.8rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  transition: 'opacity 0.2s',
                }}
              >
                Jump to Error
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
                  Fotograma Crítico del Error Biomecánico ({timestampError.toFixed(2)}s)
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
                    alt="Fotograma con articulaciones en error resaltadas"
                    style={{ maxWidth: '100%', maxHeight: '440px', objectFit: 'contain' }}
                  />
                </div>
              ) : (
                <p style={{ color: '#94a3b8', textAlign: 'center' }}>Fotograma crítico no disponible.</p>
              )}

              <div style={{ padding: '0.75rem 1rem', background: 'rgba(239, 68, 68, 0.12)', borderLeft: '4px solid #ef4444', borderRadius: '4px' }}>
                <p style={{ margin: 0, color: '#ef4444', fontWeight: 'bold', fontSize: '0.95rem' }}>
                  Articulaciones afectadas: {(result.nombres_articulaciones_criticas && result.nombres_articulaciones_criticas.length > 0) ? result.nombres_articulaciones_criticas.join(', ') : 'No especificadas'}
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
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 3. Bottom-Left: AI Analysis Card */}
        <section className="glass-panel feedback-card ai-feedback-card">
          <div className="ai-card-header">
            <span className="card-label">AI TECHNICAL ANALYSIS</span>
            <div className={`similarity-badge ${isPassing ? 'badge-excellent' : similitud >= 70 ? 'badge-good' : 'badge-needs-work'}`}>
              {Math.round(similitud)}% Match
            </div>
          </div>
          <div className="ai-card-body">
            {isPassing ? (
              <div className="pass-status">
                <svg className="check-icon" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                <p className="pass-text">Great job! Technique executed correctly.</p>
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

        {/* 4. Bottom-Right: YouTube Recommendation Card */}
        <section className="glass-panel feedback-card youtube-card">
          <div className="card-header">
            <span className="card-label">RECOMMENDED PRACTICE</span>
            <h3>Practice Recommendation</h3>
          </div>
          <div className="youtube-card-body">
            <div className="youtube-icon-wrap">
              <svg width="44" height="44" viewBox="0 0 24 24" fill="#ef4444">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
              </svg>
            </div>
            <p className="youtube-desc">Watch tutorials for this technique on YouTube to reinforce proper biomechanics and positioning.</p>
            <a
              href={practiceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-youtube"
            >
              Watch Tutorials on YouTube
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                <polyline points="15 3 21 3 21 9"></polyline>
                <line x1="10" y1="14" x2="21" y2="3"></line>
              </svg>
            </a>
          </div>
        </section>
      </div>

      <div className="feedback-actions">
        <button className="btn-primary reset-btn" onClick={onReset}>
          Analyze Another Technique
        </button>
      </div>
    </div>
  );
}
