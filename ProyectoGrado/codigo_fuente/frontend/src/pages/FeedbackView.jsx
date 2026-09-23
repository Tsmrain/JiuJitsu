import './FeedbackView.css';

export default function FeedbackView({ result, tecnica, onReset }) {
  if (!result) return null;

  const isExcellent = result.similitud >= 90;
  const isGood = result.similitud >= 75 && result.similitud < 90;
  
  let scoreClass = 'score-needs-work';
  if (isExcellent) scoreClass = 'score-excellent';
  else if (isGood) scoreClass = 'score-good';

  return (
    <div className="feedback-container">
      <div className="feedback-header">
        <h2>Resultados del Análisis Biomecánico</h2>
        <p>Comparación completada contra el patrón oficial del profesor.</p>
      </div>

      {tecnica && (
        <div className="tecnica-comparison-card glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', borderRadius: '12px', borderLeft: '4px solid var(--brand-red)' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)', letterSpacing: '1px' }}>
            TÉCNICA EVALUADA
          </span>
          <h3 style={{ margin: '0.25rem 0', fontSize: '1.25rem' }}>{tecnica.nombre}</h3>
          <p style={{ margin: 0, fontSize: '0.875rem', opacity: 0.8 }}>
            <strong>Patrón de Referencia:</strong> {tecnica.profesorRef} ({tecnica.categoria})
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
          <h3>Similitud con el Patrón</h3>
          <p>
            {isExcellent && "¡Excelente ejecución! Tu técnica es casi idéntica a la referencia del profesor."}
            {isGood && "Buen trabajo. Hay detalles menores que ajustar, pero la base es sólida."}
            {!isExcellent && !isGood && "Necesitas ajustar la biomecánica. Revisa los comentarios de la IA."}
          </p>
        </div>
      </div>

      <details className="feedback-details glass-panel" open>
        <summary>
          <span className="summary-title">Retroalimentación de Gemini AI</span>
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
        Analizar otra técnica
      </button>
    </div>
  );
}
