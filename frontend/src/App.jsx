import { useState, useEffect } from 'react'
import './App.css'
import VideoUpload from './pages/VideoUpload'
import FeedbackView from './pages/FeedbackView'
import AdminSucursales from './pages/AdminSucursales'
import ProfesorTecnicas from './pages/ProfesorTecnicas'
import StudentProgress from './pages/StudentProgress'
import ProgressRing from './components/ProgressRing'
import LoginModal from './components/LoginModal'
import UserProfileModal from './components/UserProfileModal'

function App() {
  const [appState, setAppState] = useState('ADMIN_PANEL'); // IDLE, UPLOADING, PROCESSING, FEEDBACK, ADMIN_PANEL, PROFESOR_PANEL
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [selectedTecnica, setSelectedTecnica] = useState(null);
  const [currentEvaluacionId, setCurrentEvaluacionId] = useState(null);

  // Estado de Autenticación
  const [user, setUser] = useState(null);
  const [originalAdminUser, setOriginalAdminUser] = useState(null); // Para despersonalización
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const handleUploadStart = async (uploadData) => {
    // Supports uploadData object ({ sessionId, personaIdx, tecnica, file }) and classic args (file, tecnica)
    let sessionId = null;
    let personaIdx = null;
    let tecnica = null;
    let file = null;

    if (uploadData instanceof File) {
      file = uploadData;
      tecnica = arguments[1] || selectedTecnica;
    } else if (uploadData && typeof uploadData === 'object') {
      sessionId = uploadData.sessionId;
      personaIdx = uploadData.personaIdx;
      tecnica = uploadData.tecnica || selectedTecnica;
      file = uploadData.file;
    }

    console.log("Starting analysis:", { sessionId, personaIdx, tecnica: tecnica?.nombre });
    if (tecnica) setSelectedTecnica(tecnica);
    setAppState('UPLOADING');
    setUploadProgress(10);

    const formData = new FormData();
    if (sessionId) {
      formData.append("session_id", sessionId);
      formData.append("persona_idx", String(personaIdx ?? 0));
    }
    if (file) {
      formData.append("video", file);
    }
    if (tecnica) {
      formData.append("tecnica_id", tecnica.id);
      formData.append("tecnica_nombre", tecnica.nombre);
      if (tecnica.profesor_id) {
        formData.append("profesor_id", tecnica.profesor_id);
      }
    }
    formData.append("idioma", "en");
    formData.append("alumno_id", user.user_id);

    try {
      const response = await fetch("http://localhost:8000/api/v1/evaluaciones/analizar", {
        method: "POST",
        headers: { "Authorization": `Bearer ${user.token}` },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'Error processing video.'}`);
        setAppState('IDLE');
        setUploadProgress(0);
        return;
      }
      
      const data = await response.json();
      setCurrentEvaluacionId(data.evaluacion_id);
      setUploadProgress(100);
      setAppState('PROCESSING');

    } catch (error) {
      console.error("Error uploading video:", error);
      alert("Connection error with server. Make sure the backend is running.");
      setAppState('IDLE');
      setUploadProgress(0);
    }
  };

  useEffect(() => {
    let interval;
    if (appState === 'PROCESSING' && currentEvaluacionId) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/v1/evaluaciones/${currentEvaluacionId}`, {
            headers: { "Authorization": `Bearer ${user.token}` }
          });
          if (res.ok) {
            const data = await res.json();
            if (data.estado === 'completado') {
              setResult({
                similitud: data.similitud,
                feedback: data.feedback,
                feedback_summary: data.feedback_summary,
                video_referencia_url: data.video_referencia_url,
                video_referencia_nombre: data.video_referencia_nombre,
                video_referencia_profesor_nombre: data.video_referencia_profesor_nombre,
                frame_error_url: data.frame_error_url,
                practice_url: data.practice_url,
                timestamp_error_segundos: data.timestamp_error_segundos,
                url_video_alumno: data.url_video_alumno,
                articulaciones_criticas: data.articulaciones_criticas || [],
                nombres_articulaciones_criticas: data.nombres_articulaciones_criticas || [],
              });
              setAppState('FEEDBACK');
              setCurrentEvaluacionId(null);
            } else if (data.estado === 'error') {
              alert(data.feedback || "An error occurred while processing biomechanical analysis.");
              setAppState('IDLE');
              setCurrentEvaluacionId(null);
            }
          }
        } catch(e) {
          console.error("Error checking status:", e);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [appState, currentEvaluacionId]);

  const handleReset = () => {
    setAppState('IDLE');
    setResult(null);
    setUploadProgress(0);
  };

  return (
    <div className="app-container">
      {originalAdminUser && (
        <div style={{ background: '#d01118', color: 'white', textAlign: 'center', padding: '0.5rem', fontSize: '0.85rem', fontWeight: 'bold', zIndex: 100 }}>
          Impersonation Mode: You are using the account of {user?.nombre_completo}.
          <button 
            onClick={() => { setUser(originalAdminUser); setOriginalAdminUser(null); setAppState('IDLE'); }} 
            style={{ marginLeft: '1rem', padding: '0.2rem 0.5rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid white', background: 'transparent', color: 'white', cursor: 'pointer' }}
          >
            Return to Admin Account
          </button>
        </div>
      )}
      <header className="header">
        <div className="brand" onClick={() => setAppState('ADMIN_PANEL')} style={{ cursor: 'pointer' }}>
          <img src="/logo.jpeg" alt="Corpo e Mente Logo" className="brand-logo" />
          <span className="brand-text">
          </span>
        </div>

        <div className="user-nav" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {user && user.rol !== 'profesor' && (
            <button 
              className="btn-secondary"
              onClick={() => setAppState('IDLE')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              Analyze Video
            </button>
          )}

          {user?.rol === 'alumno' && (
            <button
              className="btn-secondary"
              onClick={() => setAppState(appState === 'STUDENT_PROGRESS' ? 'IDLE' : 'STUDENT_PROGRESS')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              My Progress
            </button>
          )}

          {/* Exclusive button for Admin */}
          {user?.rol === 'admin' && (
            <button 
              className="btn-secondary"
              onClick={() => setAppState(appState === 'ADMIN_PANEL' ? 'IDLE' : 'ADMIN_PANEL')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              Admin Panel
            </button>
          )}

          {/* Exclusive button for Instructor */}
          {user?.rol === 'profesor' && (
            <button 
              className="btn-secondary"
              onClick={() => setAppState(appState === 'PROFESOR_PANEL' ? 'IDLE' : 'PROFESOR_PANEL')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              Instructor Panel
            </button>
          )}

          <div style={{ textAlign: 'right' }}>
            {user ? (
              <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold' }}>
                {user.nombre_completo}
              </span>
            ) : (
              <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold' }}>
                Guest
              </span>
            )}
          </div>

          <div 
            onClick={() => user ? setIsProfileOpen(true) : setIsLoginOpen(true)}
            title={user ? "My Profile" : "Sign In"}
            style={{
              width: '36px', height: '36px', borderRadius: '50%', 
              background: user?.rol === 'admin' ? 'var(--brand-red)' : 'var(--glass-bg)', 
              border: '2px solid var(--brand-red)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 'bold', cursor: 'pointer', color: 'white',
              overflow: 'hidden'
            }}
          >
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <>{user ? user.rol[0].toUpperCase() : "?"}</>
            )}
          </div>
        </div>
      </header>

      <main style={{flex: 1, display: 'flex', alignItems: ['ADMIN_PANEL', 'PROFESOR_PANEL', 'STUDENT_PROGRESS'].includes(appState) ? 'stretch' : 'center', justifyContent: 'center', width: '100%'}}>
        {appState === 'ADMIN_PANEL' && (
          <AdminSucursales 
            user={user} 
            onClose={() => {
              if (user?.rol === 'profesor') {
                setAppState('PROFESOR_PANEL');
              } else {
                setAppState('IDLE');
              }
            }} 
            onImpersonate={(newUser, currentAdmin) => { 
              setOriginalAdminUser(currentAdmin); 
              setUser(newUser); 
              if (newUser?.rol === 'profesor') {
                setAppState('PROFESOR_PANEL');
              } else {
                setAppState('IDLE');
              }
            }} 
          />
        )}

        {(appState === 'PROFESOR_PANEL' || (appState === 'IDLE' && user?.rol === 'profesor')) && (
          <ProfesorTecnicas user={user} onClose={() => setAppState('ADMIN_PANEL')} />
        )}

        {appState === 'IDLE' && user && user.rol !== 'profesor' && (
          <VideoUpload user={user} onUploadStart={handleUploadStart} />
        )}
        {appState === 'IDLE' && !user && (
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
             <h2>Restricted Access</h2>
             <p>You must sign in to analyze videos with artificial intelligence.</p>
             <button className="btn-primary" onClick={() => setIsLoginOpen(true)} style={{ marginTop: '1rem' }}>Sign In</button>
          </div>
        )}

        {(appState === 'UPLOADING' || appState === 'PROCESSING') && (
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem'}}>
            <ProgressRing 
              value={appState === 'UPLOADING' ? uploadProgress : 'indeterminate'} 
              statusText={appState === 'UPLOADING' ? 'Uploading Video...' : 'Processing with AI...'} 
            />
            {appState === 'PROCESSING' && (
              <p style={{color: 'var(--text-secondary)', maxWidth: '400px', textAlign: 'center'}}>
                Extracting poses and comparing against the instructor's biomechanical reference...
              </p>
            )}
          </div>
        )}

        {appState === 'FEEDBACK' && (
          <FeedbackView user={user} result={result} tecnica={selectedTecnica} onReset={handleReset} />
        )}
        {appState === 'STUDENT_PROGRESS' && user?.rol === 'alumno' && (
          <StudentProgress user={user} />
        )}
      </main>

      {/* Modal de Cambio de Rol / Login */}
      <LoginModal 
        isOpen={isLoginOpen} 
        user={user}
        onClose={() => setIsLoginOpen(false)} 
        onLoginSuccess={(userData) => {
          setUser(userData);
          if (userData.rol === 'profesor') {
            setAppState('PROFESOR_PANEL');
          }
        }} 
      />

      {/* Modal de Perfil de Usuario */}
      {isProfileOpen && (
        <UserProfileModal 
          isOpen={isProfileOpen} 
          user={user}
          onClose={() => setIsProfileOpen(false)} 
          onUpdateSuccess={(userData) => setUser(userData)}
          onLogout={() => { setUser(null); setOriginalAdminUser(null); setIsProfileOpen(false); setAppState('IDLE'); }}
        />
      )}
    </div>
  )
}

export default App
