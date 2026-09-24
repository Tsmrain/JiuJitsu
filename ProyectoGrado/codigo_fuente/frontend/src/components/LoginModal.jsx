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
      // Mock Fallback para pruebas sin servidor
      const isMockAdmin = loginUserOrEmail.toLowerCase() === 'admin';
      const isMockProfesor = loginUserOrEmail.toLowerCase() === 'profesor';
      onLoginSuccess({
        token: `mock-jwt-${isMockAdmin ? 'admin' : (isMockProfesor ? 'profesor' : 'user')}`,
        user_id: isMockProfesor ? "prof-123" : "00000000-0000-0000-0000-000000000000",
        nombre_completo: isMockAdmin ? "Administrador General" : (isMockProfesor ? "Mestre Humberto Tavares" : "Alumno Santiago"),
        username: loginUserOrEmail,
        email: `${loginUserOrEmail}@corpocmente.com`,
        rol: isMockAdmin ? 'admin' : (isMockProfesor ? 'profesor' : 'alumno'),
        sucursal_id: "11111111-1111-1111-1111-111111111111",
        sucursal_nombre: "Corpo e Mente - Sede Principal Rio de Janeiro",
        idioma_preferido: user?.idioma_preferido || 'es'
      });
      onClose();
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
