# BULLOADER+ firmware

ESP32-C3 SuperMini, PlatformIO + Arduino. Pins and defaults live in `src/config.h`; BLE constants
in `src/ble_uuids.h` (must match `web/src/content/docs/protocole-ble.md`).

## Build

```sh
pio run              # release: real IR beam
pio run -e sim       # SIMULATE_IR: fake BB pulses, no mechanism needed
pio test -e native   # run logic tests on this computer, no board needed
```

The logic lives in files with no Arduino include, so the `native` env compiles them alone with the
tests in `test/`: the run (state machine, BB counter, servo pulse maths) in `src/run.cpp`, the
battery guard in `src/battery.cpp`, the saved settings (validation, defaults, delayed target save)
in `src/settings.cpp`, the encoder, buttons, presets and what GO or a click does in
`src/controls.cpp`, and what the OLED shows in `src/screen.cpp`. `main.cpp` is the thin Arduino
layer (IR and encoder interrupts, LEDC servo output, battery ADC, simulator, serial commands),
`display.cpp` draws the screen with U8g2, and `nvs_store.cpp` reads and writes NVS.

The first build downloads the toolchain and takes a few minutes.

## Flash and monitor

```sh
pio run -e sim -t upload     # or -e release
pio device monitor           # 115200 baud
```

Serial goes through the C3's native USB (no USB-serial chip on the SuperMini), hence the
`ARDUINO_USB_*` flags in `platformio.ini`.

If the board doesn't show up as a serial port (blank chip, or crashed firmware holding the USB):
hold **BOOT**, press and release **RESET** (or plug it in while holding BOOT), release BOOT, then
upload again. Press RESET after the upload to run it.

## Controls and display

| Control        | Effect                                                                    |
| -------------- | ------------------------------------------------------------------------- |
| Encoder turn   | target ±1 per detent, ±10 when detents come less than 30 ms apart; 1–9999 |
| Encoder click  | next preset (30 → 50 → 120 → 300 → 30); during a run, stop (on the press) |
| Long click     | held 800 ms: reserved for the settings menu, does nothing yet             |
| GO             | start from Prêt, Terminé, Bourrage or Batterie faible; stop otherwise     |

The target can't change during a run, whatever drives it. GO in « Batterie faible » does nothing
while the pack is still low.

The OLED (SSD1306 128×64, I2C on SDA 10 / SCL 20 at 400 kHz, address `OLED_I2C_ADDRESS`) shows the
state in French, the battery (`7.4 V`, `USB`, with a warning triangle when low), and the target at
rest or `count / target` during and after a run. It redraws only when that changes, at most every
100 ms. A full redraw blocks `loop()` for the I2C transfer (~25 ms expected): the boot log and `?`
print the measured time. The stop doesn't wait for it, since the count interrupt cuts the servo on
its own.

If the encoder needs two clicks per step, set `ENCODER_STEPS_PER_DETENT` to 2; if clockwise lowers
the target, set `ENCODER_REVERSE`. If the screen stays dark and the boot log says `oled not found`,
try `OLED_I2C_ADDRESS = 0x3D`.

## Serial commands (still the only way to drive it without the hardware)

| Command | Effect                                                        |
| ------- | ------------------------------------------------------------- |
| `t<n>`  | set the target (clamped to 1–9999, ignored during a run)       |
| `g`     | start a run                                                   |
| `s`     | stop, from any state; the count stays                         |
| `?`     | print state, count, target, battery (`USB` when no pack) and OLED redraw time |
| `c`     | print the settings: servo/run config, presets, saved target    |
| `c<neutral>,<full>,<slow>,<rev>,<n>,<jam>` | set the config, e.g. `c1500,300,100,0,4,1500` (refused during a run or out of range) |
| `P<a>,<b>,<c>,<d>` | set the four presets, each 1–9999                  |
| `p`     | sim only: the next fake BB comes as two pulses 1 ms apart, which must count once |

Every state change is logged with the count, the servo pulse width and LEDC duty. On DONE the log
gives the stop latency (target BB to servo cut), and on the way back to IDLE the overshoot.

In the sim, fake BBs arrive at `SIM_BB_PER_SECOND` only while the servo is commanded to turn, from
a hopper of `SIM_HOPPER_CAPACITY` refilled at each `g`. A target above it ends in JAM.

## Battery

The pack is read on GPIO 0 through the 100k/27k divider every 500 ms (16 ADC samples averaged,
then the median of the last three readings). Below `BATT_WARN_MV` the log shows a warning; below
`BATT_REFUSE_MV` GO is refused and the state is LOW_BATT, which clears only 100 mV higher. During a
run the voltage sags under load, so the run stops (LOW_BATT) only after 2 s below the refusal
threshold. Anything under 3000 mV means USB power with no pack: it reads 0 mV (`USB`) and the
guard is off. Set `BATT_CALIBRATION` after comparing with a multimeter.

## Saved settings (NVS)

The presets, the last target and the config (servo neutral, full and slow offsets, reverse,
slowdown N, jam timeout: the BLE `ConfigV1` blob, version byte included) live in the `bulloader`
`Preferences` namespace and are loaded at boot. Anything missing, of the wrong length or version,
or out of range falls back to the defaults in `config.h`, with a `nvs:` log line. Accepted ranges:
neutral 1000–2000 µs, offsets ±500 µs, reverse 0/1, slowdown N 0–255, jam timeout 300–10000 ms,
presets and target 1–9999.

Presets and config are written only when they change. The target is written 2 s after it stops
changing, so a long encoder spin costs one write. Every write is logged. `pio run -t erase` wipes
it all back to the defaults.

If `CONFIG_VERSION` ever changes, the old blob reads as the wrong version and the defaults apply:
that change must say whether it migrates the old blob or accepts the reset.

## Power

Don't power the board from USB and from the 5 V buck at the same time until you've checked
whether the SuperMini has a protection diode between USB 5 V and the 5V pin. Unplug the LiPo (or
open the main switch) when flashing over USB.
