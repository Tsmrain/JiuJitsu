import { useState } from 'react';
import { getTranslation } from '../i18n/translations';
import { API_BASE } from '../api/config';

export default function UserProfileModal({ isOpen, user, onClose, onUpdateSuccess, onLogout, idioma, onLanguageChange }) {
  const [nombre, setNombre] = useState(user?.nombre_completo || '');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || '');
  const [selectedIdioma, setSelectedIdioma] = useState(user?.idioma_preferido || idioma || 'es');
  const [loading, setLoading] = useState(false);

  const t = (key) => getTranslation(selectedIdioma || idioma, key);

  if (!isOpen || !user) return null;

  // Convert file to base64
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) {
        alert("The image is too large. The limit is 2MB.");
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
        avatar_url: avatarUrl || null,
        idioma_preferido: selectedIdioma,
      };

      if (password.trim() !== '') {
        payload.password = password;
      }

      const res = await fetch(`${API_BASE}/api/v1/auth/usuarios/${user.user_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const updatedUser = await res.json();
        if (onLanguageChange) {
          onLanguageChange(selectedIdioma);
        }
        onUpdateSuccess(updatedUser);
        alert(t('profileSuccess'));
        onClose();
      } else {
        const errorData = await res.json();
        alert(errorData.detail || "Error updating profile");
      }
    } catch (err) {
      console.error(err);
      alert(t('connectionError'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="modal-content glass-panel" onClick={e => e.stopPropagation()} style={{ position: 'relative', padding: '2rem', maxWidth: '420px', width: '90%', borderRadius: '12px' }}>
        <button 
          onClick={onClose}
          aria-label="Close"
          style={{ position: 'absolute', top: '0.75rem', right: '0.75rem', width: '44px', height: '44px', background: 'transparent', border: 'none', color: 'white', fontSize: '1.2rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
        >
          ✕
        </button>
        <h2 style={{ margin: '0 0 1.5rem 0', textAlign: 'center', color: 'var(--brand-red)' }}>{t('profileTitle')}</h2>
        
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
                {t('changePhoto')}
              </label>
              <input id="avatar-upload" type="file" accept="image/*" onChange={handleFileChange} style={{ display: 'none' }} />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{t('usernameEmail')}</label>
            <input 
              type="text" value={`@${user.username} | ${user.email}`} disabled
              style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'gray', boxSizing: 'border-box' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{t('fullName')}</label>
            <input 
              type="text" required value={nombre} onChange={e => setNombre(e.target.value)}
              style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
            />
          </div>

          {/* Selector de Idioma (i18n) */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
              🌐 {t('languagePreference')}
            </label>
            <select
              value={selectedIdioma}
              onChange={(e) => setSelectedIdioma(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem',
                borderRadius: '8px',
                background: '#161b22',
                border: '1px solid rgba(255,255,255,0.25)',
                color: 'white',
                boxSizing: 'border-box',
                cursor: 'pointer'
              }}
            >
              <option value="es">🇪🇸 Español</option>
              <option value="pt">🇧🇷 Português</option>
              <option value="en">🇺🇸 English</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{t('newPassword')}</label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center', width: '100%' }}>
              <input 
                type={showPassword ? "text" : "password"} 
                value={password} 
                onChange={e => setPassword(e.target.value)}
                placeholder={t('passwordPlaceholder')}
                style={{ width: '100%', padding: '0.65rem 2.8rem 0.65rem 0.65rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
              />
              <button
                type="button"
                data-testid="toggle-profile-password-btn"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                title={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
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
                {showPassword ? (
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

          <button type="submit" disabled={loading} className="btn-primary" style={{ padding: '0.75rem', marginTop: '0.5rem', minHeight: '44px' }}>
            {loading ? t('saving') : t('saveChanges')}
          </button>
        </form>

        <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)', margin: '1.5rem 0' }} />

        <button 
          onClick={onLogout} 
          className="btn-secondary" 
          style={{ width: '100%', padding: '0.75rem', color: '#ff6b6b', borderColor: '#ff6b6b', minHeight: '44px' }}
        >
          {t('signOut')}
        </button>
      </div>
    </div>
  );
}
