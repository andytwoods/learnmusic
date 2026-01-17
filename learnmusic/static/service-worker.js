/*  Service Worker – Tootology PWA
    scope: "/"  (registered once from base.html)
    strategy:  • navigation = network-first → offline.html fallback
               • same-origin static = stale-while-revalidate
               • push notifications = Notifications API
*/

const VERSION         = "v10";
const STATIC_CACHE    = `tootology-static-${VERSION}`;
const DYNAMIC_CACHE   = `tootology-dynamic-${VERSION}`;

const STATIC_ASSETS = [
	"/",
	"/static/offline.html",

	/* core UI */
	"/static/css/project.css",
	"/static/css/sf.css",
	"/static/js/project.js",
	"/static/js/vexflow.js",

	/* vendor dependencies (offline support) */
	"/static/css/vendor/fontawesome.min.css",
	"/static/css/vendor/bootstrap.min.css",
	"/static/js/vendor/htmx.min.js",
	"/static/js/vendor/bootstrap.bundle.min.js",
	"/static/js/vendor/sweetalert2.min.js",

	/* webfonts (Font Awesome icons) */
	"/static/css/webfonts/fa-brands-400.woff2",
	"/static/css/webfonts/fa-brands-400.ttf",
	"/static/css/webfonts/fa-solid-900.woff2",
	"/static/css/webfonts/fa-solid-900.ttf",
	"/static/css/webfonts/fa-regular-400.woff2",
	"/static/css/webfonts/fa-regular-400.ttf",

	/* instrument data (for practice pages) */
	"/static/instruments/trumpet.json",
	"/static/instruments/trombone.json",
	"/static/instruments/tuba.json",
	"/static/instruments/tenor-horn.json",
	"/static/instruments/soprano_trombone.json",
	"/static/instruments/piccolo_trumpet.json",

	/* icons / manifest */
	"/static/favicon/android-chrome-192x192.png",
	"/static/favicon/android-chrome-512x512.png",
	"/static/favicon/favicon-32x32.png",
	"/static/favicon/favicon-16x16.png",
	"/static/favicon/apple-touch-icon.png",
	"/static/favicon/site.webmanifest"
];

/* ---------- install ----------------------------------------------------- */
self.addEventListener("install", event => {
	event.waitUntil(
		caches.open(STATIC_CACHE)
			.then(cache => cache.addAll(STATIC_ASSETS))
			.then(() => self.skipWaiting())
	);
});

/* ---------- activate ---------------------------------------------------- */
self.addEventListener("activate", event => {
	event.waitUntil(
		caches.keys().then(keys =>
			Promise.all(
				keys
					.filter(key => ![STATIC_CACHE, DYNAMIC_CACHE].includes(key))
					.map(key => caches.delete(key))
			)
		).then(() => self.clients.claim())
	);
});

/* ---------- helpers ----------------------------------------------------- */
const sameOrigin = req => new URL(req.url).origin === location.origin;

/* ---------- fetch ------------------------------------------------------- */
self.addEventListener("fetch", event => {
  const { request } = event;

  // ignore non-GET or cross-origin – let the browser handle them
  if (request.method !== "GET" || new URL(request.url).origin !== location.origin) return;

  // HTML – cache-first with network update (for offline support)
  if (request.headers.get("accept")?.includes("text/html")) {
    event.respondWith(
      caches.match(request).then(cached => {
        console.log('[SW] HTML request:', request.url, 'Cached:', !!cached);

        const fetchAndCache = fetch(request)
          .then(resp => {
            if (resp && resp.status === 200) {
              console.log('[SW] Fetched HTML from network, caching:', request.url);
              const copy = resp.clone();
              event.waitUntil(
                caches.open(DYNAMIC_CACHE).then(cache => {
                  cache.put(request, copy);
                  console.log('[SW] Cached HTML:', request.url);
                })
              );
            }
            return resp;
          })
          .catch((err) => {
            console.log('[SW] Network failed for HTML:', request.url, err);
            return cached || caches.match("/static/offline.html");
          });

        // Return cached immediately if available, otherwise wait for network
        return cached || fetchAndCache;
      })
    );
    return;
  }

  // other static files – stale-while-revalidate
  event.respondWith(
    caches.match(request).then(cached => {
      const fetchAndUpdate = fetch(request)
        .then(resp => {
          if (resp && resp.status === 200) {
            const copy = resp.clone();
            // ensure the put finishes even if the handler returns
            event.waitUntil(
              caches.open(DYNAMIC_CACHE).then(cache => cache.put(request, copy))
            );
          }
          return resp;
        })
        // If network fails: use cache if available; otherwise return a Response
        .catch(() => cached || Response.error());

      // If we have a cached Response, return it immediately; otherwise wait for network
      return cached || fetchAndUpdate;
    })
  );
});


/* ---------- push -------------------------------------------------------- */
self.addEventListener("push", event => {
	let data = {};
	try { data = event.data?.json() ?? {}; } catch { data.body = event.data?.text(); }

	const title   = data.title || "Time to practise!";
	const options = {
		body   : data.body  || "Open Tootology and start your drill.",
		icon   : "/static/favicon/android-chrome-192x192.png",
		badge  : "/static/favicon/favicon-32x32.png",
		data   : data.data  || {},
		actions: data.actions || [
			{ action: "open",  title: "Open App" },
			{ action: "close", title: "Dismiss"  }
		]
	};

	event.waitUntil(self.registration.showNotification(title, options));
});

/* ---------- notification click ----------------------------------------- */
self.addEventListener("notificationclick", event => {
	event.notification.close();
	if (event.action === "close") return;

	event.waitUntil(
		clients.matchAll({ type: "window", includeUncontrolled: true })
			.then(list => {
				for (const client of list) {
					if (client.url.includes("/notes/learning/")) return client.focus();
				}
				return clients.openWindow("/notes/learning/");
			})
	);
});
