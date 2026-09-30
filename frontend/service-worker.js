const CACHE_NAME = 'lumina-v8';
const STATIC_ASSETS = [
    '/',
    '/css/style.css',
    '/js/api.js',
    '/js/ui.js',
    '/js/pictos.js',
    '/js/sound.js',
    '/js/theme.js',
    '/js/auth.js',
    '/js/timer.js',
    '/js/child.js',
    '/js/activities.js',
    '/js/board.js',
    '/js/mood.js',
    '/js/admin.js',
    '/js/app.js',
    '/js/vendor/chart.umd.js',
    '/img/mascot/fox_idle.png',
    '/img/mascot/fox_happy.png',
    '/img/mascot/fox_sad.png',
    '/img/pictos/index.json',
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

// Fetch: rede primeiro (versão nova sempre que houver conexão), cache como reserva offline
self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;
    const isApi = event.request.url.includes('/api/');
    event.respondWith(
        fetch(event.request)
            .then(response => {
                if (!isApi && response.status === 200 && event.request.url.startsWith(self.location.origin)) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return response;
            })
            .catch(() => caches.match(event.request).then(cached => cached || (isApi ? Response.error() : caches.match('/'))))
    );
});
