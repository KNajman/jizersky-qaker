// Offline: stránka a data ze sítě (při výpadku z cache), knihovny a obrázky z cache. Mapové dlaždice se neukládají.
const CACHE = 'qaker-v1';
const VZDY = ['./', 'index.html', 'data.json', 'cesty.json', 'obrazky/vrstevnice.svg', 'obrazky/mapy.png'];
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(VZDY)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys()
  .then(k => Promise.all(k.filter(x => x !== CACHE).map(x => caches.delete(x)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.hostname.endsWith('tile.openstreetmap.org')) return;
  const ulozit = r => { if (r.ok || r.type === 'opaque') { const k = r.clone(); caches.open(CACHE).then(c => c.put(e.request, k)); } return r; };
  if (u.origin === location.origin && !u.pathname.includes('/obrazky/'))  // stránka a data: nejdřív síť
    e.respondWith(fetch(e.request).then(ulozit).catch(() => caches.match(e.request, {ignoreSearch: true})));
  else  // knihovny z CDN, fonty, obrázky: nejdřív cache
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(ulozit)));
});
