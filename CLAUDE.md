# BULLOADER+

Electric airsoft BB loader upgrade: load an exact number of BBs, counted by an IR beam, driven by an
encoder + OLED on the device and by an Android PWA over Bluetooth Low Energy. `BRIEF.md` is the
full spec; read it before any non-trivial change. `PRODUCT.md` holds the product context (users,
field conditions, principles) for any UI or docs work.

## Layout

- `firmware/`: ESP32-C3 SuperMini, PlatformIO + Arduino. All pins and tunable defaults live in
  `firmware/src/config.h`.
- `web/`: one Astro site on GitHub Pages. Starlight docs at the root, and the app (Chrome Android
  only) as the single page `/app/`, one Preact island that holds every screen.
- `cad/`: build123d parts. All dimensions live in `cad/params.py`.
- Docs (BLE protocol, wiring, calibration notes) are Starlight pages in `web/src/content/docs/`.

## Commands

| Where       | Build / check                                                    |
| ----------- | ---------------------------------------------------------------- |
| `firmware/` | `pio run` (real IR), `pio run -e sim` (fake BBs), `pio test -e native` (logic tests) |
| `web/`      | `bun install`, `bun run build`, `bun test`, `bun run dev`        |
| `cad/`      | `uv run python build.py` (writes STL/STEP to `cad/out/`)         |

## Rules

- **The BLE protocol has one source of truth: `web/src/content/docs/protocole-ble.md`.** Any
  change to it must update `firmware/src/ble_uuids.h` and `web/src/ble/protocol.ts` in the same
  change.
- **The ESP32 owns the state.** The PWA only sends requests and renders what the device notifies.
- **Works offline.** No network call at runtime, no backend, no Wi-Fi on the ESP32.
- **Keep it simple.** Few dependencies, plain code, no abstractions until a second use exists.
- Code, identifiers and comments in English. The app and the docs are in French and English
  (French is the original; see `PRODUCT.md`). The OLED is French only for now.
- **License:** the original BULLOADER is under the MakerWorld Exclusive License. Never commit its
  files or the remixed control panel; they go in `cad/original/` and `cad/remix/`, which are
  gitignored. Parts designed from scratch (IR collar, electronics cradle) are fine to commit.
