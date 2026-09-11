// frontend/service-worker.js
const CACHE_NAME = 'bjj-bio-cache-v1';
const STATIC_ASSETS = [
  '/',
  '/static/style.css',
  '/static/app.js',
  '/static/manifest.json',
  '/static/icons/icon.svg'
];

// Instalación: Cachear assets críticos del shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activación: Limpieza de caches antiguos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Estrategia de Fetch:
// - Rutas API: NetworkFirst (para datos en tiempo real de tareas e histórico)
// - Assets estáticos: CacheFirst con fallback a red
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Excluir uploads pesados (POST multipart) de la cache
  if (event.request.method !== 'GET') {
    return;
  }

  // Rutas de la API -> NetworkFirst
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Clonar y guardar copia fresca si es exitosa
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Assets estáticos -> CacheFirst
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });
        return networkResponse;
      });
    })
  );
});
