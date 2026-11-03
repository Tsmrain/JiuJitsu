import { useState, useEffect, useRef } from 'react';
import { getTranslation } from '../i18n/translations';
import { API_BASE } from '../api/config';

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

export default function AdminSucursales({ user, onClose, onImpersonate, idioma = 'es' }) {
  const t = (key) => getTranslation(idioma, key);
  const [activeTab, setActiveTab] = useState('sucursales'); // 'sucursales' | 'usuarios'
  
  // -- BRANCH STATES --
  const [sucursales, setSucursales] = useState([]);
  const [editingId, setEditingId] = useState(null); // null = Create Mode, UUID = Edit Mode
  const [errorSucursales, setErrorSucursales] = useState(null);
  
  // -- USER STATES --
  const [usuarios, setUsuarios] = useState([]);
  const [loadingUsuarios, setLoadingUsuarios] = useState(false);
  
  // Form fields
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

  // Smart reverse geocoding (OpenStreetMap + Plus Codes)
  const reverseGeocode = async (lat, lng, fallbackName = null, urlPlusCode = null) => {
    try {
      setMapsFeedback(' Loading address from location...');
      
      if (urlPlusCode) {
        setDireccion(urlPlusCode);
      }

      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.address) {
          const addr = data.address;
          
          const road = addr.road || addr.pedestrian || addr.building || addr.amenity || '';
          const houseNumber = addr.house_number ? ` #${addr.house_number}` : '';
          const fullRoad = road ? `${road}${houseNumber}` : '';

          const city = addr.city || addr.town || addr.village || addr.municipality || addr.state || '';
          const country = addr.country || '';

          if (fullRoad && !urlPlusCode) {
            setDireccion(fullRoad);
          }
          if (city) setCiudad(city);
          if (country) setPais(country);
          if (fallbackName && !nombre) setNombre(fallbackName);

          setMapsFeedback(` Address loaded: ${city}, ${country}`);
          return;
        }
      }
    } catch (e) {
      console.error("Error obtaining reverse address:", e);
    }
    if (urlPlusCode) setDireccion(urlPlusCode);
    setMapsFeedback(` Coordinates extracted: (${lat}, ${lng})`);
  };

  // 1. Cargar datos del backend
  const fetchSucursales = async () => {
    setErrorSucursales(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/sucursales`);
      if (res.ok) {
        setSucursales(await res.json());
      } else {
        const errorMsg = "Error de conexión con el servidor. Revisa tu red.";
        setErrorSucursales(errorMsg);
        console.error("Failed to load branches:", res.status, res.statusText);
      }
    } catch (e) {
      console.error("Error loading branches:", e);
      const errorMsg = "Error de conexión con el servidor. Revisa tu red.";
      setErrorSucursales(errorMsg);
    }
  };

  const fetchUsuarios = async () => {
    setLoadingUsuarios(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/usuarios`, {
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      if (res.ok) setUsuarios(await res.json());
    } catch (e) {
      console.error("Error loading users:", e);
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
      const res = await fetch(`${API_BASE}/api/v1/sucursales/parse-gmaps-link`, {
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
      setMapsFeedback(' No valid latitude and longitude format detected in the link.');
    }
  };

  // Reset form to creation mode
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

  // Start editing existing branch
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

  // Save (Create or Update)
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!nombre || !pais || !ciudad) {
      alert("Please fill in the required fields.");
      return;
    }

    setLoading(true);
    const payload = { nombre, pais, ciudad, direccion, latitud, longitud };
    const url = editingId 
      ? `${API_BASE}/api/v1/sucursales/${editingId}`
      : `${API_BASE}/api/v1/sucursales`;
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
        alert(editingId ? t('updateSuccess') : t('createSuccess'));
        resetForm();
        fetchSucursales();
      } else {
        alert("Error processing branch.");
      }
    } catch (e) {
      console.error("Error saving branch:", e);
      alert(t('connectionError'));
    } finally {
      setLoading(false);
    }
  };

  // Delete Branch
  const handleDelete = async (sucursalId, sucursalNombre) => {
    if (!confirm(`${t('deleteConfirm')} "${sucursalNombre}"?`)) return;

    try {
      const res = await fetch(`${API_BASE}/api/v1/sucursales/${sucursalId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${user.token}` }
      });

      if (res.ok) {
        alert(t('deleteSuccess'));
        if (editingId === sucursalId) resetForm();
        fetchSucursales();
      } else {
        alert("Could not delete branch.");
      }
    } catch (e) {
      console.error("Error deleting branch:", e);
      alert(t('connectionError'));
    }
  };

  const handleImpersonate = async (targetUserId) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/impersonate/${targetUserId}`, {
        method: 'POST',
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      if (res.ok) {
        const targetUser = await res.json();
        if (onImpersonate) onImpersonate(targetUser, user);
      } else {
        alert("Error attempting to impersonate user.");
      }
    } catch (e) {
      console.error("Error impersonating:", e);
      alert("Connection error to server.");
    }
  };

  return (
    <div style={{ padding: '1rem 0.5rem', width: '100%', maxWidth: '100%', margin: '0 auto', color: 'white', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.75rem', color: 'var(--brand-red)' }}>
            {user?.rol === 'admin' ? t('globalAcademyManagement') : t('branchCatalog')}
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
            display: 'inline-flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            minHeight: '44px',
            gap: '0.5rem',
            cursor: 'pointer',
            transition: 'transform 0.2s ease, box-shadow 0.2s ease'
          }}
          onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'}
          onMouseLeave={e => e.currentTarget.style.transform = 'scale(1.0)'}
        >
          {t('startTraining')}
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
          {user?.rol === 'admin' ? t('branchManagement') : t('ourBranches')}
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
            {t('usersTab')}
          </button>
        )}
      </div>

      <div style={{ display: activeTab === 'sucursales' ? 'block' : 'none' }}>
        {/* Branch registration/edit form */}
        {user?.rol === 'admin' && (
          <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', width: '100%', boxSizing: 'border-box', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'white' }}>
              {editingId ? t('editBranch') : t('registerNewBranch')}
            </h3>
            {editingId && (
              <button 
                type="button" 
                onClick={resetForm}
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', padding: '0.3rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', cursor: 'pointer' }}
              >
                ✕ {t('close')}
              </button>
            )}
          </div>
          
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {/* Google Maps Link Parser */}
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.15)', boxSizing: 'border-box' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', color: '#4da6ff', marginBottom: '0.25rem' }}>
                {t('mapUrlHelper')}:
              </label>
              <input 
                type="text" 
                value={googleMapsUrl} 
                onChange={e => handleGoogleMapsUrlChange(e.target.value)}
                placeholder="Google Maps link (e.g. https://www.google.com/maps/...)"
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
                {t('branchName')}
              </label>
              <input 
                type="text" required value={nombre} onChange={e => setNombre(e.target.value)}
                placeholder="e.g. Corpo e Mente - Downtown"
                style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>{t('country')}</label>
                <input 
                  type="text" required value={pais} onChange={e => setPais(e.target.value)}
                  placeholder="e.g. Bolivia"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>{t('city')}</label>
                <input 
                  type="text" required value={ciudad} onChange={e => setCiudad(e.target.value)}
                  placeholder="e.g. Santa Cruz de la Sierra"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>{t('address')}</label>
              <input 
                type="text" value={direccion} onChange={e => setDireccion(e.target.value)}
                placeholder="e.g. 450 North Avenue"
                style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', boxSizing: 'border-box' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: 'rgba(208,17,24,0.1)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(208,17,24,0.3)', boxSizing: 'border-box' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)' }}>Latitud</label>
                <input type="text" readOnly value={latitud} style={{ width: '100%', background: 'transparent', border: 'none', color: 'white', fontWeight: 'bold', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)' }}>Longitud</label>
                <input type="text" readOnly value={longitud} style={{ width: '100%', background: 'transparent', border: 'none', color: 'white', fontWeight: 'bold', boxSizing: 'border-box' }} />
              </div>
            </div>

              <button type="submit" disabled={loading} className="btn-primary" style={{ marginTop: '0.5rem', padding: '0.75rem', width: '100%' }}>
                {loading ? t('processing') : (editingId ? t('updateBranch') : t('saveGlobalBranch'))}
              </button>
            </form>
          </div>
        )}

      {/* Registered Branches List with CRUD */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', width: '100%', boxSizing: 'border-box' }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>
          {user?.rol === 'admin' ? `${t('registeredBranches')} (${sucursales.length})` : `${t('exploreOurBranches')} (${sucursales.length})`}
        </h3>

        {errorSucursales && (
          <div style={{
            background: 'rgba(208, 17, 24, 0.2)',
            border: '1px solid var(--brand-red)',
            color: '#ff8787',
            padding: '0.85rem 1.25rem',
            borderRadius: '8px',
            marginBottom: '1rem',
            textAlign: 'center',
            fontWeight: 'bold',
            fontSize: '0.9rem'
          }}>
            ⚠️ {errorSucursales}
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 280px), 1fr))', gap: '1rem' }}>
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
                <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.75rem', opacity: 0.6 }}> Coordinates: {s.latitud}, {s.longitud}</p>

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
                     {t('editBranch')}
                  </button>
                  <button
                    onClick={() => handleDelete(s.id, s.nombre)}
                    style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', background: 'rgba(208,17,24,0.2)', border: '1px solid var(--brand-red)', color: '#ff6b6b', fontSize: '0.8rem', cursor: 'pointer' }}
                  >
                     {t('deleteConfirm')}
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
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>{t('usersTab')} ({usuarios.length})</h3>
          {loadingUsuarios ? (
            <p>{t('loadingStudents')}</p>
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
                    {t('branchAcademy')}: {u.sucursal_nombre}
                  </div>
                  
                  {u.rol !== 'admin' && (
                    <button 
                      onClick={() => handleImpersonate(u.user_id)}
                      className="btn-primary"
                      style={{ marginTop: '0.5rem', padding: '0.5rem', fontSize: '0.8rem', background: 'var(--brand-red)', border: 'none' }}
                    >
                      {u.rol === 'profesor' ? t('impersonateInstructor') : t('impersonateStudent')}
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

