# BULLOADER+ PWA

Vite + Preact + TypeScript. Chrome on Android only (Web Bluetooth).

## Commands

```sh
bun install
bun run dev      # dev server
bun test         # protocol codec tests
bun run build    # tsc --noEmit, then vite build into dist/
bun run preview  # serve dist/ locally
bun run icons    # regenerate PNG icons in public/ from public/favicon.svg
```

## Notes

- **Base path.** GitHub Pages serves the app under `/bulloader-plus/`, so `vite.config.ts` sets
  `base: '/bulloader-plus/'` and the manifest `start_url` / `scope` match it. In dev and preview the
  app is at `http://localhost:5173/bulloader-plus/` (preview: port 4173).
- **Offline.** The service worker precaches the whole app, so after the first load it works with
  no network.
- **BLE protocol.** `src/ble/protocol.ts` must match `docs/ble-protocol.md` and
  `firmware/src/ble_uuids.h`; change all three together.
- **Deployment.** `.github/workflows/deploy-pwa.yml` builds and deploys on every push to `main`
  that touches `pwa/`. In the repo settings, under Pages, set **Source** to **GitHub Actions**
  once, or the deploy job fails.
