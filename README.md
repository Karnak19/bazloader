**English** · [Français](README.fr.md)

# BULLOADER+

BULLOADER+ is an upgrade for the [BULLOADER](https://makerworld.com/models/2680291), a 3D-printed
electric airsoft BB loader published on MakerWorld by its original author. You pick how many BBs you
want, and the loader stops on its own once that many have gone through, counted one by one by an
infrared beam. You set it on the loader itself (a knob and a small OLED screen) or from an Android
web app over Bluetooth. Everything works offline: no account, no cloud, no network needed on the
field.

<img src="https://raw.githubusercontent.com/Karnak19/bulloader-plus/pr-media/pr-35/en-US-1-main.png" width="260" alt="The BULLOADER+ app main screen in demo mode: target 50, presets 30, 50, 120 and 300, GO and STOP buttons">

*The app in demo mode, driving a simulated loader.*

## Links

- **Docs:** <https://karnak19.github.io/bulloader-plus/en/> (French: <https://karnak19.github.io/bulloader-plus/>)
- **The app:** <https://karnak19.github.io/bulloader-plus/app/>. No loader yet? Open
  [`/app/?mock`](https://karnak19.github.io/bulloader-plus/app/?mock) to try it against a
  simulated device.
- **Parts list:** <https://karnak19.github.io/bulloader-plus/en/liste-des-pieces/>
- **Wiring:** <https://karnak19.github.io/bulloader-plus/en/cablage/>
- **BLE protocol:** <https://karnak19.github.io/bulloader-plus/en/protocole-ble/>

## Where it stands

This is a work in progress, and **it has not been built on real hardware yet.**

- Done: the firmware and the app work end to end in simulation, with fake BBs
  ([M1](https://github.com/Karnak19/bulloader-plus/milestone/1),
  [M2](https://github.com/Karnak19/bulloader-plus/milestone/2)).
- In progress: hardware integration, meaning the real servo, the real IR beam and calibration
  ([M3](https://github.com/Karnak19/bulloader-plus/milestone/3)), and the printed parts plus the
  build guide ([M4](https://github.com/Karnak19/bulloader-plus/milestone/4)).

There are no photos of a finished build and no accuracy numbers yet. Follow along in the
[milestones](https://github.com/Karnak19/bulloader-plus/milestones) and
[issues](https://github.com/Karnak19/bulloader-plus/issues).

## What you need

- A printed BULLOADER to upgrade, and the parts in the [parts list](https://karnak19.github.io/bulloader-plus/en/liste-des-pieces/)
  (ESP32-C3 SuperMini, IR LED and phototransistor, encoder, OLED, and a few small bits).
- For the app: **Chrome on Android**, because it uses Web Bluetooth. iPhone and iPad aren't
  supported: Safari has no Web Bluetooth. The loader works fine without a phone.

## What's in the repo

| Folder      | What it is                                                         | Build / check                                                                          |
| ----------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| `firmware/` | ESP32-C3 firmware, PlatformIO + Arduino                            | `pio run` (real IR), `pio run -e sim` (fake BBs), `pio test -e native` (logic tests)   |
| `web/`      | One Astro site: the docs, and the app at `/app/` (Preact)          | `bun install`, `bun run dev`, `bun test`, `bun run build`                              |
| `cad/`      | Parts designed from scratch in build123d (IR sensor collar, etc.)  | `uv run python build.py` (writes STL/STEP to `cad/out/`), `uv run python check.py`     |

Each folder has its own README with the details. [`BRIEF.md`](BRIEF.md) is the full spec (in
French).

## License

The code in this repo and the parts designed here from scratch are under the [MIT license](LICENSE).

The original BULLOADER is under the MakerWorld Exclusive License. Its files, and the remixed
control panel made from them, are not in this repo and never will be. The remix will be published
on MakerWorld only, crediting the original.
