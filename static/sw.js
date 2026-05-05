const CACHE = "rfs-v1";
const SHELL = [
  "/read-4-sleep/static/mobile.html",
  "/read-4-sleep/static/manifest.json",
  "/read-4-sleep/generated_audio/library.json",
  "/read-4-sleep/sounds/index.json",
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  // Network-first for audio and library manifest (always want fresh)
  // Cache-first for app shell
  const url = new URL(e.request.url);
  const isAudio = /\.(mp3|wav)$/.test(url.pathname);
  const isManifest = url.pathname.endsWith("library.json") || url.pathname.endsWith("index.json");

  if (isAudio) {
    // Let audio stream directly — don't cache large files
    return;
  }

  if (isManifest) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
