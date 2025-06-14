// Service Worker for Tootology Practice PWA

const CACHE_NAME = 'tootology-practice-v1';
const urlsToCache = [
  '/',
  '/practice/',
  '/static/css/project.css',
  '/static/js/project.js',
  '/static/js/vexflow.js',
  '/static/js/chart.js',
  '/static/favicon/android-chrome-192x192.png',
  '/static/favicon/android-chrome-512x512.png',
  '/static/favicon/favicon-16x16.png',
  '/static/favicon/favicon-32x32.png',
  '/static/favicon/apple-touch-icon.png',
  '/static/favicon/site.webmanifest',
  '/static/offline.html'
];

// Install event - cache assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event - serve from cache if available, otherwise fetch from network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached response if found
        if (response) {
          return response;
        }

        // Clone the request because it's a one-time use stream
        const fetchRequest = event.request.clone();

        // Try to fetch from network
        return fetch(fetchRequest)
          .then(response => {
            // Check if we received a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone the response because it's a one-time use stream
            const responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then(cache => {
                // Only cache same-origin requests to avoid CORS issues
                if (event.request.url.startsWith(self.location.origin)) {
                  cache.put(event.request, responseToCache);
                }
              });

            return response;
          })
          .catch(error => {
            console.log('Fetch failed; returning offline page instead.', error);

            // Check if the request is for a page (HTML)
            if (event.request.headers.get('Accept').includes('text/html')) {
              // Return the offline page
              return caches.match('/static/offline.html');
            }
          });
      })
  );
});
