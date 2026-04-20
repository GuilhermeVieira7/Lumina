const CACHE_NAME = 'sistema-tea-v2.1';
const STATIC_ASSETS = [
    '/',
    '/css/style.css',
    '/js/api.js',
    '/js/auth.js',
    '/js/app.js',
    '/js/activities.js',
    '/js/admin.js',
    '/js/sound.js',
    '/js/theme.js',
    '/js/i18n.js',
    '/manifest.json',
];

// Install
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

// Activate
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// Fetch: Network first for API, Cache first for static
self.addEventListener('fetch', event => {
    if (event.request.url.includes('/api/')) {
        // Network first for API calls
        event.respondWith(
            fetch(event.request)
                .catch(() => caches.match(event.request))
        );
    } else {
        // Cache first for static assets
        event.respondWith(
            caches.match(event.request).then(cached => {
                return cached || fetch(event.request).then(response => {
                    if (response.status === 200) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                    }
                    return response;
                });
            }).catch(() => caches.match('/'))
        );
    }
});
