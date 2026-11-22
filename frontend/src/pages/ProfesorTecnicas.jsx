import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './ProfesorTecnicas.css';
import TheoryManagerModal from '../components/TheoryManagerModal';
import GlobalKnowledgeModal from '../components/GlobalKnowledgeModal';
import SelectorPersonaVideo from '../components/SelectorPersonaVideo';
import { incluirEstadoPatrones } from '../api/tecnicas';
import { getTranslation } from '../i18n/translations';
import { API_BASE } from '../api/config';

const OPACIONES_CINTURON = ['Blanco', 'Azul', 'Morado', 'Marrón', 'Negro'];

const BELT_KEYS = {
  'Blanco': 'whiteBelt',
  'Azul': 'blueBelt',
  'Morado': 'purpleBelt',
  'Marrón': 'brownBelt',
  'Negro': 'blackBelt',
  'White': 'whiteBelt',
  'Blue': 'blueBelt',
  'Purple': 'purpleBelt',
  'Brown': 'brownBelt',
  'Black': 'blackBelt',
};

function normalizarNombreVisible(nombre) {
  return String(nombre || '').trim().replace(/\s+/g, ' ');
}

function calcularClaveCanonicaTecnica(nombre) {
  return normalizarNombreVisible(nombre)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '');
}

