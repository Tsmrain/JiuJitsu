// Configuración dinámica de API para acceso local y remoto (Mobile / Wi-Fi)
export const getApiBase = () => {
  if (typeof window !== 'undefined' && window.location && window.location.hostname) {
    const protocol = window.location.protocol || 'http:';
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:8000`;
  }
  return '';
};

export const API_BASE = getApiBase();

