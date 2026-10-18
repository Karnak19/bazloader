import { defineConfig } from 'vite'
import preact from '@preact/preset-vite'
import { VitePWA } from 'vite-plugin-pwa'

// GitHub Pages serves the site under the repo name.
const base = '/bulloader-plus/'

export default defineConfig({
  base,
  plugins: [
    preact(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      // Manifest icons and the manifest itself are precached by the plugin; the rest comes
      // from globPatterns + includeAssets.
      includeAssets: ['apple-touch-icon-180x180.png'],
      workbox: {
        // Used on airsoft fields with no network: everything must be precached.
        globPatterns: ['**/*.{js,css,html,svg,ico}'],
        navigateFallback: `${base}index.html`,
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
        start_url: base,
        scope: base,
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
