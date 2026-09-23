import { useState, useEffect, useRef } from 'react';

// Función para extraer Latitud y Longitud desde cualquier URL de Google Maps o formato de texto
function parseGoogleMapsUrl(input) {
  if (!input) return null;
  const str = input.trim();

  // 1. Coordenadas en formato @lat,lng (Formato estándar Google Maps Web: https://www.google.com/maps/place/.../@-22.9711,-43.1822,15z)
  const atMatch = str.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
  if (atMatch) {
    return { lat: parseFloat(atMatch[1]), lng: parseFloat(atMatch[2]) };
  }

  // 2. Coordenadas en parametros q=lat,lng o query=lat,lng
  const queryMatch = str.match(/(?:q|query)=(-?\d+\.\d+),(-?\d+\.\d+)/);
  if (queryMatch) {
    return { lat: parseFloat(queryMatch[1]), lng: parseFloat(queryMatch[2]) };
  }

  // 3. Coordenadas brutas separadas por coma (Ej. "-22.9711, -43.1822")
  const plainMatch = str.match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);
  if (plainMatch) {
    return { lat: parseFloat(plainMatch[1]), lng: parseFloat(plainMatch[2]) };
  }

  return null;
}

export default function AdminSucursales({ onClose }) {
  const [sucursales, setSucursales] = useState([]);
  const [editingId, setEditingId] = useState(null); // null = Modo Crear, UUID = Modo Editar
  
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

  // 1. Cargar sucursales existentes del backend
  const fetchSucursales = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/sucursales");
      if (res.ok) {
        const data = await res.json();
        setSucursales(data);
      }
    } catch (e) {
      console.error("Error cargando sucursales:", e);
    }
  };

  useEffect(() => {
    fetchSucursales();
  }, []);

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
        setLatitud(parseFloat(coord.lat.toFixed(6)));
        setLongitud(parseFloat(coord.lng.toFixed(6)));
      });

      map.on('click', function (e) {
        const coord = e.latlng;
        marker.setLatLng(coord);
        setLatitud(parseFloat(coord.lat.toFixed(6)));
        setLongitud(parseFloat(coord.lng.toFixed(6)));
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
      mapInstanceRef.current.setView([newLat, newLng], 14);
    }
  };

  // Manejar pegado de enlace de Google Maps
  const handleGoogleMapsUrlChange = (val) => {
    setGoogleMapsUrl(val);
    const coords = parseGoogleMapsUrl(val);
    if (coords) {
      setLatitud(coords.lat);
      setLongitud(coords.lng);
      updateMapPosition(coords.lat, coords.lng);
      setMapsFeedback(`✅ Coordenadas extraídas con éxito: (${coords.lat}, ${coords.lng})`);
    } else if (val.trim() !== '') {
      setMapsFeedback('⚠️ No se detectó un formato válido de latitud y longitud en el enlace.');
    } else {
      setMapsFeedback('');
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
        headers: { "Content-Type": "application/json" },
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
        method: "DELETE"
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

  return (
    <div style={{ padding: '2rem', maxWidth: '1100px', margin: '0 auto', color: 'white' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.75rem', color: 'var(--brand-red)' }}>
            📍 Gestión Multi-Tenant de Sucursales Globales
          </h2>
          <p style={{ margin: '0.25rem 0 0 0', opacity: 0.8, fontSize: '0.9rem' }}>
            Crear, editar y eliminar sucursales. Puedes hacer clic en el mapa o pegar un enlace de Google Maps para obtener latitud y longitud automáticamente.
          </p>
        </div>
        <button className="btn-secondary" onClick={onClose} style={{ padding: '0.5rem 1rem' }}>
          Volver a la App
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Formulario de registro/modificación */}
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'white' }}>
              {editingId ? "✏️ Modificar Sucursal" : "➕ Registrar Nueva Sucursal"}
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
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.15)' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', color: '#4da6ff', marginBottom: '0.25rem' }}>
                🔗 Extraer Coordenadas desde Link de Google Maps:
              </label>
              <input 
                type="text" 
                value={googleMapsUrl} 
                onChange={e => handleGoogleMapsUrlChange(e.target.value)}
                placeholder="Pega aquí el enlace de Google Maps (Ej. https://www.google.com/maps/...)"
                style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(77,166,255,0.4)', color: 'white', fontSize: '0.8rem' }}
              />
              {mapsFeedback && (
                <div style={{ fontSize: '0.75rem', marginTop: '0.3rem', color: mapsFeedback.startsWith('✅') ? '#69db7c' : '#ff8787' }}>
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
                placeholder="Ej. Corpo e Mente - Sede Tokio"
                style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>País *</label>
                <input 
                  type="text" required value={pais} onChange={e => setPais(e.target.value)}
                  placeholder="Ej. Japón"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>Ciudad *</label>
                <input 
                  type="text" required value={ciudad} onChange={e => setCiudad(e.target.value)}
                  placeholder="Ej. Shibuya"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>Dirección</label>
              <input 
                type="text" value={direccion} onChange={e => setDireccion(e.target.value)}
                placeholder="Ej. Dogenzaka 2-24-1"
                style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: 'rgba(208,17,24,0.1)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(208,17,24,0.3)' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)' }}>Latitud Capturada</label>
                <input type="text" readOnly value={latitud} style={{ width: '100%', background: 'transparent', border: 'none', color: 'white', fontWeight: 'bold' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--brand-red)' }}>Longitud Capturada</label>
                <input type="text" readOnly value={longitud} style={{ width: '100%', background: 'transparent', border: 'none', color: 'white', fontWeight: 'bold' }} />
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary" style={{ marginTop: '0.5rem', padding: '0.75rem' }}>
              {loading ? "Procesando..." : (editingId ? "Actualizar Sucursal" : "Guardar Sucursal Global")}
            </button>
          </form>
        </div>

        {/* Contenedor del Mapa OpenStreetMap */}
        <div className="glass-panel" style={{ padding: '1rem', borderRadius: '12px', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 'bold', marginBottom: '0.5rem', opacity: 0.85 }}>
            🗺️ MAPA MUNDIAL INTERACTIVO (OPENSTREETMAP - GRATIS)
          </span>
          <div 
            ref={mapRef} 
            style={{ width: '100%', height: '400px', borderRadius: '8px', overflow: 'hidden', background: '#222' }} 
          />
        </div>
      </div>

      {/* Lista de Sucursales Registradas con opciones de CRUD */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>🌐 Sucursales Registradas ({sucursales.length})</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
          {sucursales.map((s) => (
            <div 
              key={s.id} 
              style={{ 
                background: editingId === s.id ? 'rgba(208,17,24,0.15)' : 'rgba(255,255,255,0.04)', 
                padding: '1rem', borderRadius: '8px', 
                border: editingId === s.id ? '2px solid var(--brand-red)' : '1px solid rgba(255,255,255,0.1)',
                display: 'flex', flexDirection: 'column', justifyContent: 'space-between'
              }}
            >
              <div>
                <h4 style={{ margin: '0 0 0.3rem 0', color: 'var(--brand-red)' }}>{s.nombre}</h4>
                <p style={{ margin: 0, fontSize: '0.85rem', opacity: 0.8 }}>📍 {s.ciudad}, {s.pais}</p>
                {s.direccion && <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', opacity: 0.7 }}>🏠 {s.direccion}</p>}
                <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.75rem', opacity: 0.6 }}>🌐 Coordenadas: {s.latitud}, {s.longitud}</p>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.75rem' }}>
                <button
                  onClick={() => handleStartEdit(s)}
                  style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', background: 'rgba(77,166,255,0.2)', border: '1px solid #4da6ff', color: '#4da6ff', fontSize: '0.8rem', cursor: 'pointer' }}
                >
                  ✏️ Editar
                </button>
                <button
                  onClick={() => handleDelete(s.id, s.nombre)}
                  style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', background: 'rgba(208,17,24,0.2)', border: '1px solid var(--brand-red)', color: '#ff6b6b', fontSize: '0.8rem', cursor: 'pointer' }}
                >
                  🗑️ Eliminar
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

