import { useState, useEffect, useRef } from 'react';
import './ProfesorTecnicas.css';
import { useTranslation } from '../i18n/translations';
import TheoryManagerModal from '../components/TheoryManagerModal';

const OPACIONES_CINTURON = ['Blanco', 'Azul', 'Morado', 'Marrón', 'Negro'];

export default function ProfesorTecnicas({ user, onClose }) {
  const [activeTab, setActiveTab] = useState('alumnos'); // 'alumnos' (default) | 'tecnicas'
  const [tecnicas, setTecnicas] = useState([]);
  const [alumnos, setAlumnos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingAlumnos, setLoadingAlumnos] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [theoryModalTecnica, setTheoryModalTecnica] = useState(null);
  const [selectedAlumnoDetail, setSelectedAlumnoDetail] = useState(null);
  const [evaluacionesPorAlumno, setEvaluacionesPorAlumno] = useState({}); // { alumno_id: [...] }
  
  const [formData, setFormData] = useState({
    nombre: '',
    nivel_cinturon: 'Blanco',
    teoria: ''
  });
  const [editingId, setEditingId] = useState(null);

  // File upload & preview state inside form
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const { t, getBeltLabel } = useTranslation(user?.idioma_preferido);

  const fetchTecnicas = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/tecnicas?profesor_id=${user?.user_id}`, {
        headers: { "Authorization": `Bearer ${user?.token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTecnicas(data);
      }
    } catch (err) {
      console.error("Error fetching técnicas", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlumnos = async () => {
    setLoadingAlumnos(true);
    try {
      // Profesor ve solo alumnos de su sucursal; admin ve todos
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
      console.error("Error cargando alumnos:", e);
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
      console.error("Error cargando evaluaciones del alumno:", e);
    }
  };

  useEffect(() => {
    const load = async () => {
      await fetchTecnicas();
      await fetchAlumnos();
    };
    load();
  }, [user?.user_id]);

  // Nuevo useEffect: cuando cambia la lista de alumnos, cargar sus evaluaciones
  useEffect(() => {
    alumnos.forEach(a => {
      if (!evaluacionesPorAlumno[a.user_id]) {
        fetchEvaluacionesAlumno(a.user_id);
      }
    });
  }, [alumnos]);

  const handleOpenNewModal = () => {
    setEditingId(null);
    setFormData({ nombre: '', nivel_cinturon: 'Blanco', teoria: '' });
    setSelectedFile(null);
    setPreviewUrl(null);
    setShowModal(true);
  };

  const handleEdit = (tech) => {
    setEditingId(tech.id);
    setFormData({
      nombre: tech.nombre,
      nivel_cinturon: tech.nivel_cinturon,
      teoria: '' // Usually theory is fetched, but keeping it simple for now
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
        alert(t.alertValidVideo);
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);

    const url = editingId 
      ? `http://localhost:8000/api/v1/tecnicas/${editingId}`
      : `http://localhost:8000/api/v1/tecnicas`;
    const method = editingId ? "PUT" : "POST";

    try {
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${user.token}`
        },
        body: JSON.stringify(formData)
      });

      if (!res.ok) {
        alert("Error guardando la técnica.");
        setSaving(false);
        return;
      }

      const savedTecnica = await res.json();

      if (selectedFile) {
        const videoData = new FormData();
        videoData.append("profesor_id", user.user_id);
        videoData.append("video", selectedFile);

        const videoRes = await fetch(`http://localhost:8000/api/v1/tecnicas/${savedTecnica.id}/video`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${user.token}` },
          body: videoData
        });

        if (!videoRes.ok) {
          alert("Técnica guardada pero falló la subida del video.");
        }
      }

      // RAG Multimodal: Ingest theory if provided
      if (formData.teoria.trim() !== '') {
        try {
          const teoriaRes = await fetch(`http://localhost:8000/api/v1/conocimiento/teoria`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${user.token}`
            },
            body: JSON.stringify({
              tecnica_id: savedTecnica.id,
              contenido_texto: formData.teoria
            })
          });
          if (!teoriaRes.ok) {
            console.error("Error al indexar la teoría en RAG Qdrant");
          }
        } catch (e) {
          console.error("No se pudo conectar al endpoint RAG", e);
        }
      }

      alert("¡Técnica, conocimiento RAG y video guardados con éxito!");
      setShowModal(false);
      fetchTecnicas();

    } catch (err) {
      console.error(err);
      alert("Error de conexión al guardar la técnica.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm(t.confirmDeleteTecnica)) return;
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
      {/* Header Principal */}
      <div className="tecnicas-header" style={{ marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.75rem', color: 'var(--brand-red)' }}>
            Panel de Control del Profesor
          </h2>
          <span style={{ fontSize: '0.9rem', opacity: 0.8 }}>
            Bienvenido, {user?.nombre_completo || 'Mestre'} — {user?.sucursal_nombre}
          </span>
        </div>
        <div>
          <button className="btn-secondary" onClick={onClose}>{t.btnClose}</button>
        </div>
      </div>

      {/* Pestañas de Navegación del Profesor */}
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
          Progreso de Mis Alumnos ({alumnos.length})
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
          Mis Técnicas y Videos ({tecnicas.length})
        </button>
      </div>

      {/* PESTAÑA 1: PROGRESO DE ALUMNOS (VISTA PRINCIPAL) */}
      {activeTab === 'alumnos' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'white' }}>
              Seguimiento Biomecánico de Alumnos en Jiu-Jitsu
            </h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Alumnos registrados en tu sucursal
            </span>
          </div>

          {loadingAlumnos ? (
            <p>Cargando información de alumnos...</p>
          ) : alumnos.length === 0 ? (
            <p style={{ opacity: 0.7 }}>No hay alumnos registrados aún en esta sucursal.</p>
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
                    {/* Encabezado del Alumno */}
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
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>@{alumno.username} • Sucursal: {alumno.sucursal_nombre}</span>
                      </div>
                    </div>

                    <h5 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', color: '#4da6ff' }}>
                      Progreso Biomecánico ({evaluacionesReales.length} {evaluacionesReales.length === 1 ? 'evaluación' : 'evaluaciones'}):
                    </h5>

                    {evaluacionesReales.length === 0 ? (
                      <p style={{ fontSize: '0.85rem', opacity: 0.6, fontStyle: 'italic' }}>
                        Este alumno aún no ha subido ningún video para evaluación.
                      </p>
                    ) : (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
                        {evaluacionesReales.map((evalItem, idx) => {
                          const similitud = parseFloat(evalItem.porcentaje_similitud) || 0;
                          const estadoLabel = similitud >= 85 ? 'Excelente' : (similitud >= 70 ? 'Bueno' : 'Requiere Ajuste');
                          const fecha = evalItem.fecha_evaluacion
                            ? new Date(evalItem.fecha_evaluacion).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })
                            : 'Fecha desconocida';

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
                                    <span>Similitud Vectorial:</span>
                                    <strong style={{ color: getScoreColor(similitud) }}>{similitud}%</strong>
                                  </div>
                                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                                    <div style={{ width: `${similitud}%`, height: '100%', background: getScoreColor(similitud), transition: 'width 0.5s ease' }} />
                                  </div>
                                </div>

                                {(evalItem.feedback_gemini_es || evalItem.feedback_gemini_pt) && (
                                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '0 0 0.5rem 0', lineHeight: '1.3' }}>
                                    "{evalItem.feedback_gemini_es || evalItem.feedback_gemini_pt}"
                                  </p>
                                )}
                              </div>

                              <div style={{ marginTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>Evaluado: {fecha}</span>
                                <button 
                                  onClick={() => setSelectedAlumnoDetail({ alumno, evalItem })}
                                  style={{ background: 'none', border: 'none', color: '#4da6ff', fontSize: '0.75rem', cursor: 'pointer', textDecoration: 'underline' }}
                                >
                                  Ver Detalle Keypoints
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

      {/* PESTAÑA 2: MIS TÉCNICAS Y VIDEOS */}
      {activeTab === 'tecnicas' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'white' }}>Técnicas y Videos de Referencia</h3>
            <button className="btn-primary" onClick={handleOpenNewModal}>{t.btnNewTecnica}</button>
          </div>

          {loading ? <p>{t.loadingTecnicas}</p> : (
            <div className="tecnicas-grid">
              {tecnicas.map(tech => (
                <div key={tech.id} className="tecnica-card">
                  <div className="tecnica-info">
                    <h3>{tech.nombre}</h3>
                    <span className={`badge-cinturon cinturon-${tech.nivel_cinturon?.toLowerCase()}`}>
                      {getBeltLabel(tech.nivel_cinturon)}
                    </span>
                    {tech.tiene_video ? (
                      <div style={{ marginTop: '0.5rem' }}>
                        <div className="video-status has-video" style={{ marginBottom: '0.5rem' }}>
                          {t.hasVideoStatus}
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
                      </div>
                    ) : (
                      <div className="video-status no-video">{t.noVideoStatus}</div>
                    )}
                  </div>
                  <div className="tecnica-actions">
                    <button
                      className="btn-icon theory-btn"
                      onClick={() => setTheoryModalTecnica(tech)}
                    >
                      📖 Ver Teoría
                    </button>
                    <button className="btn-icon edit" onClick={() => handleEdit(tech)}>{t.btnEdit}</button>
                    <button className="btn-icon delete" onClick={() => handleDelete(tech.id)}>{t.btnDelete}</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal de Detalle de Keypoints del Alumno */}
      {selectedAlumnoDetail && (
        <div className="modal-overlay">
          <div className="modal-content glass-panel" style={{ maxWidth: '500px', padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--brand-red)' }}>
              Detalle Biomecánico — {selectedAlumnoDetail.alumno.nombre_completo}
            </h3>
            <p style={{ fontSize: '0.9rem', margin: '0 0 1rem 0' }}>
              Técnica: <strong>{selectedAlumnoDetail.evalItem.tecnica_nombre}</strong>
            </p>

            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#4da6ff' }}>
                Resumen de la Evaluación:
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.25rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span>Similitud:</span>
                <strong style={{ color: '#69db7c' }}>{parseFloat(selectedAlumnoDetail.evalItem.porcentaje_similitud || 0).toFixed(1)}%</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.25rem 0' }}>
                <span>Estado:</span>
                <strong>{selectedAlumnoDetail.evalItem.estado}</strong>
              </div>
            </div>

            <div style={{ fontSize: '0.85rem', lineHeight: '1.4', marginBottom: '1.5rem', background: 'rgba(255,255,255,0.04)', padding: '0.8rem', borderRadius: '6px' }}>
              <strong>Retroalimentación Automática IA:</strong>
              <p style={{ margin: '0.3rem 0 0 0', opacity: 0.8 }}>
                {selectedAlumnoDetail.evalItem.feedback_gemini_es || selectedAlumnoDetail.evalItem.feedback_gemini_pt || "Sin feedback disponible."}
              </p>
            </div>

            <button className="btn-primary" onClick={() => setSelectedAlumnoDetail(null)} style={{ width: '100%' }}>
              Cerrar Detalle
            </button>
          </div>
        </div>
      )}

      {/* Modal Form (Crear / Editar Técnica) */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-panel" style={{ maxWidth: '560px', maxHeight: '90vh', overflowY: 'auto' }}>
            <h3>{editingId ? t.modalEditTitle : t.modalNewTitle}</h3>
            
            <form onSubmit={handleSave}>
              <div className="form-group">
                <label>{t.labelTecnicaNombre}</label>
                <input required type="text" name="nombre" value={formData.nombre} onChange={handleChange} placeholder={t.placeholderTecnicaNombre} />
              </div>

              <div className="form-group">
                <label>{t.labelNivelCinturon}</label>
                <select name="nivel_cinturon" value={formData.nivel_cinturon} onChange={handleChange}>
                  {OPACIONES_CINTURON.map(nivel => (
                    <option key={nivel} value={nivel}>
                      {t.belts[nivel] || nivel}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Manual del Maestro (Teoría RAG)</label>
                <textarea 
                  name="teoria" 
                  value={formData.teoria} 
                  onChange={handleChange} 
                  placeholder="Ej. En el Armbar, la cadera debe estar pegada al hombro..."
                  rows="3"
                  style={{ width: '100%', background: 'rgba(255,255,255,0.05)', color: 'white', padding: '0.6rem', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px' }}
                />
                <span style={{fontSize: '0.75rem', opacity: 0.7, color: 'var(--brand-red)'}}>* La IA de Gemini leerá esto para dar feedback preciso a tus alumnos.</span>
              </div>

              <div className="form-group">
                <label>{editingId && previewUrl ? t.btnReplaceVideo : t.btnUploadVideo}</label>
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
                  {selectedFile ? ` Video: ${selectedFile.name}` : (editingId && previewUrl ? t.btnReplaceVideo : t.btnUploadVideo)}
                </button>
              </div>

              {previewUrl && (
                <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                    {t.modalPreviewTitle}
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
                  {t.btnClose}
                </button>
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? "Guardando..." : "Guardar Técnica"}
                </button>
              </div>
            </form>
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
    </div>
  );
}
