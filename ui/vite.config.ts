import { defineConfig, loadEnv } from 'vite'
import type { Connect, ProxyOptions } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'
import { Agent } from 'node:https'
import { fileURLToPath } from 'node:url'
import { VitePWA } from 'vite-plugin-pwa'

const readRoutes = /^\/api\/(?:status|updates|ai\/config|internet\/config|home\/(?:config|devices)|terminal\/(?:status|leds)|voice\/status|shopping\/items(?:\/completed)?|music\/(?:config|library|players|artwork)|timers|calendar-reminders\/(?:family|status))$/
const writeRoutes = /^\/api\/(?:updates\/(?:check|install|auto-on|auto-off)|ai\/models(?:\/test)?|terminal\/leds|conversation\/(?:text|voice|reset)|shopping\/items(?:\/(?:complete|restore|rename|delete))?|music\/(?:play|control)|timers(?:\/[a-f0-9]{32}\/cancel)?|calendar-reminders\/family)$/
const restrictAlfredApi: Connect.NextHandleFunction = (request, response, next) => {
  const path = request.url?.split('?')[0] ?? ''
  if (!path.startsWith('/api/')) return next()
  if ((request.method === 'GET' && readRoutes.test(path)) ||
      (request.method === 'PATCH' && request.url === '/api/home/devices') ||
      (request.method === 'POST' && writeRoutes.test(path) &&
        (path !== '/api/conversation/voice' || request.url === path))) return next()
  response.writeHead(404, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' })
  response.end(JSON.stringify({ detail: 'Route indisponible pour cette application.' }))
}
const backend = (target: string): ProxyOptions => ({
  // Garder Host et Origin de la PWA : FastAPI contrôle leur concordance.
  target,
  agent: new Agent({
    ca: readFileSync(new URL('../.local/https/server.crt', import.meta.url)),
    keepAlive: true,
  }),
  configure(proxy) {
    proxy.on('proxyReq', forwarded => {
      forwarded.removeHeader('x-alfred-wake-source')
      forwarded.removeHeader('x-alfred-wake-turn')
      forwarded.removeHeader('x-alfred-wake-strict')
    })
  },
})
const network = (host: string, target: string) => ({
  host,
  port: 5173,
  strictPort: true,
  https: {
    cert: readFileSync(new URL('../.local/https/ui-server.crt', import.meta.url)),
    key: readFileSync(new URL('../.local/https/ui-server.key', import.meta.url)),
  },
  proxy: { '/api/': backend(target) },
})

export default defineConfig(({ command, isPreview, mode }) => {
  const config = loadEnv(mode, fileURLToPath(new URL('.', import.meta.url)), 'ALFRED_UI_')
  const options = command === 'serve' || isPreview ? network(
    config.ALFRED_UI_HOST || '127.0.0.1',
    config.ALFRED_UI_BACKEND || 'https://127.0.0.1:8765',
  ) : undefined

  return {
    plugins: [{
      name: 'alfred-api-access',
      configureServer(server) { server.middlewares.use(restrictAlfredApi) },
      configurePreviewServer(server) {
        server.middlewares.use(restrictAlfredApi)
        server.middlewares.use((request, response, next) => {
          if (request.url !== '/dev-sw.js?dev-sw') return next()
          // Les PWA déjà installées vérifient encore l'URL de leur ancien worker.
          response.writeHead(200, { 'Content-Type': 'application/javascript', 'Cache-Control': 'no-cache' })
          response.end("importScripts('/sw.js'); self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));")
        })
      },
    }, react(), VitePWA({
      registerType: 'prompt',
      injectRegister: false,
      manifest: {
        id: '/',
        name: 'Alfred — Assistant personnel',
        short_name: 'Alfred',
        description: 'Votre conversation avec Alfred.',
        lang: 'fr',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        theme_color: '#212121',
        background_color: '#212121',
        icons: [
          { src: '/icons/alfred-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: '/icons/alfred-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: '/icons/alfred-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // Uniquement le shell compilé ; aucune conversation, API ou audio en cache.
        globPatterns: ['**/*.{js,css,html,png}'],
        navigateFallbackDenylist: [/^\/api\//, /^\/alfred-local-ca\.crt$/],
        runtimeCaching: [],
        cleanupOutdatedCaches: true,
      },
      // L'installation est disponible sur le serveur 5173 utilisé actuellement.
      devOptions: { enabled: true, navigateFallback: 'index.html' },
    })],
    server: { ...options, fs: { allow: [
      fileURLToPath(new URL('.', import.meta.url)),
      ...['conversation-stream.mjs', 'audio-utils.mjs', 'speech-turn.mjs', 'recorder-worklet.js'].map(name =>
        fileURLToPath(new URL('../alfred/static/' + name, import.meta.url))),
    ] } },
    preview: options,
  }
})
