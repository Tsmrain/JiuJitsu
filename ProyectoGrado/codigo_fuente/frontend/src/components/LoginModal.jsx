import { useState } from 'react';

export default function LoginModal({ isOpen, onClose, onLoginSuccess }) {
  const [email, setEmail] = useState('hans@corpocmente.com');
  const [password, setPassword] = useState('123456');
  const [rol, setRol] = useState('alumno');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, rol }),
      });

      if (!response.ok) {
        alert("Error al iniciar sesión.");
        setLoading(false);
        return;
      }

      const userData = await response.json();
      onLoginSuccess(userData);
      onClose();
    } catch (err) {
      console.error("Error conectando con la API de Auth:", err);
      // Fallback para pruebas sin servidor
      onLoginSuccess({
        token: `mock-jwt-${rol}`,
        user_id: "user-123",
        nombre_completo: rol === 'admin' ? "Administrador General" : (rol === 'profesor' ? "Prof. Humberto Tavares" : "Alumno Santiago"),
        email,
        rol,
        sucursal_nombre: "Corpo e Mente - Sede Principal"
      });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0, 0, 0, 0.8)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000
    }}>
      <div className="glass-panel" style={{
        width: '90%', maxWidth: '420px', padding: '2rem', borderRadius: '16px',
        border: '1px solid rgba(208, 17, 24, 0.3)', position: 'relative'
      }}>
        <button 
          onClick={onClose}
          style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', color: 'white', fontSize: '1.25rem', cursor: 'pointer' }}
        >
          ✕
        </button>

        <h2 style={{ margin: '0 0 0.5rem 0', color: 'white', fontSize: '1.5rem', textAlign: 'center' }}>
          Iniciar Sesión
        </h2>
        <p style={{ margin: '0 0 1.5rem 0', color: 'var(--text-secondary)', fontSize: '0.875rem', textAlign: 'center' }}>
          Selecciona tu rol en la academia Corpo e Mente
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--brand-red)', marginBottom: '0.3rem' }}>
              SELECCIONA ROL / PERFIL:
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
              {['alumno', 'profesor', 'admin'].map((r) => (
                <button
                  type="button"
                  key={r}
                  onClick={() => setRol(r)}
                  style={{
                    padding: '0.5rem', borderRadius: '6px', fontSize: '0.8rem', textTransform: 'capitalize',
                    border: rol === r ? '2px solid var(--brand-red)' : '1px solid rgba(255,255,255,0.1)',
                    background: rol === r ? 'var(--brand-red)' : 'rgba(255,255,255,0.05)',
                    color: 'white', cursor: 'pointer', fontWeight: rol === r ? 'bold' : 'normal'
                  }}
                >
                  {r === 'admin' ? 'Admin' : r}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
              Correo Electrónico
            </label>
            <input 
              type="email" required value={email} onChange={e => setEmail(e.target.value)}
              style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
              Contraseña
            </label>
            <input 
              type="password" required value={password} onChange={e => setPassword(e.target.value)}
              style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
            />
          </div>

          <button 
            type="submit" disabled={loading}
            className="btn btn-primary" style={{ marginTop: '0.5rem', width: '100%', padding: '0.85rem' }}
          >
            {loading ? "Ingresando..." : `Ingresar como ${rol.toUpperCase()}`}
          </button>
        </form>
      </div>
    </div>
  );
}
