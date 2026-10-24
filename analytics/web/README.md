# Vogelring Analyse – Web-App

Vue 3 + Vuetify 3 + TypeScript (Vite). Wird vom Python-Server unter `/app/` ausgeliefert (`WEB_DIR`).

```bash
npm ci
npm run dev      # http://localhost:5173/app/  (Proxy auf http://127.0.0.1:8000 für /api, /viz, /tiles …)
npm run build    # vue-tsc + vite build → dist/
npm test         # vitest (Option-Builder)
```

Aufbau: `src/api/client.ts` (REST), `src/lib/events.ts` (SSE-Live-Spiegel), `src/lib/chartOption.ts` und
`src/lib/mapRender.ts` (Ports der Server-Renderer), `src/stores/*` (Pinia), `src/pages/*` (Hash-Routen), `src/components/*`.
