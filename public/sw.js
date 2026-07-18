/* ================================================================
   Ev2Ev — Service Worker
   App-shell precache, offline fallback, and runtime caching.
   Hand-rolled (no Serwist/Workbox) to stay Turbopack-compatible.
   Bump CACHE_VERSION to force clients onto a fresh cache.
   ================================================================ */

const CACHE_VERSION = "ev2ev-v1";
const PRECACHE = `${CACHE_VERSION}-precache`;
const RUNTIME = `${CACHE_VERSION}-runtime`;
const TILES = `${CACHE_VERSION}-tiles`;

// Minimal app shell precached on install.
const APP_SHELL = [
  "/",
  "/offline",
  "/manifest.json",
  "/icons/icon-192x192.png",
  "/icons/icon-512x512.png",
];

const MAX_RUNTIME_ENTRIES = 60;
const MAX_TILE_ENTRIES = 200;

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(PRECACHE)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => !key.startsWith(CACHE_VERSION))
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

// Allow the page to trigger an immediate activation after an update.
self.addEventListener("message", (event) => {
  if (event.data === "SKIP_WAITING") self.skipWaiting();
});

function isTileRequest(url) {
  return (
    /tile\.openstreetmap\.org/.test(url.hostname) ||
    /(basemaps|tiles?|carto|maptiler|stadiamaps)/i.test(url.hostname) ||
    /\/tiles?\//i.test(url.pathname)
  );
}

function isStaticAsset(url) {
  return (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/icons/") ||
    url.pathname.startsWith("/images/") ||
    /\.(?:css|js|woff2?|ttf|png|jpg|jpeg|gif|webp|svg|ico)$/i.test(url.pathname)
  );
}

// Never cache auth/state-changing traffic.
function isBypass(url, request) {
  if (request.method !== "GET") return true;
  if (url.pathname.startsWith("/auth/")) return true;
  if (url.pathname.startsWith("/api/")) return true;
  if (/supabase\.(co|in|net)/.test(url.hostname)) return true;
  if (url.hostname.includes("supabase")) return true;
  return false;
}

async function trimCache(cacheName, maxEntries) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  if (keys.length <= maxEntries) return;
  for (let i = 0; i < keys.length - maxEntries; i++) {
    await cache.delete(keys[i]);
  }
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (isBypass(url, request)) return; // let the network handle it

  // 1) Navigations: network-first, fall back to cache, then offline page.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(RUNTIME).then((cache) => {
            cache.put(request, copy);
            trimCache(RUNTIME, MAX_RUNTIME_ENTRIES);
          });
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          return cached || (await caches.match("/offline")) || Response.error();
        })
    );
    return;
  }

  // 2) Map tiles: cache-first with a bounded tile cache.
  if (isTileRequest(url)) {
    event.respondWith(
      caches.open(TILES).then(async (cache) => {
        const cached = await cache.match(request);
        if (cached) return cached;
        try {
          const response = await fetch(request);
          if (response.ok) {
            cache.put(request, response.clone());
            trimCache(TILES, MAX_TILE_ENTRIES);
          }
          return response;
        } catch {
          return cached || Response.error();
        }
      })
    );
    return;
  }

  // 3) Static assets: stale-while-revalidate.
  if (isStaticAsset(url)) {
    event.respondWith(
      caches.open(RUNTIME).then(async (cache) => {
        const cached = await cache.match(request);
        const network = fetch(request)
          .then((response) => {
            if (response.ok) cache.put(request, response.clone());
            return response;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  // Everything else: try network, fall back to any cached copy.
  event.respondWith(fetch(request).catch(() => caches.match(request)));
});

/* ---------- Web Push (wired for later; safe no-op until used) ---------- */
self.addEventListener("push", (event) => {
  if (!event.data) return;
  let data = {};
  try {
    data = event.data.json();
  } catch {
    data = { title: "Ev2Ev", body: event.data.text() };
  }
  const options = {
    body: data.body,
    icon: data.icon || "/icons/icon-192x192.png",
    badge: "/icons/badge.png",
    vibrate: [100, 50, 100],
    data: { url: data.url || "/" },
  };
  event.waitUntil(
    self.registration.showNotification(data.title || "Ev2Ev", options)
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = event.notification.data?.url || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window" }).then((clients) => {
      const existing = clients.find((c) => "focus" in c);
      if (existing) return existing.focus();
      return self.clients.openWindow(target);
    })
  );
});
