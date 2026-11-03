// Configuración unificada de API mediante Reverse Proxy de Vite
// Al usar rutas relativas (''), todas las peticiones (/api, /static) son proxeadas por Vite
// hacia FastAPI (localhost:8000), garantizando compatibilidad idéntica en localhost,
// red local (LAN) y túneles públicos (Cloudflare Tunnel) sin problemas de CORS ni puertos adicionales.
export const getApiBase = () => '';

export const API_BASE = getApiBase();
