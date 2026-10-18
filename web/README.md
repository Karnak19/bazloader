# BULLOADER+ web

One Astro site: the Starlight docs at the root, and the app as a single page, `/app/`, with one
Preact island. The app targets Chrome on Android only (Web Bluetooth).

## Commands

```sh
bun install
bun run dev      # dev server
bun test         # protocol codec tests
bun run build    # astro sync, tsc --noEmit, then astro build into dist/
bun run preview  # serve dist/ locally
bun run icons    # regenerate PNG icons in public/ from public/favicon.svg
```

## Layout

- `src/content/docs/`: the docs pages (Markdown). The UI is in French.
- `src/pages/app.astro`: the app page. It mounts `src/app.tsx` with `client:only="preact"`,
  because `navigator.bluetooth` does not exist at build time.
- `src/ble/protocol.ts`: UUIDs and byte codecs.

## Notes

- **One page for the app.** In Astro, changing page is a full page load, which drops the Web
  Bluetooth connection. All the app's screens live inside the one island, which switches between
  them itself.
- **Base path.** GitHub Pages serves the site under `/bulloader-plus/`, so `astro.config.mjs` sets
  `base: '/bulloader-plus/'`. Links in Markdown must include it. In dev and preview the site is at
  `http://localhost:4321/bulloader-plus/`.
- **Offline.** `@vite-pwa/astro` builds the manifest and `sw.js`. Both the manifest's `start_url`
  / `scope` and the service worker's scope are `/bulloader-plus/app/`, and the precache holds only
  the app page and the files it loads. The docs always come from the network.
- **BLE protocol.** `src/ble/protocol.ts` must match `src/content/docs/protocole-ble.md` and
  `firmware/src/ble_uuids.h`; change all three together.
- **Deployment.** `.github/workflows/deploy-web.yml` builds and deploys on every push to `main`
  that touches `web/`. In the repo settings, under Pages, set **Source** to **GitHub Actions**
  once, or the deploy job fails.
