// Service Worker for Tootology Practice PWA

const CACHE_NAME = 'tootology-practice-v2';
const STATIC_CACHE_NAME = 'tootology-static-v2';
const DYNAMIC_CACHE_NAME = 'tootology-dynamic-v2';

// Assets to cache on install
const urlsToCache = [
  '/',
  '/practice/',
  '/notes/learning/',
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
  '/static/offline.html',
  'https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.3/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.3/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/sweetalert2@11',
  'https://unpkg.com/htmx.org@2.0.4',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.1/css/all.min.css'
];

// Install event - cache assets
self.addEventListener('install', event => {
  console.log('[Service Worker] Installing Service Worker...');
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Pre-caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('[Service Worker] Installation complete');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[Service Worker] Activating Service Worker...');
  const cacheWhitelist = [STATIC_CACHE_NAME, DYNAMIC_CACHE_NAME];
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheWhitelist.indexOf(cacheName) === -1) {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[Service Worker] Claiming clients');
        return self.clients.claim();
      })
  );
});

// Helper function to determine if a request should be cached
function isRequestCacheable(request) {
  const url = new URL(request.url);

  // Don't cache API calls or admin pages
  if (url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/admin/')) {
    return false;
  }

  // Only cache GET requests
  if (request.method !== 'GET') {
    return false;
  }

  return true;
}

// Fetch event - implement stale-while-revalidate strategy
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        // Return cached response immediately if available (stale)
        const fetchPromise = fetch(event.request.clone())
          .then(networkResponse => {
            // If we got a valid response and the request is cacheable
            if (networkResponse && networkResponse.status === 200 && isRequestCacheable(event.request)) {
              // Cache the new response for next time
              const responseToCache = networkResponse.clone();
              caches.open(DYNAMIC_CACHE_NAME)
                .then(cache => {
                  cache.put(event.request, responseToCache);
                });
            }
            return networkResponse;
          })
          .catch(error => {
            console.log('[Service Worker] Fetch failed:', error);

            // If it's an HTML request, return the offline page
            if (event.request.headers.get('Accept').includes('text/html')) {
              return caches.match('/static/offline.html');
            }

            // For other resources, we've already returned the cached version if available
            // or we'll just let the error propagate
          });

        // Return the cached response if we have it, otherwise wait for the network response
        return cachedResponse || fetchPromise;
      })
  );
});

// Push notification event handler
self.addEventListener('push', event => {
  console.log('[Service Worker] Push received');

  let notificationData = {};

  if (event.data) {
    try {
      notificationData = event.data.json();
    } catch (e) {
      notificationData = {
        title: 'Tootology Notification',
        body: event.data.text(),
        icon: '/static/favicon/android-chrome-192x192.png'
      };
    }
  } else {
    notificationData = {
      title: 'Tootology Notification',
      body: 'New notification from Tootology',
      icon: '/static/favicon/android-chrome-192x192.png'
    };
  }

  const options = {
    body: notificationData.body || 'Time to practice!',
    icon: notificationData.icon || '/static/favicon/android-chrome-192x192.png',
    badge: '/static/favicon/favicon-32x32.png',
    data: notificationData.data || {},
    actions: notificationData.actions || [
      { action: 'open', title: 'Open App' },
      { action: 'close', title: 'Dismiss' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(notificationData.title || 'Tootology Notification', options)
  );
});

// Notification click event handler
self.addEventListener('notificationclick', event => {
  console.log('[Service Worker] Notification click received', event);

  event.notification.close();

  if (event.action === 'open' || !event.action) {
    // Open the app and focus if already open
    event.waitUntil(
      clients.matchAll({ type: 'window' })
        .then(clientList => {
          // If we have a client, focus it
          for (const client of clientList) {
            if (client.url.includes('/notes/learning/') && 'focus' in client) {
              return client.focus();
            }
          }
          // Otherwise open a new window
          if (clients.openWindow) {
            return clients.openWindow('/notes/learning/');
          }
        })
    );
  }
});
