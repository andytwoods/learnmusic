/*  Service Worker – Tootology PWA
    scope: “/”  (registered once from base.html)
    strategy:  • navigation = network-first → offline.html fallback
               • same-origin static = stale-while-revalidate
               • push notifications = Notifications API
*/

const VERSION         = "v4";
const STATIC_CACHE    = `tootology-static-${VERSION}`;
const DYNAMIC_CACHE   = `tootology-dynamic-${VERSION}`;

const STATIC_ASSETS = [
	"/",
	"/static/offline.html",

	/* core UI */
	"/static/css/project.css",
	"/static/js/project.js",

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

	/* ignore non-GET or cross-origin – let the browser handle them */
	if (request.method !== "GET" || !sameOrigin(request)) return;

	/* HTML – network-first, fallback to offline */
	if (request.headers.get("accept")?.includes("text/html")) {
		event.respondWith(
			fetch(request)
				.then(resp => resp)
				.catch(() => caches.match("/static/offline.html"))
		);
		return;
	}

	/* other static files – stale-while-revalidate */
	event.respondWith(
		caches.match(request).then(cached => {
			const fetchAndUpdate = fetch(request)
				.then(resp => {
					if (resp && resp.status === 200) {
						// Clone the response before using it
						const respToCache = resp.clone();
						caches.open(DYNAMIC_CACHE)
							.then(cache => cache.put(request, respToCache));
					}
					return resp;
				})
				.catch(() => cached); // network failed – use cache if we have it
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
