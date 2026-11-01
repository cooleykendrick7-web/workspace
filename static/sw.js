// Workspace service worker: cache ONLY the app shell, never data.
const CACHE = 'workspace-shell-v1';
const SHELL = ['/static/icons/icon-192.png', '/static/icons/icon-512.png', '/manifest.webmanifest'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (SHELL.includes(url.pathname)) { e.respondWith(caches.match(e.request).then(r => r || fetch(e.request))); }
});
