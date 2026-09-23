import { useState, useEffect, useRef } from 'react';

export default function AdminSucursales({ onClose }) {
  const [sucursales, setSucursales] = useState([]);
  const [nombre, setNombre] = useState('');
  const [pais, setPais] = useState('');
  const [ciudad, setCiudad] = useState('');
  const [direccion, setDireccion] = useState('');
  const [latitud, setLatitud] = useState(-22.9711);
  const [longitud, setLongitud] = useState(-43.1822);
  const [loading, setLoading] = useState(false);

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
    // Inyectar CSS de Leaflet si no existe
    if (!document.getElementById('leaflet-css')) {
      const link = document.createElement('link');
      link.id = 'leaflet-css';
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(link);
    }

    // Inyectar JS de Leaflet si no existe
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

      // Inicializar mapa centrado en Brasil (-22.9711, -43.1822)
      const L = window.L;
      const map = L.map(mapRef.current).setView([latitud, longitud], 4);
      mapInstanceRef.current = map;

      // Tile Layer de OpenStreetMap (100% Gratuito y Libre)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map);

      // Marcador inicial
      const marker = L.marker([latitud, longitud], { draggable: true }).addTo(map);
      markerRef.current = marker;

      // Evento al arrastrar el marcador
      marker.on('dragend', function (e) {
        const coord = e.target.getLatLng();
        setLatitud(parseFloat(coord.lat.toFixed(6)));
        setLongitud(parseFloat(coord.lng.toFixed(6)));
      });

      // Evento al hacer clic en cualquier punto del mundo
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

  const handleCreateSucursal = async (e) => {
    e.preventDefault();
    if (!nombre || !pais || !ciudad) {
      alert("Por favor completa los campos obligatorios.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/sucursales", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre, pais, ciudad, direccion, latitud, longitud })
      });

      if (res.ok) {
        alert("¡Sucursal global creada con éxito!");
        setNombre('');
        setPais('');
        setCiudad('');
        setDireccion('');
        fetchSucursales();
      } else {
        alert("Error creando la sucursal.");
      }
    } catch (e) {
      console.error("Error guardando sucursal:", e);
      alert("Error de conexión guardando la sucursal.");
    } finally {
      setLoading(false);
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
            Mapa interactivo gratuito (OpenStreetMap). Haz clic en cualquier lugar del mundo para marcar las coordenadas de la academia.
          </p>
        </div>
        <button className="btn-secondary" onClick={onClose} style={{ padding: '0.5rem 1rem' }}>
          Volver a la App
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Formulario de registro */}
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', color: 'white' }}>➕ Registrar Nueva Sucursal</h3>
          
          <form onSubmit={handleCreateSucursal} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
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
              {loading ? "Guardando..." : "Guardar Sucursal Global"}
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
            style={{ width: '100%', height: '350px', borderRadius: '8px', overflow: 'hidden', background: '#222' }} 
          />
        </div>
      </div>

      {/* Lista de Sucursales Registradas */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>🌐 Sucursales Registradas ({sucursales.length})</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
          {sucursales.map((s) => (
            <div key={s.id} style={{ background: 'rgba(255,255,255,0.04)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
              <h4 style={{ margin: '0 0 0.3rem 0', color: 'var(--brand-red)' }}>{s.nombre}</h4>
              <p style={{ margin: 0, fontSize: '0.85rem', opacity: 0.8 }}>📍 {s.ciudad}, {s.pais}</p>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.75rem', opacity: 0.6 }}>Coordenadas: {s.latitud}, {s.longitud}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
