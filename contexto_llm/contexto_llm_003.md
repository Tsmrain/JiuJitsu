

--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/App.jsx ---
import { useState, useEffect } from 'react'
import './App.css'
import VideoUpload from './pages/VideoUpload'
import FeedbackView from './pages/FeedbackView'
import AdminSucursales from './pages/AdminSucursales'
import ProfesorTecnicas from './pages/ProfesorTecnicas'
import ProgressRing from './components/ProgressRing'
import LoginModal from './components/LoginModal'
import UserProfileModal from './components/UserProfileModal'
import { useTranslation } from './i18n/translations'

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

  const { t } = useTranslation(user?.idioma_preferido || 'es');

  const handleUploadStart = async (file, tecnica) => {
    console.log("Iniciando subida de:", file.name, "para técnica:", tecnica?.nombre);
    if (tecnica) setSelectedTecnica(tecnica);
    setAppState('UPLOADING');
    setUploadProgress(10);

    const formData = new FormData();
    formData.append("video", file);
    if (tecnica) {
      formData.append("tecnica_id", tecnica.id);
      formData.append("tecnica_nombre", tecnica.nombre);
      if (tecnica.profesor_id) {
        formData.append("profesor_id", tecnica.profesor_id);
      }
    }
    formData.append("idioma", user?.idioma_preferido || 'es');
    formData.append("alumno_id", user.user_id);

    try {
      const response = await fetch("http://localhost:8000/api/v1/evaluaciones/analizar", {
        method: "POST",
        headers: { "Authorization": `Bearer ${user.token}` },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'Error al procesar el video.'}`);
        setAppState('IDLE');
        setUploadProgress(0);
        return;
      }
      
      const data = await response.json();
      setCurrentEvaluacionId(data.evaluacion_id);
      setUploadProgress(100);
      setAppState('PROCESSING');

    } catch (error) {
      console.error("Error subiendo el video:", error);
      alert("Hubo un error de conexión con el servidor. Asegúrate de que el backend esté corriendo.");
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
                video_referencia_url: data.video_referencia_url,
                video_referencia_profesor_nombre: data.video_referencia_profesor_nombre,
              });
              setAppState('FEEDBACK');
              setCurrentEvaluacionId(null);
            }
          }
        } catch(e) {
          console.error("Error consultando estado:", e);
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
          Modo Impersonalización: Estás usando la cuenta de {user?.nombre_completo}.
          <button 
            onClick={() => { setUser(originalAdminUser); setOriginalAdminUser(null); setAppState('IDLE'); }} 
            style={{ marginLeft: '1rem', padding: '0.2rem 0.5rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid white', background: 'transparent', color: 'white', cursor: 'pointer' }}
          >
            Volver a mi cuenta Admin
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
          {/* Selector de Idioma (ES / PT) */}
          <select 
            value={user?.idioma_preferido || 'es'} 
            onChange={(e) => {
              if (user) {
                setUser(prev => ({ ...prev, idioma_preferido: e.target.value }));
              }
            }}
            title="Seleccionar Idioma del Sistema"
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '6px',
              padding: '0.35rem 0.6rem',
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            <option value="es" style={{ background: '#111', color: 'white' }}>ES</option>
            <option value="pt" style={{ background: '#111', color: 'white' }}>PT</option>
          </select>

          {user && user.rol !== 'profesor' && (
            <button 
              className="btn-secondary"
              onClick={() => setAppState('IDLE')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              Analizar Video
            </button>
          )}

          {/* Botón exclusivo para Admin */}
          {user?.rol === 'admin' && (
            <button 
              className="btn-secondary"
              onClick={() => setAppState(appState === 'ADMIN_PANEL' ? 'IDLE' : 'ADMIN_PANEL')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              {t.adminBtn}
            </button>
          )}

          {/* Botón exclusivo para Profesor */}
          {user?.rol === 'profesor' && (
            <button 
              className="btn-secondary"
              onClick={() => setAppState(appState === 'PROFESOR_PANEL' ? 'IDLE' : 'PROFESOR_PANEL')}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', borderColor: 'var(--brand-red)', color: 'white' }}
            >
              {t.profesorBtn}
            </button>
          )}

          <div style={{ textAlign: 'right' }}>
            {user ? (
              <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold' }}>
                {user.nombre_completo}
              </span>
            ) : (
              <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold' }}>
                Invitado
              </span>
            )}
          </div>

          <div 
            onClick={() => user ? setIsProfileOpen(true) : setIsLoginOpen(true)}
            title={user ? "Mi Perfil" : "Iniciar Sesión"}
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

      <main style={{flex: 1, display: 'flex', alignItems: appState === 'ADMIN_PANEL' || appState === 'PROFESOR_PANEL' ? 'stretch' : 'center', justifyContent: 'center', width: '100%'}}>
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
             <h2>Acceso Restringido</h2>
             <p>Debes iniciar sesión para poder analizar videos con inteligencia artificial.</p>
             <button className="btn-primary" onClick={() => setIsLoginOpen(true)} style={{ marginTop: '1rem' }}>Iniciar Sesión</button>
          </div>
        )}

        {(appState === 'UPLOADING' || appState === 'PROCESSING') && (
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem'}}>
            <ProgressRing 
              value={appState === 'UPLOADING' ? uploadProgress : 'indeterminate'} 
              statusText={appState === 'UPLOADING' ? t.uploadingVideo : t.processingIA} 
            />
            {appState === 'PROCESSING' && (
              <p style={{color: 'var(--text-secondary)', maxWidth: '400px', textAlign: 'center'}}>
                {t.processingHint}
              </p>
            )}
          </div>
        )}

        {appState === 'FEEDBACK' && (
          <FeedbackView user={user} result={result} tecnica={selectedTecnica} onReset={handleReset} />
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



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/index.css ---
*, *::before, *::after {
  box-sizing: border-box;
}

:root {
  /* Brand Colors from Logo */
  --brand-red: #d01118;
  --brand-red-dark: #a30e13;
  --brand-black: #080808;
  --brand-white: #ffffff;
  --brand-gray: #1a1a1a;
  --brand-gray-light: #2a2a2a;

  /* Semantic Tokens */
  --bg-color: var(--brand-black);
  --text-primary: var(--brand-white);
  --text-secondary: #a0a0a0;
  --accent-color: var(--brand-red);
  
  /* Glassmorphism Tokens */
  --glass-bg: rgba(26, 26, 26, 0.75);
  --glass-border: rgba(255, 255, 255, 0.12);
  --glass-blur: blur(16px);

  /* Typography */
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  color-scheme: dark;
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--bg-color);
  color: var(--text-primary);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-image: 
    radial-gradient(circle at 15% 50%, rgba(208, 17, 24, 0.1) 0%, transparent 45%),
    radial-gradient(circle at 85% 30%, rgba(208, 17, 24, 0.06) 0%, transparent 45%);
  overflow-x: hidden;
}

#root {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
}

/* Glass Panel Utility */
.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  box-shadow: 0 10px 32px 0 rgba(0, 0, 0, 0.5);
  max-width: 100%;
}

/* Form Controls Reset & Containment */
input, select, textarea {
  box-sizing: border-box;
  max-width: 100%;
  font-family: inherit;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

input:focus, select:focus, textarea:focus {
  border-color: var(--brand-red) !important;
  box-shadow: 0 0 0 3px rgba(208, 17, 24, 0.25) !important;
}

/* Typography utilities */
h1, h2, h3, h4, h5, h6 {
  letter-spacing: -0.02em;
  margin-top: 0;
  word-break: break-word;
}

/* Button Reset & Styling */
button {
  font-family: inherit;
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.btn-primary {
  background-color: var(--brand-red);
  color: var(--brand-white);
  box-shadow: 0 4px 14px 0 rgba(208, 17, 24, 0.39);
}

.btn-primary:hover {
  background-color: var(--brand-red-dark);
  transform: translateY(-1px);
}

.btn-primary:active {
  transform: translateY(1px);
}

.btn-secondary {
  background-color: rgba(255, 255, 255, 0.08);
  color: var(--brand-white);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.btn-secondary:hover {
  background-color: rgba(255, 255, 255, 0.15);
}

/* Custom Scrollbars */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--brand-red);
}




--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/main.jsx ---
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/components/LoginModal.jsx ---
import { useState, useEffect } from 'react';
import { useTranslation } from '../i18n/translations';

export default function LoginModal({ isOpen, user, onClose, onLoginSuccess }) {
  const [tab, setTab] = useState('login'); // 'login' | 'signup'

  const { t } = useTranslation(user?.idioma_preferido);

  // Login form state
  const [loginUserOrEmail, setLoginUserOrEmail] = useState('admin');
  const [loginPassword, setLoginPassword] = useState('admin123');

  // Signup form state
  const [signupNombre, setSignupNombre] = useState('');
  const [signupUsername, setSignupUsername] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupRol, setSignupRol] = useState('alumno');
  const [signupSucursalId, setSignupSucursalId] = useState('');

  const [sucursales, setSucursales] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (isOpen) {
      // Cargar sucursales para el formulario de registro
      fetch("http://localhost:8000/api/v1/sucursales")
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            setSucursales(data);
            if (data.length > 0) setSignupSucursalId(data[0].id);
          }
        })
        .catch(err => console.error("Error al cargar sucursales:", err));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');

    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username_or_email: loginUserOrEmail,
          password: loginPassword,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: "Error al iniciar sesión" }));
        setErrorMsg(errData.detail || "Credenciales incorrectas.");
        setLoading(false);
        return;
      }

      const userData = await response.json();
      onLoginSuccess({
        ...userData,
        idioma_preferido: user?.idioma_preferido || 'es'
      });
      onClose();
    } catch (err) {
      console.error("Error conectando con la API de Auth:", err);
      setErrorMsg("No se pudo conectar con el servidor. Verifica que el backend esté corriendo.");
      setLoading(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');

    if (signupRol === 'admin') {
      setErrorMsg(user?.idioma_preferido === 'pt' ? 'A função de Administrador é reservada.' : 'El rol de Administrador es exclusivo y reservado.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre_completo: signupNombre,
          username: signupUsername,
          password: signupPassword,
          rol: signupRol,
          sucursal_id: signupSucursalId || null,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: "Error al registrar cuenta" }));
        setErrorMsg(errData.detail || "No se pudo registrar la cuenta.");
        setLoading(false);
        return;
      }

      const userData = await response.json();
      onLoginSuccess({
        ...userData,
        idioma_preferido: user?.idioma_preferido || 'es'
      });
      onClose();
    } catch (err) {
      console.error("Error al registrar cuenta en backend:", err);
      alert(err.message || "Error al registrarse");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0, 0, 0, 0.85)', backdropFilter: 'blur(10px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: '1rem', boxSizing: 'border-box'
    }}>
      <div className="glass-panel" style={{
        width: '100%', maxWidth: '440px', padding: '2rem', borderRadius: '16px',
        border: '1px solid rgba(208, 17, 24, 0.3)', position: 'relative',
        maxHeight: '90vh', overflowY: 'auto', boxSizing: 'border-box'
      }}>
        <button 
          onClick={onClose}
          style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', color: 'white', fontSize: '1.25rem', cursor: 'pointer' }}
        >
          ✕
        </button>

        {/* Tabs header */}
        <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '1.5rem' }}>
          <button
            onClick={() => { setTab('login'); setErrorMsg(''); }}
            style={{
              flex: 1, padding: '0.75rem', background: 'none', border: 'none',
              borderBottom: tab === 'login' ? '3px solid var(--brand-red)' : '3px solid transparent',
              color: tab === 'login' ? 'white' : 'var(--text-secondary)',
              fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer'
            }}
          >
            {t.tabLogin}
          </button>
          <button
            onClick={() => { setTab('signup'); setErrorMsg(''); }}
            style={{
              flex: 1, padding: '0.75rem', background: 'none', border: 'none',
              borderBottom: tab === 'signup' ? '3px solid var(--brand-red)' : '3px solid transparent',
              color: tab === 'signup' ? 'white' : 'var(--text-secondary)',
              fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer'
            }}
          >
            {t.tabSignup}
          </button>
        </div>

        {errorMsg && (
          <div style={{
            background: 'rgba(208, 17, 24, 0.2)', border: '1px solid var(--brand-red)',
            color: '#ff6b6b', padding: '0.75rem', borderRadius: '8px', fontSize: '0.85rem',
            marginBottom: '1rem', textAlign: 'center'
          }}>
             {errorMsg}
          </div>
        )}

        {/* Formulario de Login */}
        {tab === 'login' && (
          <form onSubmit={handleLoginSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                {t.labelUserOrEmail}
              </label>
              <input 
                type="text" required value={loginUserOrEmail} onChange={e => setLoginUserOrEmail(e.target.value)}
                placeholder={t.placeholderUserOrEmail}
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                {t.labelPassword}
              </label>
              <input 
                type="password" required value={loginPassword} onChange={e => setLoginPassword(e.target.value)}
                placeholder="••••••••"
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
              />
            </div>

            <button 
              type="submit" disabled={loading}
              className="btn btn-primary" style={{ marginTop: '0.5rem', width: '100%', padding: '0.85rem' }}
            >
              {loading ? t.btnLoggingIn : t.btnLogin}
            </button>
          </form>
        )}

        {/* Formulario de Signup */}
        {tab === 'signup' && (
          <form onSubmit={handleSignupSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                {t.labelNombreCompleto}
              </label>
              <input 
                type="text" required value={signupNombre} onChange={e => setSignupNombre(e.target.value)}
                placeholder={t.placeholderNombreCompleto}
                style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                  {t.labelUsername}
                </label>
                <input 
                  type="text" required value={signupUsername} onChange={e => setSignupUsername(e.target.value)}
                  placeholder="lucas_jiujitsu"
                  style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                {t.labelPassword}
              </label>
              <input 
                type="password" required value={signupPassword} onChange={e => setSignupPassword(e.target.value)}
                placeholder="••••••••"
                style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--brand-red)', marginBottom: '0.3rem' }}>
                {t.labelUserRole}
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                {['alumno', 'profesor'].map((r) => (
                  <button
                    type="button"
                    key={r}
                    onClick={() => setSignupRol(r)}
                    style={{
                      padding: '0.5rem', borderRadius: '6px', fontSize: '0.8rem', textTransform: 'capitalize',
                      border: signupRol === r ? '2px solid var(--brand-red)' : '1px solid rgba(255,255,255,0.1)',
                      background: signupRol === r ? 'var(--brand-red)' : 'rgba(255,255,255,0.05)',
                      color: 'white', cursor: 'pointer', fontWeight: signupRol === r ? 'bold' : 'normal'
                    }}
                  >
                    {r === 'alumno' ? t.roleAlumno : t.roleProfesor}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                {t.labelSucursal}
              </label>
              <select
                value={signupSucursalId}
                onChange={e => setSignupSucursalId(e.target.value)}
                style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: '#1e1e2d', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
              >
                {sucursales.map(s => (
                  <option key={s.id} value={s.id}>
                    {s.nombre} ({s.ciudad}, {s.pais})
                  </option>
                ))}
              </select>
            </div>

            <button 
              type="submit" disabled={loading}
              className="btn btn-primary" style={{ marginTop: '0.5rem', width: '100%', padding: '0.85rem' }}
            >
              {loading ? t.btnSigningUp : t.btnSignupSubmit}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/components/ProgressRing.css ---
@property --value {
  syntax: '<number>';
  inherits: true;
  initial-value: 0;
}

.ring-wrapper {
  position: relative;
  display: grid;
  place-items: center;
}

/* Hide native bars */
progress.progress-ring::-webkit-progress-bar {
  display: none;
  background: none;
}
progress.progress-ring::-webkit-progress-value {
  display: none;
  background: none;
}
progress.progress-ring::-moz-progress-bar {
  display: none;
  background: none;
}

progress.progress-ring {
  --size: 150px;
  --thickness: 12px;
  --track-color: rgba(255, 255, 255, 0.1);
  --fill-color: var(--brand-red);
  --value: attr(value type(<number>));
  
  width: var(--size);
  height: var(--size);
  appearance: none;
  border-radius: 50%;
  
  transition: --value 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  background: conic-gradient(
    var(--fill-color) calc(var(--value) * 1%),
    var(--track-color) 0
  );

  /* Clip the background to the border-area for modern browsers */
  background-clip: border-area;
  border: var(--thickness) solid transparent;
  background-origin: border-box;
}

/* Fallback for browsers that don't support border-area */
@supports not (background-clip: border-area) {
  progress.progress-ring {
    mask-image: radial-gradient(
      transparent calc(50% - var(--thickness)),
      black calc(50% - var(--thickness) + 0.5px)
    );
    -webkit-mask-image: radial-gradient(
      transparent calc(50% - var(--thickness)),
      black calc(50% - var(--thickness) + 0.5px)
    );
    border: 0;
  }
}

/* Respect user's motion preference */
@media (prefers-reduced-motion: reduce) {
  progress.progress-ring {
    transition: none;
  }
}

.ring-content {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.ring-percentage {
  font-size: 1.5rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.ring-status {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 0.25rem;
}

progress.progress-ring.indeterminate {
  background: conic-gradient(
    from 0deg,
    transparent 0deg,
    var(--fill-color) 90deg,
    transparent 180deg
  );
  animation: ring-spin 1.5s linear infinite;
}

@keyframes ring-spin {
  to { rotate: 360deg; }
}

progress.progress-ring.indeterminate::before {
  content: '';  /* Ocultar el % del centro */
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/components/ProgressRing.jsx ---
import { useEffect, useRef } from 'react';
import './ProgressRing.css';

export default function ProgressRing({ value = 0, statusText = "Processing" }) {
  const progressRef = useRef(null);

  // Fallback for browsers that don't support `attr()` CSS function for properties yet
  useEffect(() => {
    if (value === 'indeterminate') return;
    if (progressRef.current && !CSS.supports("width: attr(value type(<number>))")) {
      progressRef.current.style.setProperty("--value", value);
    }
  }, [value]);

  return (
    <div className="ring-wrapper">
      <progress 
        ref={progressRef}
        {...(value === 'indeterminate' ? {} : {value})} 
        max="100" 
        aria-label={`Upload and analysis progress: ${value === 'indeterminate' ? 'processing' : value + '%'}`} 
        className={`progress-ring ${value === 'indeterminate' ? 'indeterminate' : ''}`}
      ></progress>
      <div className="ring-content">
        {value !== 'indeterminate' && <span className="ring-percentage">{Math.round(value)}%</span>}
        <span className="ring-status">{statusText}</span>
      </div>
    </div>
  );
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/components/TheoryManagerModal.jsx ---
import { useState, useEffect } from 'react';

/**
 * Modal de gestión de teoría RAG para una técnica.
 * Permite al profesor ver todos los chunks que subió y borrarlos de golpe.
 */
export default function TheoryManagerModal({ isOpen, user, tecnica, onClose }) {
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen || !tecnica) return;
    fetchChunks();
  }, [isOpen, tecnica?.id]);

  const fetchChunks = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(
        `http://localhost:8000/api/v1/conocimiento/teoria/${tecnica.id}?solo_mios=true`,
        { headers: { Authorization: `Bearer ${user.token}` } }
      );
      if (!res.ok) {
        setError('No se pudo cargar la teoría.');
        setLoading(false);
        return;
      }
      const data = await res.json();
      setChunks(data.chunks || []);
    } catch (e) {
      console.error(e);
      setError('Error de conexión con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm(`¿Eliminar TODOS los aportes de teoría que subiste para "${tecnica.nombre}"? Esta acción no se puede deshacer.`)) {
      return;
    }
    setDeleting(true);
    setError('');
    try {
      const res = await fetch(
        `http://localhost:8000/api/v1/conocimiento/teoria/${tecnica.id}`,
        {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${user.token}` }
        }
      );
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || 'Error al eliminar.');
        setDeleting(false);
        return;
      }
      const data = await res.json();
      alert(`Eliminados: ${data.chunks_eliminados_postgres} de Postgres y ${data.chunks_eliminados_qdrant} de Qdrant.`);
      setChunks([]);
    } catch (e) {
      console.error(e);
      setError('Error de conexión al eliminar.');
    } finally {
      setDeleting(false);
    }
  };

  if (!isOpen || !tecnica) return null;

  const formatFecha = (iso) => {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString('es-ES', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content glass-panel"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '680px', maxHeight: '85vh', overflowY: 'auto' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, color: 'var(--brand-red)' }}>
            Teoría RAG — {tecnica.nombre}
          </h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'white', fontSize: '1.25rem', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 1rem 0' }}>
          Estos son los fragmentos de teoría que subiste. Gemini los leerá para dar feedback a tus alumnos.
        </p>

        {error && (
          <div style={{
            background: 'rgba(208, 17, 24, 0.2)',
            border: '1px solid var(--brand-red)',
            color: '#ff6b6b',
            padding: '0.6rem',
            borderRadius: '6px',
            fontSize: '0.85rem',
            marginBottom: '1rem'
          }}>
            {error}
          </div>
        )}

        {loading ? (
          <p>Cargando teoría...</p>
        ) : chunks.length === 0 ? (
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            padding: '1.5rem',
            borderRadius: '8px',
            textAlign: 'center',
            color: 'var(--text-secondary)',
            fontSize: '0.9rem'
          }}>
            Aún no has subido teoría para esta técnica.<br />
            <span style={{ fontSize: '0.8rem', opacity: 0.7 }}>
              Edita la técnica y usa el campo "Manual del Maestro (Teoría RAG)" para agregar contenido.
            </span>
          </div>
        ) : (
          <>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {chunks.length} {chunks.length === 1 ? 'fragmento' : 'fragmentos'} en total
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.25rem' }}>
              {chunks.map((c, idx) => (
                <div
                  key={c.id || idx}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    padding: '0.9rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                    <span>Chunk #{c.chunk_index}</span>
                    <span>{formatFecha(c.fecha_ingesta)}</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.85rem', lineHeight: '1.4', whiteSpace: 'pre-wrap' }}>
                    {c.contenido_texto}
                  </p>
                </div>
              ))}
            </div>

            <button
              onClick={handleDeleteAll}
              disabled={deleting}
              style={{
                width: '100%',
                padding: '0.75rem',
                background: 'rgba(208, 17, 24, 0.15)',
                border: '1px solid var(--brand-red)',
                color: '#ff6b6b',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '0.9rem'
              }}
            >
              {deleting ? 'Eliminando...' : '🗑 Eliminar toda mi teoría de esta técnica'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/components/UserProfileModal.jsx ---
import { useState } from 'react';
import { useTranslation } from '../i18n/translations';

export default function UserProfileModal({ isOpen, user, onClose, onUpdateSuccess, onLogout }) {
  const { t } = useTranslation(user?.idioma_preferido || 'es');
  
  const [nombre, setNombre] = useState(user?.nombre_completo || '');
  const [password, setPassword] = useState('');
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || '');
  const [loading, setLoading] = useState(false);

  if (!isOpen || !user) return null;

  // Convertir archivo a base64
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) {
        alert("La imagen es demasiado grande. El límite es 2MB.");
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarUrl(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        nombre_completo: nombre,
        avatar_url: avatarUrl || null
      };

      if (password.trim() !== '') {
        payload.password = password;
      }

      const res = await fetch(`http://localhost:8000/api/v1/auth/usuarios/${user.user_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const updatedUser = await res.json();
        onUpdateSuccess(updatedUser);
        alert("¡Perfil actualizado con éxito!");
        onClose();
      } else {
        const errorData = await res.json();
        alert(errorData.detail || "Error al actualizar perfil");
      }
    } catch (err) {
      console.error(err);
      alert("Error de conexión al servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="modal-content glass-panel" onClick={e => e.stopPropagation()} style={{ padding: '2rem', maxWidth: '400px', width: '90%', borderRadius: '12px' }}>
        <h2 style={{ margin: '0 0 1.5rem 0', textAlign: 'center', color: 'var(--brand-red)' }}>Mi Perfil</h2>
        
        <form onSubmit={handleUpdate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          
          {/* Avatar Preview & Upload */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '100px', height: '100px', borderRadius: '50%', background: 'var(--glass-bg)',
              border: '2px solid var(--brand-red)', display: 'flex', alignItems: 'center', justifyContent: 'center',
              overflow: 'hidden', fontSize: '2rem', fontWeight: 'bold'
            }}>
              {avatarUrl ? (
                <img src={avatarUrl} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <>{user.rol[0].toUpperCase()}</>
              )}
            </div>
            
            <div>
              <label htmlFor="avatar-upload" style={{ cursor: 'pointer', padding: '0.4rem 0.8rem', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', fontSize: '0.8rem' }}>
                Cambiar Foto (Max 2MB)
              </label>
              <input id="avatar-upload" type="file" accept="image/*" onChange={handleFileChange} style={{ display: 'none' }} />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Usuario / Email</label>
            <input 
              type="text" value={`@${user.username} | ${user.email}`} disabled
              style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'gray', boxSizing: 'border-box' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Nombre Completo</label>
            <input 
              type="text" required value={nombre} onChange={e => setNombre(e.target.value)}
              style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Nueva Contraseña (Opcional)</label>
            <input 
              type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Dejar en blanco para no cambiar"
              style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
            />
          </div>

          <button type="submit" disabled={loading} className="btn-primary" style={{ padding: '0.75rem', marginTop: '0.5rem' }}>
            {loading ? 'Guardando...' : 'Guardar Cambios'}
          </button>
        </form>

        <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)', margin: '1.5rem 0' }} />

        <button 
          onClick={onLogout} 
          className="btn-secondary" 
          style={{ width: '100%', padding: '0.75rem', color: '#ff6b6b', borderColor: '#ff6b6b' }}
        >
          Cerrar Sesión
        </button>
      </div>
    </div>
  );
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/i18n/translations.js ---
// Sistema de Internacionalización (i18n) Multilingüe para Corpo e Mente IA
// Los nombres de las técnicas son nombres propios universales de Jiu-Jitsu y no se traducen.

export const translations = {
  es: {
    // Header & Navegación
    brandSub: "IA",
    adminBtn: " Gestionar Sucursales (Admin)",
    profesorBtn: " Mis Técnicas",
    loginTooltip: "Cambiar de Rol / Iniciar Sesión",
    roleLabel: "Rol",
    
    // Status & Progress
    uploadingVideo: "Subiendo video...",
    processingIA: "IA Analizando Biomecánica...",
    processingHint: "Extrayendo keypoints con YOLO y comparando similitud vectorial en Qdrant...",

    // VideoUpload Page
    uploadTitle: "Sube tu ejecución",
    uploadSubtitle: "Selecciona el profesor de tu sucursal y la técnica que deseas practicar para comparar tu movimiento.",
    selectProfesorLabel: "1. SELECCIONA EL PROFESOR DE TU SUCURSAL:",
    selectTecnicaLabelStep: "2. SELECCIONA LA TÉCNICA A EVALUAR:",
    patronProfesor: "PATRÓN PROFESOR",
    dropText: "Arrastra tu video aquí o",
    dropClick: "haz clic para explorar",
    dropHint: "MP4, MOV o WebM (Máx 50MB)",
    btnChange: "Cambiar",
    btnAnalyze: "Analizar Técnica",
    alertValidVideo: "Por favor selecciona un archivo de video válido.",
    noProfessorsFound: "Cargando profesores de la sucursal...",
    noTecnicasFound: "Este profesor aún no tiene técnicas con video de referencia.",
    hasVideoTag: " Con Video de Referencia",
    noVideoTag: " Sin Video del Profesor",

    // FeedbackView Page
    feedbackTitle: "Análisis Biomecánico Completado",
    tecnicaEvaluada: "TÉCNICA EVALUADA",
    patronRefLabel: "Patrón de Referencia:",
    similarityLabel: "Similitud Biomecánica",
    detailSummary: "Ver Detalle Biomecánico Completo",
    btnReset: " Evaluar Otra Técnica",
    videoReferenciaLabel: "VIDEO DE REFERENCIA DEL PROFESOR",
    videoReferenciaDemoDe: "Demostración de",
    videoReferenciaHint: "Compara tu ejecución contra el patrón del profesor para entender las diferencias biomecánicas que la IA señala abajo.",

    // ProfesorTecnicas Page
    tecnicasTitle: "Catálogo de Técnicas",
    btnNewTecnica: "+ Nueva Técnica",
    btnClose: "Cerrar",
    loadingTecnicas: "Cargando técnicas...",
    hasVideoStatus: " Video subido por ti",
    noVideoStatus: " No tienes video para esta técnica",
    btnEdit: " Editar",
    btnDelete: " Eliminar",
    btnReplaceVideo: " Reemplazar Video",
    btnUploadVideo: " Subir Video",
    confirmDeleteTecnica: "¿Seguro que deseas eliminar esta técnica del catálogo?",
    alertVideoUploaded: "Video subido exitosamente.",
    modalPreviewTitle: "Previsualización del Video",
    modalNewTitle: "Nueva Técnica",
    modalEditTitle: "Editar Técnica",
    labelTecnicaNombre: "Nombre de la Técnica (Nombre Propio)",
    placeholderTecnicaNombre: "Ej: Armbar, Kimura, De la Riva",
    labelNivelCinturon: "Nivel Cinturón",
    labelVideoReferencia: "Video de Referencia (Demostración del Profesor)",
    dropVideoHint: "Haz clic para seleccionar o arrastra un video de referencia",
    btnSelectVideo: " Seleccionar Video",
    btnChangeVideo: " Cambiar Video",
    btnCancel: "Cancelar",
    btnSave: "Guardar Técnica",
    savingTecnica: "Guardando...",

    // Belt Levels (Español)
    beltPrefix: "Cinturón",
    belts: {
      Blanco: "Blanco",
      Azul: "Azul",
      Morado: "Morado",
      Marrón: "Marrón",
      Negro: "Negro"
    },

    // AdminSucursales Page
    adminTitle: "Gestión de Sucursales Globales",
    btnNewBranch: "+ Nueva Sucursal",
    searchMapsPlaceholder: "Pegar enlace de Google Maps para autocompletar...",
    btnSearchLocation: " Autocompletar Ubicación",
    tableNombre: "Nombre",
    tablePais: "País",
    tableCiudad: "Ciudad",
    tableDireccion: "Dirección",
    tableAcciones: "Acciones",
    confirmDeleteBranch: "¿Seguro que deseas eliminar esta sucursal?",
    modalNewBranchTitle: "Nueva Sucursal",
    modalEditBranchTitle: "Editar Sucursal",
    labelBranchNombre: "Nombre de la Sucursal",
    labelBranchPais: "País",
    labelBranchCiudad: "Ciudad",
    labelBranchDireccion: "Dirección",

    // LoginModal Component
    tabLogin: "Iniciar Sesión",
    tabSignup: "Crear Cuenta",
    labelUserOrEmail: "Usuario o Correo Electrónico",
    placeholderUserOrEmail: "Ej. admin o usuario@ejemplo.com",
    labelPassword: "Contraseña",
    btnLogin: "Ingresar",
    btnLoggingIn: "Verificando...",
    labelNombreCompleto: "Nombre Completo",
    placeholderNombreCompleto: "Ej. Lucas Lepri",
    labelUsername: "Usuario",
    labelEmail: "Correo",
    labelUserRole: "ROL DE USUARIO:",
    labelSucursal: "Sucursal / Academia",
    btnSignupSubmit: "Crear mi Cuenta",
    btnSigningUp: "Creando cuenta...",
    roleAlumno: "alumno",
    roleProfesor: "profesor"
  },

  pt: {
    // Header & Navegación
    brandSub: "IA",
    adminBtn: " Gerenciar Filiais (Admin)",
    profesorBtn: " Minhas Técnicas",
    loginTooltip: "Alterar Função / Entrar",
    roleLabel: "Função",
    
    // Status & Progress
    uploadingVideo: "Enviando vídeo...",
    processingIA: "IA Analisando Biomecânica...",
    processingHint: "Extraindo keypoints com YOLO e comparando semelhança vetorial no Qdrant...",

    // VideoUpload Page
    uploadTitle: "Envie sua execução",
    uploadSubtitle: "Selecione o professor da sua filial e a técnica que deseja praticar para comparar seu movimento.",
    selectProfesorLabel: "1. SELECIONE O PROFESSOR DA SUA FILIAL:",
    selectTecnicaLabelStep: "2. SELECIONE A TÉCNICA A AVALIAR:",
    patronProfesor: "PADRÃO PROFESSOR",
    dropText: "Arraste seu vídeo aqui ou",
    dropClick: "clique para explorar",
    dropHint: "MP4, MOV ou WebM (Máx 50MB)",
    btnChange: "Alterar",
    btnAnalyze: "Analisar Técnica",
    alertValidVideo: "Por favor selecione um arquivo de vídeo válido.",
    noProfessorsFound: "Carregando professores da filial...",
    noTecnicasFound: "Este professor ainda não possui técnicas com vídeo de referência.",
    hasVideoTag: " Com Vídeo de Referência",
    noVideoTag: " Sem Vídeo do Professor",

    // FeedbackView Page
    feedbackTitle: "Análise Biomecânica Concluída",
    tecnicaEvaluada: "TÉCNICA AVALIADA",
    patronRefLabel: "Padrão de Referência:",
    similarityLabel: "Semelhança Biomecânica",
    detailSummary: "Ver Detalhe Biomecânico Completo",
    btnReset: " Avaliar Outra Técnica",
    videoReferenciaLabel: "VÍDEO DE REFERÊNCIA DO PROFESSOR",
    videoReferenciaDemoDe: "Demonstração de",
    videoReferenciaHint: "Compare sua execução com o padrão do professor para entender as diferenças biomecânicas apontadas pela IA abaixo.",

    // ProfesorTecnicas Page
    tecnicasTitle: "Catálogo de Técnicas",
    btnNewTecnica: "+ Nova Técnica",
    btnClose: "Fechar",
    loadingTecnicas: "Carregando técnicas...",
    hasVideoStatus: " Vídeo enviado por você",
    noVideoStatus: " Sem vídeo cadastrado",
    btnEdit: " Editar",
    btnDelete: " Excluir",
    btnReplaceVideo: " Substituir Vídeo",
    btnUploadVideo: " Enviar Vídeo",
    confirmDeleteTecnica: "Deseja remover esta técnica do catálogo?",
    alertVideoUploaded: "Vídeo enviado com sucesso.",
    modalPreviewTitle: "Pré-visualização do Vídeo",
    modalNewTitle: "Nova Técnica",
    modalEditTitle: "Editar Técnica",
    labelTecnicaNombre: "Nome da Técnica (Nome Próprio)",
    placeholderTecnicaNombre: "Ex: Armbar, Kimura, De la Riva",
    labelNivelCinturon: "Nível de Faixa",
    labelVideoReferencia: "Vídeo de Referência (Demonstração do Professor)",
    dropVideoHint: "Clique para selecionar ou arraste um vídeo de referência",
    btnSelectVideo: " Selecionar Vídeo",
    btnChangeVideo: " Alterar Vídeo",
    btnCancel: "Cancelar",
    btnSave: "Salvar Técnica",
    savingTecnica: "Salvando...",

    // Belt Levels (Português)
    beltPrefix: "Faixa",
    belts: {
      Blanco: "Branca",
      Azul: "Azul",
      Morado: "Roxa",
      Marrón: "Marrom",
      Negro: "Preta"
    },

    // AdminSucursales Page
    adminTitle: "Gerenciamento de Filiais Globais",
    btnNewBranch: "+ Nova Filial",
    searchMapsPlaceholder: "Colar link do Google Maps para preencher...",
    btnSearchLocation: " Preencher Localização",
    tableNombre: "Nome",
    tablePais: "País",
    tableCiudad: "Cidade",
    tableDireccion: "Endereço",
    tableAcciones: "Ações",
    confirmDeleteBranch: "Deseja remover esta filial?",
    modalNewBranchTitle: "Nova Filial",
    modalEditBranchTitle: "Editar Filial",
    labelBranchNombre: "Nome da Filial",
    labelBranchPais: "País",
    labelBranchCiudad: "Cidade",
    labelBranchDireccion: "Endereço",

    // LoginModal Component
    tabLogin: "Entrar",
    tabSignup: "Criar Conta",
    labelUserOrEmail: "Usuário ou E-mail",
    placeholderUserOrEmail: "Ex. admin ou usuario@exemplo.com",
    labelPassword: "Senha",
    btnLogin: "Entrar",
    btnLoggingIn: "Verificando...",
    labelNombreCompleto: "Nome Completo",
    placeholderNombreCompleto: "Ex. Lucas Lepri",
    labelUsername: "Usuário",
    labelEmail: "E-mail",
    labelUserRole: "FUNÇÃO DO USUÁRIO:",
    labelSucursal: "Filial / Academia",
    btnSignupSubmit: "Criar minha Conta",
    btnSigningUp: "Criando conta...",
    roleAlumno: "aluno",
    roleProfesor: "professor"
  }
};

export function useTranslation(language = 'es') {
  const lang = (language || 'es').toLowerCase().startsWith('pt') ? 'pt' : 'es';
  const t = translations[lang] || translations.es;
  
  const getBeltLabel = (beltKey) => {
    const beltName = t.belts[beltKey] || beltKey;
    return `${t.beltPrefix} ${beltName}`;
  };

  return { t, lang, getBeltLabel };
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/pages/AdminSucursales.jsx ---
import { useState, useEffect, useRef } from 'react';
import { useTranslation } from '../i18n/translations';

// Función para extraer Latitud, Longitud, Nombre y Código de Plus Code desde cualquier URL de Google Maps o texto
function parseGoogleMapsUrl(input) {
  if (!input) return null;
  const str = input.trim();

  let placeName = null;
  let plusCode = null;

  // Extraer Plus Code si existe (ej. 6RW2+Q64, Santa Cruz de la Sierra)
  const plusMatch = str.match(/([2-9A-Z]{4,8}(?:\+|\%2[bB])[2-9A-Z]{2,4}(?:,\s*[^&/]+)?)/i);
  if (plusMatch) {
    try {
      plusCode = decodeURIComponent(plusMatch[1].replace(/\+/g, ' '));
    } catch (e) {
      plusCode = plusMatch[1];
    }
  }

  // Extraer el nombre del lugar del path /place/NOMBRE_DEL_LUGAR/
  const placeMatch = str.match(/\/place\/([^/@]+)/);
  if (placeMatch) {
    try {
      const decoded = decodeURIComponent(placeMatch[1].replace(/\+/g, ' '));
      // Si el decoded contiene un Plus Code (tiene signo + o código), guardarlo en plusCode y no como nombre comercial
      if (/[2-9A-Z]{4,8}\+[2-9A-Z]{2,4}/i.test(decoded)) {
        plusCode = decoded;
      } else {
        placeName = decoded;
      }
    } catch (e) {
      placeName = placeMatch[1].replace(/\+/g, ' ');
    }
  }

  // 1. PRIORIDAD MÁXIMA: Coordenadas exactas del PIN del lugar (!3dLatitud!4dLongitud)
  const pinMatch = str.match(/!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)/);
  if (pinMatch) {
    return { lat: parseFloat(pinMatch[1]), lng: parseFloat(pinMatch[2]), placeName, plusCode };
  }

  // 2. Coordenadas en parametros query q=lat,lng, query=lat,lng o ll=lat,lng
  const queryMatch = str.match(/(?:q|query|ll)=(-?\d+\.\d+),(-?\d+\.\d+)/);
  if (queryMatch) {
    return { lat: parseFloat(queryMatch[1]), lng: parseFloat(queryMatch[2]), placeName, plusCode };
  }

  // 3. Coordenadas del centro de la camara / encuadre visual (@lat,lng)
  const atMatch = str.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
  if (atMatch) {
    return { lat: parseFloat(atMatch[1]), lng: parseFloat(atMatch[2]), placeName, plusCode };
  }

  // 4. Coordenadas brutas separadas por coma (Ej. "-17.7530773, -63.1993584")
  const plainMatch = str.match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);
  if (plainMatch) {
    return { lat: parseFloat(plainMatch[1]), lng: parseFloat(plainMatch[2]), placeName, plusCode };
  }

  return null;
}

export default function AdminSucursales({ user, onClose, onImpersonate }) {
  const [activeTab, setActiveTab] = useState('sucursales'); // 'sucursales' | 'usuarios'
  
  // -- ESTADOS PARA SUCURSALES --
  const [sucursales, setSucursales] = useState([]);
  const [editingId, setEditingId] = useState(null); // null = Modo Crear, UUID = Modo Editar
  const { t } = useTranslation(user?.idioma_preferido);
  
  // -- ESTADOS PARA USUARIOS --
  const [usuarios, setUsuarios] = useState([]);
  const [loadingUsuarios, setLoadingUsuarios] = useState(false);
  
  // Campos del formulario
  const [nombre, setNombre] = useState('');
  const [pais, setPais] = useState('');
  const [ciudad, setCiudad] = useState('');
  const [direccion, setDireccion] = useState('');
  const [latitud, setLatitud] = useState(-22.9711);
  const [longitud, setLongitud] = useState(-43.1822);
  const [googleMapsUrl, setGoogleMapsUrl] = useState('');

  const [loading, setLoading] = useState(false);
  const [mapsFeedback, setMapsFeedback] = useState('');

  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);

  // Geocodificación inversa inteligente (OpenStreetMap + Soporte de Plus Codes)
  const reverseGeocode = async (lat, lng, fallbackName = null, urlPlusCode = null) => {
    try {
      setMapsFeedback(' Cargando dirección de la ubicación...');
      
      // Si se extrajo un Plus Code de la URL de Google Maps (ej. "6RW2+Q64, Santa Cruz de la Sierra"), asignarlo directamente
      if (urlPlusCode) {
        setDireccion(urlPlusCode);
      }

      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.address) {
          const addr = data.address;
          
          // Solo usar calle real (road, pedestrian, building), ignorar barrios o zonas imprecisas como "Piraí"
          const road = addr.road || addr.pedestrian || addr.building || addr.amenity || '';
          const houseNumber = addr.house_number ? ` #${addr.house_number}` : '';
          const fullRoad = road ? `${road}${houseNumber}` : '';

          const city = addr.city || addr.town || addr.village || addr.municipality || addr.state || '';
          const country = addr.country || '';

          // Si hay calle real y no se extrajo plus code, usar la calle real
          if (fullRoad && !urlPlusCode) {
            setDireccion(fullRoad);
          }
          if (city) setCiudad(city);
          if (country) setPais(country);
          if (fallbackName && !nombre) setNombre(fallbackName);

          setMapsFeedback(` Dirección cargada: ${city}, ${country}`);
          return;
        }
      }
    } catch (e) {
      console.error("Error obteniendo dirección inversa:", e);
    }
    if (urlPlusCode) setDireccion(urlPlusCode);
    setMapsFeedback(` Coordenadas extraídas: (${lat}, ${lng})`);
  };

  // 1. Cargar datos del backend
  const fetchSucursales = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/sucursales");
      if (res.ok) setSucursales(await res.json());
    } catch (e) { console.error("Error cargando sucursales:", e); }
  };

  const fetchUsuarios = async () => {
    setLoadingUsuarios(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/usuarios", {
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      if (res.ok) setUsuarios(await res.json());
    } catch (e) {
      console.error("Error cargando usuarios:", e);
    } finally {
      setLoadingUsuarios(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'sucursales') fetchSucursales();
    if (activeTab === 'usuarios') fetchUsuarios();
  }, [activeTab]);

  // 2. Inyección dinámica de Leaflet (OpenStreetMap 100% Gratis sin API Key)
  useEffect(() => {
    if (!document.getElementById('leaflet-css')) {
      const link = document.createElement('link');
      link.id = 'leaflet-css';
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(link);
    }

    const loadLeafletScript = () => {
      if (window.L && mapRef.current && !mapInstanceRef.current) {
        initMap();
        return;
      }
      if (!document.getElementById('leaflet-js')) {
        const script = document.createElement('script');
        script.id = 'leaflet-js';
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.onload = () => initMap();
        document.body.appendChild(script);
      }
    };

    const initMap = () => {
      if (!window.L || !mapRef.current || mapInstanceRef.current) return;

      const L = window.L;
      const map = L.map(mapRef.current).setView([latitud, longitud], 4);
      mapInstanceRef.current = map;

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map);

      const marker = L.marker([latitud, longitud], { draggable: true }).addTo(map);
      markerRef.current = marker;

      marker.on('dragend', function (e) {
        const coord = e.target.getLatLng();
        const newLat = parseFloat(coord.lat.toFixed(6));
        const newLng = parseFloat(coord.lng.toFixed(6));
        setLatitud(newLat);
        setLongitud(newLng);
        reverseGeocode(newLat, newLng);
      });

      map.on('click', function (e) {
        const coord = e.latlng;
        const newLat = parseFloat(coord.lat.toFixed(6));
        const newLng = parseFloat(coord.lng.toFixed(6));
        marker.setLatLng(coord);
        setLatitud(newLat);
        setLongitud(newLng);
        reverseGeocode(newLat, newLng);
      });
    };

    loadLeafletScript();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Actualizar posición del mapa y marcador al modificar lat/lng programáticamente
  const updateMapPosition = (newLat, newLng) => {
    if (markerRef.current) {
      markerRef.current.setLatLng([newLat, newLng]);
    }
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([newLat, newLng], 15);
    }
  };

  // Manejar pegado de enlace de Google Maps con Backend Scraping + Geocoding
  const handleGoogleMapsUrlChange = async (val) => {
    setGoogleMapsUrl(val);
    if (!val || val.trim() === '') {
      setMapsFeedback('');
      return;
    }

    setMapsFeedback(' Analizando enlace de Google Maps...');
    
    try {
      // 1. Intentar analizar con el backend scraper / geocoder
      const res = await fetch("http://localhost:8000/api/v1/sucursales/parse-gmaps-link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: val.trim() })
      });

      if (res.ok) {
        const data = await res.json();
        setLatitud(data.latitud);
        setLongitud(data.longitud);
        if (data.nombre) setNombre(data.nombre);
        if (data.direccion) setDireccion(data.direccion);
        if (data.ciudad) setCiudad(data.ciudad);
        if (data.pais) setPais(data.pais);

        updateMapPosition(data.latitud, data.longitud);
        setMapsFeedback(` ¡Ubicación obtenida con precisión! ${data.ciudad || ''}, ${data.pais || ''}`);
        return;
      }
    } catch (e) {
      console.warn("Backend parser no disponible, usando fallback cliente:", e);
    }

    // 2. Fallback a parser cliente si falla la conexión
    const coords = parseGoogleMapsUrl(val);
    if (coords) {
      setLatitud(coords.lat);
      setLongitud(coords.lng);
      if (coords.placeName) setNombre(coords.placeName);
      if (coords.plusCode) setDireccion(coords.plusCode);
      updateMapPosition(coords.lat, coords.lng);
      reverseGeocode(coords.lat, coords.lng, coords.placeName, coords.plusCode);
    } else {
      setMapsFeedback(' No se detectó un formato válido de latitud y longitud en el enlace.');
    }
  };

  // Limpiar formulario y restablecer modo creación
  const resetForm = () => {
    setEditingId(null);
    setNombre('');
    setPais('');
    setCiudad('');
    setDireccion('');
    setLatitud(-22.9711);
    setLongitud(-43.1822);
    setGoogleMapsUrl('');
    setMapsFeedback('');
    updateMapPosition(-22.9711, -43.1822);
  };

  // Iniciar edición de sucursal existente
  const handleStartEdit = (sucursal) => {
    setEditingId(sucursal.id);
    setNombre(sucursal.nombre);
    setPais(sucursal.pais);
    setCiudad(sucursal.ciudad);
    setDireccion(sucursal.direccion || '');
    setLatitud(sucursal.latitud);
    setLongitud(sucursal.longitud);
    setGoogleMapsUrl('');
    setMapsFeedback('');
    updateMapPosition(sucursal.latitud, sucursal.longitud);
  };

  // Guardar (Crear o Modificar)
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!nombre || !pais || !ciudad) {
      alert("Por favor completa los campos obligatorios.");
      return;
    }

    setLoading(true);
    const payload = { nombre, pais, ciudad, direccion, latitud, longitud };
    const url = editingId 
      ? `http://localhost:8000/api/v1/sucursales/${editingId}`
      : "http://localhost:8000/api/v1/sucursales";
    const method = editingId ? "PUT" : "POST";

    try {
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${user.token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        alert(editingId ? "¡Sucursal modificada con éxito!" : "¡Sucursal creada con éxito!");
        resetForm();
        fetchSucursales();
      } else {
        alert("Error al procesar la sucursal.");
      }
    } catch (e) {
      console.error("Error guardando sucursal:", e);
      alert("Error de conexión guardando la sucursal.");
    } finally {
      setLoading(false);
    }
  };

  // Eliminar Sucursal
  const handleDelete = async (sucursalId, sucursalNombre) => {
    if (!confirm(`¿Estás seguro de eliminar la sucursal "${sucursalNombre}"?`)) return;

    try {
      const res = await fetch(`http://localhost:8000/api/v1/sucursales/${sucursalId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${user.token}` }
      });

      if (res.ok) {
        alert("Sucursal eliminada correctamente.");
        if (editingId === sucursalId) resetForm();
        fetchSucursales();
      } else {
        alert("No se pudo eliminar la sucursal.");
      }
    } catch (e) {
      console.error("Error eliminando sucursal:", e);
      alert("Error de conexión al eliminar la sucursal.");
    }
  };

  const handleImpersonate = async (targetUserId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/auth/impersonate/${targetUserId}`, {
        method: 'POST',
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      if (res.ok) {
        const targetUser = await res.json();
        if (onImpersonate) onImpersonate(targetUser, user);
      } else {
        alert("Error al intentar impersonalizar al usuario.");
      }
    } catch (e) {
      console.error("Error de impersonalización:", e);
      alert("Error de conexión al servidor.");
    }
  };

  return (
    <div style={{ padding: '1.5rem', width: '100%', maxWidth: '100%', margin: '0 auto', color: 'white', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.75rem', color: 'var(--brand-red)' }}>
            {user?.rol === 'admin' ? t.adminTitle : 'Catálogo de Sucursales'}
          </h2>
        </div>
        <button 
          className="btn-primary" 
          onClick={onClose} 
          style={{ 
            padding: '0.75rem 1.6rem', 
            fontSize: '1rem', 
            fontWeight: 'bold', 
            borderRadius: '30px', 
            boxShadow: '0 0 20px rgba(208,17,24,0.7)', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.5rem',
            cursor: 'pointer',
            transition: 'transform 0.2s ease, box-shadow 0.2s ease'
          }}
          onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'}
          onMouseLeave={e => e.currentTarget.style.transform = 'scale(1.0)'}
        >
          Empieza a Entrenar
        </button>
      </div>

      <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('sucursales')}
          style={{
            flex: 1, padding: '0.75rem', background: 'none', border: 'none',
            borderBottom: activeTab === 'sucursales' ? '3px solid var(--brand-red)' : '3px solid transparent',
            color: activeTab === 'sucursales' ? 'white' : 'var(--text-secondary)',
            fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer'
          }}
        >
          {user?.rol === 'admin' ? 'Gestión de Sucursales' : 'Nuestras Sucursales'}
        </button>
        {user?.rol === 'admin' && (
          <button
            onClick={() => setActiveTab('usuarios')}
            style={{
              flex: 1, padding: '0.75rem', background: 'none', border: 'none',
              borderBottom: activeTab === 'usuarios' ? '3px solid var(--brand-red)' : '3px solid transparent',
              color: activeTab === 'usuarios' ? 'white' : 'var(--text-secondary)',
              fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer'
            }}
          >
            Gestión de Usuarios
          </button>
        )}
      </div>

      <div style={{ display: activeTab === 'sucursales' ? 'block' : 'none' }}>
        {/* Formulario de registro/modificación */}
        {user?.rol === 'admin' && (
          <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', width: '100%', boxSizing: 'border-box', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'white' }}>
              {editingId ? " Modificar Sucursal" : " Registrar Nueva Sucursal"}
            </h3>
            {editingId && (
              <button 
                type="button" 
                onClick={resetForm}
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', padding: '0.3rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', cursor: 'pointer' }}
              >
                Cancelar Edición
              </button>
            )}
          </div>
          
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {/* Parser de Enlace de Google Maps */}
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.15)', boxSizing: 'border-box' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', color: '#4da6ff', marginBottom: '0.25rem' }}>
                 Extraer Coordenadas desde Link de Google Maps:
              </label>
              <input 
                type="text" 
                value={googleMapsUrl} 
                onChange={e => handleGoogleMapsUrlChange(e.target.value)}
                placeholder="Pega aquí el enlace de Google Maps (Ej. https://www.google.com/maps/...)"
                style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(77,166,255,0.4)', color: 'white', fontSize: '0.8rem', boxSizing: 'border-box' }}
              />
              {mapsFeedback && (
                <div style={{ fontSize: '0.75rem', marginTop: '0.3rem', color: mapsFeedback.startsWith('') ? '#69db7c' : '#ff8787' }}>
                  {mapsFeedback}
                </div>
              )}
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                Nombre de la Sucursal *
              </label>
              <input 
                type="text" required value={nombre} onChange={e => setNombre(e.target.value)}
                placeholder="Ej. Corpo e Mente - Sede La Paz"
                style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>País *</label>
                <input 
                  type="text" required value={pais} onChange={e => setPais(e.target.value)}
                  placeholder="Ej. Bolivia"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>Ciudad *</label>
                <input 
                  type="text" required value={ciudad} onChange={e => setCiudad(e.target.value)}
                  placeholder="Ej. Santa Cruz de la Sierra"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>Dirección</label>
              <input 
                type="text" value={direccion} onChange={e => setDireccion(e.target.value)}
                placeholder="Ej. Equipetrol Norte #450"
                style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: 'rgba(208,17,24,0.1)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(208,17,24,0.3)', boxSizing: 'border-box' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)' }}>Latitud Capturada</label>
                <input type="text" readOnly value={latitud} style={{ width: '100%', background: 'transparent', border: 'none', color: 'white', fontWeight: 'bold', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)' }}>Longitud Capturada</label>
                <input type="text" readOnly value={longitud} style={{ width: '100%', background: 'transparent', border: 'none', color: 'white', fontWeight: 'bold', boxSizing: 'border-box' }} />
              </div>
            </div>

              <button type="submit" disabled={loading} className="btn-primary" style={{ marginTop: '0.5rem', padding: '0.75rem', width: '100%' }}>
                {loading ? "Procesando..." : (editingId ? "Actualizar Sucursal" : "Guardar Sucursal Global")}
              </button>
            </form>
          </div>
        )}

      {/* Lista de Sucursales Registradas con opciones de CRUD */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', width: '100%', boxSizing: 'border-box' }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>
          {user?.rol === 'admin' ? `Sucursales Registradas (${sucursales.length})` : `Explora Nuestras Sucursales (${sucursales.length})`}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
          {sucursales.map((s) => (
            <div 
              key={s.id} 
              style={{ 
                background: editingId === s.id ? 'rgba(208,17,24,0.15)' : 'rgba(255,255,255,0.04)', 
                padding: '1rem', borderRadius: '8px', 
                border: editingId === s.id ? '2px solid var(--brand-red)' : '1px solid rgba(255,255,255,0.1)',
                display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
                boxSizing: 'border-box'
              }}
            >
              <div>
                <h4 style={{ margin: '0 0 0.3rem 0', color: 'var(--brand-red)' }}>{s.nombre}</h4>
                <p style={{ margin: 0, fontSize: '0.85rem', opacity: 0.8 }}> {s.ciudad}, {s.pais}</p>
                {s.direccion && <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', opacity: 0.7 }}> {s.direccion}</p>}
                <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.75rem', opacity: 0.6 }}> Coordenadas: {s.latitud}, {s.longitud}</p>

                <div style={{ marginTop: '1rem', borderRadius: '8px', overflow: 'hidden' }}>
                  <iframe 
                    width="100%" 
                    height="180" 
                    frameBorder="0" 
                    scrolling="no" 
                    marginHeight="0" 
                    marginWidth="0" 
                    src={`https://www.openstreetmap.org/export/embed.html?bbox=${s.longitud-0.005},${s.latitud-0.005},${s.longitud+0.005},${s.latitud+0.005}&layer=mapnik&marker=${s.latitud},${s.longitud}`} 
                    style={{ border: '1px solid rgba(255,255,255,0.1)' }}
                  ></iframe>
                </div>
              </div>

              {user?.rol === 'admin' && (
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.75rem' }}>
                  <button
                    onClick={() => handleStartEdit(s)}
                    style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', background: 'rgba(77,166,255,0.2)', border: '1px solid #4da6ff', color: '#4da6ff', fontSize: '0.8rem', cursor: 'pointer' }}
                  >
                     Editar
                  </button>
                  <button
                    onClick={() => handleDelete(s.id, s.nombre)}
                    style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', background: 'rgba(208,17,24,0.2)', border: '1px solid var(--brand-red)', color: '#ff6b6b', fontSize: '0.8rem', cursor: 'pointer' }}
                  >
                     Eliminar
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      </div>

      {activeTab === 'usuarios' && (
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', width: '100%', boxSizing: 'border-box' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>Usuarios Registrados ({usuarios.length})</h3>
          {loadingUsuarios ? (
            <p>Cargando usuarios...</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
              {usuarios.map(u => (
                <div key={u.user_id} style={{
                  background: 'rgba(255,255,255,0.04)', padding: '1rem', borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.1)', display: 'flex', flexDirection: 'column', gap: '0.5rem'
                }}>
                  <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{u.nombre_completo}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>@{u.username}</div>
                  <div style={{ fontSize: '0.85rem' }}>
                    <span style={{ 
                      padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold', textTransform: 'uppercase',
                      background: u.rol === 'admin' ? 'rgba(208,17,24,0.2)' : (u.rol === 'profesor' ? 'rgba(77,166,255,0.2)' : 'rgba(255,255,255,0.1)'),
                      color: u.rol === 'admin' ? '#ff6b6b' : (u.rol === 'profesor' ? '#4da6ff' : 'white')
                    }}>
                      {u.rol}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                    Sucursal: {u.sucursal_nombre}
                  </div>
                  
                  {u.rol !== 'admin' && (
                    <button 
                      onClick={() => handleImpersonate(u.user_id)}
                      className="btn-primary"
                      style={{ marginTop: '0.5rem', padding: '0.5rem', fontSize: '0.8rem', background: 'var(--brand-red)', border: 'none' }}
                    >
                      Impersonalizar (Entrar como)
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}




--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/pages/FeedbackView.css ---
.feedback-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.feedback-header {
  text-align: center;
}

.feedback-header p {
  color: var(--text-secondary);
}

.score-card {
  display: flex;
  align-items: center;
  padding: 2rem;
  gap: 2rem;
}

.score-circle {
  width: 120px;
  height: 120px;
  flex-shrink: 0;
}

.circular-chart {
  display: block;
  margin: 0 auto;
  max-width: 100%;
  max-height: 250px;
}

.circle-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.1);
  stroke-width: 2.5;
}

.circle {
  fill: none;
  stroke-width: 2.5;
  stroke-linecap: round;
  animation: progress 1s ease-out forwards;
}

@keyframes progress {
  0% {
    stroke-dasharray: 0 100;
  }
}

.score-excellent { stroke: #10b981; }
.score-good { stroke: #f59e0b; }
.score-needs-work { stroke: var(--brand-red); }

.percentage {
  fill: var(--text-primary);
  font-family: inherit;
  font-size: 0.5em;
  font-weight: bold;
  text-anchor: middle;
}

.score-info h3 {
  margin-bottom: 0.5rem;
}

.score-info p {
  color: var(--text-secondary);
  line-height: 1.5;
}

/* Details and Summary native styling */
.feedback-details {
  padding: 1.5rem;
}

.feedback-details summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  list-style: none; /* Hide default triangle */
  font-weight: 600;
  font-size: 1.1rem;
}

.feedback-details summary::-webkit-details-marker {
  display: none;
}

.chevron {
  transition: transform 0.3s ease;
  color: var(--brand-red);
}

.feedback-details[open] .chevron {
  transform: rotate(180deg);
}

.feedback-content {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--glass-border);
  color: #d1d5db;
  line-height: 1.6;
}

.feedback-content p {
  margin-bottom: 1rem;
}

.feedback-content p:last-child {
  margin-bottom: 0;
}

.reset-btn {
  align-self: center;
  margin-top: 1rem;
}

@media (max-width: 600px) {
  .score-card {
    flex-direction: column;
    text-align: center;
  }
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/pages/FeedbackView.jsx ---
import './FeedbackView.css';
import { useTranslation } from '../i18n/translations';

export default function FeedbackView({ user, result, tecnica, onReset }) {
  if (!result) return null;

  const { t } = useTranslation(user?.idioma_preferido);

  const isExcellent = result.similitud >= 90;
  const isGood = result.similitud >= 75 && result.similitud < 90;
  
  let scoreClass = 'score-needs-work';
  if (isExcellent) scoreClass = 'score-excellent';
  else if (isGood) scoreClass = 'score-good';

  const isPt = user?.idioma_preferido === 'pt';

  // URL absoluta del video (el backend devuelve /static/videos/xxx.mp4)
  const API_BASE = "http://localhost:8000";
  const videoUrl = result.video_referencia_url
    ? `${API_BASE}${result.video_referencia_url}`
    : null;

  return (
    <div className="feedback-container">
      <div className="feedback-header">
        <h2>{t.feedbackTitle}</h2>
        <p>{isPt ? "Comparação concluída com o padrão oficial do professor." : "Comparación completada contra el patrón oficial del profesor."}</p>
      </div>

      {tecnica && (
        <div className="tecnica-comparison-card glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', borderRadius: '12px', borderLeft: '4px solid var(--brand-red)' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)', letterSpacing: '1px' }}>
            {t.tecnicaEvaluada}
          </span>
          <h3 style={{ margin: '0.25rem 0', fontSize: '1.25rem' }}>{tecnica.nombre}</h3>
          <p style={{ margin: 0, fontSize: '0.875rem', opacity: 0.8 }}>
            <strong>{t.patronRefLabel}</strong> {tecnica.profesorRef}
          </p>
        </div>
      )}

      {/* ── Video de Referencia del Profesor ────────────────── */}
      {videoUrl && (
        <div
          className="glass-panel"
          style={{
            padding: '1.25rem 1.5rem',
            borderRadius: '12px',
            borderLeft: '4px solid var(--brand-red)',
            marginBottom: '1.5rem',
          }}
        >
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 'bold',
              color: 'var(--brand-red)',
              letterSpacing: '1px',
            }}
          >
            {isPt ? 'VÍDEO DE REFERÊNCIA DO PROFESSOR' : 'VIDEO DE REFERENCIA DEL PROFESOR'}
          </span>

          {result.video_referencia_profesor_nombre && (
            <p style={{ margin: '0.35rem 0 0.75rem 0', fontSize: '0.9rem', opacity: 0.85 }}>
              <strong>{isPt ? 'Demonstração de' : 'Demostración de'}:</strong>{' '}
              {result.video_referencia_profesor_nombre}
            </p>
          )}

          <video
            src={videoUrl}
            controls
            playsInline
            preload="metadata"
            style={{
              width: '100%',
              maxHeight: '400px',
              borderRadius: '8px',
              backgroundColor: '#000',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              display: 'block',
            }}
          />

          <p
            style={{
              margin: '0.75rem 0 0 0',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              lineHeight: 1.5,
            }}
          >
            {isPt
              ? 'Compare sua execução com o padrão do professor para entender as diferenças biomecânicas apontadas pela IA abaixo.'
              : 'Compara tu ejecución contra el patrón del profesor para entender las diferencias biomecánicas que la IA señala abajo.'}
          </p>
        </div>
      )}

      <div className="score-card glass-panel">
        <div className="score-circle">
          <svg viewBox="0 0 36 36" className="circular-chart">
            <path className="circle-bg"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path className={`circle ${scoreClass}`}
              strokeDasharray={`${result.similitud}, 100`}
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <text x="18" y="20.35" className="percentage">{Math.round(result.similitud)}%</text>
          </svg>
        </div>
        <div className="score-info">
          <h3>{t.similarityLabel}</h3>
          <p>
            {isExcellent && (isPt ? "Execução excelente! Sua técnica é quase idêntica à referência do professor." : "¡Excelente ejecución! Tu técnica es casi idéntica a la referencia del profesor.")}
            {isGood && (isPt ? "Bom trabalho. Há detalhes menores a ajustar, mas a base é sólida." : "Buen trabajo. Hay detalles menores que ajustar, pero la base es sólida.")}
            {!isExcellent && !isGood && (isPt ? "Você precisa ajustar a biomecânica. Verifique os comentários da IA." : "Necesitas ajustar la biomecánica. Revisa los comentarios de la IA.")}
          </p>
        </div>
      </div>

      <details className="feedback-details glass-panel" open>
        <summary>
          <span className="summary-title">{isPt ? "Feedback da Gemini AI" : "Retroalimentación de Gemini AI"}</span>
          <svg className="chevron" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </summary>
        <div className="feedback-content">
          {result.feedback.split('\n').map((paragraph, idx) => (
            <p key={idx}>{paragraph}</p>
          ))}
        </div>
      </details>

      <button className="btn-primary reset-btn" onClick={onReset}>
        {t.btnReset}
      </button>
    </div>
  );
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/pages/ProfesorTecnicas.css ---
.profesor-tecnicas-container {
  width: 100%;
  max-width: 100%;
  height: 80vh;
  margin: 2rem auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.tecnicas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.tecnicas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.tecnica-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.2s, box-shadow 0.2s;
}

.tecnica-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.2);
}

.tecnica-info h3 {
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
  font-size: 1.2rem;
}

.badge-cinturon {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}

.cinturon-blanco { background: #f0f0f0; color: #111; text-shadow: none; }
.cinturon-azul { background: #1e3a8a; color: white; }
.cinturon-morado { background: #5b21b6; color: white; }
.cinturon-marrón { background: #78350f; color: white; }
.cinturon-negro { background: #111; color: white; border: 1px solid #333; }

.badge-categoria {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.8rem;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
}

.tecnica-info p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: 1rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-status {
  margin-top: 1rem;
  font-size: 0.85rem;
  font-weight: bold;
  padding: 0.5rem;
  border-radius: 6px;
}

.has-video {
  background: rgba(34, 197, 94, 0.1);
  color: #4ade80;
}

.no-video {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}

.tecnica-actions {
  margin-top: 1.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.btn-icon {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
  flex: 1;
}

.btn-icon:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-icon.video-btn {
  flex-basis: 100%;
  background: var(--brand-red);
  color: white;
  border: none;
  font-weight: bold;
}

.btn-icon.video-btn:hover {
  background: #a00d12;
}

.btn-icon.delete:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.5);
}

/* Modal form styles */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 90%;
  max-width: 500px;
  padding: 2rem;
}

.preview-modal {
  max-width: 700px;
}

.video-preview {
  width: 100%;
  border-radius: 8px;
  margin: 1rem 0;
  max-height: 60vh;
  background: #000;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0.8rem;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: white;
  font-family: inherit;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--brand-red);
  box-shadow: 0 0 0 2px rgba(208, 17, 24, 0.2);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

.btn-icon.theory-btn {
  flex-basis: 100%;
  background: rgba(208, 17, 24, 0.12);
  border: 1px solid var(--brand-red);
  color: #ff8a8a;
}

.btn-icon.theory-btn:hover {
  background: rgba(208, 17, 24, 0.25);
  color: #ff6b6b;
}




--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/pages/ProfesorTecnicas.jsx ---
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



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/pages/VideoUpload.css ---
.upload-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

.upload-header {
  text-align: center;
}

.upload-header p {
  color: var(--text-secondary);
}

.drop-zone {
  position: relative;
  min-height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  transition: all 0.3s ease;
  border-style: dashed;
}

.drop-zone.active {
  border-color: var(--brand-red);
  background: rgba(208, 17, 24, 0.1);
  box-shadow: 0 0 20px rgba(208, 17, 24, 0.2);
}

.file-input {
  display: none;
}

.drop-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  width: 100%;
  height: 100%;
}

.upload-icon {
  color: var(--brand-red);
  margin-bottom: 0.5rem;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0); }
}

.drop-text {
  font-size: 1.1rem;
}

.drop-text strong {
  color: var(--brand-red);
}

.drop-hint {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.file-preview {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  align-items: center;
  width: 100%;
}

.file-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  padding: 1.5rem;
  border-radius: 12px;
  width: 100%;
  box-sizing: border-box;
}

.file-name {
  font-weight: 600;
  word-break: break-all;
}

.file-size {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.file-actions {
  display: flex;
  gap: 1rem;
  width: 100%;
}

.file-actions button {
  flex: 1;
}

.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--glass-border);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.05);
}



--- ARCHIVO: ProyectoGrado/codigo_fuente/frontend/src/pages/VideoUpload.jsx ---
import { useState, useEffect } from 'react';
import './VideoUpload.css';
import { useTranslation } from '../i18n/translations';

export default function VideoUpload({ user, onUploadStart }) {
  const { t } = useTranslation(user?.idioma_preferido);

  const [profesores, setProfesores] = useState([]);
  const [selectedProfesor, setSelectedProfesor] = useState(null);
  const [tecnicas, setTecnicas] = useState([]);
  const [selectedTecnica, setSelectedTecnica] = useState(null);
  const [loadingProfesores, setLoadingProfesores] = useState(true);
  const [loadingTecnicas, setLoadingTecnicas] = useState(false);

  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);

  // 1. Cargar profesores de la sucursal del alumno
  const fetchProfesores = async () => {
    setLoadingProfesores(true);
    try {
      const sucursalQuery = user?.sucursal_id ? `?sucursal_id=${user.sucursal_id}` : '';
      const res = await fetch(`http://localhost:8000/api/v1/profesores${sucursalQuery}`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          setProfesores(data);
          setSelectedProfesor(data[0]);
        } else {
          // Fallback a todos los profesores si no hay en la sucursal específica
          const resAll = await fetch(`http://localhost:8000/api/v1/profesores`);
          if (resAll.ok) {
            const dataAll = await resAll.json();
            setProfesores(dataAll);
            if (dataAll.length > 0) setSelectedProfesor(dataAll[0]);
          }
        }
      }
    } catch (err) {
      console.error("Error cargando profesores:", err);
    } finally {
      setLoadingProfesores(false);
    }
  };

  const fetchTecnicasDelProfesor = async (profesorId) => {
    setLoadingTecnicas(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/tecnicas?profesor_id=${profesorId}`);
      if (res.ok) {
        const data = await res.json();
        setTecnicas(data);
        if (data && data.length > 0) {
          // Priorizar seleccionar una técnica que tenga video de referencia
          const conVideo = data.find(t => t.tiene_video);
          setSelectedTecnica(conVideo || data[0]);
        } else {
          setSelectedTecnica(null);
        }
      }
    } catch (err) {
      console.error("Error cargando técnicas del profesor:", err);
    } finally {
      setLoadingTecnicas(false);
    }
  };

  useEffect(() => {
    fetchProfesores();
  }, [user?.sucursal_id]);

  useEffect(() => {
    if (selectedProfesor?.user_id) {
      fetchTecnicasDelProfesor(selectedProfesor.user_id);
    }
  }, [selectedProfesor]);

  const handleProfesorChange = (e) => {
    const profId = e.target.value;
    const found = profesores.find(p => p.user_id === profId);
    if (found) setSelectedProfesor(found);
  };

  const handleTecnicaChange = (e) => {
    const techId = e.target.value;
    const found = tecnicas.find(t => t.id === techId);
    if (found) setSelectedTecnica(found);
  };

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
      alert(t.alertValidVideo);
    }
  };

  const handleSubmit = () => {
    if (file && selectedTecnica) {
      onUploadStart(file, {
        ...selectedTecnica,
        profesorRef: selectedProfesor ? selectedProfesor.nombre_completo : "Mestre Oficial",
        profesor_id: selectedProfesor?.user_id
      });
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h2>{t.uploadTitle}</h2>
        <p>{t.uploadSubtitle}</p>
      </div>

      {/* Paso 1: Selección de Profesor de la Sucursal */}
      <div className="tecnica-selector-card glass-panel" style={{ padding: '1.25rem 1.5rem', marginBottom: '1rem', borderRadius: '12px' }}>
        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--brand-red)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {t.selectProfesorLabel}
        </label>
        
        {loadingProfesores ? (
          <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>{t.noProfessorsFound}</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
            {/* Grid de Tarjetas de Profesores con Foto Arriba y Nombre Abajo */}
            <div className="profesores-container" style={{ display: 'flex', gap: '1.25rem', flexWrap: 'wrap', justifyContent: 'center', width: '100%' }}>
              {profesores.map(p => {
                const isSelected = selectedProfesor?.user_id === p.user_id;
                return (
                  <div 
                    key={p.user_id}
                    onClick={() => setSelectedProfesor(p)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      padding: '1.25rem 1.5rem',
                      borderRadius: '16px',
                      background: isSelected ? 'rgba(208, 17, 24, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                      border: isSelected ? '2px solid var(--brand-red)' : '1px solid rgba(255, 255, 255, 0.1)',
                      boxShadow: isSelected ? '0 0 20px rgba(208, 17, 24, 0.35)' : 'none',
                      cursor: 'pointer',
                      transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                      minWidth: '160px',
                      textAlign: 'center',
                      transform: isSelected ? 'scale(1.02)' : 'scale(1)'
                    }}
                  >
                    {/* Foto del Perfil del Profesor */}
                    <div style={{
                      width: '90px',
                      height: '90px',
                      borderRadius: '50%',
                      border: isSelected ? '3px solid var(--brand-red)' : '2px solid rgba(255, 255, 255, 0.2)',
                      boxShadow: isSelected ? '0 0 15px rgba(208, 17, 24, 0.5)' : 'none',
                      overflow: 'hidden',
                      background: 'linear-gradient(135deg, rgba(208,17,24,0.3) 0%, rgba(20,20,20,0.9) 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '2rem',
                      fontWeight: 'bold',
                      color: 'white',
                      marginBottom: '0.75rem'
                    }}>
                      {p.avatar_url ? (
                        <img 
                          src={p.avatar_url} 
                          alt={p.nombre_completo} 
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.style.display = 'none';
                          }}
                        />
                      ) : (
                        <span>{p.nombre_completo ? p.nombre_completo.charAt(0).toUpperCase() : 'P'}</span>
                      )}
                    </div>

                    {/* Nombre del Profesor debajo de la Foto */}
                    <span style={{ 
                      fontWeight: 'bold', 
                      fontSize: '1rem', 
                      color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                      marginTop: '0.25rem'
                    }}>
                      {p.nombre_completo}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)', marginTop: '0.2rem' }}>
                      {p.sucursal_nombre}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Select alternativo cuando hay varios profesores */}
            {profesores.length > 2 && (
              <select 
                value={selectedProfesor?.user_id || ''}
                onChange={handleProfesorChange}
                style={{
                  width: '100%',
                  padding: '0.65rem 1rem',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: 'white',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  marginTop: '0.5rem'
                }}
              >
                {profesores.map(p => (
                  <option key={p.user_id} value={p.user_id} style={{ background: '#111', color: 'white' }}>
                    {p.nombre_completo} ({p.sucursal_nombre})
                  </option>
                ))}
              </select>
            )}
          </div>
        )}
      </div>

      {/* Paso 2: Selección de Técnica enseñada por el Profesor */}
      <div className="tecnica-selector-card glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', borderRadius: '12px' }}>
        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--brand-red)', marginBottom: '0.5rem' }}>
          {t.selectTecnicaLabelStep}
        </label>

        {loadingTecnicas ? <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>{t.loadingTecnicas}</p> : (
          <>
            {tecnicas.length === 0 ? (
              <p style={{ fontSize: '0.9rem', color: '#ff8787' }}>{t.noTecnicasFound}</p>
            ) : (
              <select 
                value={selectedTecnica?.id || ''}
                onChange={handleTecnicaChange}
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
                {tecnicas.map(tech => (
                  <option key={tech.id} value={tech.id} style={{ background: '#111', color: 'white' }}>
                    {tech.nombre} {tech.tiene_video ? '' : ''}
                  </option>
                ))}
              </select>
            )}

            {selectedTecnica && (
              <div className="profesor-ref-info" style={{ marginTop: '0.85rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(255,255,255,0.03)', padding: '0.5rem 0.75rem', borderRadius: '8px' }}>
                {selectedProfesor && (
                  <div style={{ width: '32px', height: '32px', borderRadius: '50%', border: '1.5 solid var(--brand-red)', overflow: 'hidden', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(208,17,24,0.3)' }}>
                    {selectedProfesor.avatar_url ? (
                      <img src={selectedProfesor.avatar_url} alt={selectedProfesor.nombre_completo} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                      <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'white' }}>{selectedProfesor.nombre_completo.charAt(0)}</span>
                    )}
                  </div>
                )}
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontWeight: 'bold', color: 'white' }}>{selectedProfesor ? selectedProfesor.nombre_completo : ''}</span>
                  <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.7)' }}>{selectedTecnica.nombre}</span>
                </div>
                <span style={{ marginLeft: 'auto', background: selectedTecnica.tiene_video ? '#22c55e' : 'var(--brand-red)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 'bold', fontSize: '0.75rem', color: 'white' }}>
                  {selectedTecnica.tiene_video ? t.hasVideoTag : t.noVideoTag}
                </span>
              </div>
            )}
          </>
        )}
      </div>

      {/* Paso 3: Carga del Video del Alumno */}
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
            <span className="drop-text">{t.dropText} <strong>{t.dropClick}</strong></span>
            <span className="drop-hint">{t.dropHint}</span>
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
              <button type="button" className="btn-secondary" onClick={() => setFile(null)}>{t.btnChange}</button>
              <button type="button" className="btn-primary" onClick={handleSubmit}>{t.btnAnalyze}</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

