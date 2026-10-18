import { defineConfig, minimal2023Preset } from '@vite-pwa/assets-generator/config'

// Regenerate the PNG icons in public/ with `bun run icons` after editing favicon.svg.
export default defineConfig({
  preset: {
    ...minimal2023Preset,
    maskable: { ...minimal2023Preset.maskable, resizeOptions: { background: '#111214' } },
    apple: { ...minimal2023Preset.apple, resizeOptions: { background: '#111214' } },
  },
  images: ['public/favicon.svg'],
})
