// Service Worker for Vogelring app
// This service worker will check for app updates and refresh the page when a new version is available

const CACHE_NAME = 'vogelring-cache-v1';
const APP_VERSION_URL = '/version.json';
let currentVersion = null;

// Install event - cache basic assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Install');
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activate');
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[ServiceWorker] Removing old cache', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Check for app updates periodically
const checkForUpdates = async () => {
  try {
    // Add cache-busting query parameter
    const versionUrl = `${APP_VERSION_URL}?_=${Date.now()}`;
    const response = await fetch(versionUrl, { cache: 'no-store' });
    
    if (!response.ok) {
      throw new Error('Failed to fetch version info');
    }
    
    const data = await response.json();
    
    // If this is the first check, just store the version
    if (!currentVersion) {
      currentVersion = data.version;
      console.log('[ServiceWorker] Current app version:', currentVersion);
      return;
    }
    
    // If version has changed, notify clients to refresh
    if (data.version !== currentVersion) {
      console.log('[ServiceWorker] New version available:', data.version);
      
      const clients = await self.clients.matchAll({ type: 'window' });
      clients.forEach(client => {
        client.postMessage({
          type: 'UPDATE_AVAILABLE',
          version: data.version
        });
      });
      
      currentVersion = data.version;
    }
  } catch (error) {
    console.error('[ServiceWorker] Error checking for updates:', error);
  }
};

// Check for updates every 5 minutes
setInterval(checkForUpdates, 5 * 60 * 1000);

// Initial check
checkForUpdates();

// Listen for messages from clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'CHECK_UPDATE') {
    checkForUpdates();
  }
}); 