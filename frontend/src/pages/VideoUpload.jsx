import { useState, useEffect } from 'react';
import './VideoUpload.css';
import SelectorPersonaVideo from '../components/SelectorPersonaVideo';
import { incluirEstadoPatrones } from '../api/tecnicas';
import { getTranslation } from '../i18n/translations';
import { API_BASE } from '../api/config';

export default function VideoUpload({ user, onUploadStart, idioma }) {
  const [profesores, setProfesores] = useState([]);
  const [selectedProfesor, setSelectedProfesor] = useState(null);
  const [tecnicas, setTecnicas] = useState([]);
  const [selectedTecnica, setSelectedTecnica] = useState(null);
  const [loadingProfesores, setLoadingProfesores] = useState(true);
  const [loadingTecnicas, setLoadingTecnicas] = useState(false);

  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);

  const t = (key) => getTranslation(idioma, key);

  const isAlumno = user?.rol === 'alumno';
  const isExpired = isAlumno && (
    user?.estado_suscripcion === 'expirado' ||
    (user?.fecha_expiracion && new Date(user.fecha_expiracion) <= new Date())
  );
  const isPassActive = !isAlumno || (user?.estado_suscripcion === 'activo' && !isExpired);
  const isPending = isAlumno && !isPassActive && !isExpired;

  // 1. Load academy instructors
  const fetchProfesores = async () => {
    setLoadingProfesores(true);
    try {
      const sucursalQuery = user?.sucursal_id ? `?sucursal_id=${user.sucursal_id}` : '';
      const res = await fetch(`${API_BASE}/api/v1/profesores${sucursalQuery}`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          setProfesores(data);
          setSelectedProfesor(data[0]);
        } else {
          // Fallback to all instructors if none registered for this branch
          const resAll = await fetch(`${API_BASE}/api/v1/profesores`);
          if (resAll.ok) {
            const dataAll = await resAll.json();
            setProfesores(dataAll);
            if (dataAll.length > 0) setSelectedProfesor(dataAll[0]);
          }
        }
      }
    } catch (err) {
      console.error("Error loading instructors:", err);
    } finally {
      setLoadingProfesores(false);
    }
  };

  const fetchTecnicasDelProfesor = async (profesorId) => {
    setLoadingTecnicas(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/tecnicas?profesor_id=${profesorId}`, {
        headers: { Authorization: `Bearer ${user?.token}` }
      });
      if (res.ok) {
        const data = await incluirEstadoPatrones(await res.json(), user?.token);
        setTecnicas(data);
        if (data && data.length > 0) {
          // Prioritize technique with reference video
          const conVideo = data.find(item => item.tiene_patron || item.tiene_video);
          setSelectedTecnica(conVideo || data[0]);
        } else {
          setSelectedTecnica(null);
        }
      }
    } catch (err) {
      console.error("Error loading instructor techniques:", err);
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
  const [validatingSpam, setValidatingSpam] = useState(false);
  const [spamError, setSpamError] = useState(null);

  const handleFile = async (selectedFile) => {
    if (!selectedFile.type.startsWith('video/')) {
      alert(t('invalidVideoFile'));
      return;
    }
    setFile(selectedFile);
    setSessionData(null);
    setSelectedPersonaIdx(null);
    setUserRejectedPersona(false);
    setErrorMessage(null);
    setSpamError(null);
    setValidatingSpam(true);

    try {
      // 1. Validar video con filtro anti-spam (YOLO + Clasificador ViCoS)
      const spamForm = new FormData();
      spamForm.append("video", selectedFile);
      const spamRes = await fetch(`${API_BASE}/api/v1/evaluaciones/validar-spam`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${user?.token}` },
        body: spamForm,
      });

      if (spamRes.status === 422 || !spamRes.ok) {
        const spamData = await spamRes.json().catch(() => ({}));
        const msg = spamRes.status === 422
          ? t('spamNotBjj')
          : (spamData.detail || "Error validating video content.");
        setSpamError(msg);
        setFile(null);
        setValidatingSpam(false);
        alert(msg);
        return;
      }
      setValidatingSpam(false);

      // 2. Extraer primer frame y detectar personas
      setExtractingPrimerFrame(true);
      const formData = new FormData();
      formData.append("video", selectedFile);

      const res = await fetch(`${API_BASE}/api/v1/evaluaciones/primer-frame`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${user?.token}` },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Error detecting persons in the initial frame.");
      }

      const data = await res.json();
      setSessionData(data);
      if (data.personas && data.personas.length === 1) {
        setSelectedPersonaIdx(data.personas[0].idx);
      } else {
        setSelectedPersonaIdx(null);
      }
    } catch (err) {
      console.error("Error processing video:", err);
      setErrorMessage(err.message || "Error processing initial video frame.");
    } finally {
      setValidatingSpam(false);
      setExtractingPrimerFrame(false);
    }
  };

  const handleResetVideo = () => {
    setFile(null);
    setSessionData(null);
    setSelectedPersonaIdx(null);
    setUserRejectedPersona(false);
    setErrorMessage(null);
    setSpamError(null);
    setValidatingSpam(false);
    setExtractingPrimerFrame(false);
  };

  const handleSubmit = async () => {
    if (!file || !selectedTecnica) return;

    if (!sessionData || selectedPersonaIdx === null) {
      alert(t('selectPersonPrompt'));
      return;
    }

    setConfirmingSelection(true);
    setErrorMessage(null);

    try {
      // 1. Confirm person selection in backend session
      const res = await fetch(`${API_BASE}/api/v1/evaluaciones/${sessionData.session_id}/seleccionar-persona`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${user?.token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ persona_idx: selectedPersonaIdx })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Error confirming person selection.");
      }

      // 2. Trigger analysis
      onUploadStart({
        sessionId: sessionData.session_id,
        personaIdx: selectedPersonaIdx,
        tecnica: {
          ...selectedTecnica,
          profesorRef: selectedProfesor ? selectedProfesor.nombre_completo : "Official Instructor",
          profesor_id: selectedProfesor?.user_id
        },
        file
      });
    } catch (err) {
      console.error("Error confirming person:", err);
      setErrorMessage(err.message || "Error confirming selected person.");
    } finally {
      setConfirmingSelection(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h2>{t('uploadTitle')}</h2>
        <p>{t('uploadSubtitle')}</p>
      </div>

      {/* Control de Suscripción (Pase de Tatami) */}
      {isAlumno && isPassActive && (
        <div className="glass-panel" style={{
          background: 'rgba(34, 197, 94, 0.12)',
          border: '1px solid #22c55e',
          padding: '0.75rem 1.25rem',
          borderRadius: '10px',
          marginBottom: '1rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.5rem',
          fontSize: '0.88rem'
        }}>
          <span style={{ color: '#4ade80', fontWeight: 'bold' }}>
            🥋 {t('passStatus')}: {t('activeStatus')}
          </span>
          {user?.fecha_expiracion && (
            <span style={{ color: 'rgba(255,255,255,0.85)', fontSize: '0.82rem' }}>
              📅 {t('passActiveUntil')} {new Date(user.fecha_expiracion).toLocaleDateString(idioma === 'pt' ? 'pt-BR' : (idioma === 'en' ? 'en-US' : 'es-ES'), { day: 'numeric', month: 'long', year: 'numeric' })}
            </span>
          )}
        </div>
      )}

      {isAlumno && !isPassActive && (
        <div className="subscription-wall-banner" style={{
          background: 'linear-gradient(135deg, rgba(208, 17, 24, 0.25) 0%, rgba(20, 20, 20, 0.95) 100%)',
          border: '2px solid var(--brand-red)',
          borderRadius: '14px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          textAlign: 'center',
          boxShadow: '0 0 25px rgba(208, 17, 24, 0.45)'
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🥋🔒</div>
          <h3 style={{ color: 'var(--brand-red)', margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 'bold' }}>
            {t('passStatus')}: {isExpired ? t('expiredStatus') : t('pendingStatus')}
          </h3>
          <p style={{ color: 'white', fontSize: '0.95rem', lineHeight: '1.5', maxWidth: '620px', margin: '0 auto 1.25rem auto' }}>
            {isExpired ? t('subscriptionExpiredWarning') : t('subscriptionPendingWarning')}
          </p>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'rgba(255, 255, 255, 0.08)',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            fontSize: '0.85rem',
            color: 'rgba(255,255,255,0.85)'
          }}>
            📍 {user?.sucursal_nombre || 'Tu Academia'}
          </div>
        </div>
      )}

      {/* Main Grid: Step 1 & 2 Config on Left, Step 3 Video Upload on Right */}
      <div className="upload-main-layout">
        <div className="upload-config-column">
          {/* Step 1: Select Instructor */}
          <div className="step-card glass-panel">
            <div className="step-header">
              <span className="step-badge">1</span>
              <label className="step-title">
                {t('selectInstructorStep')}
              </label>
            </div>

        {loadingProfesores ? (
          <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>{t('loadingInstructors')}</p>
        ) : profesores.length === 0 ? (
          <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>{t('noInstructorsFound')}</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
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

      {/* Step 2: Select Technique */}
      <div className="step-card glass-panel">
        <div className="step-header">
          <span className="step-badge">2</span>
          <label className="step-title">
            {t('selectTechniqueStep')}
          </label>
        </div>

        {loadingTecnicas ? <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>{t('loadingTechniques')}</p> : (
          <>
            {tecnicas.length === 0 ? (
              <p style={{ fontSize: '0.9rem', color: '#ff8787' }}>{t('noTechniquesFound')}</p>
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
                  <div style={{ width: '32px', height: '32px', borderRadius: '50%', border: '1.5px solid var(--brand-red)', overflow: 'hidden', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(208,17,24,0.3)' }}>
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
                  {(selectedTecnica.tiene_patron || selectedTecnica.tiene_video) ? t('withReferenceVideo') : t('noReferenceVideo')}
                </span>
                </div>
                {selectedTecnica.mensaje_profesor && (
                  <div style={{ borderTop: '1px solid rgba(255,255,255,.1)', paddingTop: '.65rem', lineHeight: 1.5 }}>
                    <strong style={{ color: 'white' }}>{t('instructorInstructions')}</strong>
                    <p style={{ margin: '.3rem 0 0', color: 'rgba(255,255,255,.78)', whiteSpace: 'pre-wrap' }}>{selectedTecnica.mensaje_profesor}</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>

    {/* Right Column: Step 3 Upload & Interactive Calibration */}
    <div className="upload-action-column">
      <div className="step-card glass-panel" style={{ minHeight: '100%', justifyContent: 'flex-start' }}>
        <div className="step-header">
          <span className="step-badge">3</span>
          <label className="step-title">
            {t('uploadVideoStep')}
          </label>
        </div>

        {spamError && (
          <div style={{ background: 'rgba(208, 17, 24, 0.2)', border: '1px solid var(--brand-red)', padding: '0.85rem 1.25rem', borderRadius: '10px', color: '#ff8787', fontSize: '0.9rem', marginBottom: '0.5rem', textAlign: 'center' }}>
            ⚠️ {spamError}
          </div>
        )}

      {!isPassActive ? (
        <div className="glass-panel" style={{
          padding: '2.5rem 1.5rem',
          borderRadius: '12px',
          textAlign: 'center',
          border: '1px dashed rgba(208, 17, 24, 0.5)',
          background: 'rgba(208, 17, 24, 0.05)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <div style={{ fontSize: '2.5rem', opacity: 0.8 }}>🔒</div>
          <h4 style={{ margin: 0, fontSize: '1.1rem', color: 'white' }}>
            {t('uploadTitle')}
          </h4>
          <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)', maxWidth: '480px' }}>
            {isExpired ? t('subscriptionExpiredWarning') : t('subscriptionPendingWarning')}
          </p>
          <button
            type="button"
            disabled
            className="btn-primary"
            style={{
              minHeight: '44px',
              padding: '0.75rem 1.75rem',
              fontSize: '0.95rem',
              opacity: 0.6,
              cursor: 'not-allowed',
              background: 'rgba(208, 17, 24, 0.3)',
              border: '1px solid var(--brand-red)'
            }}
          >
            🔒 {t('passStatus')}: {isExpired ? t('expiredStatus') : t('pendingStatus')}
          </button>
        </div>
      ) : !file ? (
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
            <span className="drop-text">{t('dragDropText')} <strong>{t('browseFile')}</strong></span>
            <span className="drop-hint">{t('supportedFormats')}</span>
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
              {t('changeVideo')}
            </button>
          </div>

          {errorMessage && (
            <div style={{ background: 'rgba(208, 17, 24, 0.2)', border: '1px solid var(--brand-red)', padding: '0.75rem 1rem', borderRadius: '8px', color: '#ff8787', fontSize: '0.85rem' }}>
              {errorMessage}
            </div>
          )}

          {validatingSpam ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '2rem 1rem' }}>
              <div style={{ width: '40px', height: '40px', border: '3px solid rgba(255,255,255,0.1)', borderTop: '3px solid var(--brand-red)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{t('validatingVideoContent')}</p>
            </div>
          ) : extractingPrimerFrame ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '2rem 1rem' }}>
              <div style={{ width: '40px', height: '40px', border: '3px solid rgba(255,255,255,0.1)', borderTop: '3px solid var(--brand-red)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{t('extractingFirstFrame')}</p>
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
                heading={t('identifyYourselfHeading')}
                subtitle={sessionData.personas.length > 1 ? t('multiplePersonsDetected') : t('singlePersonDetected')}
                candidateLabel={t('candidate')}
                selectedLabel={t('identified')}
                showCandidates={false}
              />

              {/* Case A: Single person detected */}
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
                      {t('secondPersonNotFound')}
                    </div>
                  ) : (
                    <>
                      <span style={{ fontSize: '0.9rem', color: 'rgba(255, 255, 255, 0.85)', fontWeight: 'bold' }}>
                        {t('isThisYou')}
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
                          {t('noNotMe')}
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
                          {confirmingSelection ? t('confirming') : t('yesAnalyzeMe')}
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <>
                  {/* Case B: Multiple persons */}
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
                          <span>{isSelected ? t('identified') : `${t('candidate')} #${p.idx}`}</span>
                          <span style={{ fontSize: '0.75rem', opacity: 0.7 }}>({Math.round(p.confianza * 100)}%)</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Confirmation button */}
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
                      {confirmingSelection ? t('confirming') : t('confirmSelectionAndAnalyze')}
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : null}
        </div>
      )}
          </div>
        </div>
      </div>
    </div>
  );
}
