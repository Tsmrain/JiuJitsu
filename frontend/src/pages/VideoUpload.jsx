import { useState, useEffect, useRef } from 'react';
import './VideoUpload.css';
import { useTranslation } from '../i18n/translations';
import SelectorPersonaVideo from '../components/SelectorPersonaVideo';
import { incluirEstadoPatrones } from '../api/tecnicas';

export default function VideoUpload({ user, onUploadStart }) {
  const { t } = useTranslation(user?.idioma_preferido);

  const [profesores, setProfesores] = useState([]);
  const [selectedProfesor, setSelectedProfesor] = useState(null);
  const [tecnicas, setTecnicas] = useState([]);
  const [selectedTecnica, setSelectedTecnica] = useState(null);
  const [loadingProfesores, setLoadingProfesores] = useState(true);
  const [loadingTecnicas, setLoadingTecnicas] = useState(false);

  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);

  // 1. Cargar profesores de la sucursal del alumno
  const fetchProfesores = async () => {
    setLoadingProfesores(true);
    try {
      const sucursalQuery = user?.sucursal_id ? `?sucursal_id=${user.sucursal_id}` : '';
      const res = await fetch(`http://localhost:8000/api/v1/profesores${sucursalQuery}`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          setProfesores(data);
          setSelectedProfesor(data[0]);
        } else {
          // Fallback a todos los profesores si no hay en la sucursal específica
          const resAll = await fetch(`http://localhost:8000/api/v1/profesores`);
          if (resAll.ok) {
            const dataAll = await resAll.json();
            setProfesores(dataAll);
            if (dataAll.length > 0) setSelectedProfesor(dataAll[0]);
          }
        }
      }
    } catch (err) {
      console.error("Error cargando profesores:", err);
    } finally {
      setLoadingProfesores(false);
    }
  };

  const fetchTecnicasDelProfesor = async (profesorId) => {
    setLoadingTecnicas(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/tecnicas?profesor_id=${profesorId}`, {
        headers: { Authorization: `Bearer ${user?.token}` }
      });
      if (res.ok) {
        const data = await incluirEstadoPatrones(await res.json(), user?.token);
        setTecnicas(data);
        if (data && data.length > 0) {
          // Priorizar seleccionar una técnica que tenga video de referencia
          const conVideo = data.find(t => t.tiene_patron || t.tiene_video);
          setSelectedTecnica(conVideo || data[0]);
        } else {
          setSelectedTecnica(null);
        }
      }
    } catch (err) {
      console.error("Error cargando técnicas del profesor:", err);
    } finally {
      setLoadingTecnicas(false);
    }
  };

  useEffect(() => {
    fetchProfesores();
  }, [user?.sucursal_id]);

  useEffect(() => {
    if (selectedProfesor?.user_id) {
      fetchTecnicasDelProfesor(selectedProfesor.user_id);
    }
  }, [selectedProfesor]);

  const handleProfesorChange = (e) => {
    const profId = e.target.value;
    const found = profesores.find(p => p.user_id === profId);
    if (found) setSelectedProfesor(found);
  };

  const handleTecnicaChange = (e) => {
    const techId = e.target.value;
    const found = tecnicas.find(t => t.id === techId);
    if (found) setSelectedTecnica(found);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const [extractingPrimerFrame, setExtractingPrimerFrame] = useState(false);
  const [sessionData, setSessionData] = useState(null);
  const [selectedPersonaIdx, setSelectedPersonaIdx] = useState(null);
  const [userRejectedPersona, setUserRejectedPersona] = useState(false);
  const [confirmingSelection, setConfirmingSelection] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [comparisonVideoUrl, setComparisonVideoUrl] = useState(null);
  const [comparisonError, setComparisonError] = useState(null);
  const [selectedAlignment, setSelectedAlignment] = useState(null);
  const comparisonPlayerRef = useRef(null);

  const selectAlignmentFrame = (pair) => {
    setSelectedAlignment(pair);
    if (comparisonPlayerRef.current && Number.isFinite(pair.video_idx)) {
      comparisonPlayerRef.current.currentTime = pair.video_idx / 24;
    }
  };

  const handleCompareVideos = async () => {
    if (!file || !selectedTecnica?.video_url || selectedPersonaIdx === null) return;
    setComparisonLoading(true);
    setComparisonResult(null);
    if (comparisonVideoUrl) URL.revokeObjectURL(comparisonVideoUrl);
    setComparisonVideoUrl(null);
    setComparisonError(null);
    try {
      const referenceUrl = new URL(selectedTecnica.video_url, 'http://localhost:8000');
      const teacherResponse = await fetch(referenceUrl);
      if (!teacherResponse.ok) throw new Error('No se pudo cargar el video de referencia del profesor.');
      const teacherBlob = await teacherResponse.blob();
      const teacherFile = new File([teacherBlob], `referencia_${selectedTecnica.nombre || 'tecnica'}.mp4`, { type: teacherBlob.type || 'video/mp4' });
      const form = new FormData();
      form.append('video_alumno', file);
      form.append('video_maestro', teacherFile);
      form.append('tecnica_id', selectedTecnica.id);
      form.append('persona_idx_alumno', String(selectedPersonaIdx));
      form.append('idioma', user?.idioma_preferido || 'en');
      form.append('video_maestro_nombre', `${selectedProfesor?.nombre_completo || 'Profesor'} — ${selectedTecnica.nombre || 'Técnica'}`);
      const headers = { Authorization: `Bearer ${user?.token}` };
      const start = await fetch('http://localhost:8000/api/v1/comparaciones/video-a-video', { method: 'POST', headers, body: form });
      const startData = await start.json().catch(() => ({}));
      if (!start.ok) throw new Error(startData.detail || 'No se pudo iniciar la comparación.');
      let result;
      for (let attempt = 0; attempt < 180; attempt += 1) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        const response = await fetch(`http://localhost:8000/api/v1/comparaciones/${startData.comparacion_id}`, { headers });
        result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(result.detail || 'No se pudo consultar la comparación.');
        if (result.estado === 'completado') break;
        if (result.estado === 'error_procesamiento') throw new Error(result.error_message || 'Falló el análisis de los videos.');
      }
      if (result?.estado !== 'completado') throw new Error('La comparación sigue procesándose. Intenta consultar el reporte más tarde.');
      if (result.video_url) {
        const videoResponse = await fetch(`http://localhost:8000${result.video_url}`, { headers });
        if (!videoResponse.ok) throw new Error('No se pudo cargar el video comparativo.');
        setComparisonVideoUrl(URL.createObjectURL(await videoResponse.blob()));
      }
      setComparisonResult(result);
    } catch (err) {
      setComparisonError(err.message || 'Error al comparar los videos.');
    } finally {
      setComparisonLoading(false);
    }
  };

  const handleFile = async (selectedFile) => {
    if (!selectedFile.type.startsWith('video/')) {
      alert(t.alertValidVideo);
      return;
    }
    setFile(selectedFile);
    setSessionData(null);
    setSelectedPersonaIdx(null);
    setUserRejectedPersona(false);
    setErrorMessage(null);
    setExtractingPrimerFrame(true);

    const formData = new FormData();
    formData.append("video", selectedFile);

    try {
      const res = await fetch("http://localhost:8000/api/v1/evaluaciones/primer-frame", {
        method: "POST",
        headers: { "Authorization": `Bearer ${user?.token}` },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Error detectando personas en el fotograma inicial.");
      }

      const data = await res.json();
      setSessionData(data);
      if (data.personas && data.personas.length === 1) {
        setSelectedPersonaIdx(data.personas[0].idx);
      } else {
        setSelectedPersonaIdx(null);
      }
    } catch (err) {
      console.error("Error al obtener primer frame:", err);
      setErrorMessage(err.message || "Error al procesar el fotograma inicial del video.");
    } finally {
      setExtractingPrimerFrame(false);
    }
  };

  const handleResetVideo = () => {
    setFile(null);
    setSessionData(null);
    setSelectedPersonaIdx(null);
    setUserRejectedPersona(false);
    setErrorMessage(null);
    setExtractingPrimerFrame(false);
  };

  const handleSubmit = async () => {
    if (!file || !selectedTecnica) return;

    if (!sessionData || selectedPersonaIdx === null) {
      alert(t.alertSelectPerson || "Por favor selecciona cuál persona eres en el video antes de continuar.");
      return;
    }

    setConfirmingSelection(true);
    setErrorMessage(null);

    try {
      // 1. Confirmar explícitamente la selección en la sesión de backend
      const res = await fetch(`http://localhost:8000/api/v1/evaluaciones/${sessionData.session_id}/seleccionar-persona`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${user?.token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ persona_idx: selectedPersonaIdx })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Error al confirmar selección de persona.");
      }

      // 2. Disparar análisis
      onUploadStart({
        sessionId: sessionData.session_id,
        personaIdx: selectedPersonaIdx,
        tecnica: {
          ...selectedTecnica,
          profesorRef: selectedProfesor ? selectedProfesor.nombre_completo : "Mestre Oficial",
          profesor_id: selectedProfesor?.user_id
        },
        file
      });
    } catch (err) {
      console.error("Error confirmando persona:", err);
      setErrorMessage(err.message || "Error al confirmar la persona seleccionada.");
    } finally {
      setConfirmingSelection(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h2>{t.uploadTitle}</h2>
        <p>{t.uploadSubtitle}</p>
      </div>

      {/* Paso 1: Selección de Profesor de la Sucursal */}
      <div className="tecnica-selector-card glass-panel" style={{ padding: '1.25rem 1.5rem', marginBottom: '1rem', borderRadius: '12px' }}>
        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--brand-red)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {t.selectProfesorLabel}
        </label>

        {loadingProfesores ? (
          <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>{t.noProfessorsFound}</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
            {/* Grid de Tarjetas de Profesores con Foto Arriba y Nombre Abajo */}
            <div className="profesores-container" style={{ display: 'flex', gap: '1.25rem', flexWrap: 'wrap', justifyContent: 'center', width: '100%' }}>
              {profesores.map(p => {
                const isSelected = selectedProfesor?.user_id === p.user_id;
                return (
                  <div
                    key={p.user_id}
                    onClick={() => setSelectedProfesor(p)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      padding: '1.25rem 1.5rem',
                      borderRadius: '16px',
                      background: isSelected ? 'rgba(208, 17, 24, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                      border: isSelected ? '2px solid var(--brand-red)' : '1px solid rgba(255, 255, 255, 0.1)',
                      boxShadow: isSelected ? '0 0 20px rgba(208, 17, 24, 0.35)' : 'none',
                      cursor: 'pointer',
                      transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                      minWidth: '160px',
                      textAlign: 'center',
                      transform: isSelected ? 'scale(1.02)' : 'scale(1)'
                    }}
                  >
                    {/* Foto del Perfil del Profesor */}
                    <div style={{
                      width: '90px',
                      height: '90px',
                      borderRadius: '50%',
                      border: isSelected ? '3px solid var(--brand-red)' : '2px solid rgba(255, 255, 255, 0.2)',
                      boxShadow: isSelected ? '0 0 15px rgba(208, 17, 24, 0.5)' : 'none',
                      overflow: 'hidden',
                      background: 'linear-gradient(135deg, rgba(208,17,24,0.3) 0%, rgba(20,20,20,0.9) 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '2rem',
                      fontWeight: 'bold',
                      color: 'white',
                      marginBottom: '0.75rem'
                    }}>
                      {p.avatar_url ? (
                        <img
                          src={p.avatar_url}
                          alt={p.nombre_completo}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.style.display = 'none';
                          }}
                        />
                      ) : (
                        <span>{p.nombre_completo ? p.nombre_completo.charAt(0).toUpperCase() : 'P'}</span>
                      )}
                    </div>

                    {/* Nombre del Profesor debajo de la Foto */}
                    <span style={{
                      fontWeight: 'bold',
                      fontSize: '1rem',
                      color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                      marginTop: '0.25rem'
                    }}>
                      {p.nombre_completo}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)', marginTop: '0.2rem' }}>
                      {p.sucursal_nombre}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Select alternativo cuando hay varios profesores */}
            {profesores.length > 2 && (
              <select
                value={selectedProfesor?.user_id || ''}
                onChange={handleProfesorChange}
                style={{
                  width: '100%',
                  padding: '0.65rem 1rem',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: 'white',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  marginTop: '0.5rem'
                }}
              >
                {profesores.map(p => (
                  <option key={p.user_id} value={p.user_id} style={{ background: '#111', color: 'white' }}>
                    {p.nombre_completo} ({p.sucursal_nombre})
                  </option>
                ))}
              </select>
            )}
          </div>
        )}
      </div>

      {/* Paso 2: Selección de Técnica enseñada por el Profesor */}
      <div className="tecnica-selector-card glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', borderRadius: '12px' }}>
        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--brand-red)', marginBottom: '0.5rem' }}>
          {t.selectTecnicaLabelStep}
        </label>

        {loadingTecnicas ? <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>{t.loadingTecnicas}</p> : (
          <>
            {tecnicas.length === 0 ? (
              <p style={{ fontSize: '0.9rem', color: '#ff8787' }}>{t.noTecnicasFound}</p>
            ) : (
              <select
                value={selectedTecnica?.id || ''}
                onChange={handleTecnicaChange}
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: 'white',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  fontSize: '1rem',
                  cursor: 'pointer'
                }}
              >
                {tecnicas.map(tech => (
                  <option key={tech.id} value={tech.id} style={{ background: '#111', color: 'white' }}>
                    {tech.nombre}
                  </option>
                ))}
              </select>
            )}

            {selectedTecnica && (
              <div className="profesor-ref-info" style={{ marginTop: '0.85rem', fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                {selectedProfesor && (
                  <div style={{ width: '32px', height: '32px', borderRadius: '50%', border: '1.5 solid var(--brand-red)', overflow: 'hidden', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(208,17,24,0.3)' }}>
                    {selectedProfesor.avatar_url ? (
                      <img src={selectedProfesor.avatar_url} alt={selectedProfesor.nombre_completo} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                      <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'white' }}>{selectedProfesor.nombre_completo.charAt(0)}</span>
                    )}
                  </div>
                )}
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontWeight: 'bold', color: 'white' }}>{selectedProfesor ? selectedProfesor.nombre_completo : ''}</span>
                  <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.7)' }}>{selectedTecnica.nombre}</span>
                </div>
                <span style={{ marginLeft: 'auto', background: (selectedTecnica.tiene_patron || selectedTecnica.tiene_video) ? '#22c55e' : 'var(--brand-red)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 'bold', fontSize: '0.75rem', color: 'white' }}>
                  {(selectedTecnica.tiene_patron || selectedTecnica.tiene_video) ? t.hasVideoTag : t.noVideoTag}
                </span>
                </div>
                {selectedTecnica.mensaje_profesor && (
                  <div style={{ borderTop: '1px solid rgba(255,255,255,.1)', paddingTop: '.65rem', lineHeight: 1.5 }}>
                    <strong style={{ color: 'white' }}>Indicaciones del profesor</strong>
                    <p style={{ margin: '.3rem 0 0', color: 'rgba(255,255,255,.78)', whiteSpace: 'pre-wrap' }}>{selectedTecnica.mensaje_profesor}</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Paso 3: Carga del Video y Calibración Interactiva */}
      {!file ? (
        <div
          className={`drop-zone glass-panel ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            accept="video/*"
            onChange={handleChange}
            className="file-input"
          />
          <label htmlFor="file-upload" className="drop-label">
            <div className="upload-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
            </div>
            <span className="drop-text">{t.dropText} <strong>{t.dropClick}</strong></span>
            <span className="drop-hint">{t.dropHint}</span>
          </label>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ display: 'block', fontWeight: 'bold', fontSize: '0.95rem' }}>{file.name}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
            </div>
            <button type="button" className="btn-secondary" onClick={handleResetVideo} style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>
              {t.btnChange}
            </button>
          </div>

          {errorMessage && (
            <div style={{ background: 'rgba(208, 17, 24, 0.2)', border: '1px solid var(--brand-red)', padding: '0.75rem 1rem', borderRadius: '8px', color: '#ff8787', fontSize: '0.85rem' }}>
              {errorMessage}
            </div>
          )}

          {selectedTecnica?.video_url && selectedPersonaIdx !== null && (
            <button type="button" className="btn-secondary" onClick={handleCompareVideos} disabled={comparisonLoading}>
              {comparisonLoading ? 'Comparando videos…' : 'Comparar con el video del profesor'}
            </button>
          )}
          {comparisonError && <div role="alert" style={{ color: '#ff8787' }}>{comparisonError}</div>}
          {comparisonResult && (
            <section className="glass-panel" aria-live="polite" style={{ padding: '1rem', borderRadius: '10px' }}>
              <h3>Comparación con {selectedTecnica?.nombre}</h3>
              <p>Video del profesor: {comparisonResult.video_maestro_nombre} · Tu video: {comparisonResult.video_alumno_nombre}</p>
              <p>Similitud de movimiento: {comparisonResult.score_similitud}%</p>
              {comparisonVideoUrl && <video ref={comparisonPlayerRef} controls src={comparisonVideoUrl} style={{ width: '100%', maxHeight: '480px' }} />}
              {Array.isArray(comparisonResult.alineacion) && comparisonResult.alineacion.length > 0 && (
                <div aria-label="Alineación temporal entre ambos videos" style={{ display: 'flex', alignItems: 'end', gap: '2px', height: '44px', marginTop: '0.75rem' }}>
                  {comparisonResult.alineacion.filter((_, i) => i % Math.max(1, Math.ceil(comparisonResult.alineacion.length / 100)) === 0).map((pair, i) => (
                    <button key={i} type="button" onClick={() => selectAlignmentFrame(pair)} aria-label={`Ver comparación: alumno fotograma ${pair.frame_alumno_idx}, profesor fotograma ${pair.frame_maestro_idx}`} title={`Alumno fotograma ${pair.frame_alumno_idx ?? '?'} · Profesor fotograma ${pair.frame_maestro_idx ?? '?'}`} style={{ flex: 1, minWidth: '2px', height: `${Math.max(5, Math.min(100, (pair.similitud_frame ?? 0) * 100))}%`, padding: 0, border: selectedAlignment?.video_idx === pair.video_idx ? '1px solid white' : 0, background: (pair.similitud_frame ?? 0) >= 0.7 ? '#35c878' : '#e04444', cursor: 'pointer' }} />
                  ))}
                </div>
              )}
              {selectedAlignment && <p>Fotogramas alineados: alumno #{selectedAlignment.frame_alumno_idx} · profesor #{selectedAlignment.frame_maestro_idx}</p>}
              <small>La línea resume cómo se alinean los fotogramas del alumno con los del profesor a lo largo del movimiento.</small>
            </section>
          )}

          {extractingPrimerFrame ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '2rem 1rem' }}>
              <div style={{ width: '40px', height: '40px', border: '3px solid rgba(255,255,255,0.1)', borderTop: '3px solid var(--brand-red)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{t.extractingFrame}</p>
            </div>
          ) : sessionData ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <SelectorPersonaVideo
                sessionData={sessionData}
                selectedPersonaIdx={selectedPersonaIdx}
                onSelect={(idx) => {
                  setSelectedPersonaIdx(idx);
                  setUserRejectedPersona(false);
                }}
                heading={t.selectPersonStep}
                subtitle={sessionData.personas.length > 1 ? t.multiplePersonsDetected : t.singlePersonDetected}
                candidateLabel={t.personCandidate}
                selectedLabel={t.personIdentified}
                showCandidates={false}
              />

              {/* Caso A: Solo 1 persona detectada -> Preguntar explícitamente si es el usuario o negarse */}
              {sessionData.personas.length === 1 ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem', marginTop: '0.5rem', width: '100%' }}>
                  {userRejectedPersona ? (
                    <div style={{
                      background: 'rgba(208, 17, 24, 0.2)',
                      border: '1px solid var(--brand-red)',
                      borderRadius: '8px',
                      padding: '0.9rem 1.25rem',
                      color: '#ff8787',
                      fontSize: '0.88rem',
                      textAlign: 'center',
                      width: '100%',
                      boxSizing: 'border-box'
                    }}>
                      {t.bodyNotDetectedMsg}
                    </div>
                  ) : (
                    <>
                      <span style={{ fontSize: '0.9rem', color: 'rgba(255, 255, 255, 0.85)', fontWeight: 'bold' }}>
                        {t.isThisYou}
                      </span>
                      <div style={{ display: 'flex', gap: '1rem', width: '100%' }}>
                        <button
                          type="button"
                          className="btn-secondary"
                          onClick={() => {
                            setUserRejectedPersona(true);
                            setSelectedPersonaIdx(null);
                          }}
                          style={{
                            flex: 1,
                            padding: '0.85rem',
                            borderColor: '#ff4d4f',
                            color: '#ff8787',
                            borderRadius: '8px',
                            cursor: 'pointer'
                          }}
                        >
                          {t.notThisPersonBtn}
                        </button>
                        <button
                          type="button"
                          className="btn-primary"
                          onClick={handleSubmit}
                          disabled={confirmingSelection}
                          style={{
                            flex: 1,
                            padding: '0.85rem',
                            borderRadius: '8px',
                            cursor: confirmingSelection ? 'not-allowed' : 'pointer'
                          }}
                        >
                          {confirmingSelection ? t.confirmingSelection : t.yesItsMeBtn}
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <>
                  {/* Caso B: Múltiples personas -> Chips para seleccionar persona */}
                  <div style={{ display: 'flex', gap: '0.75rem', width: '100%', justifyContent: 'center', flexWrap: 'wrap' }}>
                    {sessionData.personas.map((p) => {
                      const isSelected = selectedPersonaIdx === p.idx;
                      return (
                        <button
                          key={p.idx}
                          type="button"
                          onClick={() => {
                            setSelectedPersonaIdx(p.idx);
                            setUserRejectedPersona(false);
                          }}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.6rem 1rem',
                            borderRadius: '8px',
                            background: isSelected ? 'rgba(208, 17, 24, 0.2)' : 'rgba(255,255,255,0.05)',
                            border: isSelected ? '2px solid var(--brand-red)' : '1px solid rgba(255,255,255,0.15)',
                            color: isSelected ? '#fff' : 'rgba(255,255,255,0.75)',
                            cursor: 'pointer',
                            fontWeight: isSelected ? 'bold' : 'normal',
                            transition: 'all 0.2s'
                          }}
                        >
                          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: isSelected ? 'var(--brand-red)' : 'rgba(255,255,255,0.4)' }} />
                          <span>{isSelected ? t.personIdentified : `${t.personCandidate} #${p.idx}`}</span>
                          <span style={{ fontSize: '0.75rem', opacity: 0.7 }}>({Math.round(p.confianza * 100)}%)</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Botón de Confirmación y Análisis */}
                  <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={handleSubmit}
                      disabled={selectedPersonaIdx === null || confirmingSelection}
                      style={{
                        width: '100%',
                        padding: '0.85rem',
                        fontSize: '1rem',
                        opacity: selectedPersonaIdx === null || confirmingSelection ? 0.6 : 1,
                        cursor: selectedPersonaIdx === null || confirmingSelection ? 'not-allowed' : 'pointer'
                      }}
                    >
                      {confirmingSelection ? t.confirmingSelection : t.confirmPersonBtn}
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
