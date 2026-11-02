import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './ProfesorTecnicas.css';
import TheoryManagerModal from '../components/TheoryManagerModal';
import GlobalKnowledgeModal from '../components/GlobalKnowledgeModal';
import SelectorPersonaVideo from '../components/SelectorPersonaVideo';
import { incluirEstadoPatrones } from '../api/tecnicas';
import { getTranslation } from '../i18n/translations';

const OPACIONES_CINTURON = ['Blanco', 'Azul', 'Morado', 'Marrón', 'Negro'];

const BELT_LABELS = {
  'Blanco': 'White Belt',
  'Azul': 'Blue Belt',
  'Morado': 'Purple Belt',
  'Marrón': 'Brown Belt',
  'Negro': 'Black Belt',
  'White': 'White Belt',
  'Blue': 'Blue Belt',
  'Purple': 'Purple Belt',
  'Brown': 'Brown Belt',
  'Black': 'Black Belt',
};

const getBeltLabel = (nivel) => BELT_LABELS[nivel] || `${nivel} Belt`;

export default function ProfesorTecnicas({ user, onClose, idioma }) {
  const t = (key) => getTranslation(idioma, key);
  const [activeTab, setActiveTab] = useState('alumnos'); // 'alumnos' (default) | 'tecnicas'
  const [tecnicas, setTecnicas] = useState([]);
  const [alumnos, setAlumnos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingAlumnos, setLoadingAlumnos] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [showGlobalKnowledge, setShowGlobalKnowledge] = useState(false);
  const [personaSelection, setPersonaSelection] = useState(null);
  const [personaSelectionError, setPersonaSelectionError] = useState('');
  const [confirmingPersona, setConfirmingPersona] = useState(false);
  const [theoryModalTecnica, setTheoryModalTecnica] = useState(null);
  const [selectedAlumnoDetail, setSelectedAlumnoDetail] = useState(null);
  const [evaluacionesPorAlumno, setEvaluacionesPorAlumno] = useState({}); // { alumno_id: [...] }
  
  const [formData, setFormData] = useState({
    nombre: '',
    nivel_cinturon: 'Blanco',
    mensaje_profesor: ''
  });
  const [editingId, setEditingId] = useState(null);

  // File upload & preview state inside form
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const fetchTecnicas = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/tecnicas?profesor_id=${user?.user_id}`, {
        headers: { "Authorization": `Bearer ${user?.token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTecnicas(await incluirEstadoPatrones(data, user?.token));
      }
    } catch (err) {
      console.error("Error fetching techniques", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlumnos = async () => {
    setLoadingAlumnos(true);
    try {
      // Instructor sees students from their branch; admin sees all
      const sucursalQuery = user?.rol === 'profesor' && user?.sucursal_id
        ? `?p_sucursal_id=${user.sucursal_id}`
        : '';
      const res = await fetch(`http://localhost:8000/api/v1/auth/alumnos${sucursalQuery}`, {
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAlumnos(data);
      }
    } catch (e) {
      console.error("Error loading students:", e);
    } finally {
      setLoadingAlumnos(false);
    }
  };

  const fetchEvaluacionesAlumno = async (alumnoId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/auth/alumnos/${alumnoId}/evaluaciones`, {
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setEvaluacionesPorAlumno(prev => ({ ...prev, [alumnoId]: data }));
      }
    } catch (e) {
      console.error("Error loading student evaluations:", e);
    }
  };

  useEffect(() => {
    const load = async () => {
      await fetchTecnicas();
      await fetchAlumnos();
    };
    load();
  }, [user?.user_id]);

  useEffect(() => {
    alumnos.forEach(a => {
      if (!evaluacionesPorAlumno[a.user_id]) {
        fetchEvaluacionesAlumno(a.user_id);
      }
    });
  }, [alumnos]);

  const handleOpenNewModal = () => {
    setEditingId(null);
    setFormData({ nombre: '', nivel_cinturon: 'Blanco', mensaje_profesor: '' });
    setSelectedFile(null);
    setPreviewUrl(null);
    setShowModal(true);
  };

  const handleEdit = (tech) => {
    setEditingId(tech.id);
    setFormData({
      nombre: tech.nombre,
      nivel_cinturon: tech.nivel_cinturon,
      mensaje_profesor: tech.mensaje_profesor || ''
    });
    setSelectedFile(null);
    setPreviewUrl(tech.video_url || null);
    setShowModal(true);
  };

  const handleChange = (e) => {
    setFormData({...formData, [e.target.name]: e.target.value});
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('video/')) {
        alert("Please select a valid video file.");
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!selectedFile && !previewUrl) {
      alert('You must upload the reference video for this technique.');
      return;
    }
    if (!formData.mensaje_profesor.trim()) {
      alert('Write a message explaining the technique to your students.');
      return;
    }
    setSaving(true);

    try {
      if (!editingId) {
        // Nueva técnica: primero procesar el video y obtener el primer frame
        const frameData = new FormData();
        frameData.append("video", selectedFile);
        const frameRes = await fetch("http://localhost:8000/api/v1/evaluaciones/primer-frame", {
          method: "POST",
          headers: { "Authorization": `Bearer ${user.token}` },
          body: frameData
        });
        if (!frameRes.ok) {
          const err = await frameRes.json().catch(() => ({}));
          throw new Error(err.detail || "Error processing video. Could not extract initial frame.");
        }
        const frame = await frameRes.json();
        setPersonaSelection({
          tecnicaId: null,
          pendingTecnica: {
            nombre: formData.nombre,
            nivel_cinturon: formData.nivel_cinturon,
            mensaje_profesor: formData.mensaje_profesor.trim(),
          },
          sessionData: frame,
          selectedIdx: frame.personas?.length === 1 ? frame.personas[0].idx : null,
        });
        setPersonaSelectionError('');
        setShowModal(false);
      } else {
        // Editando técnica existente
        if (selectedFile) {
          const frameData = new FormData();
          frameData.append("video", selectedFile);
          const frameRes = await fetch("http://localhost:8000/api/v1/evaluaciones/primer-frame", {
            method: "POST",
            headers: { "Authorization": `Bearer ${user.token}` },
            body: frameData
          });
          if (!frameRes.ok) {
            const err = await frameRes.json().catch(() => ({}));
            throw new Error(err.detail || "Error processing video.");
          }
          const frame = await frameRes.json();
          setPersonaSelection({
            tecnicaId: editingId,
            pendingTecnica: {
              nombre: formData.nombre,
              nivel_cinturon: formData.nivel_cinturon,
              mensaje_profesor: formData.mensaje_profesor.trim(),
            },
            sessionData: frame,
            selectedIdx: frame.personas?.length === 1 ? frame.personas[0].idx : null,
          });
          setPersonaSelectionError('');
          setShowModal(false);
        } else {
          // Solo actualizar datos de texto de la técnica existente
          const res = await fetch(`http://localhost:8000/api/v1/tecnicas/${editingId}`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${user.token}`
            },
            body: JSON.stringify({
              nombre: formData.nombre,
              nivel_cinturon: formData.nivel_cinturon,
              mensaje_profesor: formData.mensaje_profesor.trim(),
            })
          });
          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "Error updating technique.");
          }
          alert("Technique updated successfully.");
          setShowModal(false);
          fetchTecnicas();
        }
      }
    } catch (err) {
      console.error(err);
      alert(err.message || "Connection error saving technique.");
    } finally {
      setSaving(false);
    }
  };

  const handleConfirmPersona = async () => {
    if (!personaSelection || personaSelection.selectedIdx === null) return;
    setConfirmingPersona(true);
    setPersonaSelectionError('');
    let createdTecnicaId = null;

    try {
      const { tecnicaId, pendingTecnica, sessionData, selectedIdx } = personaSelection;
      let targetTecnicaId = tecnicaId;

      // 1. Si es nueva técnica, crear la entidad en la base de datos ahora
      if (!targetTecnicaId && pendingTecnica) {
        const createRes = await fetch("http://localhost:8000/api/v1/tecnicas", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${user.token}`
          },
          body: JSON.stringify(pendingTecnica)
        });
        if (!createRes.ok) {
          const err = await createRes.json().catch(() => ({}));
          throw new Error(err.detail || "Error creating technique in database.");
        }
        const savedTecnica = await createRes.json();
        targetTecnicaId = savedTecnica.id;
        createdTecnicaId = savedTecnica.id;
      } else if (targetTecnicaId && pendingTecnica) {
        // Si estamos editando, actualizar campos
        await fetch(`http://localhost:8000/api/v1/tecnicas/${targetTecnicaId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${user.token}`
          },
          body: JSON.stringify(pendingTecnica)
        });
      }

      // 2. Confirmar persona seleccionada en la sesión
      const selectionRes = await fetch(`http://localhost:8000/api/v1/evaluaciones/${sessionData.session_id}/seleccionar-persona`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${user.token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ persona_idx: selectedIdx }),
      });
      if (!selectionRes.ok) {
        const err = await selectionRes.json().catch(() => ({}));
        throw new Error(err.detail || 'Could not confirm selected person.');
      }

      // 3. Registrar el patrón biomecánico
      const patronForm = new FormData();
      patronForm.append('session_id', sessionData.session_id);
      patronForm.append('persona_idx', String(selectedIdx));
      const patronRes = await fetch(`http://localhost:8000/api/v1/tecnicas/${targetTecnicaId}/patron`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${user.token}` },
        body: patronForm,
      });
      if (!patronRes.ok) {
        const err = await patronRes.json().catch(() => ({}));
        throw new Error(err.detail || 'Could not register biomechanical pattern.');
      }
      const patron = await patronRes.json();
      alert(`Biomechanical pattern active: ${patron.total_frames} frames.`);
      setPersonaSelection(null);
      fetchTecnicas();
    } catch (err) {
      // Si falló el registro del patrón para una técnica recién creada, eliminarla como rollback
      if (createdTecnicaId) {
        try {
          await fetch(`http://localhost:8000/api/v1/tecnicas/${createdTecnicaId}`, {
            method: 'DELETE',
            headers: { "Authorization": `Bearer ${user.token}` }
          });
        } catch (_) {}
      }
      setPersonaSelectionError(err.message || 'Error registering pattern.');
    } finally {
      setConfirmingPersona(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this technique?')) return;
    try {
      const res = await fetch(`http://localhost:8000/api/v1/tecnicas/${id}`, {
        method: 'DELETE',
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      if (res.ok) fetchTecnicas();
    } catch (err) {
      console.error(err);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 85) return '#69db7c';
    if (score >= 70) return '#ffd43b';
    return '#ff6b6b';
  };

  return (
    <div className="profesor-tecnicas-container glass-panel" style={{ width: '100%', boxSizing: 'border-box' }}>
      {/* Main Header */}
      <div className="tecnicas-header" style={{ marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.75rem', color: 'var(--brand-red)' }}>
            {t('instructorPanel')}
          </h2>
          <span style={{ fontSize: '0.9rem', opacity: 0.8 }}>
            {user?.nombre_completo || t('coach')} — {user?.sucursal_nombre}
          </span>
        </div>
        <div>
          <button className="btn-secondary" onClick={onClose}>{t('close')}</button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('alumnos')}
          style={{
            flex: 1, padding: '0.85rem', background: 'none', border: 'none',
            borderBottom: activeTab === 'alumnos' ? '3px solid var(--brand-red)' : '3px solid transparent',
            color: activeTab === 'alumnos' ? 'white' : 'var(--text-secondary)',
            fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem'
          }}
        >
          {t('studentsTab')} ({alumnos.length})
        </button>
        <button
          onClick={() => setActiveTab('tecnicas')}
          style={{
            flex: 1, padding: '0.85rem', background: 'none', border: 'none',
            borderBottom: activeTab === 'tecnicas' ? '3px solid var(--brand-red)' : '3px solid transparent',
            color: activeTab === 'tecnicas' ? 'white' : 'var(--text-secondary)',
            fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem'
          }}
        >
          {t('techniquesTab')} ({tecnicas.length})
        </button>
      </div>

      {/* TAB 1: STUDENT PROGRESS */}
      {activeTab === 'alumnos' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'white' }}>
              {t('biomechanicalTracking')}
            </h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {t('studentsRegisteredBranch')}
            </span>
          </div>

          {loadingAlumnos ? (
            <p>{t('loadingStudents')}</p>
          ) : alumnos.length === 0 ? (
            <p style={{ opacity: 0.7 }}>{t('noStudentsInBranch')}</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {alumnos.map(alumno => {
                const evaluacionesReales = evaluacionesPorAlumno[alumno.user_id] || [];

                return (
                  <div 
                    key={alumno.user_id} 
                    className="glass-panel" 
                    style={{ padding: '1.5rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.03)' }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '1rem', marginBottom: '1rem' }}>
                      <div style={{
                        width: '48px', height: '48px', borderRadius: '50%', background: 'var(--brand-red)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', fontWeight: 'bold', color: 'white'
                      }}>
                        {alumno.avatar_url ? (
                          <img src={alumno.avatar_url} alt={alumno.nombre_completo} style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
                        ) : (
                          alumno.nombre_completo[0].toUpperCase()
                        )}
                      </div>
                      <div style={{ flex: 1 }}>
                        <h4 style={{ margin: 0, fontSize: '1.2rem', color: 'white' }}>{alumno.nombre_completo}</h4>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>@{alumno.username} • {t('branchAcademy')}: {alumno.sucursal_nombre}</span>
                      </div>
                    </div>

                    <h5 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', color: '#4da6ff' }}>
                      {t('biomechanicalProgress')} ({evaluacionesReales.length} {evaluacionesReales.length === 1 ? t('evaluationSingular') : t('evaluationPlural')}):
                    </h5>

                    {evaluacionesReales.length === 0 ? (
                      <p style={{ fontSize: '0.85rem', opacity: 0.6, fontStyle: 'italic' }}>
                        {t('noEvaluationsForStudent')}
                      </p>
                    ) : (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 280px), 1fr))', gap: '1rem' }}>
                        {evaluacionesReales.map((evalItem, idx) => {
                          const similitud = parseFloat(evalItem.porcentaje_similitud) || 0;
                          const estadoLabel = similitud >= 85 ? 'Excellent' : (similitud >= 70 ? 'Good' : 'Needs Work');
                          const fecha = evalItem.fecha_evaluacion
                            ? new Date(evalItem.fecha_evaluacion).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' })
                            : t('dateUnavailable');

                          return (
                            <div 
                              key={idx} 
                              style={{
                                background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px',
                                border: '1px solid rgba(255,255,255,0.1)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'
                              }}
                            >
                              <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                  <strong style={{ fontSize: '0.95rem', color: 'white' }}>{evalItem.tecnica_nombre}</strong>
                                  <span style={{
                                    fontSize: '0.75rem', fontWeight: 'bold', padding: '0.15rem 0.5rem', borderRadius: '4px',
                                    background: `${getScoreColor(similitud)}22`, color: getScoreColor(similitud),
                                    border: `1px solid ${getScoreColor(similitud)}`
                                  }}>
                                    {estadoLabel}
                                  </span>
                                </div>

                                <div style={{ marginBottom: '0.75rem' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.2rem' }}>
                                    <span>{t('similarity')}:</span>
                                    <strong style={{ color: getScoreColor(similitud) }}>{similitud}%</strong>
                                  </div>
                                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                                    <div style={{ width: `${similitud}%`, height: '100%', background: getScoreColor(similitud), transition: 'width 0.5s ease' }} />
                                  </div>
                                </div>

                                <p style={{ fontSize: '0.85rem', color: '#ffffff', margin: '0 0 0.5rem 0', fontWeight: '600', lineHeight: '1.4' }}>
                                  {evalItem.feedback_summary || (evalItem.feedback_gemini_es ? evalItem.feedback_gemini_es.split('.')[0] : t('practiceRecommendation'))}
                                </p>
                              </div>

                              <div style={{ marginTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>{fecha}</span>
                                <button 
                                  onClick={() => setSelectedAlumnoDetail({ alumno, evalItem })}
                                  className="btn-secondary"
                                  style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem', borderRadius: '4px', cursor: 'pointer' }}
                                >
                                  {t('viewDetail')}
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: MY TECHNIQUES & VIDEOS */}
      {activeTab === 'tecnicas' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'white' }}>{t('techniquesAndReferenceVideos')}</h3>
            <div style={{ display: 'flex', gap: '.65rem', flexWrap: 'wrap' }}>
              <button className="btn-secondary" onClick={() => setShowGlobalKnowledge(true)}>{t('globalKnowledge')}</button>
              <button className="btn-primary" onClick={handleOpenNewModal}>{t('newTechnique')}</button>
            </div>
          </div>

          {loading ? <p>{t('loadingTechniques')}</p> : (
            <div className="tecnicas-grid">
              {tecnicas.map(tech => (
                <div key={tech.id} className="tecnica-card">
                  <div className="tecnica-info">
                    <h3>{tech.nombre}</h3>
                    <span className={`badge-cinturon cinturon-${tech.nivel_cinturon?.toLowerCase()}`}>
                      {getBeltLabel(tech.nivel_cinturon)}
                    </span>
                    {(tech.tiene_patron || tech.tiene_video) ? (
                      <div style={{ marginTop: '0.5rem' }}>
                        <div className="video-status has-video" style={{ marginBottom: '0.5rem' }}>
                          {tech.tiene_patron ? `✅ ${t('activeBiomechanicalPattern')}` : t('hasReferenceVideo')}
                        </div>
                        {tech.video_url && (
                          <div className="card-video-preview" style={{ marginTop: '0.5rem' }}>
                            <video 
                              src={tech.video_url} 
                              controls 
                              playsInline
                              preload="metadata"
                              style={{ 
                                width: '100%', 
                                maxHeight: '180px', 
                                borderRadius: '8px', 
                                backgroundColor: '#000',
                                border: '1px solid rgba(255, 255, 255, 0.15)',
                                display: 'block'
                              }} 
                            />
                          </div>
                        )}
                        {tech.tiene_patron && !tech.video_url && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
                            {t('referenceVideoUnavailable')}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="video-status no-video">{t('noVideoYet')}</div>
                    )}
                  </div>
                  <div className="tecnica-actions">
                    <button
                      className="btn-icon theory-btn"
                      onClick={() => setTheoryModalTecnica(tech)}
                    >
                      📖 {t('techniqueTheory')}
                    </button>
                    <button className="btn-icon edit" onClick={() => handleEdit(tech)}>✏️</button>
                    <button className="btn-icon delete" onClick={() => handleDelete(tech.id)}>🗑️</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal Keypoints Detail */}
      {selectedAlumnoDetail && (
        <div className="modal-overlay">
          <div className="modal-content glass-panel" style={{ maxWidth: '500px', padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--brand-red)' }}>
              {t('biomechanicalDetail')} — {selectedAlumnoDetail.alumno.nombre_completo}
            </h3>
            <p style={{ fontSize: '0.9rem', margin: '0 0 1rem 0' }}>
              {t('evaluatedTechnique')}: <strong>{selectedAlumnoDetail.evalItem.tecnica_nombre}</strong>
            </p>

            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#4da6ff' }}>
                {t('aiTechnicalAnalysis')}:
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.25rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span>{t('similarity')}:</span>
                <strong style={{ color: '#69db7c' }}>{parseFloat(selectedAlumnoDetail.evalItem.porcentaje_similitud || 0).toFixed(1)}%</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.25rem 0' }}>
                <span>{t('match')}:</span>
                <strong>{selectedAlumnoDetail.evalItem.estado}</strong>
              </div>
            </div>

            <div style={{ fontSize: '0.85rem', lineHeight: '1.4', marginBottom: '1.5rem', background: 'rgba(255,255,255,0.04)', padding: '0.8rem', borderRadius: '6px' }}>
              <strong>{t('aiTechnicalAnalysis')}:</strong>
              <p style={{ margin: '0.3rem 0 0 0', opacity: 0.8 }}>
                {selectedAlumnoDetail.evalItem.feedback_gemini_es || selectedAlumnoDetail.evalItem.feedback_gemini_pt || t('noCorrectionAvailable')}
              </p>
            </div>

            <button className="btn-primary" onClick={() => setSelectedAlumnoDetail(null)} style={{ width: '100%' }}>
              {t('close')}
            </button>
          </div>
        </div>
      )}

      {/* Modal Form (Create / Edit Technique) */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-panel" style={{ maxWidth: '560px', maxHeight: '90vh', overflowY: 'auto' }}>
            <h3>{editingId ? t('editBranch') : t('newTechnique')}</h3>
            
            <form onSubmit={handleSave}>
              <div className="form-group">
                <label>{t('techniqueName')}</label>
                <input required type="text" name="nombre" value={formData.nombre} onChange={handleChange} placeholder="e.g. Armbar from Guard" />
              </div>

              <div className="form-group">
                <label>{t('minBeltLevel')}</label>
                <select name="nivel_cinturon" value={formData.nivel_cinturon} onChange={handleChange}>
                  {OPACIONES_CINTURON.map(nivel => (
                    <option key={nivel} value={nivel}>
                      {getBeltLabel(nivel)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="mensaje_profesor">{t('instructorMessage')}</label>
                <textarea
                  id="mensaje_profesor"
                  name="mensaje_profesor"
                  value={formData.mensaje_profesor}
                  onChange={handleChange}
                  placeholder="Explain in your own words how to execute this technique."
                  rows={5}
                  required
                  style={{ width: '100%', background: 'rgba(255,255,255,0.05)', color: 'white', padding: '0.75rem', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', resize: 'vertical' }}
                />
              </div>

              <div className="form-group">
                <label>{t('referenceVideoFile')}</label>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  accept="video/*" 
                  onChange={handleFileChange} 
                  style={{ display: 'none' }} 
                />
                <button 
                  type="button" 
                  className="btn-secondary" 
                  style={{ width: '100%', padding: '0.6rem' }} 
                  onClick={() => fileInputRef.current?.click()}
                >
                  {selectedFile ? ` Video: ${selectedFile.name}` : (editingId && previewUrl ? "Replace Video" : "Upload Video")}
                </button>
              </div>

              {previewUrl && (
                <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                    {t('coachReferenceVideo')}
                  </label>
                  <video 
                    src={previewUrl} 
                    controls 
                    playsInline 
                    style={{ width: '100%', maxHeight: '200px', borderRadius: '8px', backgroundColor: '#000' }} 
                  />
                </div>
              )}

              <div className="modal-actions" style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)} disabled={saving}>
                  {t('close')}
                </button>
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? t('savingTechnique') : t('saveTechnique')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {personaSelection && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="persona-selection-title">
          <div className="modal-content glass-panel" style={{ maxWidth: '760px', maxHeight: '90vh', overflowY: 'auto' }}>
            <h3 id="persona-selection-title" style={{ marginTop: 0, color: 'var(--brand-red)' }}>
              {t('selectInstructorVideoStep')}
            </h3>
            <p style={{ color: 'var(--text-secondary)' }}>
              {t('selectInstructorVideoDesc')}
            </p>
            <SelectorPersonaVideo
              sessionData={personaSelection.sessionData}
              selectedPersonaIdx={personaSelection.selectedIdx}
              onSelect={(selectedIdx) => setPersonaSelection((current) => ({ ...current, selectedIdx }))}
              candidateLabel={t('instructorRole')}
              selectedLabel={t('identified')}
              heading={t('selectInstructorVideoStep')}
              subtitle={personaSelection.sessionData.personas?.length > 1 ? t('multiplePersonsDetected') : t('confirmInstructorPersona')}
            />
            {personaSelectionError && (
              <div role="alert" style={{ marginTop: '1rem', padding: '.75rem', borderRadius: '8px', background: 'rgba(208,17,24,.2)', color: '#ff8787' }}>
                {personaSelectionError}
              </div>
            )}
            <div className="modal-actions" style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
              <button 
                type="button" 
                className="btn-secondary" 
                onClick={() => {
                  setPersonaSelection(null);
                  fetchTecnicas();
                }} 
                disabled={confirmingPersona}
              >
                {t('close')}
              </button>
              <button 
                type="button" 
                className="btn-primary" 
                onClick={handleConfirmPersona} 
                disabled={personaSelection.selectedIdx === null || confirmingPersona}
              >
                {confirmingPersona ? t('saving') : t('confirmSelectionAndAnalyze')}
              </button>
            </div>
          </div>
        </div>
      )}

      {theoryModalTecnica && (
        <TheoryManagerModal
          isOpen={true}
          user={user}
          tecnica={theoryModalTecnica}
          onClose={() => setTheoryModalTecnica(null)}
        />
      )}
      {showGlobalKnowledge && <GlobalKnowledgeModal user={user} onClose={() => setShowGlobalKnowledge(false)} />}

      {selectedAlumnoDetail && (
        <div className="modal-overlay" role="dialog" aria-modal="true" onClick={() => setSelectedAlumnoDetail(null)}>
          <div className="modal-content glass-panel" style={{ maxWidth: '650px', maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)', letterSpacing: '1px' }}>
                  EVALUATION DETAILS
                </span>
                <h3 style={{ margin: '0.25rem 0 0 0', fontSize: '1.25rem', color: 'white' }}>
                  {selectedAlumnoDetail.evalItem.tecnica_nombre}
                </h3>
                <small style={{ color: 'var(--text-secondary)' }}>
                  Student: {selectedAlumnoDetail.alumno.nombre_completo}
                </small>
              </div>
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '0.35rem 0.75rem' }}
                onClick={() => setSelectedAlumnoDetail(null)}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
              <div style={{
                padding: '0.35rem 0.75rem', borderRadius: '6px', fontWeight: 'bold', fontSize: '0.9rem',
                background: `${getScoreColor(selectedAlumnoDetail.evalItem.porcentaje_similitud)}22`,
                color: getScoreColor(selectedAlumnoDetail.evalItem.porcentaje_similitud),
                border: `1px solid ${getScoreColor(selectedAlumnoDetail.evalItem.porcentaje_similitud)}`
              }}>
                {selectedAlumnoDetail.evalItem.porcentaje_similitud >= 85 ? 'Excellent' : selectedAlumnoDetail.evalItem.porcentaje_similitud >= 70 ? 'Good' : 'Needs Work'} ({Math.round(selectedAlumnoDetail.evalItem.porcentaje_similitud)}%)
              </div>
              {selectedAlumnoDetail.evalItem.practice_url && (
                <a
                  href={selectedAlumnoDetail.evalItem.practice_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: '#ef4444', textDecoration: 'none', fontSize: '0.85rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                >
                  YouTube Practice Tutorials ↗
                </a>
              )}
            </div>

            {selectedAlumnoDetail.evalItem.feedback_summary && (
              <div style={{ marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                  SUMMARY
                </span>
                <strong style={{ color: 'white', fontSize: '1.05rem' }}>
                  {selectedAlumnoDetail.evalItem.feedback_summary}
                </strong>
              </div>
            )}

            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.5rem' }}>
                FULL TECHNICAL FEEDBACK (MARKDOWN)
              </span>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)', color: '#d1d5db', lineHeight: 1.6 }}>
                <ReactMarkdown>
                  {selectedAlumnoDetail.evalItem.feedback_gemini_es || selectedAlumnoDetail.evalItem.feedback_gemini_pt || 'No detailed feedback available.'}
                </ReactMarkdown>
              </div>
            </div>

            <div className="modal-actions" style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
              <button type="button" className="btn-secondary" onClick={() => setSelectedAlumnoDetail(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
