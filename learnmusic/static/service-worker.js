/* -------------------------------------------------------------------
   Django PWA + Web-Push merged service-worker
   -------------------------------------------------------------------
   - Offline-first caching strategy (from django-pwa)
   - Push-notification display and click handling (from django-pwa-webpush)
   ------------------------------------------------------------------ */

/* ---------- 1.  Cache settings ----------------------------------- */
const STATIC_CACHE   = 'django-pwa-v' + Date.now();   // bump on every deploy
const OFFLINE_URL    = '/offline/';                  // must return 200!
const FILES_TO_CACHE = [
  OFFLINE_URL,
  '/static/css/django-pwa-app.css',
  '/static/images/icons/icon-72x72.png',
  '/static/images/icons/icon-96x96.png',
  '/static/images/icons/icon-128x128.png',
  '/static/images/icons/icon-144x144.png',
  '/static/images/icons/icon-152x152.png',
  '/static/images/icons/icon-192x192.png',
  '/static/images/icons/icon-384x384.png',
  '/static/images/icons/icon-512x512.png',
  '/static/images/icons/splash-640x1136.png',
  '/static/images/icons/splash-750x1334.png',
  '/static/images/icons/splash-1125x2436.png',
  '/static/images/icons/splash-1242x2208.png',
  '/static/images/icons/splash-828x1792.png',
  '/static/images/icons/splash-1242x2688.png',
  '/static/images/icons/splash-1536x2048.png',
  '/static/images/icons/splash-1668x2224.png',
  '/static/images/icons/splash-1668x2388.png',
  '/static/images/icons/splash-2048x2732.png',
];

/* ---------- 2.  Install: pre-cache critical assets ---------------- */
self.addEventListener('install', event => {
  self.skipWaiting();                       // activate immediately
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(FILES_TO_CACHE))
      .catch(err => {
        // Don’t brick the worker if one file 404s during development
        console.error('Pre-cache failed:', err);
      })
  );
});

/* ---------- 3.  Activate: clean out old caches -------------------- */
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames =>
      Promise.all(
        cacheNames
          .filter(name => name.startsWith('django-pwa-') && name !== STATIC_CACHE)
          .map(name => caches.delete(name))
      )
    )
  );
});

/* ---------- 4.  Fetch: network-first, fall back to cache ---------- */
self.addEventListener('fetch', event => {
  // Only handle GETs from the same origin
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== location.origin) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then(resp => {
        // Cache a clone of successful responses
        if (resp.ok) {
          const respClone = resp.clone();
          caches.open(STATIC_CACHE).then(c => c.put(event.request, respClone));
        }
        return resp;
      })
      .catch(() =>
        // Network failed – try cache, else offline page
        caches.match(event.request).then(r => r || caches.match(OFFLINE_URL))
      )
  );
});

/* ---------- 5.  Push: display the incoming notification ---------- */
self.addEventListener('push', event => {
  if (!event.data) return;

  let data;
  try {
    data = event.data.json();               // expects JSON payload
  } catch {
    // Fallback if server sent raw text
    data = { head: event.data.text() };
  }

  const title = data.head || 'Notification';
  const opts  = {
    body:   data.body   || '',
    icon:   data.icon   || '/static/images/icons/icon-192x192.png',
    badge:  data.badge  || '/static/images/icons/icon-96x96.png',
    data:   { url: data.url || '/' },
    actions: data.actions || []
  };

  event.waitUntil(self.registration.showNotification(title, opts));
});

/* ---------- 6.  Notification click: open / focus tab ------------- */
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = event.notification.data?.url || '/';

  event.waitUntil(
    // Focus an open tab if we already have one, otherwise open a new one
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(winClients => {
        for (const client of winClients) {
          if (client.url === target && 'focus' in client) return client.focus();
        }
        return clients.openWindow(target);
      })
  );
});
