import { useState } from 'react';
import './FeedbackView.css';

const API_BASE = 'http://localhost:8000';

export default function FeedbackView({ user, result, tecnica, onReset }) {
  const [videoError, setVideoError] = useState(false);
  if (!result) return null;

  const isExcellent = result.similitud >= 90;
  const isGood = result.similitud >= 75 && result.similitud < 90;
  
  let scoreClass = 'score-needs-work';
  if (isExcellent) scoreClass = 'score-excellent';
  else if (isGood) scoreClass = 'score-good';

  // Absolute video URL (backend returns /static/videos/xxx.mp4)
  const videoUrl = result.video_referencia_url
    ? `${API_BASE}${result.video_referencia_url}`
    : null;
  const frameErrorUrl = result.frame_error_url
    ? `${API_BASE}${result.frame_error_url}`
    : null;

  return (
    <div className="feedback-container">
      <div className="feedback-header">
        <h2>Biomechanical Analysis Completed</h2>
        <p>Comparison completed against the instructor's official reference.</p>
      </div>

      {tecnica && (
        <div className="tecnica-comparison-card glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', borderRadius: '12px', borderLeft: '4px solid var(--brand-red)' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)', letterSpacing: '1px' }}>
            EVALUATED TECHNIQUE
          </span>
          <h3 style={{ margin: '0.25rem 0', fontSize: '1.25rem' }}>{tecnica.nombre}</h3>
          <p style={{ margin: 0, fontSize: '0.875rem', opacity: 0.8 }}>
            <strong>Reference Pattern:</strong> {tecnica.profesorRef}
          </p>
        </div>
      )}

      <div className="comparison-media">
        <section className="glass-panel comparison-media-card">
          <h3>INSTRUCTOR REFERENCE VIDEO</h3>
          <p>
            {result.video_referencia_profesor_nombre || tecnica?.profesorRef || 'Selected instructor'}
            {result.video_referencia_nombre ? ` · ${result.video_referencia_nombre}` : ''}
          </p>
          {videoUrl && !videoError ? (
            <video src={videoUrl} controls playsInline preload="metadata" onError={() => setVideoError(true)} />
          ) : (
            <p role="status">The reference video is not available for playback.</p>
          )}
        </section>
        <section className="glass-panel comparison-media-card critical-frame-card">
          <h3>STUDENT CRITICAL FRAME</h3>
          {frameErrorUrl ? (
            <img src={frameErrorUrl} alt="Analyzed student frame" />
          ) : (
            <p role="status">The analyzed frame is not available.</p>
          )}
        </section>
      </div>

      <div className="score-card glass-panel">
        <div className="score-circle">
          <svg viewBox="0 0 36 36" className="circular-chart">
            <path className="circle-bg"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path className={`circle ${scoreClass}`}
              strokeDasharray={`${result.similitud}, 100`}
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <text x="18" y="20.35" className="percentage">{Math.round(result.similitud)}%</text>
          </svg>
        </div>
        <div className="score-info">
          <h3>Biomechanical Similarity</h3>
          <p>
            {isExcellent && "Excellent execution! Your technique closely matches the instructor reference."}
            {isGood && "Good job. Minor details need adjustment, but your foundation is solid."}
            {!isExcellent && !isGood && "You need to adjust your biomechanics. Review the AI technical feedback below."}
          </p>
        </div>
      </div>

      <details className="feedback-details glass-panel" open>
        <summary>
          <span className="summary-title">Technical Correction</span>
          <svg className="chevron" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </summary>
        <div className="feedback-content">
          <p>{(result.feedback || '').replace(/[#*_`~]/g, '').replace(/^\s*[-+•]\s+/gm, '').trim()}</p>
        </div>
      </details>

      <button className="btn-primary reset-btn" onClick={onReset}>
        Analyze Another Video
      </button>
    </div>
  );
}
