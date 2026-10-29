import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';

const API_BASE = 'http://localhost:8000';

export default function StudentProgress({ user }) {
  const [evaluaciones, setEvaluaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    fetch(`${API_BASE}/api/v1/auth/alumnos/${user.user_id}/evaluaciones`, {
      headers: { Authorization: `Bearer ${user.token}` },
    })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || 'Could not load your progress.');
        }
        return response.json();
      })
      .then((data) => { if (active) setEvaluaciones(data); })
      .catch((cause) => { if (active) setError(cause.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [user.user_id, user.token]);

  return (
    <section style={{ width: 'min(1100px, 100%)', margin: '2rem auto', padding: '1.5rem', color: 'white' }}>
      <h2 style={{ color: 'var(--brand-red)', marginTop: 0 }}>My Progress</h2>
      <p style={{ color: 'var(--text-secondary)' }}>Review your technical corrections and compare your movement with the coach's demonstration.</p>
      {loading && <p>Loading your evaluations...</p>}
      {error && <p role="alert" style={{ color: '#ff8787' }}>{error}</p>}
      {!loading && !error && evaluaciones.length === 0 && <p>You have no evaluations yet. Upload and analyze a video to start your progress history.</p>}
      <div style={{ display: 'grid', gap: '1.25rem' }}>
        {evaluaciones.map((item) => {
          const score = Number(item.porcentaje_similitud || 0);
          const videoAlumno = item.url_video_alumno ? `${API_BASE}${item.url_video_alumno}` : null;
          const videoProfesor = item.video_referencia_url ? `${API_BASE}${item.video_referencia_url}` : null;
          const coachNombre = (item.video_referencia_profesor_nombre || 'Coach').replace(/Mestre/gi, 'Coach');

          return (
            <article key={item.id} className="glass-panel" style={{ padding: '1.25rem', borderRadius: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{item.tecnica_nombre}</h3>
                  <small style={{ color: 'var(--text-secondary)' }}>
                    {item.fecha_evaluacion ? new Date(item.fecha_evaluacion).toLocaleString('en-US') : 'Date unavailable'}
                  </small>
                </div>
                <strong style={{ color: score >= 85 ? '#69db7c' : score >= 70 ? '#ffd43b' : '#ff8787', fontSize: '1.25rem' }}>
                  {Math.round(score)}% similarity
                </strong>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>My Video</h4>
                  {videoAlumno ? (
                    <video src={videoAlumno} controls playsInline preload="metadata" style={{ width: '100%', height: 260, objectFit: 'contain', background: '#08090b', borderRadius: 8 }} />
                  ) : (
                    <p>Student video not available.</p>
                  )}
                </div>
                <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
                    Coach Demonstration · {coachNombre}
                  </h4>
                  {videoProfesor ? (
                    <video src={videoProfesor} controls playsInline preload="metadata" style={{ width: '100%', height: 260, objectFit: 'contain', background: '#08090b', borderRadius: 8 }} />
                  ) : (
                    <p>Reference video not available.</p>
                  )}
                </div>
              </div>
              <div style={{ marginTop: '1rem', lineHeight: 1.5, borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '0.75rem' }}>
                {item.feedback_summary && (
                  <p style={{ margin: '0 0 0.4rem 0', color: '#ffffff', fontSize: '1rem' }}>
                    <strong>{item.feedback_summary}</strong>
                  </p>
                )}
                <div style={{ color: '#d1d5db', fontSize: '0.95rem' }}>
                  <ReactMarkdown>{item.feedback_gemini_es || item.feedback_gemini_pt || 'No correction available yet.'}</ReactMarkdown>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
