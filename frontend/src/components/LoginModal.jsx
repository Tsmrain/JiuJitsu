import { useState, useEffect } from 'react';
import { getTranslation } from '../i18n/translations';
import { API_BASE } from '../api/config';

export default function LoginModal({ isOpen, user, onClose, onLoginSuccess, idioma = 'es' }) {
  const [tab, setTab] = useState('login'); // 'login' | 'signup'
  const t = (key) => getTranslation(idioma, key);

  // Login form state (sin credenciales hardcodeadas por seguridad)
  const [loginUserOrEmail, setLoginUserOrEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // Signup form state
  const [signupNombre, setSignupNombre] = useState('');
  const [signupUsername, setSignupUsername] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [showSignupPassword, setShowSignupPassword] = useState(false);
  const [signupRol, setSignupRol] = useState('alumno');
  const [signupSucursalId, setSignupSucursalId] = useState('');

  const [sucursales, setSucursales] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (isOpen) {
      // Load branches for signup form
      fetch(`${API_BASE}/api/v1/sucursales`)
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            setSucursales(data);
            if (data.length > 0) setSignupSucursalId(data[0].id);
          }
        })
        .catch(err => console.error("Error loading branches:", err));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');

    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username_or_email: loginUserOrEmail,
          password: loginPassword,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: t('incorrectCredentials') }));
        setErrorMsg(errData.detail || t('incorrectCredentials'));
        setLoading(false);
        return;
      }

      const userData = await response.json();
      // Respetar idioma_preferido del backend o idioma actual en localStorage (nunca forzar 'en')
      const targetIdioma = userData?.idioma_preferido || idioma || localStorage.getItem('app_idioma') || 'es';
      onLoginSuccess({
        ...userData,
        idioma_preferido: targetIdioma
      });
      onClose();
    } catch (err) {
      console.error("Error connecting to Auth API:", err);
      setErrorMsg(t('connectionError'));
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
      setErrorMsg(t('adminRoleReserved'));
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/signup`, {
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
        const errData = await response.json().catch(() => ({ detail: t('errorRegistering') }));
        setErrorMsg(errData.detail || t('errorRegistering'));
        setLoading(false);
        return;
      }

      const userData = await response.json();
      const targetIdioma = userData?.idioma_preferido || idioma || localStorage.getItem('app_idioma') || 'es';
      onLoginSuccess({
        ...userData,
        idioma_preferido: targetIdioma
      });
      onClose();
    } catch (err) {
      console.error("Error registering account:", err);
      alert(err.message || t('errorRegistering'));
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
          style={{ position: 'absolute', top: '0.75rem', right: '0.75rem', width: '44px', height: '44px', background: 'none', border: 'none', color: 'white', fontSize: '1.25rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          title={t('close')}
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
              fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer', minHeight: '44px'
            }}
          >
            {t('loginTab')}
          </button>
          <button
            onClick={() => { setTab('signup'); setErrorMsg(''); }}
            style={{
              flex: 1, padding: '0.75rem', background: 'none', border: 'none',
              borderBottom: tab === 'signup' ? '3px solid var(--brand-red)' : '3px solid transparent',
              color: tab === 'signup' ? 'white' : 'var(--text-secondary)',
              fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer', minHeight: '44px'
            }}
          >
            {t('signupTab')}
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

        {/* Login Form */}
        {tab === 'login' && (
          <form onSubmit={handleLoginSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                {t('usernameOrEmail')}
              </label>
              <input 
                type="text" required 
                data-testid="login-username-input"
                value={loginUserOrEmail} 
                onChange={e => setLoginUserOrEmail(e.target.value)}
                placeholder="admin or student@email.com"
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                {t('password')}
              </label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center', width: '100%' }}>
                <input 
                  type={showLoginPassword ? "text" : "password"} 
                  required 
                  data-testid="login-password-input"
                  value={loginPassword} 
                  onChange={e => setLoginPassword(e.target.value)}
                  placeholder="••••••••"
                  style={{ width: '100%', padding: '0.75rem 2.8rem 0.75rem 0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
                />
                <button
                  type="button"
                  data-testid="toggle-login-password-btn"
                  onClick={() => setShowLoginPassword(!showLoginPassword)}
                  aria-label={showLoginPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  title={showLoginPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  style={{
                    position: 'absolute',
                    right: '0.3rem',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '0.4rem',
                    minWidth: '44px',
                    minHeight: '44px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'rgba(255,255,255,0.7)',
                    outline: 'none'
                  }}
                >
                  {showLoginPassword ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                      <line x1="1" y1="1" x2="23" y2="23"></line>
                    </svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <button 
              type="submit" disabled={loading}
              className="btn btn-primary" style={{ marginTop: '0.5rem', width: '100%', padding: '0.85rem', minHeight: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              {loading ? t('signingIn') : t('signIn')}
            </button>
          </form>
        )}

        {/* Signup Form */}
        {tab === 'signup' && (
          <form onSubmit={handleSignupSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                {t('fullName')}
              </label>
              <input 
                type="text" required value={signupNombre} onChange={e => setSignupNombre(e.target.value)}
                placeholder="e.g. John Doe"
                style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                  {t('usernameField')}
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
                {t('password')}
              </label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center', width: '100%' }}>
                <input 
                  type={showSignupPassword ? "text" : "password"} 
                  required 
                  data-testid="signup-password-input"
                  value={signupPassword} 
                  onChange={e => setSignupPassword(e.target.value)}
                  placeholder="••••••••"
                  style={{ width: '100%', padding: '0.65rem 2.8rem 0.65rem 0.65rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
                />
                <button
                  type="button"
                  data-testid="toggle-signup-password-btn"
                  onClick={() => setShowSignupPassword(!showSignupPassword)}
                  aria-label={showSignupPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  title={showSignupPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  style={{
                    position: 'absolute',
                    right: '0.3rem',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '0.4rem',
                    minWidth: '44px',
                    minHeight: '44px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'rgba(255,255,255,0.7)',
                    outline: 'none'
                  }}
                >
                  {showSignupPassword ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                      <line x1="1" y1="1" x2="23" y2="23"></line>
                    </svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--brand-red)', marginBottom: '0.3rem' }}>
                {t('userRole')}
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
                    {r === 'alumno' ? t('studentRole') : t('instructorRole')}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                {t('branchAcademy')}
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
              className="btn btn-primary" style={{ marginTop: '0.5rem', width: '100%', padding: '0.85rem', minHeight: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              {loading ? t('creatingAccount') : t('signupTab')}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
