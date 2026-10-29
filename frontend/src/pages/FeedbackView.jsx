import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './FeedbackView.css';

const API_BASE = 'http://localhost:8000';

export default function FeedbackView({ user, result, tecnica, onReset }) {
  const [videoError, setVideoError] = useState(false);
  if (!result) return null;

  const similitud = typeof result.similitud === 'number' ? result.similitud : 0;
  const isPassing = similitud >= 85;

  const videoUrl = result.video_referencia_url
    ? `${API_BASE}${result.video_referencia_url}`
    : null;
  const frameErrorUrl = result.frame_error_url
    ? `${API_BASE}${result.frame_error_url}`
    : null;

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

        {/* 2. Top-Right: Student Critical Frame */}
        <section className="glass-panel feedback-card">
          <div className="card-header">
            <span className="card-label">STUDENT CRITICAL FRAME</span>
            <h3>Biomechanic Error</h3>
          </div>
          <div className="media-wrapper">
            {frameErrorUrl ? (
              <img src={frameErrorUrl} alt="Analyzed student critical frame" />
            ) : (
              <div className="media-placeholder" role="status">
                The analyzed critical frame is not available.
              </div>
            )}
          </div>
        </section>

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
