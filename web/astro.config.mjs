import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'astro/config'
import preact from '@astrojs/preact'
import starlight from '@astrojs/starlight'
import AstroPWA from '@vite-pwa/astro'

// GitHub Pages serves the site under the repo name.
const base = '/bazloader/'
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
  // Starlight prefixes every sidebar link with the locale, so the English sidebar's « App » points
  // to /en/app/ (and likewise /es/app/, /de/app/). There is one app for every language (it picks
  // its own, French or English), so send those back to it. The destination needs the base; the
  // source doesn't.
  redirects: { '/en/app/': appScope, '/es/app/': appScope, '/de/app/': appScope },
  integrations: [
    starlight({
      title: 'BazLoader',
      description: 'Chargeur de billes BazLoader piloté en Bluetooth',
      // French is the original and stays at the root, so its URLs don't change. English, Spanish and
      // German are under /en/, /es/ and /de/, with the same file names: that is how the language
      // picker pairs the pages.
      defaultLocale: 'root',
      locales: {
        root: { label: 'Français', lang: 'fr' },
        en: { label: 'English', lang: 'en' },
        es: { label: 'Español', lang: 'es' },
        de: { label: 'Deutsch', lang: 'de' },
      },
      favicon: '/favicon.svg',
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/Karnak19/bazloader' },
      ],
      sidebar: [
        // The app is one page for every language: it picks its own (see src/i18n/).
        { label: 'Application', translations: { en: 'App', es: 'Aplicación', de: 'App' }, link: '/app/' },
        {
          label: 'Protocole BLE',
          translations: { en: 'BLE protocol', es: 'Protocolo BLE', de: 'BLE-Protokoll' },
          slug: 'protocole-ble',
        },
        {
          label: 'Liste des pièces',
          translations: { en: 'Parts list', es: 'Lista de piezas', de: 'Stückliste' },
          slug: 'liste-des-pieces',
        },
        { label: 'Câblage', translations: { en: 'Wiring', es: 'Cableado', de: 'Verkabelung' }, slug: 'cablage' },
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
        // precached, fonts included. Docs pages are left out on purpose.
        globPatterns: ['app/index.html', '_astro/*.{js,css}', '*.{svg,png}', 'fonts/*.woff2'],
        manifestTransforms: [keepAppAssets],
        navigateFallback: appScope,
        navigateFallbackAllowlist: [new RegExp(`^${appScope}`)],
      },
      manifest: {
        name: 'BazLoader',
        short_name: 'BazLoader',
        description: 'Chargeur de billes BazLoader piloté en Bluetooth',
        lang: 'fr',
        display: 'standalone',
        orientation: 'portrait',
        // The dark theme's ground. The page updates its own theme-color per theme at runtime.
        theme_color: '#0b0c0e',
        background_color: '#0b0c0e',
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
