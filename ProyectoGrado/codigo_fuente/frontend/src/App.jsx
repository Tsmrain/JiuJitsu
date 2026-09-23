import { useState, useEffect } from 'react'
import './App.css'
import VideoUpload from './pages/VideoUpload'
import FeedbackView from './pages/FeedbackView'
import ProgressRing from './components/ProgressRing'

function App() {
  const [appState, setAppState] = useState('IDLE'); // IDLE, UPLOADING, PROCESSING, FEEDBACK
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState(null);

  const handleUploadStart = async (file) => {
    console.log("Iniciando subida de:", file.name);
    setAppState('UPLOADING');
    setUploadProgress(10); // Show initial progress

    const formData = new FormData();
    formData.append("video", file);

    try {
      // 1. Llamada real al backend para validar SPAM
      const response = await fetch("http://localhost:8000/api/v1/evaluaciones/validar-spam", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'El video fue rechazado por la IA.'}`);
        setAppState('IDLE');
        setUploadProgress(0);
        return; // Detener flujo
      }

      // Si es válido, simulamos el resto del proceso por ahora
      const uploadInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 100) {
            clearInterval(uploadInterval);
            startProcessing();
            return 100;
          }
          return prev + 10;
        });
      }, 200);

    } catch (error) {
      console.error("Error validando el video:", error);
      alert("Hubo un error de conexión con el servidor (Filtro SPAM). Asegúrate de que el backend esté corriendo.");
      setAppState('IDLE');
      setUploadProgress(0);
    }
  };

  const startProcessing = () => {
    setAppState('PROCESSING');
    
    // Simular el tiempo de inferencia de YOLO y Gemini
    setTimeout(() => {
      setResult({
        similitud: 88.5,
        feedback: "Tu postura base es excelente y los keypoints de tu cadera coinciden con el patrón.\n\nSin embargo, el ángulo de tu brazo derecho durante el agarre está ligeramente desviado (15 grados más abierto que el profesor). Esto reduce la palanca. Ajusta el codo más cerca de tus costillas para finalizar el movimiento."
      });
      setAppState('FEEDBACK');
    }, 3000);
  };

  const handleReset = () => {
    setAppState('IDLE');
    setResult(null);
    setUploadProgress(0);
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="brand">
          <img src="/logo.jpeg" alt="Corpo e Mente Logo" className="brand-logo" />
          <span className="brand-text">
            Corpo e Mente <span className="brand-accent">IA</span>
          </span>
        </div>
        <div className="user-nav">
          <span style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>Humberto Tavares Academy</span>
          <div style={{
            width: '32px', height: '32px', borderRadius: '50%', 
            background: 'var(--glass-bg)', border: '1px solid var(--glass-border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 'bold'
          }}>
            A
          </div>
        </div>
      </header>

      <main style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {appState === 'IDLE' && (
          <VideoUpload onUploadStart={handleUploadStart} />
        )}

        {(appState === 'UPLOADING' || appState === 'PROCESSING') && (
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem'}}>
            <ProgressRing 
              value={appState === 'UPLOADING' ? uploadProgress : 100} 
              statusText={appState === 'UPLOADING' ? 'Subiendo video...' : 'IA Analizando Biomecánica...'} 
            />
            {appState === 'PROCESSING' && (
              <p style={{color: 'var(--text-secondary)', maxWidth: '400px', textAlign: 'center'}}>
                Extrayendo keypoints con YOLO y comparando similitud vectorial en Qdrant...
              </p>
            )}
          </div>
        )}

        {appState === 'FEEDBACK' && (
          <FeedbackView result={result} onReset={handleReset} />
        )}
      </main>
    </div>
  )
}

export default App
