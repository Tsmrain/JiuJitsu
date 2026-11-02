import { useState, useEffect } from 'react'
import './App.css'
import VideoUpload from './pages/VideoUpload'
import FeedbackView from './pages/FeedbackView'
import AdminSucursales from './pages/AdminSucursales'
import ProfesorTecnicas from './pages/ProfesorTecnicas'
import StudentProgress from './pages/StudentProgress'
import LibraryView from './pages/LibraryView'
import ProgressRing from './components/ProgressRing'
import LoginModal from './components/LoginModal'
import UserProfileModal from './components/UserProfileModal'
import { getTranslation } from './i18n/translations'

function App() {
  const [appState, setAppState] = useState('ADMIN_PANEL'); // IDLE, UPLOADING, PROCESSING, FEEDBACK, ADMIN_PANEL, PROFESOR_PANEL, STUDENT_PROGRESS, LIBRARY
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [selectedTecnica, setSelectedTecnica] = useState(null);
  const [currentEvaluacionId, setCurrentEvaluacionId] = useState(null);

  // Estado de Idioma (i18n)
  const [idioma, setIdioma] = useState(() => {
    return localStorage.getItem('app_idioma') || 'es';
  });

  const t = (key) => getTranslation(idioma, key);

  // Estado de Autenticación
  const [user, setUser] = useState(null);
  const [originalAdminUser, setOriginalAdminUser] = useState(null); // Para despersonalización
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  useEffect(() => {
    // Hook de testing visual para automatizaciones Playwright / E2E
    window.__setAppState = (state, resData, tecData) => {
      if (state) setAppState(state);
      if (resData) setResult(resData);
      if (tecData) setSelectedTecnica(tecData);
    };
  }, []);

  const handleLanguageChange = async (newLang) => {
    if (!newLang) return;
    const clean = newLang.toLowerCase().trim();
    setIdioma(clean);
    localStorage.setItem('app_idioma', clean);

    if (user?.user_id && user?.token) {
      try {
        await fetch(`http://localhost:8000/api/v1/auth/usuarios/${user.user_id}/idioma`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${user.token}`
          },
          body: JSON.stringify({ idioma: clean })
        });
      } catch (err) {
        console.warn('Could not persist language to user profile:', err);
      }
    }
  };

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

    console.log("Starting analysis:", { sessionId, personaIdx, tecnica: tecnica?.nombre, idioma });
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
    formData.append("idioma", idioma);
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
      alert(t('connectionError'));
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
          {t('impersonationNotice')} {user?.nombre_completo}.
          <button 
            onClick={() => { setUser(originalAdminUser); setOriginalAdminUser(null); setAppState('IDLE'); }} 
            style={{ marginLeft: '1rem', padding: '0.2rem 0.5rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid white', background: 'transparent', color: 'white', cursor: 'pointer' }}
          >
            {t('returnToAdmin')}
          </button>
        </div>
      )}
      <header className="header">
        <div className="brand" onClick={() => setAppState('ADMIN_PANEL')} style={{ cursor: 'pointer' }}>
          <img src="/logo.jpeg" alt="Corpo e Mente Logo" className="brand-logo" />
          <span className="brand-text">
          </span>
        </div>

        <div className="user-nav" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Botón de Biblioteca (Pública para usuarios autenticados) */}
          {user && (
            <button
              className="btn-secondary"
              onClick={() => setAppState(appState === 'LIBRARY' ? 'IDLE' : 'LIBRARY')}
              style={{
                fontSize: '0.8rem',
                padding: '0.4rem 0.8rem',
                borderColor: appState === 'LIBRARY' ? '#ffd43b' : 'rgba(255, 212, 59, 0.6)',
                color: appState === 'LIBRARY' ? '#ffd43b' : 'white',
                background: appState === 'LIBRARY' ? 'rgba(255, 212, 59, 0.15)' : 'transparent',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              📖 {t('library')}
            </button>
          )}

          {user && user.rol !== 'profesor' && (
            <button 
              className="btn-secondary"
              onClick={() => setAppState('IDLE')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              {t('analyzeVideo')}
            </button>
          )}

          {user?.rol === 'alumno' && (
            <button
              className="btn-secondary"
              onClick={() => setAppState(appState === 'STUDENT_PROGRESS' ? 'IDLE' : 'STUDENT_PROGRESS')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              {t('myProgress')}
            </button>
          )}

          {/* Exclusive button for Admin */}
          {user?.rol === 'admin' && (
            <button 
              className="btn-secondary"
              onClick={() => setAppState(appState === 'ADMIN_PANEL' ? 'IDLE' : 'ADMIN_PANEL')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              {t('adminPanel')}
            </button>
          )}

          {/* Exclusive button for Instructor */}
          {user?.rol === 'profesor' && (
            <button 
              className="btn-secondary"
              onClick={() => setAppState(appState === 'PROFESOR_PANEL' ? 'IDLE' : 'PROFESOR_PANEL')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              {t('instructorPanel')}
            </button>
          )}

          {/* Selector Global de Idioma (i18n) en Header */}
          <select
            value={idioma}
            onChange={(e) => handleLanguageChange(e.target.value)}
            style={{
              background: 'rgba(0, 0, 0, 0.45)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.25)',
              borderRadius: '6px',
              padding: '0.35rem 0.5rem',
              fontSize: '0.8rem',
              cursor: 'pointer',
              outline: 'none',
            }}
            title="Idioma / Language"
          >
            <option value="es">🇪🇸 ES</option>
            <option value="pt">🇧🇷 PT</option>
            <option value="en">🇺🇸 EN</option>
          </select>

          <div style={{ textAlign: 'right' }}>
            {user ? (
              <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold' }}>
                {user.nombre_completo}
              </span>
            ) : (
              <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold' }}>
                {t('guest')}
              </span>
            )}
          </div>

          <div 
            onClick={() => user ? setIsProfileOpen(true) : setIsLoginOpen(true)}
            title={user ? t('myProfile') : t('signIn')}
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

      <main style={{flex: 1, display: 'flex', alignItems: ['ADMIN_PANEL', 'PROFESOR_PANEL', 'STUDENT_PROGRESS', 'LIBRARY'].includes(appState) ? 'stretch' : 'center', justifyContent: 'center', width: '100%'}}>
        {appState === 'LIBRARY' && (
          <LibraryView
            user={user}
            idioma={idioma}
            onClose={() => setAppState(user?.rol === 'profesor' ? 'PROFESOR_PANEL' : 'IDLE')}
          />
        )}

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
              if (newUser?.idioma_preferido) {
                handleLanguageChange(newUser.idioma_preferido);
              }
              if (newUser?.rol === 'profesor') {
                setAppState('PROFESOR_PANEL');
              } else {
                setAppState('IDLE');
              }
            }} 
          />
        )}

        {(appState === 'PROFESOR_PANEL' || (appState === 'IDLE' && user?.rol === 'profesor')) && (
          <ProfesorTecnicas user={user} onClose={() => setAppState('ADMIN_PANEL')} idioma={idioma} />
        )}

        {appState === 'IDLE' && user && user.rol !== 'profesor' && (
          <VideoUpload user={user} onUploadStart={handleUploadStart} idioma={idioma} />
        )}
        {appState === 'IDLE' && !user && (
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
             <h2>{t('restrictedAccess')}</h2>
             <p>{t('restrictedMsg')}</p>
             <button className="btn-primary" onClick={() => setIsLoginOpen(true)} style={{ marginTop: '1rem' }}>{t('signIn')}</button>
          </div>
        )}

        {(appState === 'UPLOADING' || appState === 'PROCESSING') && (
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem'}}>
            <ProgressRing 
              value={appState === 'UPLOADING' ? uploadProgress : 'indeterminate'} 
              statusText={appState === 'UPLOADING' ? t('uploadingVideo') : t('processingAI')} 
            />
            {appState === 'PROCESSING' && (
              <p style={{color: 'var(--text-secondary)', maxWidth: '400px', textAlign: 'center'}}>
                {t('processingDesc')}
              </p>
            )}
          </div>
        )}

        {appState === 'FEEDBACK' && (
          <FeedbackView user={user} result={result} tecnica={selectedTecnica} onReset={handleReset} idioma={idioma} />
        )}
        {appState === 'STUDENT_PROGRESS' && user?.rol === 'alumno' && (
          <StudentProgress user={user} idioma={idioma} />
        )}
      </main>

      {/* Modal de Cambio de Rol / Login */}
      <LoginModal 
        isOpen={isLoginOpen} 
        user={user}
        onClose={() => setIsLoginOpen(false)} 
        onLoginSuccess={(userData) => {
          setUser(userData);
          if (userData?.idioma_preferido) {
            handleLanguageChange(userData.idioma_preferido);
          }
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
          idioma={idioma}
          onLanguageChange={handleLanguageChange}
          onClose={() => setIsProfileOpen(false)} 
          onUpdateSuccess={(userData) => {
            setUser(userData);
            if (userData?.idioma_preferido) {
              handleLanguageChange(userData.idioma_preferido);
            }
          }}
          onLogout={() => { setUser(null); setOriginalAdminUser(null); setIsProfileOpen(false); setAppState('IDLE'); }}
        />
      )}
    </div>
  )
}

export default App
