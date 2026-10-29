import { useEffect, useState } from 'react';

const API_BASE = 'http://localhost:8000/api/v1';

export default function GlobalKnowledgeModal({ user, onClose }) {
  const [file, setFile] = useState(null);
  const [sourceName, setSourceName] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(null);
  const [hasError, setHasError] = useState(false);

  const loadSources = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/conocimiento/fuentes/globales`, {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      if (response.status === 404) throw new Error('Local API does not recognize this function. Restart backend and try again.');
      if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        throw new Error(result.detail || 'Could not load sources.');
      }
      setSources(await response.json());
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSources(); }, []);

  const handleUpload = async (event) => {
    event.preventDefault();
    if (!file) return;
    setSaving(true);
    setMessage('');
    setHasError(false);
    setProgress(0);
    const data = new FormData();
    data.append('archivo', file);
    data.append('alcance', 'global');
    data.append('fuente_nombre', sourceName.trim() || file.name);
    try {
      let { response, result } = await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE}/conocimiento/fuentes/archivo`);
        xhr.setRequestHeader('Authorization', `Bearer ${user.token}`);
        xhr.upload.onprogress = (uploadEvent) => {
          if (uploadEvent.lengthComputable) {
            const uploadProgress = Math.round((uploadEvent.loaded / uploadEvent.total) * 10);
            setProgress(uploadProgress);
            setMessage(`Uploading file: ${Math.round((uploadEvent.loaded / uploadEvent.total) * 100)}%`);
          }
        };
        xhr.onerror = () => reject(new Error('Could not connect to backend.'));
        xhr.onload = () => {
          let body = {};
          try { body = JSON.parse(xhr.responseText || '{}'); } catch { /* non-JSON response */ }
          resolve({ response: { ok: xhr.status >= 200 && xhr.status < 300, status: xhr.status }, result: body });
        };
        xhr.send(data);
      });
      if (!response.ok) {
        const detail = response.status === 404
          ? 'Local API route not found. Restart backend and try again.'
          : (result.detail || 'Could not save source.');
        throw new Error(detail);
      }
      if (result.status === 'procesando' && result.job_id) {
        setFile(null);
        setSourceName('');
        setProgress(10);
        setMessage('File received. Preparing processing...');
        let job;
        do {
          await new Promise((resolve) => setTimeout(resolve, 2000));
          const statusResponse = await fetch(`${API_BASE}/conocimiento/fuentes/procesamiento/${result.job_id}`, {
            headers: { Authorization: `Bearer ${user.token}` },
          });
          job = await statusResponse.json().catch(() => ({}));
          if (!statusResponse.ok) throw new Error(job.detail || 'Lost connection to upload status.');
          if (job.estado === 'procesando') {
            setProgress(Math.max(10, job.avance || 10));
            setMessage(`${job.etapa || 'Indexing manual'}${job.paginas_procesadas ? ` · ${job.paginas_procesadas} of ${job.total_paginas} pages` : ''}`);
          }
        } while (job.estado === 'procesando');
        if (job.estado !== 'completado') throw new Error(job.error || 'Could not index manual.');
        result = job;
      }
      setProgress(100);
      const visualCount = result.paginas_imagen_indexadas || result.imagenes_indexadas || 0;
      setMessage(`Manual indexed: ${result.chunks_procesados} chunks${visualCount ? ` and ${visualCount} visual elements` : ''}.`);
      setFile(null);
      setSourceName('');
      await loadSources();
    } catch (error) {
      setHasError(true);
      setMessage(error.message);
    } finally {
      setSaving(false);
    }
  };

  const groupedSources = Object.values(sources.reduce((groups, item) => {
    const key = item.fuente_url || item.fuente_nombre || item.id;
    if (!groups[key]) groups[key] = { ...item, chunks: 0 };
    groups[key].chunks += 1;
    return groups;
  }, {}));

  return (
    <div className="modal-overlay" role="presentation" onClick={onClose}>
      <section className="modal-content glass-panel" role="dialog" aria-modal="true" aria-labelledby="global-knowledge-title" onClick={(event) => event.stopPropagation()} style={{ width: 'min(720px, 96vw)', maxHeight: '90vh', overflowY: 'auto' }}>
        <h2 id="global-knowledge-title" style={{ color: 'var(--brand-red)', marginTop: 0 }}>Global Knowledge Sources</h2>
        <form onSubmit={handleUpload} style={{ display: 'grid', gap: '.75rem', padding: '1rem', borderRadius: 10, background: 'rgba(255,255,255,.04)' }}>
          <label htmlFor="global-source-name">Source Name</label>
          <input id="global-source-name" value={sourceName} onChange={(event) => setSourceName(event.target.value)} placeholder="e.g. Jiu-Jitsu University Fundamentals Manual" />
          <label htmlFor="global-source-file">Manual, text or image file</label>
          <input id="global-source-file" type="file" accept=".pdf,.docx,.txt,.jpg,.jpeg,.png,.webp,.bmp,.tif,.tiff,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,image/*" onChange={(event) => setFile(event.target.files?.[0] || null)} required />
          <button className="btn-primary" type="submit" disabled={!file || saving}>{saving ? 'Saving...' : 'Save Global Source'}</button>
        </form>
        {saving && progress !== null && (
          <div aria-live="polite" style={{ display: 'grid', gap: '.35rem' }}>
            <progress aria-label="Manual upload and indexing progress" max="100" value={progress} style={{ width: '100%', height: 14, accentColor: 'var(--brand-red)' }} />
            <small>{progress}%</small>
          </div>
        )}
        {message && <p role="status" style={{ color: hasError ? '#ff8787' : '#69db7c' }}>{message}</p>}
        <h3>Added Sources</h3>
        {loading ? <p>Loading...</p> : groupedSources.length === 0 ? <p>No global sources added yet.</p> : (
          <ul style={{ paddingLeft: '1.2rem' }}>
            {groupedSources.map((source) => (
              <li key={source.fuente_url || source.id} style={{ marginBottom: '.75rem' }}>
                <strong>{source.fuente_nombre || 'Unnamed source'}</strong>
                <span style={{ color: 'var(--text-secondary)' }}> · {source.chunks} chunks</span>
              </li>
            ))}
          </ul>
        )}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button type="button" className="btn-secondary" onClick={onClose}>Close</button>
        </div>
      </section>
    </div>
  );
}
