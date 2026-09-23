import { useState } from 'react'
import './App.css'
import VideoUpload from './pages/VideoUpload'
import FeedbackView from './pages/FeedbackView'
import AdminSucursales from './pages/AdminSucursales'
import ProgressRing from './components/ProgressRing'
import LoginModal from './components/LoginModal'

function App() {
  const [appState, setAppState] = useState('IDLE'); // IDLE, UPLOADING, PROCESSING, FEEDBACK, ADMIN_PANEL
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [selectedTecnica, setSelectedTecnica] = useState(null);

  // Estado de Autenticación / Roles (Default: Alumno)
  const [user, setUser] = useState({
    nombre_completo: "Alumno Santiago",
    rol: "alumno", // 'alumno', 'profesor', 'admin'
    email: "santiago@corpocmente.com",
    sucursal_nombre: "Corpo e Mente - Sede Principal"
  });
  const [isLoginOpen, setIsLoginOpen] = useState(false);

  const handleUploadStart = async (file, tecnica) => {
    console.log("Iniciando subida de:", file.name, "para técnica:", tecnica?.nombre);
    if (tecnica) setSelectedTecnica(tecnica);
    setAppState('UPLOADING');
    setUploadProgress(10);

    const formData = new FormData();
    formData.append("video", file);
    if (tecnica) {
      formData.append("tecnica_id", tecnica.id);
    }

    try {
      const response = await fetch("http://localhost:8000/api/v1/evaluaciones/validar-spam", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'El video fue rechazado por la IA.'}`);
        setAppState('IDLE');
        setUploadProgress(0);
        return;
      }

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
        <div className="brand" onClick={() => setAppState('IDLE')} style={{ cursor: 'pointer' }}>
          <img src="/logo.jpeg" alt="Corpo e Mente Logo" className="brand-logo" />
          <span className="brand-text">
            Corpo e Mente <span className="brand-accent">IA</span>
          </span>
        </div>

        <div className="user-nav" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {/* Botón exclusivo para Admin */}
          {user.rol === 'admin' && (
            <button 
              className="btn-secondary"
              onClick={() => setAppState(appState === 'ADMIN_PANEL' ? 'IDLE' : 'ADMIN_PANEL')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              🗺️ Gestionar Sucursales (Admin)
            </button>
          )}

          <div style={{ textAlign: 'right' }}>
            <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold' }}>
              {user.nombre_completo}
            </span>
            <span style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
              {user.rol} • {user.sucursal_nombre}
            </span>
          </div>

          <div 
            onClick={() => setIsLoginOpen(true)}
            title="Cambiar de Rol / Iniciar Sesión"
            style={{
              width: '36px', height: '36px', borderRadius: '50%', 
              background: user.rol === 'admin' ? 'var(--brand-red)' : 'var(--glass-bg)', 
              border: '2px solid var(--brand-red)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 'bold', cursor: 'pointer', color: 'white'
            }}
          >
            {user.rol[0].toUpperCase()}
          </div>
        </div>
      </header>

      <main style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {appState === 'ADMIN_PANEL' && (
          <AdminSucursales onClose={() => setAppState('IDLE')} />
        )}

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
          <FeedbackView result={result} tecnica={selectedTecnica} onReset={handleReset} />
        )}
      </main>

      {/* Modal de Cambio de Rol / Login */}
      <LoginModal 
        isOpen={isLoginOpen} 
        onClose={() => setIsLoginOpen(false)} 
        onLoginSuccess={(userData) => setUser(userData)} 
      />
    </div>
  )
}

export default App
