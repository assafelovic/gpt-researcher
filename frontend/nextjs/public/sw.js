const CACHE_NAME = 'gptr-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/img/gptr-logo.png',
  '/img/gptr-icon-192.png',
  '/img/gptr-icon-512.png',
  '/img/gptr-icon-96.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
}); 