# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary: the author**, an airsoft player who owns a 3D-printed BULLOADER and builds this upgrade.
- **Next: other BULLOADER makers.** Hobbyists who printed the original loader and want to do the upgrade. They're comfortable with 3D printing, less so with electronics and firmware, so the docs have to carry them through soldering, wiring and calibration.

Their job: load an exact number of BBs into a magazine quickly, without counting by hand.

## Product Purpose

BULLOADER+ upgrades the BULLOADER, an electric airsoft BB loader printed in 3D (MakerWorld #2680291). With it, you choose how many BBs to load and the loader stops on its own once that many have gone through, counted by an infrared beam. It's driven either from the device (encoder + small OLED) or from an Android PWA over Bluetooth Low Energy.

Success: the right number of BBs lands in the mag, set in a few seconds, with or without the phone.

The project ships three things in one public repo: the firmware, the web app, and a docs site that teaches someone else to build it.

## Positioning

- It upgrades a loader people already own. It isn't a new loader.
- Counting is real: an IR beam counts BBs as they pass. It doesn't estimate from motor time.
- Fully offline: no account, no backend, no cloud, works on a field with no network.
- Open source (MIT) for everything designed from scratch.

## Operating Context

- **At the safe zone, during a game day:** between rounds, outdoors, often in direct sunlight, with gloves on. The phone comes out for a few seconds, or it stays in a pocket and the device's own controls are used. No Wi-Fi, no mobile data.
- **At home before a game:** preparing several mags calmly.
- **At the bench, occasionally:** calibration after assembly (servo neutral, speeds, slowdown, jam timeout). Rare, but it must be possible from the app.
- The device and the app can both change the target. The device is the source of truth and the app shows what the device reports.

## Capabilities and Constraints

- **App:** Chrome on Android only (Web Bluetooth). iOS is out of scope, because Safari has no Web Bluetooth. A clear message is shown when Bluetooth is unavailable. The app is installable and works offline after the first visit.
- **Web stack:** one Astro site on GitHub Pages under `/bulloader-plus/`. Starlight docs are at the root. The app is the single page `/app/`, one Preact island holding every screen, because a page change would drop the Bluetooth connection.
- **App screens:**
  - Connect.
  - Main: target, presets, GO/STOP, live count/target, state, battery.
  - Settings: presets, servo calibration with test spins, slowdown N, jam timeout.
  - Plus a disconnect banner with automatic reconnection.
- **Device states:** idle, running, slowdown, done, jam (« bourrage / trémie vide »), low battery, testing. Target 1–9999, 4 presets (default 30 / 50 / 120 / 300).
- **Languages: internationalised from the start.** French and English for the app; French, English, Spanish and German for the docs and the README. French is the original language. Code and identifiers stay in English.
  - *Open decision:* whether the device's OLED is also translated, or stays French only.
- **Keep it simple:** few dependencies, plain CSS, no UI kit.
- **Hardware unknowns** (still being measured): barrel diameter, servo rating, IR signal quality.

## Brand Commitments

- **Name:** BULLOADER+.
- **Attribution:** always credit the original BULLOADER on MakerWorld.
- **License boundary:** the original model is under the MakerWorld Exclusive License. Its files and the remixed control panel must never appear in this repo or on the site; the remix is published only on MakerWorld.
- **Voice:** plain and friendly, maker to maker, no jargon without a short explanation.

## Evidence on Hand

- Real screenshots of the app, driven by the mock device: the `pr-media` branch, PRs #25, #27, #30.
- Docs pages: `web/src/content/docs/` (home, BLE protocol, wiring with an SVG schematic, parts list).
- Collar preview renders: PR #32.

There are no photos of the physical build yet, and no field usage numbers, BB accuracy results or user testimonials. Don't fabricate any of these. Accuracy figures will come from issue #14.

## Product Principles

1. **The device is the truth.** The UI shows what the device reports, never an optimistic guess.
2. **Usable in five seconds, with gloves, in the sun.** Big targets, high contrast, the count readable at arm's length.
3. **Offline or nothing.** Every feature must work on a field with no network.
4. **Teach the build.** The docs exist so a maker who isn't an electronics person can finish the upgrade safely.
5. **Stay small.** Prefer the plainest thing that works over a dependency or an abstraction.

## Accessibility & Inclusion

- **Outdoor legibility:** strong contrast in direct sunlight; dark theme by default.
- **Touch targets:** at least 56 px, usable with gloves.
- **Colour:** never rely on colour alone for state (battery level, errors). Text always accompanies it.
- **Languages:** docs and README in French, English, Spanish and German (French is the source); app in French and English; OLED in French.
