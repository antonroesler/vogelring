import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

const backend = process.env.VITE_BACKEND || 'http://127.0.0.1:8000'

export default defineConfig({
  base: '/app/',
  plugins: [vue(), vuetify({ autoImport: true })],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: {
    port: 5173,
    proxy: Object.fromEntries(['/api', '/viz', '/tiles', '/files', '/reports', '/decks', '/static'].map((p) => [p, { target: backend, changeOrigin: true }])),
  },
  build: { chunkSizeWarningLimit: 2000 },
  test: { environment: 'node' },
} as any)
