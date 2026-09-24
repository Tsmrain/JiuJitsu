import { useState } from 'react'
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
  const [appState, setAppState] = useState('IDLE'); // IDLE, UPLOADING, PROCESSING, FEEDBACK, ADMIN_PANEL, PROFESOR_PANEL
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [selectedTecnica, setSelectedTecnica] = useState(null);

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
        feedback: (user?.idioma_preferido || 'es') === 'pt' 
          ? "Sua postura base é excelente e os keypoints do seu quadril coincidem com o padrão.\n\nNo entanto, o ângulo do seu braço direito durante a pegada está ligeiramente desviado (15 graus mais aberto que o professor). Isso reduz a alavanca. Ajuste o cotovelo mais perto das costelas para finalizar o movimento."
          : "Tu postura base es excelente y los keypoints de tu cadera coinciden con el patrón.\n\nSin embargo, el ángulo de tu brazo derecho durante el agarre está ligeramente desviado (15 grados más abierto que el profesor). Esto reduce la palanca. Ajusta el codo más cerca de tus costillas para finalizar el movimiento."
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
        <div className="brand" onClick={() => setAppState('IDLE')} style={{ cursor: 'pointer' }}>
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

      <main style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {appState === 'ADMIN_PANEL' && (
          <AdminSucursales 
            user={user} 
            onClose={() => setAppState('IDLE')} 
            onImpersonate={(newUser, currentAdmin) => { 
              setOriginalAdminUser(currentAdmin); 
              setUser(newUser); 
              setAppState('IDLE'); 
            }} 
          />
        )}

        {appState === 'PROFESOR_PANEL' && (
          <ProfesorTecnicas user={user} onClose={() => setAppState('IDLE')} />
        )}

        {appState === 'IDLE' && (
          <VideoUpload user={user} onUploadStart={handleUploadStart} />
        )}

        {(appState === 'UPLOADING' || appState === 'PROCESSING') && (
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem'}}>
            <ProgressRing 
              value={appState === 'UPLOADING' ? uploadProgress : 100} 
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
        onLoginSuccess={(userData) => setUser(userData)} 
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
