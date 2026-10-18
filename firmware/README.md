# BULLOADER+ firmware

ESP32-C3 SuperMini, PlatformIO + Arduino. Pins and defaults live in `src/config.h`; BLE constants
in `src/ble_uuids.h` (must match `web/src/content/docs/protocole-ble.md`).

## Build

```sh
pio run              # release: real IR beam
pio run -e sim       # SIMULATE_IR: fake BB pulses, no mechanism needed
pio test -e native   # run logic tests on this computer, no board needed
```

The run logic (state machine, BB counter, servo pulse maths) lives in `src/run.cpp` and the
battery guard in `src/battery.cpp`, both with no Arduino include, so the `native` env compiles them
alone with the tests in `test/`. `main.cpp` is the thin Arduino layer: IR interrupt, LEDC servo
output, battery ADC, simulator, serial commands.

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

## Serial commands (temporary, until the OLED and BLE exist)

| Command | Effect                                                        |
| ------- | ------------------------------------------------------------- |
| `t<n>`  | set the target (clamped to 1–9999, ignored during a run)       |
| `g`     | start a run                                                   |
| `s`     | stop, from any state; the count stays                         |
| `?`     | print state, count, target and battery (`USB` when no pack)   |
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

## Power

Don't power the board from USB and from the 5 V buck at the same time until you've checked
whether the SuperMini has a protection diode between USB 5 V and the 5V pin. Unplug the LiPo (or
open the main switch) when flashing over USB.
