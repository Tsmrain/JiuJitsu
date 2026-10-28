import { useEffect, useState } from 'react';

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
          throw new Error(body.detail || 'No se pudo cargar tu progreso.');
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
      <h2 style={{ color: 'var(--brand-red)', marginTop: 0 }}>Mi progreso</h2>
      <p style={{ color: 'var(--text-secondary)' }}>Revisa tus correcciones y compara tu ejecución con la demostración del profesor.</p>
      {loading && <p>Cargando tus evaluaciones…</p>}
      {error && <p role="alert" style={{ color: '#ff8787' }}>{error}</p>}
      {!loading && !error && evaluaciones.length === 0 && <p>Aún no tienes evaluaciones. Analiza un video para comenzar tu historial.</p>}
      <div style={{ display: 'grid', gap: '1rem' }}>
        {evaluaciones.map((item) => {
          const score = Number(item.porcentaje_similitud || 0);
          const videoAlumno = item.url_video_alumno ? `${API_BASE}${item.url_video_alumno}` : null;
          const videoProfesor = item.video_referencia_url ? `${API_BASE}${item.video_referencia_url}` : null;
          return (
            <article key={item.id} className="glass-panel" style={{ padding: '1rem', borderRadius: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                <div>
                  <h3 style={{ margin: 0 }}>{item.tecnica_nombre}</h3>
                  <small style={{ color: 'var(--text-secondary)' }}>
                    {item.fecha_evaluacion ? new Date(item.fecha_evaluacion).toLocaleString('es-ES') : 'Fecha no disponible'}
                  </small>
                </div>
                <strong style={{ color: score >= 85 ? '#69db7c' : score >= 70 ? '#ffd43b' : '#ff8787', fontSize: '1.25rem' }}>
                  {Math.round(score)}% de similitud
                </strong>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                <div>
                  <h4>Mi video</h4>
                  {videoAlumno ? <video src={videoAlumno} controls playsInline preload="metadata" style={{ width: '100%', maxHeight: 300, background: '#08090b', borderRadius: 8 }} /> : <p>Video de alumno no disponible.</p>}
                </div>
                <div>
                  <h4>Demostración del profesor{item.video_referencia_profesor_nombre ? ` · ${item.video_referencia_profesor_nombre}` : ''}</h4>
                  {videoProfesor ? <video src={videoProfesor} controls playsInline preload="metadata" style={{ width: '100%', maxHeight: 300, background: '#08090b', borderRadius: 8 }} /> : <p>Video de referencia no disponible.</p>}
                </div>
              </div>
              <div style={{ marginTop: '1rem', lineHeight: 1.5 }}>
                <strong>Corrección</strong>
                <p style={{ marginBottom: 0 }}>{item.feedback_gemini_es || item.feedback_gemini_pt || 'Aún no hay corrección disponible.'}</p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
