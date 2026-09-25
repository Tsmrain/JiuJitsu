import { useState, useEffect } from 'react';
import './VideoUpload.css';
import { useTranslation } from '../i18n/translations';

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
      const res = await fetch(`http://localhost:8000/api/v1/tecnicas?profesor_id=${profesorId}`);
      if (res.ok) {
        const data = await res.json();
        setTecnicas(data);
        if (data && data.length > 0) {
          // Priorizar seleccionar una técnica que tenga video de referencia
          const conVideo = data.find(t => t.tiene_video);
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

  const handleFile = (selectedFile) => {
    if (selectedFile.type.startsWith('video/')) {
      setFile(selectedFile);
    } else {
      alert(t.alertValidVideo);
    }
  };

  const handleSubmit = () => {
    if (file && selectedTecnica) {
      onUploadStart(file, {
        ...selectedTecnica,
        profesorRef: selectedProfesor ? selectedProfesor.nombre_completo : "Mestre Oficial"
      });
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
                    {tech.nombre} {tech.tiene_video ? '' : ''}
                  </option>
                ))}
              </select>
            )}

            {selectedTecnica && (
              <div className="profesor-ref-info" style={{ marginTop: '0.85rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(255,255,255,0.03)', padding: '0.5rem 0.75rem', borderRadius: '8px' }}>
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
                <span style={{ marginLeft: 'auto', background: selectedTecnica.tiene_video ? '#22c55e' : 'var(--brand-red)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 'bold', fontSize: '0.75rem', color: 'white' }}>
                  {selectedTecnica.tiene_video ? t.hasVideoTag : t.noVideoTag}
                </span>
              </div>
            )}
          </>
        )}
      </div>

      {/* Paso 3: Carga del Video del Alumno */}
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
        
        {!file ? (
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
        ) : (
          <div className="file-preview" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', width: '100%' }}>
            <video 
              src={URL.createObjectURL(file)} 
              controls 
              className="video-player"
              style={{ width: '100%', maxHeight: '300px', borderRadius: '8px', backgroundColor: 'black' }}
            />
            <div className="file-info" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
              <span className="file-name" style={{ fontWeight: 'bold' }}>{file.name}</span>
              <span className="file-size" style={{ fontSize: '0.875rem', opacity: 0.7 }}>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
            </div>
            <div className="file-actions" style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
              <button type="button" className="btn-secondary" onClick={() => setFile(null)}>{t.btnChange}</button>
              <button type="button" className="btn-primary" onClick={handleSubmit}>{t.btnAnalyze}</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
