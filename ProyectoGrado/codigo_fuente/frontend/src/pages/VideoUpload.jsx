import { useState } from 'react';
import './VideoUpload.css';

const TECNICAS_DISPONIBLES = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    nombre: "Armbar desde Guardia Cerrada",
    categoria: "Finalizaciones",
    profesorRef: "Mestre Humberto Tavares",
    descripcion: "Palanca de brazo clásica aplicando control hip-control y rotación de muñeca."
  },
  {
    id: "22222222-2222-2222-2222-222222222222",
    nombre: "Estrangulamiento Triángulo (Sankaku-Jime)",
    categoria: "Finalizaciones",
    profesorRef: "Mestre Humberto Tavares",
    descripcion: "Cierre de piernas envolviendo cuello y brazo del oponente con presión de aductores."
  },
  {
    id: "33333333-3333-3333-3333-333333333333",
    nombre: "Pase de Guardia Torreando (Passagem Torreadora)",
    categoria: "Pases de Guardia",
    profesorRef: "Mestre Humberto Tavares",
    descripcion: "Control de pantorrillas con desplazamiento lateral rápido y fijación de cadera."
  }
];

export default function VideoUpload({ onUploadStart }) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [selectedTecnica, setSelectedTecnica] = useState(TECNICAS_DISPONIBLES[0]);

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
      alert("Por favor selecciona un archivo de video válido.");
    }
  };

  const handleSubmit = () => {
    if (file && selectedTecnica) {
      onUploadStart(file, selectedTecnica);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h2>Sube tu ejecución</h2>
        <p>Selecciona la técnica que deseas practicar y compara tu movimiento contra el patrón del profesor.</p>
      </div>

      {/* Selector de Técnica */}
      <div className="tecnica-selector-card glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', borderRadius: '12px' }}>
        <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 'bold', color: 'var(--brand-red)', marginBottom: '0.5rem' }}>
          1. SELECCIONA LA TÉCNICA A EVALUAR:
        </label>
        <select 
          value={selectedTecnica.id}
          onChange={(e) => setSelectedTecnica(TECNICAS_DISPONIBLES.find(t => t.id === e.target.value))}
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
          {TECNICAS_DISPONIBLES.map(t => (
            <option key={t.id} value={t.id} style={{ background: '#111', color: 'white' }}>
              {t.nombre} ({t.categoria})
            </option>
          ))}
        </select>
        
        <div className="profesor-ref-info" style={{ marginTop: '0.75rem', fontSize: '0.85rem', opacity: 0.85, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ background: 'var(--brand-red)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 'bold', fontSize: '0.75rem' }}>
            PATRÓN PROFESOR
          </span>
          <span>{selectedTecnica.profesorRef} - {selectedTecnica.descripcion}</span>
        </div>
      </div>

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
            <span className="drop-text">Arrastra tu video aquí o <strong>haz clic para explorar</strong></span>
            <span className="drop-hint">MP4, MOV o WebM (Máx 50MB)</span>
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
              <button type="button" className="btn-secondary" onClick={() => setFile(null)}>Cambiar</button>
              <button type="button" className="btn-primary" onClick={handleSubmit}>Analizar Técnica</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
