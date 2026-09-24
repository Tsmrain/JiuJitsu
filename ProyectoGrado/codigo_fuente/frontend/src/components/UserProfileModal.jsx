import { useState } from 'react';
import { useTranslation } from '../i18n/translations';

export default function UserProfileModal({ isOpen, user, onClose, onUpdateSuccess, onLogout }) {
  if (!isOpen || !user) return null;

  const { t } = useTranslation(user.idioma_preferido || 'es');
  
  const [nombre, setNombre] = useState(user.nombre_completo || '');
  const [password, setPassword] = useState('');
  const [avatarUrl, setAvatarUrl] = useState(user.avatar_url || '');
  const [loading, setLoading] = useState(false);

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
        headers: { 'Content-Type': 'application/json' },
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
