import { useState } from 'react';
import './VideoUpload.css';

export default function VideoUpload({ onUploadStart }) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);

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
    // Aceptamos video/mp4, video/quicktime, etc.
    if (selectedFile.type.startsWith('video/')) {
      setFile(selectedFile);
    } else {
      alert("Por favor selecciona un archivo de video válido.");
    }
  };

  const handleSubmit = () => {
    if (file) {
      onUploadStart(file);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h2>Sube tu ejecución</h2>
        <p>Nuestro modelo biomecánico YOLO evaluará tu técnica.</p>
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
