import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'astro/config'
import preact from '@astrojs/preact'
import starlight from '@astrojs/starlight'
import AstroPWA from '@vite-pwa/astro'

// GitHub Pages serves the site under the repo name.
const base = '/bulloader-plus/'
// The installable app is the single page /app/. The docs stay outside the service worker's
// scope: they need the network, the app does not.
const appScope = `${base}app/`
const outDir = fileURLToPath(new URL('./dist/', import.meta.url))

// Astro puts the app's and the docs' bundles side by side in _astro/. Keep only the files the app
// page reaches, following imports from file to file, so the docs' scripts and styles stay out of
// the precache. Also maps app/index.html to the URL the browser asks for, app/.
async function keepAppAssets(entries) {
  const reached = new Set()
  const visit = (file) => {
    if (reached.has(file)) return
    reached.add(file)
    const text = readFileSync(`${outDir}${file}`, 'utf8')
    for (const entry of entries) {
      const name = entry.url.split('/').pop()
      if (entry.url.startsWith('_astro/') && text.includes(name)) visit(entry.url)
    }
  }
  visit('app/index.html')
  const manifest = entries
    .filter((e) => !e.url.startsWith('_astro/') || reached.has(e.url))
    .map((e) => (e.url === 'app/index.html' ? { ...e, url: 'app/' } : e))
  return { manifest, warnings: [] }
}

export default defineConfig({
  site: 'https://karnak19.github.io',
  base,
  trailingSlash: 'always',
  integrations: [
    starlight({
      title: 'BULLOADER+',
      description: 'Chargeur de billes BULLOADER+ piloté en Bluetooth',
      defaultLocale: 'root',
      locales: { root: { label: 'Français', lang: 'fr' } },
      favicon: '/favicon.svg',
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/Karnak19/bulloader-plus' },
      ],
      sidebar: [
        { label: 'Application', link: '/app/' },
        { label: 'Protocole BLE', slug: 'protocole-ble' },
        { label: 'Liste des pièces', slug: 'liste-des-pieces' },
        { label: 'Câblage', slug: 'cablage' },
      ],
    }),
    preact(),
    AstroPWA({
      registerType: 'autoUpdate',
      // Registered by hand in src/pages/app.astro: Astro has no index.html to inject into, and a
      // plain register() call saves the workbox-window dependency.
      injectRegister: false,
      // sw.js stays at the site root (same URL as the M0 PWA, so an old install updates to it)
      // but only controls /app/.
      scope: appScope,
      workbox: {
        // Used on airsoft fields with no network: the app page and everything it loads must be
        // precached. Docs pages are left out on purpose.
        globPatterns: ['app/index.html', '_astro/*.{js,css}', '*.{svg,png}'],
        manifestTransforms: [keepAppAssets],
        navigateFallback: appScope,
        navigateFallbackAllowlist: [new RegExp(`^${appScope}`)],
      },
      manifest: {
        name: 'BULLOADER+',
        short_name: 'BULLOADER+',
        description: 'Chargeur de billes BULLOADER+ piloté en Bluetooth',
        lang: 'fr',
        display: 'standalone',
        orientation: 'portrait',
        theme_color: '#111214',
        background_color: '#111214',
        start_url: appScope,
        scope: appScope,
        icons: [
          { src: 'pwa-64x64.png', sizes: '64x64', type: 'image/png' },
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: 'maskable-icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
    }),
  ],
})
