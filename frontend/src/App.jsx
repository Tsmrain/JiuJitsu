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
import { API_BASE } from './api/config'

function App() {
  const [appState, setAppState] = useState('ADMIN_PANEL'); // IDLE, UPLOADING, PROCESSING, FEEDBACK, ADMIN_PANEL, PROFESOR_PANEL, STUDENT_PROGRESS, LIBRARY
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [selectedTecnica, setSelectedTecnica] = useState(null);
  const [currentEvaluacionId, setCurrentEvaluacionId] = useState(null);
  const [libraryInitialQuery, setLibraryInitialQuery] = useState(null);
  const [libraryInitialImage, setLibraryInitialImage] = useState(null);

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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const isAlumno = user?.rol === 'alumno';
  const isExpired = isAlumno && (
    user?.estado_suscripcion === 'expirado' ||
    (user?.fecha_expiracion && new Date(user.fecha_expiracion) <= new Date())
  );
  const isPassActive = !isAlumno || (user?.estado_suscripcion === 'activo' && !isExpired);

  useEffect(() => {
    // Hook de testing visual para automatizaciones Playwright / E2E
    window.__setAppState = (state, resData, tecData, extra) => {
      if (state) setAppState(state);
      if (resData) setResult(resData);
      if (tecData) setSelectedTecnica(tecData);
      if (extra && extra.libraryInitialQuery !== undefined) {
        setLibraryInitialQuery(extra.libraryInitialQuery);
      }
      if (extra && extra.libraryInitialImage !== undefined) {
        setLibraryInitialImage(extra.libraryInitialImage);
      }
    };
  }, []);

  const handleLanguageChange = async (newLang) => {
    if (!newLang) return;
    const clean = newLang.toLowerCase().trim();
    setIdioma(clean);
    localStorage.setItem('app_idioma', clean);

    if (user?.user_id && user?.token) {
      try {
        await fetch(`${API_BASE}/api/v1/auth/usuarios/${user.user_id}/idioma`, {
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
      const response = await fetch(`${API_BASE}/api/v1/evaluaciones/analizar`, {
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
          const res = await fetch(`${API_BASE}/api/v1/evaluaciones/${currentEvaluacionId}`, {
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
        <div className="impersonation-banner">
          <span>{t('impersonationNotice')} {user?.nombre_completo}.</span>
          <button 
            onClick={() => { setUser(originalAdminUser); setOriginalAdminUser(null); setAppState('IDLE'); }} 
            className="impersonation-return-btn"
          >
            {t('returnToAdmin')}
          </button>
        </div>
      )}
      <header className="header">
        <div className="brand" onClick={() => setAppState('ADMIN_PANEL')} style={{ cursor: 'pointer' }}>
          <img src="/logo.jpeg" alt="Corpo e Mente Logo" className="brand-logo" />
          <span className="brand-text">
            Corpo <span className="brand-accent">e</span> Mente
          </span>
        </div>

        {/* Desktop Navigation Bar */}
        <div className="nav-desktop">
          {/* Botón de Biblioteca (Pública para usuarios autenticados) */}
          {user && (
            <button
              className="btn-secondary"
              onClick={() => {
                if (appState === 'LIBRARY') {
                  setLibraryInitialQuery(null);
                  setAppState('IDLE');
                } else {
                  setLibraryInitialQuery(null);
                  setAppState('LIBRARY');
                }
              }}
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
              style={{
                fontSize: '0.8rem',
                padding: '0.4rem 0.8rem',
                borderColor: !isPassActive ? 'rgba(208, 17, 24, 0.6)' : 'var(--brand-red)',
                color: 'white',
                opacity: !isPassActive ? 0.85 : 1
              }}
              title={!isPassActive ? t('subscriptionPendingWarning') : ''}
            >
              {!isPassActive ? `🔒 ${t('analyzeVideo')}` : t('analyzeVideo')}
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
              <>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold' }}>
                  {user.nombre_completo}
                </span>
                {isAlumno && (
                  <span style={{
                    display: 'block',
                    fontSize: '0.72rem',
                    fontWeight: 'bold',
                    color: isPassActive ? '#4ade80' : '#ff8787'
                  }}>
                    {isPassActive ? `🥋 ${t('activeStatus')}` : `🔒 ${t('pendingStatus')}`}
                  </span>
                )}
              </>
            ) : (
              <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold' }}>
                {t('guest')}
              </span>
            )}
          </div>

          <div 
            data-testid="user-avatar-btn"
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

        {/* Mobile Navigation Controls */}
        <div className="nav-mobile-right">
          <div 
            data-testid="user-avatar-btn-mobile"
            onClick={() => user ? setIsProfileOpen(true) : setIsLoginOpen(true)}
            title={user ? t('myProfile') : t('signIn')}
            style={{
              width: '38px', height: '38px', borderRadius: '50%', 
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

          <button 
            type="button"
            className="hamburger-btn"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label="Toggle navigation menu"
            title="Menu"
          >
            ☰
          </button>
        </div>
      </header>

      {/* Mobile Drawer (Touch UI) */}
      {isMobileMenuOpen && (
        <div className="drawer-backdrop" onClick={() => setIsMobileMenuOpen(false)}>
          <div className="mobile-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div className="drawer-user-info">
                <div 
                  onClick={() => { setIsMobileMenuOpen(false); user ? setIsProfileOpen(true) : setIsLoginOpen(true); }}
                  style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--glass-bg)', border: '2px solid var(--brand-red)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', overflow: 'hidden' }}
                >
                  {user?.avatar_url ? (
                    <img src={user.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  ) : (
                    <span>{user ? user.rol[0].toUpperCase() : '?'}</span>
                  )}
                </div>
                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '0.95rem' }}>{user ? user.nombre_completo : t('guest')}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span>{user ? user.rol.toUpperCase() : (idioma === 'pt' ? 'Visitante' : idioma === 'en' ? 'Visitor' : 'Invitado')}</span>
                    {isAlumno && (
                      <span style={{ color: isPassActive ? '#4ade80' : '#ff8787', fontWeight: 'bold' }}>
                        • {isPassActive ? t('activeStatus') : t('pendingStatus')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <button 
                type="button"
                className="drawer-close-btn" 
                onClick={() => setIsMobileMenuOpen(false)} 
                aria-label="Close menu"
              >
                ✕
              </button>
            </div>

            <div className="drawer-links">
              {user && (
                <button
                  type="button"
                  className="btn-secondary drawer-nav-btn"
                  onClick={() => {
                    setLibraryInitialQuery(null);
                    setAppState('LIBRARY');
                    setIsMobileMenuOpen(false);
                  }}
                  style={{
                    borderColor: appState === 'LIBRARY' ? '#ffd43b' : 'rgba(255, 212, 59, 0.4)',
                    color: appState === 'LIBRARY' ? '#ffd43b' : 'white',
                    background: appState === 'LIBRARY' ? 'rgba(255, 212, 59, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                  }}
                >
                  📖 {t('library')}
                </button>
              )}

              {user && user.rol !== 'profesor' && (
                <button 
                  type="button"
                  className="btn-secondary drawer-nav-btn"
                  onClick={() => { setAppState('IDLE'); setIsMobileMenuOpen(false); }}
                  style={{
                    borderColor: appState === 'IDLE' ? 'var(--brand-red)' : 'rgba(255,255,255,0.15)',
                    opacity: !isPassActive ? 0.85 : 1
                  }}
                >
                  {!isPassActive ? `🔒 📹 ${t('analyzeVideo')}` : `📹 ${t('analyzeVideo')}`}
                </button>
              )}

              {user?.rol === 'alumno' && (
                <button
                  type="button"
                  className="btn-secondary drawer-nav-btn"
                  onClick={() => { setAppState('STUDENT_PROGRESS'); setIsMobileMenuOpen(false); }}
                  style={{ borderColor: appState === 'STUDENT_PROGRESS' ? 'var(--brand-red)' : 'rgba(255,255,255,0.15)' }}
                >
                  📊 {t('myProgress')}
                </button>
              )}

              {user?.rol === 'admin' ? (
                <button 
                  type="button"
                  className="btn-secondary drawer-nav-btn"
                  onClick={() => { setAppState('ADMIN_PANEL'); setIsMobileMenuOpen(false); }}
                  style={{ borderColor: appState === 'ADMIN_PANEL' ? 'var(--brand-red)' : 'rgba(255,255,255,0.15)' }}
                >
                  ⚙️ {t('adminPanel')}
                </button>
              ) : (
                <button 
                  type="button"
                  className="btn-secondary drawer-nav-btn"
                  onClick={() => { setAppState('ADMIN_PANEL'); setIsMobileMenuOpen(false); }}
                  style={{ borderColor: appState === 'ADMIN_PANEL' ? 'var(--brand-red)' : 'rgba(255,255,255,0.15)' }}
                >
                  📍 {t('ourBranches')}
                </button>
              )}

              {user?.rol === 'profesor' && (
                <button 
                  type="button"
                  className="btn-secondary drawer-nav-btn"
                  onClick={() => { setAppState('PROFESOR_PANEL'); setIsMobileMenuOpen(false); }}
                  style={{ borderColor: appState === 'PROFESOR_PANEL' ? 'var(--brand-red)' : 'rgba(255,255,255,0.15)' }}
                >
                  🥋 {t('instructorPanel')}
                </button>
              )}
            </div>

            <div className="drawer-footer">
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>🌐 {t('languagePreference')}:</label>
              <select
                value={idioma}
                onChange={(e) => { handleLanguageChange(e.target.value); }}
                style={{
                  width: '100%',
                  background: 'rgba(0, 0, 0, 0.5)',
                  color: 'white',
                  border: '1px solid rgba(255, 255, 255, 0.25)',
                  borderRadius: '8px',
                  padding: '0.65rem',
                  fontSize: '0.9rem',
                  minHeight: '44px',
                  boxSizing: 'border-box'
                }}
              >
                <option value="es">🇪🇸 Español</option>
                <option value="pt">🇧🇷 Português</option>
                <option value="en">🇺🇸 English</option>
              </select>

              {user ? (
                <button
                  type="button"
                  className="btn-secondary drawer-nav-btn"
                  onClick={() => { setIsMobileMenuOpen(false); setIsProfileOpen(true); }}
                  style={{ marginTop: '0.5rem', justifyContent: 'center' }}
                >
                  👤 {t('myProfile')}
                </button>
              ) : (
                <button
                  type="button"
                  className="btn-primary drawer-nav-btn"
                  onClick={() => { setIsMobileMenuOpen(false); setIsLoginOpen(true); }}
                  style={{ marginTop: '0.5rem', justifyContent: 'center' }}
                >
                  🔑 {t('signIn')}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      <main style={{flex: 1, display: 'flex', alignItems: 'stretch', justifyContent: 'center', width: '100%'}}>
        {appState === 'LIBRARY' && (
          <LibraryView
            user={user}
            idioma={idioma}
            initialQuery={libraryInitialQuery}
            initialImageUrl={libraryInitialImage}
            onClose={() => {
              setLibraryInitialQuery(null);
              setLibraryInitialImage(null);
              setAppState(user?.rol === 'profesor' ? 'PROFESOR_PANEL' : 'IDLE');
            }}
          />
        )}

        {appState === 'ADMIN_PANEL' && (
          <AdminSucursales 
            user={user} 
            idioma={idioma}
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
          <StudentProgress
            user={user}
            idioma={idioma}
            onViewTheory={(tecnicaNombre, frameErrorUrl) => {
              setLibraryInitialQuery(tecnicaNombre);
              setLibraryInitialImage(frameErrorUrl);
              setAppState('LIBRARY');
            }}
          />
        )}
      </main>

      {/* Modal de Cambio de Rol / Login */}
      <LoginModal 
        isOpen={isLoginOpen} 
        user={user}
        idioma={idioma}
        onClose={() => setIsLoginOpen(false)} 
        onLoginSuccess={(userData) => {
          setUser(userData);
          const lang = userData?.idioma_preferido || idioma || localStorage.getItem('app_idioma') || 'es';
          handleLanguageChange(lang);
          if (userData.rol === 'profesor') {
            setAppState('PROFESOR_PANEL');
          } else if (userData.rol === 'alumno') {
            setAppState('IDLE');
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
            setUser(prev => ({
              ...prev,
              ...userData,
              estado_suscripcion: userData?.estado_suscripcion || prev?.estado_suscripcion || 'pendiente',
              fecha_expiracion: userData?.fecha_expiracion !== undefined ? userData.fecha_expiracion : prev?.fecha_expiracion
            }));
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
