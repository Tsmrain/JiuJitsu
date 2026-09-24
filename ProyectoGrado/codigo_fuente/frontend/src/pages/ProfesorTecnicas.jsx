import { useState, useEffect, useRef } from 'react';
import './ProfesorTecnicas.css';
import { useTranslation } from '../i18n/translations';

const OPACIONES_CINTURON = ['Blanco', 'Azul', 'Morado', 'Marrón', 'Negro'];

export default function ProfesorTecnicas({ user, onClose }) {
  const [tecnicas, setTecnicas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    nombre: '',
    nivel_cinturon: 'Blanco'
  });
  const [editingId, setEditingId] = useState(null);

  // File upload & preview state inside form
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const { t, getBeltLabel } = useTranslation(user?.idioma_preferido);

  useEffect(() => {
    fetchTecnicas();
  }, [user?.user_id]);

  const fetchTecnicas = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/tecnicas?profesor_id=${user?.user_id}`);
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

  const handleOpenNewModal = () => {
    setEditingId(null);
    setFormData({ nombre: '', nivel_cinturon: 'Blanco' });
    setSelectedFile(null);
    setPreviewUrl(null);
    setShowModal(true);
  };

  const handleEdit = (tech) => {
    setEditingId(tech.id);
    setFormData({
      nombre: tech.nombre,
      nivel_cinturon: tech.nivel_cinturon
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
      // 1. Guardar metadatos de la técnica
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });

      if (!res.ok) {
        alert("Error guardando la técnica.");
        setSaving(false);
        return;
      }

      const savedTecnica = await res.json();
      const tecnicaId = savedTecnica.id || editingId;

      // 2. Si se seleccionó un video de referencia, subirlo inmediatamente
      if (selectedFile && tecnicaId) {
        const body = new FormData();
        body.append("video", selectedFile);
        body.append("profesor_id", user.user_id);

        const videoRes = await fetch(`http://localhost:8000/api/v1/tecnicas/${tecnicaId}/video`, {
          method: "POST",
          body
        });

        if (!videoRes.ok) {
          alert("La técnica se guardó pero hubo un error al subir el video.");
        }
      }

      setShowModal(false);
      setEditingId(null);
      setSelectedFile(null);
      setPreviewUrl(null);
      setFormData({ nombre: '', nivel_cinturon: 'Blanco' });
      fetchTecnicas();
    } catch (err) {
      console.error("Error guardando técnica", err);
      alert("Error de conexión guardando técnica.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(t.confirmDeleteTecnica)) return;
    try {
      await fetch(`http://localhost:8000/api/v1/tecnicas/${id}`, { method: "DELETE" });
      fetchTecnicas();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="profesor-tecnicas-container glass-panel">
      <div className="tecnicas-header">
        <h2>{t.tecnicasTitle}</h2>
        <div>
          <button className="btn-primary" onClick={handleOpenNewModal}>{t.btnNewTecnica}</button>
          <button className="btn-secondary" onClick={onClose} style={{ marginLeft: '1rem' }}>{t.btnClose}</button>
        </div>
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
                  <div className="video-status has-video">{t.hasVideoStatus}</div>
                ) : (
                  <div className="video-status no-video">{t.noVideoStatus}</div>
                )}
              </div>
              <div className="tecnica-actions">
                <button className="btn-icon edit" onClick={() => handleEdit(tech)}>{t.btnEdit}</button>
                <button className="btn-icon delete" onClick={() => handleDelete(tech.id)}>{t.btnDelete}</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Form Modal (Crear / Editar Técnica con Video Integrado) */}
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

              {/* Campo e Previsualización del Video de Referencia */}
              <div className="form-group" style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
                <label style={{ color: 'var(--brand-red)', fontWeight: 'bold', marginBottom: '0.5rem', display: 'block' }}>
                   {t.labelVideoReferencia}
                </label>

                {previewUrl ? (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                    <video 
                      src={previewUrl} 
                      controls 
                      autoPlay 
                      loop 
                      muted 
                      style={{ width: '100%', maxHeight: '220px', borderRadius: '8px', backgroundColor: '#000' }}
                    />
                    <div style={{ display: 'flex', gap: '0.5rem', width: '100%' }}>
                      <button 
                        type="button" 
                        className="btn-secondary"
                        style={{ flex: 1, fontSize: '0.8rem', padding: '0.4rem' }}
                        onClick={() => fileInputRef.current.click()}
                      >
                        {t.btnChangeVideo}
                      </button>
                      {selectedFile && (
                        <button 
                          type="button" 
                          className="btn-secondary"
                          style={{ flex: 1, fontSize: '0.8rem', padding: '0.4rem', borderColor: 'rgba(239, 68, 68, 0.5)', color: '#f87171' }}
                          onClick={() => { setSelectedFile(null); setPreviewUrl(null); }}
                        >
                          ✕ Quitar
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div 
                    onClick={() => fileInputRef.current.click()}
                    style={{
                      border: '2px dashed rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      padding: '1.5rem',
                      textAlign: 'center',
                      cursor: 'pointer',
                      background: 'rgba(0,0,0,0.2)',
                      transition: 'border-color 0.2s'
                    }}
                  >
                    <div style={{ fontSize: '1.75rem', marginBottom: '0.25rem' }}></div>
                    <span style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {t.dropVideoHint}
                    </span>
                    <span style={{ display: 'inline-block', marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--brand-red)', fontWeight: 'bold' }}>
                      {t.btnSelectVideo}
                    </span>
                  </div>
                )}

                {/* Input oculto de archivo de video */}
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  style={{ display: 'none' }} 
                  accept="video/mp4,video/x-m4v,video/*" 
                  onChange={handleFileChange}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>{t.btnCancel}</button>
                <button type="submit" disabled={saving} className="btn-primary">
                  {saving ? t.savingTecnica : t.btnSave}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
