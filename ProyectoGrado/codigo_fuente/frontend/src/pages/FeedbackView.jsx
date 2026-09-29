import './FeedbackView.css';
import { useTranslation } from '../i18n/translations';

export default function FeedbackView({ user, result, tecnica, onReset }) {
  if (!result) return null;

  const { t } = useTranslation(user?.idioma_preferido);

  const isExcellent = result.similitud >= 90;
  const isGood = result.similitud >= 75 && result.similitud < 90;
  
  let scoreClass = 'score-needs-work';
  if (isExcellent) scoreClass = 'score-excellent';
  else if (isGood) scoreClass = 'score-good';

  const isPt = user?.idioma_preferido === 'pt';

  // URL absoluta del video (el backend devuelve /static/videos/xxx.mp4)
  const API_BASE = "http://localhost:8000";
  const videoUrl = result.video_referencia_url
    ? `${API_BASE}${result.video_referencia_url}`
    : null;

  return (
    <div className="feedback-container">
      <div className="feedback-header">
        <h2>{t.feedbackTitle}</h2>
        <p>{isPt ? "Comparação concluída com o padrão oficial do professor." : "Comparación completada contra el patrón oficial del profesor."}</p>
      </div>

      {tecnica && (
        <div className="tecnica-comparison-card glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', borderRadius: '12px', borderLeft: '4px solid var(--brand-red)' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)', letterSpacing: '1px' }}>
            {t.tecnicaEvaluada}
          </span>
          <h3 style={{ margin: '0.25rem 0', fontSize: '1.25rem' }}>{tecnica.nombre}</h3>
          <p style={{ margin: 0, fontSize: '0.875rem', opacity: 0.8 }}>
            <strong>{t.patronRefLabel}</strong> {tecnica.profesorRef}
          </p>
        </div>
      )}

      {/* ── Video de Referencia del Profesor ────────────────── */}
      {videoUrl && (
        <div
          className="glass-panel"
          style={{
            padding: '1.25rem 1.5rem',
            borderRadius: '12px',
            borderLeft: '4px solid var(--brand-red)',
            marginBottom: '1.5rem',
          }}
        >
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 'bold',
              color: 'var(--brand-red)',
              letterSpacing: '1px',
            }}
          >
            {isPt ? 'VÍDEO DE REFERÊNCIA DO PROFESSOR' : 'VIDEO DE REFERENCIA DEL PROFESOR'}
          </span>

          {result.video_referencia_profesor_nombre && (
            <p style={{ margin: '0.35rem 0 0.75rem 0', fontSize: '0.9rem', opacity: 0.85 }}>
              <strong>{isPt ? 'Demonstração de' : 'Demostración de'}:</strong>{' '}
              {result.video_referencia_profesor_nombre}
            </p>
          )}

          <video
            src={videoUrl}
            controls
            playsInline
            preload="metadata"
            style={{
              width: '100%',
              maxHeight: '400px',
              borderRadius: '8px',
              backgroundColor: '#000',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              display: 'block',
            }}
          />

          <p
            style={{
              margin: '0.75rem 0 0 0',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              lineHeight: 1.5,
            }}
          >
            {isPt
              ? 'Compare sua execução com o padrão do professor para entender as diferenças biomecânicas apontadas pela IA abaixo.'
              : 'Compara tu ejecución contra el patrón del profesor para entender las diferencias biomecánicas que la IA señala abajo.'}
          </p>
        </div>
      )}

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
          <h3>{t.similarityLabel}</h3>
          <p>
            {isExcellent && (isPt ? "Execução excelente! Sua técnica é quase idêntica à referência do professor." : "¡Excelente ejecución! Tu técnica es casi idéntica a la referencia del profesor.")}
            {isGood && (isPt ? "Bom trabalho. Há detalhes menores a ajustar, mas a base é sólida." : "Buen trabajo. Hay detalles menores que ajustar, pero la base es sólida.")}
            {!isExcellent && !isGood && (isPt ? "Você precisa ajustar a biomecânica. Verifique os comentários da IA." : "Necesitas ajustar la biomecánica. Revisa los comentarios de la IA.")}
          </p>
        </div>
      </div>

      <details className="feedback-details glass-panel" open>
        <summary>
          <span className="summary-title">{isPt ? "Feedback da Gemini AI" : "Retroalimentación de Gemini AI"}</span>
          <svg className="chevron" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </summary>
        <div className="feedback-content">
          {result.feedback.split('\n').map((paragraph, idx) => (
            <p key={idx}>{paragraph}</p>
          ))}
        </div>
      </details>

      <button className="btn-primary reset-btn" onClick={onReset}>
        {t.btnReset}
      </button>
    </div>
  );
}