export default function ProfesorTecnicas({ user, onClose, idioma }) {
  const t = (key) => getTranslation(idioma, key);
  const getBeltLabel = (nivel) => {
    const key = BELT_KEYS[nivel];
    return key ? t(key) : nivel;
  };
  const [activeTab, setActiveTab] = useState('alumnos'); // 'alumnos' (default) | 'pases' | 'tecnicas'
  const [tecnicas, setTecnicas] = useState([]);
  const [alumnos, setAlumnos] = useState([]);
  const [pendientes, setPendientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingAlumnos, setLoadingAlumnos] = useState(false);
  const [loadingPendientes, setLoadingPendientes] = useState(false);
  const [activandoId, setActivandoId] = useState(null);
  const [activacionSuccess, setActivacionSuccess] = useState(null);
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [showGlobalKnowledge, setShowGlobalKnowledge] = useState(false);
  const [personaSelection, setPersonaSelection] = useState(null);
  const [personaSelectionError, setPersonaSelectionError] = useState('');
  const [brokenVideoIds, setBrokenVideoIds] = useState({});
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
      const res = await fetch(`${API_BASE}/api/v1/tecnicas?profesor_id=${user?.user_id}`, {
        headers: { "Authorization": `Bearer ${user?.token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setBrokenVideoIds({});
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
      const res = await fetch(`${API_BASE}/api/v1/auth/alumnos${sucursalQuery}`, {
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

  const fetchPendientes = async () => {
    setLoadingPendientes(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/alumnos/pendientes`, {
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPendientes(data);
      }
    } catch (e) {
      console.error("Error loading pending students:", e);
    } finally {
      setLoadingPendientes(false);
    }
  };

  const handleActivarPase = async (alumnoId, alumnoNombre) => {
    setActivandoId(alumnoId);
    setActivacionSuccess(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/alumnos/${alumnoId}/activar`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${user.token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ dias: 30 })
      });
      if (res.ok) {
        const msg = `${t('passActivatedSuccess')} (${alumnoNombre || t('studentLabel') || 'Alumno'})`;
        setActivacionSuccess(msg);
        alert(msg);
        await fetchPendientes();
        await fetchAlumnos();
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(errData.detail || t('errorActivatingPass') || "Error activando pase.");
      }
    } catch (e) {
      console.error("Error activando pase:", e);
      alert(t('connectionError') || "Error de conexión al activar pase.");
    } finally {
      setActivandoId(null);
    }
  };

  const fetchEvaluacionesAlumno = async (alumnoId) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/alumnos/${alumnoId}/evaluaciones`, {
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
      await fetchPendientes();
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
        alert(t('invalidVideoFile') || "Por favor selecciona un archivo de video válido.");
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const claveNombreActual = calcularClaveCanonicaTecnica(formData.nombre);
  const nombreInvalido = formData.nombre.trim().length > 0 && claveNombreActual.length === 0;
  const tecnicaDuplicada = claveNombreActual
    ? tecnicas.find(
        (tech) =>
          String(tech.id) !== String(editingId || '') &&
          calcularClaveCanonicaTecnica(tech.nombre) === claveNombreActual
      )
    : null;
  const duplicateErrorMessage = tecnicaDuplicada
    ? `${t('duplicateTechniqueError') || 'Ya existe una técnica registrada con ese nombre'}: "${tecnicaDuplicada.nombre}"`
    : '';

  const handleSave = async (e) => {
    e.preventDefault();
    const nombreVisible = normalizarNombreVisible(formData.nombre);
    const claveCanonica = calcularClaveCanonicaTecnica(nombreVisible);
    if (!claveCanonica) {
      alert(t('techniqueNameInvalid') || 'El nombre de la técnica debe contener al menos una letra o número.');
      return;
    }
    if (tecnicaDuplicada) {
      alert(duplicateErrorMessage);
      return;
    }
    if (!selectedFile && !previewUrl) {
      alert(t('mustUploadReferenceVideo') || 'Debes subir el video de referencia para esta técnica.');
      return;
    }
    setSaving(true);

    try {
      if (!editingId) {
        // Nueva técnica: primero procesar el video y obtener el primer frame
        const frameData = new FormData();
        frameData.append("video", selectedFile);
        const frameRes = await fetch(`${API_BASE}/api/v1/evaluaciones/primer-frame`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${user.token}` },
          body: frameData
        });
        if (!frameRes.ok) {
          const err = await frameRes.json().catch(() => ({}));
          throw new Error(err.detail || t('errorExtractingInitialFrame') || "Error procesando el video. No se pudo extraer el fotograma inicial.");
        }
        const frame = await frameRes.json();
        setPersonaSelection({
          tecnicaId: null,
          pendingTecnica: {
            nombre: nombreVisible,
            nivel_cinturon: formData.nivel_cinturon,
            mensaje_profesor: (formData.mensaje_profesor || "").trim(),
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
          const frameRes = await fetch(`${API_BASE}/api/v1/evaluaciones/primer-frame`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${user.token}` },
            body: frameData
          });
          if (!frameRes.ok) {
            const err = await frameRes.json().catch(() => ({}));
            throw new Error(err.detail || t('errorProcessingVideo') || "Error procesando el video.");
          }
          const frame = await frameRes.json();
          setPersonaSelection({
            tecnicaId: editingId,
            pendingTecnica: {
              nombre: nombreVisible,
              nivel_cinturon: formData.nivel_cinturon,
              mensaje_profesor: (formData.mensaje_profesor || "").trim(),
            },
            sessionData: frame,
            selectedIdx: frame.personas?.length === 1 ? frame.personas[0].idx : null,
          });
          setPersonaSelectionError('');
          setShowModal(false);
        } else {
          // Solo actualizar datos de texto de la técnica existente
          const res = await fetch(`${API_BASE}/api/v1/tecnicas/${editingId}`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${user.token}`
            },
            body: JSON.stringify({
              nombre: nombreVisible,
              nivel_cinturon: formData.nivel_cinturon,
              mensaje_profesor: (formData.mensaje_profesor || "").trim(),
            })
          });
          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || t('errorUpdatingTechnique') || "Error actualizando técnica.");
          }
          alert(t('techniqueUpdatedSuccess') || "Técnica actualizada exitosamente.");
          setShowModal(false);
          fetchTecnicas();
        }
      }
    } catch (err) {
      console.error(err);
      alert(err.message || t('connectionError') || "Error de conexión al guardar la técnica.");
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
        const createRes = await fetch(`${API_BASE}/api/v1/tecnicas`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${user.token}`
          },
          body: JSON.stringify(pendingTecnica)
        });
        if (!createRes.ok) {
          const err = await createRes.json().catch(() => ({}));
          throw new Error(err.detail || t('errorCreatingTechnique') || "Error creando técnica en la base de datos.");
        }
        const savedTecnica = await createRes.json();
        targetTecnicaId = savedTecnica.id;
        createdTecnicaId = savedTecnica.id;
      } else if (targetTecnicaId && pendingTecnica) {
        // Si estamos editando, actualizar campos
        const updateRes = await fetch(`${API_BASE}/api/v1/tecnicas/${targetTecnicaId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${user.token}`
          },
          body: JSON.stringify(pendingTecnica)
        });
        if (!updateRes.ok) {
          const err = await updateRes.json().catch(() => ({}));
          throw new Error(err.detail || t('errorUpdatingTechnique') || "Error actualizando técnica.");
        }
      }

      // 2. Confirmar persona seleccionada en la sesión
      const selectionRes = await fetch(`${API_BASE}/api/v1/evaluaciones/${sessionData.session_id}/seleccionar-persona`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${user.token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ persona_idx: selectedIdx }),
      });
      if (!selectionRes.ok) {
        const err = await selectionRes.json().catch(() => ({}));
        throw new Error(err.detail || t('couldNotConfirmPerson') || 'No se pudo confirmar la persona seleccionada.');
      }

      // 3. Registrar el patrón biomecánico
      const patronForm = new FormData();
      patronForm.append('session_id', sessionData.session_id);
      patronForm.append('persona_idx', String(selectedIdx));
      const patronRes = await fetch(`${API_BASE}/api/v1/tecnicas/${targetTecnicaId}/patron`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${user.token}` },
        body: patronForm,
      });
      if (!patronRes.ok) {
        const err = await patronRes.json().catch(() => ({}));
        throw new Error(err.detail || t('couldNotRegisterPattern') || 'No se pudo registrar el patrón biomecánico.');
      }
      const patron = await patronRes.json();
      alert(`✅ ${t('activeBiomechanicalPattern')}: ${patron.total_frames} ${t('frames')}.`);
      setPersonaSelection(null);
      fetchTecnicas();
    } catch (err) {
      // Si falló el registro del patrón para una técnica recién creada, eliminarla como rollback
      if (createdTecnicaId) {
        try {
          await fetch(`${API_BASE}/api/v1/tecnicas/${createdTecnicaId}`, {
            method: 'DELETE',
            headers: { "Authorization": `Bearer ${user.token}` }
          });
        } catch (_) {}
      }
      setPersonaSelectionError(err.message || t('errorRegisteringPattern') || 'Error registrando el patrón.');
    } finally {
      setConfirmingPersona(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm(t('confirmDeleteTechnique') || '¿Estás seguro de que deseas eliminar esta técnica?')) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/tecnicas/${id}`, {
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
      <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <button
          onClick={() => setActiveTab('alumnos')}
          style={{
            flex: 1, padding: '0.85rem', background: 'none', border: 'none',
            borderBottom: activeTab === 'alumnos' ? '3px solid var(--brand-red)' : '3px solid transparent',
            color: activeTab === 'alumnos' ? 'white' : 'var(--text-secondary)',
            fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
            minHeight: '44px'
          }}
        >
          {t('studentsTab')} ({alumnos.length})
        </button>
        <button
          data-testid="tab-pases-pendientes"
          onClick={() => { setActiveTab('pases'); fetchPendientes(); }}
          style={{
            flex: 1, padding: '0.85rem', background: 'none', border: 'none',
            borderBottom: activeTab === 'pases' ? '3px solid var(--brand-red)' : '3px solid transparent',
            color: activeTab === 'pases' ? 'white' : 'var(--text-secondary)',
            fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
            minHeight: '44px'
          }}
        >
          🥋 {t('pendingPassesTab')} ({pendientes.length})
        </button>
        <button
          onClick={() => setActiveTab('tecnicas')}
          style={{
            flex: 1, padding: '0.85rem', background: 'none', border: 'none',
            borderBottom: activeTab === 'tecnicas' ? '3px solid var(--brand-red)' : '3px solid transparent',
            color: activeTab === 'tecnicas' ? 'white' : 'var(--text-secondary)',
            fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
            minHeight: '44px'
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
                          const estadoLabel = similitud >= 85 ? t('excellent') : (similitud >= 70 ? t('good') : t('needsWork'));
                          const fechaLocale = idioma === 'pt' ? 'pt-BR' : idioma === 'en' ? 'en-US' : 'es-ES';
                          const fecha = evalItem.fecha_evaluacion
                            ? new Date(evalItem.fecha_evaluacion).toLocaleDateString(fechaLocale, { day: '2-digit', month: 'short', year: 'numeric' })
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
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.25rem' }}>
                                  <strong style={{ fontSize: '0.95rem', color: 'white' }}>{evalItem.tecnica_nombre}</strong>
                                  <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
                                    {evalItem.sucursal_nombre && (
                                      <span style={{
                                        fontSize: '0.7rem',
                                        padding: '0.15rem 0.45rem',
                                        borderRadius: '4px',
                                        background: 'rgba(255,255,255,0.08)',
                                        color: 'rgba(255,255,255,0.7)',
                                        border: '1px solid rgba(255,255,255,0.15)'
                                      }}>
                                        📍 {evalItem.sucursal_nombre}
                                      </span>
                                    )}
                                    <span style={{
                                      fontSize: '0.75rem', fontWeight: 'bold', padding: '0.15rem 0.5rem', borderRadius: '4px',
                                      background: `${getScoreColor(similitud)}22`, color: getScoreColor(similitud),
                                      border: `1px solid ${getScoreColor(similitud)}`
                                    }}>
                                      {estadoLabel}
                                    </span>
                                  </div>
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
                                  {evalItem.feedback_summary || (evalItem.feedback_gemini_es ? evalItem.feedback_gemini_es.split('.')[0] : t('aiTechnicalAnalysis'))}
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

      {/* TAB 2: PASES DE TATAMI PENDIENTES */}
      {activeTab === 'pases' && (
        <div>
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', color: 'white', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              🥋 {t('pendingPassesHeading')}
            </h3>
            <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              {t('pendingPassesDesc')}
            </p>
          </div>

          {activacionSuccess && (
            <div style={{
              background: 'rgba(34, 197, 94, 0.15)',
              border: '1px solid #22c55e',
              color: '#4ade80',
              padding: '0.85rem 1.25rem',
              borderRadius: '8px',
              marginBottom: '1rem',
              fontWeight: 'bold',
              textAlign: 'center'
            }}>
              {activacionSuccess}
            </div>
          )}

          {loadingPendientes ? (
            <p>{t('loadingStudents')}</p>
          ) : pendientes.length === 0 ? (
            <div className="glass-panel" style={{ padding: '2.5rem 1.5rem', textAlign: 'center', borderRadius: '12px', color: 'var(--text-secondary)' }}>
              <p style={{ margin: 0, fontSize: '1.1rem' }}>🎉 {t('noPendingPasses')}</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 320px), 1fr))', gap: '1.25rem' }}>
              {pendientes.map(alumno => (
                <div
                  key={alumno.id}
                  className="glass-panel"
                  style={{
                    padding: '1.25rem',
                    borderRadius: '12px',
                    border: '1px solid rgba(255,255,255,0.12)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '1rem'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                      <div style={{
                        width: '46px',
                        height: '46px',
                        borderRadius: '50%',
                        background: 'var(--brand-red)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        fontSize: '1.2rem',
                        color: 'white',
                        flexShrink: 0
                      }}>
                        {alumno.avatar_url ? (
                          <img src={alumno.avatar_url} alt={alumno.nombre_completo} style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
                        ) : (
                          (alumno.nombre_completo ? alumno.nombre_completo[0].toUpperCase() : 'A')
                        )}
                      </div>
                      <div style={{ overflow: 'hidden' }}>
                        <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'white', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                          {alumno.nombre_completo}
                        </h4>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          @{alumno.username} • {alumno.sucursal_nombre}
                        </span>
                      </div>
                    </div>

                    <div style={{
                      background: 'rgba(255,255,255,0.03)',
                      padding: '0.75rem',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.4rem'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>{t('studentStatus')}:</span>
                        <span style={{
                          fontWeight: 'bold',
                          color: alumno.estado_suscripcion === 'activo' ? '#4ade80' : (alumno.estado_suscripcion === 'expirado' ? '#ff6b6b' : '#ffd43b')
                        }}>
                          {alumno.estado_suscripcion === 'activo' ? t('activeStatus') : (alumno.estado_suscripcion === 'expirado' ? t('expiredStatus') : t('pendingStatus'))}
                        </span>
                      </div>
                      {alumno.fecha_registro && (
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: 'var(--text-secondary)' }}>{t('registrationDate')}:</span>
                          <span>{new Date(alumno.fecha_registro).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <button
                    data-testid="btn-activar-pase"
                    type="button"
                    className="btn-primary"
                    disabled={activandoId === alumno.id}
                    onClick={() => handleActivarPase(alumno.id, alumno.nombre_completo)}
                    style={{
                      width: '100%',
                      minHeight: '44px',
                      padding: '0.75rem 1rem',
                      fontSize: '0.95rem',
                      fontWeight: 'bold',
                      borderRadius: '8px',
                      cursor: activandoId === alumno.id ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.5rem',
                      background: '#22c55e',
                      borderColor: '#22c55e',
                      color: 'white',
                      boxShadow: '0 0 15px rgba(34, 197, 94, 0.4)'
                    }}
                  >
                    {activandoId === alumno.id ? `⏳ ${t('activating') || 'Activando...'}` : t('activatePass30Days')}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: MY TECHNIQUES & VIDEOS */}
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
                        {tech.video_url && !brokenVideoIds[tech.id] ? (
                          <div className="card-video-preview" style={{ marginTop: '0.5rem' }}>
                            <video 
                              src={tech.video_url} 
                              controls 
                              playsInline
                              preload="metadata"
                              onError={() => setBrokenVideoIds(prev => ({ ...prev, [tech.id]: true }))}
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
                        ) : (
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => handleEdit(tech)}
                            style={{ marginTop: '0.45rem', width: '100%', fontSize: '0.8rem', padding: '0.5rem 0.75rem' }}
                          >
                            📹 {t('reuploadReferenceVideo')}
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="video-status no-video">{t('noVideoYet')}</div>
                    )}
                  </div>
                  <div className="tecnica-actions">
                    <button
                      data-testid="open-theory-modal-btn"
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
            <h3>{editingId ? t('editTechnique') : t('newTechnique')}</h3>
            
            <form onSubmit={handleSave}>
              <div className="form-group">
                <label>{t('techniqueName')}</label>
                <input required type="text" name="nombre" value={formData.nombre} onChange={handleChange} placeholder={t('techniqueNamePlaceholder') || "Ej: Armbar desde la Guardia"} />
                {tecnicaDuplicada && (
                  <p style={{ color: '#f87171', fontSize: '0.82rem', marginTop: '0.4rem' }}>
                    {duplicateErrorMessage}
                  </p>
                )}
                {!tecnicaDuplicada && nombreInvalido && (
                  <p style={{ color: '#f87171', fontSize: '0.82rem', marginTop: '0.4rem' }}>
                    {t('techniqueNameInvalid') || 'El nombre de la técnica debe contener al menos una letra o número.'}
                  </p>
                )}
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
                  placeholder={t('instructorMessagePlaceholder') || "Explica con tus propias palabras cómo ejecutar esta técnica."}
                  rows={5}
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
                  {selectedFile ? ` 📹 ${selectedFile.name}` : (editingId && previewUrl ? t('replaceVideo') : t('uploadVideo'))}
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
                <button type="submit" className="btn-primary" disabled={saving || Boolean(tecnicaDuplicada) || nombreInvalido}>
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
          idioma={idioma}
          onClose={() => setTheoryModalTecnica(null)}
        />
      )}
      {showGlobalKnowledge && <GlobalKnowledgeModal user={user} idioma={idioma} onClose={() => setShowGlobalKnowledge(false)} />}

      {selectedAlumnoDetail && (
        <div className="modal-overlay" role="dialog" aria-modal="true" onClick={() => setSelectedAlumnoDetail(null)}>
          <div className="modal-content glass-panel" style={{ maxWidth: '650px', maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)', letterSpacing: '1px' }}>
                  {t('evaluationDetails')}
                </span>
                <h3 style={{ margin: '0.25rem 0 0 0', fontSize: '1.25rem', color: 'white' }}>
                  {selectedAlumnoDetail.evalItem.tecnica_nombre}
                </h3>
                <small style={{ color: 'var(--text-secondary)' }}>
                  {t('studentLabel') || 'Alumno'}: {selectedAlumnoDetail.alumno.nombre_completo}
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
                {selectedAlumnoDetail.evalItem.porcentaje_similitud >= 85 ? t('excellent') : selectedAlumnoDetail.evalItem.porcentaje_similitud >= 70 ? t('good') : t('needsWork')} ({Math.round(selectedAlumnoDetail.evalItem.porcentaje_similitud)}%)
              </div>
            </div>

            {selectedAlumnoDetail.evalItem.feedback_summary && (
              <div style={{ marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                  {t('summary')}
                </span>
                <strong style={{ color: 'white', fontSize: '1.05rem' }}>
                  {selectedAlumnoDetail.evalItem.feedback_summary}
                </strong>
              </div>
            )}

            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.5rem' }}>
                {t('fullTechnicalFeedback')}
              </span>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)', color: '#d1d5db', lineHeight: 1.6 }}>
                <ReactMarkdown>
                  {selectedAlumnoDetail.evalItem.feedback_gemini_es || selectedAlumnoDetail.evalItem.feedback_gemini_pt || t('noDetailedFeedback')}
                </ReactMarkdown>
              </div>
            </div>

            <div className="modal-actions" style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
              <button type="button" className="btn-secondary" onClick={() => setSelectedAlumnoDetail(null)}>
                {t('close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
